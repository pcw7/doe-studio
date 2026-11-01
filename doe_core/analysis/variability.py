"""산포 분석 — Minitab 'Pre-Process Responses for Analyze Variability' 와 'Analyze Variability'(최소제곱).

문서(Example, Methods and formulas: model information · goodness-of-fit)
- 모형: ln(σ) = Aγ. 최소제곱(기본)은 ln(s) 의 가중 회귀, 가중치 w_i = 4 / ψ'(ν_i / 2)
  (ψ' = 삼감마 함수, ν_i = 표준편차의 자유도 = 개수 − 1). 개수 열이 없으면 가중치 1.
- 효과 = 2 × 계수(2수준 항), Ratio Effect = exp(Effect).
- −2lnL(최소제곱) = n·ln(R/n) + n + n·ln(2π) − Σln(w_i).
- 전처리: 한 행의 반복 응답 열들 → 행별 표준편차·개수 / 한 열의 반복 런(같은 요인 설정, 블록 안) → 표준편차를 그 설정의
  첫 행에만 저장하고 나머지 행은 결측 / 이미 있는 표준편차·개수 열.
- 출력: Method(Estimation | Least squares), Coded Coefficients for Ln(Std)(Effect, Ratio Effect, Coef, SE Coef, T, P, VIF),
  Model Summary for Ln(Std), Analysis of Variance for Ln(Std), Regression Equation in Uncoded Units(Ln(Std) = …).

검증: 문서 예제(InsulationStrength, 2차, N = 6)의 Method·계수표(Ratio Effect 포함)·모형 요약·분산분석표·회귀식·별칭 구조가
글자 단위로 일치(원자료가 없어 표 숫자로부터 런별 ln(Std) 를 역산). 가중 회귀는 statsmodels WLS 와 일치.

문서에 없어 정한 것
- 반복 런의 '첫 행' 은 런 순서가 가장 앞선 행. 개수가 1 이하라 표준편차를 구할 수 없으면 결측.
- Ratio Effect 는 Effect 와 같은 소수 자리(문서 예제 0.3830 / −0.9598).
- 단계적 선택은 가중 회귀로 같은 규칙(포화 모형 ¼ 선제거 포함). 최대우도와 함께는 쓸 수 없다.

최대우도(Maximum likelihood, 문서 'Specify the options', 'Coded coefficients table', 'Model summary table', 우도식 이미지)
- 원자료가 정규분포라고 보고 s² 가 σ²·χ²_ν/ν 를 따른다. −2lnL = Σ[2lnΓ(ν/2) + ν·ln2 − (ν−2)·ln(νs²) + 2ν·x'β + νs²·e^(−2x'β)].
- 계수표는 T 대신 Z-Value, 모형 요약·분산분석표는 표시하지 않는다. 포화 모형에서는 최소제곱과 같은 계수.
- 표준편차가 0 인 런도 쓸 수 있다(최소제곱은 ln 0 이라 불가).
문서에 없어 정한 것: 뉴턴법(관측 정보, 안 되면 기대 정보 Σ2ν·xx' 의 Fisher scoring, 목적함수가 줄 때까지 보폭 반감), SE = √diag((X'·diag(2ν)·X)⁻¹)(포화 모형에서는 관측 정보와 같음),
시작값은 s > 0 인 런의 ln s 가중 최소제곱. 개수(count) 열이 있어야 한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import special

from . import fmt
from .factorial import FactorialAnalysis, _build, _prepare, _prepare_w
from .model import factorial_terms


def weights_from_counts(counts) -> np.ndarray:
    """개수 → 가중치 4/ψ'((n−1)/2). 개수가 2 미만이면 nan."""
    n = np.asarray(counts, dtype=float)
    nu = n - 1
    with np.errstate(invalid="ignore"):
        w = np.where(nu > 0, 4.0 / special.polygamma(1, np.where(nu > 0, nu, 1.0) / 2), np.nan)
    return w


# ---------------------------------------------------------------- 전처리


def repeat_std(ws, columns: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """한 행의 반복 응답 열들(2개 이상)의 표준편차·개수. 값은 표준 순서(StdOrder) 행 순서."""
    if len(columns) < 2:
        raise ValueError("반복 응답 열은 2개 이상이어야 합니다.")
    M = np.column_stack([ws.column(c).astype(float).values for c in columns])
    cnt = np.sum(np.isfinite(M), axis=1).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        sd = np.nanstd(np.where(np.isfinite(M), M, np.nan), axis=1, ddof=1)
    sd[cnt < 2] = np.nan
    return sd, cnt


def replicate_std(ws, response: str) -> tuple[np.ndarray, np.ndarray]:
    """한 열의 반복 런(같은 요인 설정·블록)의 표준편차·개수. 각 설정의 첫 런(런 순서) 행에만 값, 나머지는 결측."""
    d = ws.design
    coded = d.coded.reset_index(drop=True)
    y = ws.column(response).astype(float).values
    key_cols = list(d.letters) + (["Blocks"] if "Blocks" in coded else [])
    g = coded[key_cols].astype(str).agg("|".join, axis=1).values
    order = coded["RunOrder"].values if "RunOrder" in coded else np.arange(len(coded))
    sd = np.full(len(coded), np.nan)
    cnt = np.full(len(coded), np.nan)
    for key in pd.unique(g):
        idx = np.where(g == key)[0]
        vals = y[idx][np.isfinite(y[idx])]
        first = idx[np.argmin(order[idx])]
        cnt[first] = len(vals)
        if len(vals) >= 2:
            sd[first] = float(np.std(vals, ddof=1))
    return sd, cnt


def store_preprocessed(ws, sd: np.ndarray, cnt: np.ndarray, std_name: str, count_name: str | None = None) -> None:
    """전처리 결과를 워크시트 열로 저장(값은 design.coded 행 순서)."""
    keys = ws.design.coded["StdOrder"].values
    order = np.argsort(keys)
    ws.add_column(std_name, list(np.asarray(sd)[order]), order="std")
    if count_name:
        ws.add_column(count_name, list(np.asarray(cnt)[order]), order="std")


# ---------------------------------------------------------------- 분석


@dataclass
class VariabilityAnalysis(FactorialAnalysis):
    """ln(표준편차) 가중 회귀(Least squares) 결과."""

    is_variability = True

    @property
    def response_label(self) -> str:
        return f"Ln({self.response})"

    @property
    def y_original(self) -> np.ndarray:
        return np.exp(self.y)

    def to_original(self, z):
        return np.exp(z)

    def method_table(self) -> pd.DataFrame:
        return pd.DataFrame([{"Method": "Estimation", "Value": "Least squares"}])

    def coefficients_title(self) -> str:
        return f"Coded Coefficients for {self.response_label}"

    def summary_title(self) -> str:
        return f"Model Summary for {self.response_label}"

    def anova_title(self) -> str:
        return f"Analysis of Variance for {self.response_label}"

    def coefficients_table(self, expanded: bool = False, confidence: float = 0.95) -> pd.DataFrame:
        out = super().coefficients_table(expanded, confidence)
        if "Effect" not in out.columns:
            return out
        c = self.coefficients()
        ratio = ["" if np.isnan(e) else fmt.by_se(float(np.exp(e)), se) for e, se in zip(c["Effect"], c["SE Coef"])]
        out.insert(out.columns.get_loc("Effect") + 1, "Ratio Effect", ratio)
        return out


def fit_variability_ml(X: np.ndarray, s: np.ndarray, nu: np.ndarray, *, max_iter: int = 200, tol: float = 1e-12):
    """ln σ = Xβ 의 최대우도(Fisher scoring). (β, 작업 반응 z, 가중치 2ν)."""
    W = 2.0 * nu
    pos = s > 0
    if not np.any(pos):
        raise ValueError("표준편차가 모두 0 이라 추정할 수 없습니다.")
    start = np.where(pos, np.log(np.where(pos, s, 1.0)), np.log(np.min(s[pos])) - 1.0)
    sw = np.sqrt(W)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], start * sw, rcond=None)
    s2 = s ** 2
    XtW = X.T * W

    def objective(b):                               # −2lnL 에서 β 에 달린 부분: Σ ν(2η + s²e^(−2η))
        eta = X @ b
        return float(np.sum(nu * (2 * eta + s2 * np.exp(-2 * eta))))

    f = objective(beta)
    for _ in range(max_iter):
        eta = X @ beta
        r = s2 * np.exp(-2 * eta)
        grad = X.T @ (nu * (r - 1))                 # lnL 의 기울기
        H = (X.T * (2 * nu * r)) @ X                # 관측 정보(뉴턴); 특이하면 기대 정보(Fisher scoring)
        try:
            step = np.linalg.solve(H, grad)
            if not np.all(np.isfinite(step)) or float(step @ grad) <= 0:
                raise np.linalg.LinAlgError
        except np.linalg.LinAlgError:
            step = np.linalg.solve(XtW @ X, grad)
        t = 1.0
        while t > 1e-10:                            # 목적함수가 줄어들 때까지 보폭을 반으로
            cand = beta + t * step
            fc = objective(cand)
            if np.isfinite(fc) and fc <= f + 1e-12 * abs(f):
                break
            t /= 2
        else:
            raise ValueError("최대우도 추정이 수렴하지 않았습니다.")
        done = np.max(np.abs(cand - beta)) < tol
        beta, f = cand, fc
        if done:
            break
    else:
        raise ValueError("최대우도 추정이 수렴하지 않았습니다.")
    eta = X @ beta
    return beta, eta + (s2 * np.exp(-2 * eta) - 1) / 2, W


@dataclass
class VariabilityMLAnalysis(VariabilityAnalysis):
    """ln(표준편차)의 최대우도 결과. y·weights 는 수렴점의 작업 반응·가중치 2ν(계수·SE·VIF·회귀식 재사용)."""
    std_values: np.ndarray = field(default=None, repr=False)

    is_ml = True

    @property
    def df_error(self) -> int:                      # Z 검정(정규)
        return 10 ** 9

    @property
    def mse(self) -> float:
        return 1.0

    @property
    def y_original(self) -> np.ndarray:
        return self.std_values

    def method_table(self) -> pd.DataFrame:
        return pd.DataFrame([{"Method": "Estimation", "Value": "Maximum likelihood"}])

    def coefficients_table(self, expanded: bool = False, confidence: float = 0.95) -> pd.DataFrame:
        return super().coefficients_table(expanded, confidence).rename(columns={"T-Value": "Z-Value"})

    def summary_table(self, expanded: bool = False):
        raise ValueError("최대우도 추정에서는 모형 요약을 표시하지 않습니다.")

    def anova_table(self, seq_ss: bool = False):
        raise ValueError("최대우도 추정에서는 분산분석표를 표시하지 않습니다.")


def analyze_variability(ws, std_column: str, counts_column: str | None = None, *, order: int | None = 2,
                        terms: list[str] | None = None, include_blocks: bool | None = None,
                        stepwise=None, method: str = "ls") -> VariabilityAnalysis:
    """표준편차 열(전처리 결과)로 산포 분석. counts_column 이 있으면 가중치 4/ψ'((n−1)/2).
    method: 'ls'(최소제곱, 기본) / 'ml'(최대우도, 개수 열 필요)."""
    if method == "ml":
        return _analyze_variability_ml(ws, std_column, counts_column, order=order, terms=terms,
                                       include_blocks=include_blocks, stepwise=stepwise)
    if method != "ls":
        raise ValueError("추정 방법은 'ls' 또는 'ml' 입니다.")
    from ..designs.definitive_screening import DefinitiveScreeningDesign
    from ..designs.mixture import MixtureDesign
    from ..designs.response_surface import ResponseSurfaceDesign
    from ..designs.split_plot import SplitPlotDesign
    d = ws.design
    if isinstance(d, (ResponseSurfaceDesign, DefinitiveScreeningDesign, MixtureDesign, SplitPlotDesign)) or \
            type(d).__name__ == "TaguchiDesign":
        raise ValueError("산포 분석은 요인설계(2수준·Plackett-Burman·일반 완전요인)에서만 쓸 수 있습니다.")
    s = ws.column(std_column).astype(float).values
    if np.any(s[np.isfinite(s)] <= 0):
        raise ValueError("표준편차는 모두 양수여야 합니다(ln 을 씁니다).")
    with np.errstate(divide="ignore", invalid="ignore"):
        y = np.log(s)
    w = None
    if counts_column:
        w = weights_from_counts(ws.column(counts_column).astype(float).values)
        w = np.where(np.isfinite(y), w, np.nan)
    coded, yv, used, cov, wv = _prepare_w(d, y, {}, w)
    if len(yv) < 2:
        raise ValueError("분석할 표준편차가 2개 이상 있어야 합니다.")
    tl = factorial_terms(d, order=order, terms=terms, include_blocks=include_blocks, include_center=False,
                         blocks_present=coded["Blocks"].nunique() > 1, center_present=False)
    if stepwise is not None and getattr(stepwise, "active", False):
        from .stepwise import select_model
        a = select_model(d, std_column, coded, yv, used, tl, {}, stepwise, factorial=True, weights=wv)
    else:
        a = _build(d, std_column, coded, yv, used, tl, {}, weights=wv)
    v = VariabilityAnalysis(a.design, a.response, a.y, a.used_rows, a.terms, a.removed_terms, a.X,
                            a.col_labels, a.col_term, a.covariates, weights=a.weights)
    v.selection = a.selection
    return v


def _analyze_variability_ml(ws, std_column, counts_column, *, order, terms, include_blocks, stepwise):
    from ..designs.definitive_screening import DefinitiveScreeningDesign
    from ..designs.mixture import MixtureDesign
    from ..designs.response_surface import ResponseSurfaceDesign
    from ..designs.split_plot import SplitPlotDesign
    d = ws.design
    if isinstance(d, (ResponseSurfaceDesign, DefinitiveScreeningDesign, MixtureDesign, SplitPlotDesign)) or \
            type(d).__name__ == "TaguchiDesign":
        raise ValueError("산포 분석은 요인설계(2수준·Plackett-Burman·일반 완전요인)에서만 쓸 수 있습니다.")
    if stepwise is not None and getattr(stepwise, "active", False):
        raise ValueError("최대우도 추정에는 단계적 선택을 쓸 수 없습니다(최소제곱으로 항을 고른 뒤 최대우도로 추정하세요).")
    if not counts_column:
        raise ValueError("최대우도 추정에는 개수(count) 열이 필요합니다.")
    s = ws.column(std_column).astype(float).values
    if np.any(s[np.isfinite(s)] < 0):
        raise ValueError("표준편차는 0 이상이어야 합니다.")
    nu = ws.column(counts_column).astype(float).values - 1
    ok = np.isfinite(s) & np.isfinite(nu) & (nu > 0)
    dummy = np.where(ok, 0.0, np.nan)
    coded, _, used, _ = _prepare(d, dummy, {})
    if len(used) < 2:
        raise ValueError("분석할 표준편차가 2개 이상 있어야 합니다.")
    tl = factorial_terms(d, order=order, terms=terms, include_blocks=include_blocks, include_center=False,
                         blocks_present=coded["Blocks"].nunique() > 1, center_present=False)
    base = _build(d, std_column, coded, np.zeros(len(used)), used, tl, {})
    sv, nv = s[used], nu[used]
    beta, z, W = fit_variability_ml(base.X, sv, nv)
    return VariabilityMLAnalysis(d, std_column, z, used, base.terms, base.removed_terms, base.X, base.col_labels,
                                 base.col_term, {}, weights=W, std_values=sv)
