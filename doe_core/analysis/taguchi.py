"""Taguchi 분석 — Minitab 'Analyze Taguchi Design'(정적 설계).

- 반응 열 여러 개(잡음 조건·반복)를 런마다 묶어 특성값을 만든다:
  S/N 비(Larger is better = −10·log10(Σ(1/y²)/n), Smaller is better = −10·log10(Σy²/n),
  Nominal is best = 10·log10(ȳ²/s²), Nominal is best(−10·log10(s²))), 평균, 표준편차, ln(표준편차).
- 특성값마다 선형 모형(기본: 주효과, 교호작용 선택 가능)을 적합. 요인은 효과 코딩(마지막 수준이 −1)이라
  계수 = 그 수준 평균 − 전체 평균. 계수표 항 이름은 '요인명(8자) 수준값'(예: 'Material Liquid', 'Thicknes 0.03'),
  교호작용은 'Material*Diameter Liquid 118'. 분산분석표는 항 → Residual Error → Total(그룹 행 없음).
- 반응표(Response Table): 요인 수준별 특성값 평균, Delta = 최대 − 최소, Rank 1 = 가장 큰 Delta.

표시 형식(문서 GolfBall 예제 값에서 역추적, Minitab 의 예전 출력 형식)
- SE Coef 유효숫자 4자리, Coef 는 SE 보다 소수 한 자리 적게, T·P 소수 3자리, F 소수 2자리, S 소수 4자리,
  R-Sq 백분율 소수 2자리. Seq SS·Adj SS·Adj MS 열은 열에서 가장 작은 값이 유효숫자 4자리가 되는 소수 자리
  (3.273·94.427·413.083 / 1049·10871·49465 / 1.637 / 524.6·10870.8). 반응표는 소수 2자리.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import combinations, product

import numpy as np
import pandas as pd
from scipy import stats

from . import fmt

SN_TYPES = {
    "larger": "Larger is better",
    "smaller": "Smaller is better",
    "nominal": "Nominal is best (10*Log10(Ybar**2/s**2))",
    "nominal_s": "Nominal is best (-10*Log10(s**2))",
}
CHARACTERISTICS = {"sn": "SN ratios", "mean": "Means", "std": "StDevs", "lnstd": "Ln(StDevs)"}
RESPONSE_TITLES = {"sn": "Response Table for Signal to Noise Ratios", "mean": "Response Table for Means",
                   "std": "Response Table for Standard Deviations",
                   "lnstd": "Response Table for Natural Log of Standard Deviations"}


def sn_ratio(Y, kind: str = "larger") -> np.ndarray:
    """런별 S/N 비. Y: 런 × 반복(빈 칸 NaN 허용)."""
    Y = np.atleast_2d(np.asarray(Y, dtype=float))
    out = np.full(len(Y), np.nan)
    for i, row in enumerate(Y):
        y = row[np.isfinite(row)]
        if not len(y):
            continue
        if kind == "larger":
            out[i] = -10 * np.log10(np.mean(1 / y ** 2)) if np.all(y != 0) else np.nan
        elif kind == "smaller":
            out[i] = -10 * np.log10(np.mean(y ** 2))
        elif kind in ("nominal", "nominal_s"):
            if len(y) < 2:
                continue
            s2 = np.var(y, ddof=1)
            if s2 <= 0:
                continue
            out[i] = 10 * np.log10(np.mean(y) ** 2 / s2) if kind == "nominal" else -10 * np.log10(s2)
        else:
            raise ValueError(f"S/N 종류는 {list(SN_TYPES)} 중 하나입니다.")
    return out


def characteristic_values(Y, characteristic: str, sn_type: str = "larger") -> np.ndarray:
    Y = np.atleast_2d(np.asarray(Y, dtype=float))
    if characteristic == "sn":
        return sn_ratio(Y, sn_type)
    with np.errstate(invalid="ignore", divide="ignore"):
        if characteristic == "mean":
            return np.nanmean(Y, axis=1)
        sd = np.nanstd(Y, axis=1, ddof=1)
        if characteristic == "std":
            return sd
        if characteristic == "lnstd":
            return np.log(sd)
    raise ValueError(f"특성은 {list(CHARACTERISTICS)} 중 하나입니다.")


def _val(v) -> str:
    return f"{v:g}" if isinstance(v, (int, float, np.integer, np.floating)) else str(v)


def _effect_columns(codes: np.ndarray, n_levels: int) -> np.ndarray:
    cols = np.zeros((len(codes), n_levels - 1))
    for j in range(n_levels - 1):
        cols[:, j] = np.where(codes == j + 1, 1.0, np.where(codes == n_levels, -1.0, 0.0))
    return cols


def parse_terms(design, specs) -> list[tuple[str, ...]]:
    """'A', 'AB', 'A*B', 'Material', 'Material*Diameter' → 요인 문자 튜플."""
    names = {f.name: L for L, f in zip(design.letters, design.factors)}
    out = []
    for s in specs:
        s = str(s).strip()
        parts = [p.strip() for p in s.split("*")] if "*" in s else ([s] if s in names or len(s) == 1 else list(s))
        letters = tuple(names.get(p, p) for p in parts)
        if any(L not in design.letters for L in letters) or len(set(letters)) != len(letters):
            raise ValueError(f"항을 해석할 수 없습니다: {s!r}")
        out.append(tuple(sorted(letters, key=design.letters.index)))
    return list(dict.fromkeys(out))


@dataclass
class TaguchiAnalysis:
    design: object
    characteristic: str
    y: np.ndarray
    terms: list[tuple[str, ...]]
    sn_type: str | None = None
    X: np.ndarray = field(init=False)
    col_labels: list[str] = field(init=False)
    col_term: list[int] = field(init=False)
    beta: np.ndarray = field(init=False)

    def __post_init__(self):
        d = self.design
        coded = d.coded.reset_index(drop=True)
        fac = dict(zip(d.letters, d.factors))
        cols, labels, owner = [np.ones((len(coded), 1))], ["Constant"], [-1]
        for ti, t in enumerate(self.terms):
            parts = [(_effect_columns(coded[L].values.astype(int), len(fac[L].levels)), fac[L]) for L in t]
            for combo in product(*[range(p[0].shape[1]) for p in parts]):
                col = np.ones(len(coded))
                for (mat, _), j in zip(parts, combo):
                    col = col * mat[:, j]
                cols.append(col[:, None])
                name = "*".join(f.name[:8] for _, f in parts)
                lv = " ".join(_val(f.levels[j]) for (_, f), j in zip(parts, combo))
                labels.append(f"{name} {lv}")
                owner.append(ti)
        X = np.hstack(cols)
        ok = np.isfinite(self.y)
        if not ok.all():
            raise ValueError("특성값이 비어 있는 런이 있습니다(반응 값을 확인하세요).")
        if X.shape[1] > len(self.y):
            raise ValueError("모형 항이 런 수보다 많습니다.")
        if np.linalg.matrix_rank(X) < X.shape[1]:
            raise ValueError("이 배열로는 선택한 항을 모두 추정할 수 없습니다(교호작용 열이 겹침).")
        self.X, self.col_labels, self.col_term = X, labels, owner
        self.cov_unscaled = np.linalg.inv(X.T @ X)
        self.beta = self.cov_unscaled @ X.T @ self.y
        self.fitted = X @ self.beta
        self.resid = self.y - self.fitted

    # ------------------------------------------------------------ 통계량
    @property
    def label(self) -> str:
        return CHARACTERISTICS[self.characteristic]

    @property
    def n(self) -> int:
        return len(self.y)

    @property
    def p(self) -> int:
        return self.X.shape[1]

    @property
    def df_error(self) -> int:
        return self.n - self.p

    @property
    def sse(self) -> float:
        return float(self.resid @ self.resid)

    @property
    def sst(self) -> float:
        return float(np.sum((self.y - self.y.mean()) ** 2))

    @property
    def mse(self) -> float | None:
        return self.sse / self.df_error if self.df_error > 0 else None

    def _sse_without(self, cols: list[int]) -> float:
        keep = [j for j in range(self.p) if j not in cols]
        Xr = self.X[:, keep]
        b, *_ = np.linalg.lstsq(Xr, self.y, rcond=None)
        r = self.y - Xr @ b
        return float(r @ r)

    def _cols(self, ti: int) -> list[int]:
        return [j for j, t in enumerate(self.col_term) if t == ti]

    # ------------------------------------------------------------ 표
    def coefficients_title(self) -> str:
        return f"Estimated Model Coefficients for {self.label}"

    def anova_title(self) -> str:
        return f"Analysis of Variance for {self.label}"

    def coefficients_table(self) -> pd.DataFrame:
        se = np.sqrt(np.diag(self.cov_unscaled) * self.mse) if self.mse else np.full(self.p, np.nan)
        rows = []
        for lab, b, s in zip(self.col_labels, self.beta, se):
            if np.isfinite(s) and s > 0:
                se_dec = fmt.decimals_for_sig(s, 4)
                t = b / s
                p = 2 * stats.t.sf(abs(t), self.df_error)
                rows.append({"Term": lab, "Coef": fmt.fixed(b, max(0, se_dec - 1)), "SE Coef": fmt.fixed(s, se_dec),
                             "T": f"{t:.3f}", "P": f"{p:.3f}"})
            else:
                rows.append({"Term": lab, "Coef": f"{b:.4f}", "SE Coef": fmt.MISSING, "T": fmt.MISSING, "P": fmt.MISSING})
        return pd.DataFrame(rows)

    def summary_table(self) -> pd.DataFrame:
        r2 = 1 - self.sse / self.sst
        if self.mse is None:
            return pd.DataFrame([{"S": fmt.MISSING, "R-Sq": f"{100 * r2:.2f}%", "R-Sq(adj)": fmt.MISSING}])
        adj = max(0.0, 1 - self.mse / (self.sst / (self.n - 1)))
        return pd.DataFrame([{"S": f"{math.sqrt(self.mse):.4f}", "R-Sq": f"{100 * r2:.2f}%",
                              "R-Sq(adj)": f"{100 * adj:.2f}%"}])

    def anova_rows(self) -> list[dict]:
        names = dict(zip(self.design.letters, [f.name for f in self.design.factors]))
        rows, prev = [], float(np.sum((self.y - self.y.mean()) ** 2))
        cum: list[int] = [0]
        for ti, t in enumerate(self.terms):
            cols = self._cols(ti)
            cum += cols
            Xs = self.X[:, cum]
            b, *_ = np.linalg.lstsq(Xs, self.y, rcond=None)
            cur = float(np.sum((self.y - Xs @ b) ** 2))
            seq = prev - cur
            prev = cur
            adj = self._sse_without(cols) - self.sse
            df = len(cols)
            ms = adj / df
            f = ms / self.mse if self.mse else None
            p = float(stats.f.sf(f, df, self.df_error)) if f is not None else None
            rows.append({"Source": "*".join(names[L] for L in t), "DF": df, "Seq SS": seq, "Adj SS": adj,
                         "Adj MS": ms, "F": f, "P": p})
        rows.append({"Source": "Residual Error", "DF": self.df_error, "Seq SS": self.sse, "Adj SS": self.sse,
                     "Adj MS": self.mse, "F": None, "P": None})
        rows.append({"Source": "Total", "DF": self.n - 1, "Seq SS": self.sst, "Adj SS": None, "Adj MS": None,
                     "F": None, "P": None})
        return rows

    def anova_table(self) -> pd.DataFrame:
        rows = self.anova_rows()

        def dec(col):
            vals = [abs(r[col]) for r in rows if r[col] is not None and abs(r[col]) > 1e-12]
            return fmt.decimals_for_sig(min(vals), 4) if vals else 0

        d = {c: dec(c) for c in ("Seq SS", "Adj SS", "Adj MS")}
        out = []
        for r in rows:
            out.append({"Source": r["Source"], "DF": str(r["DF"]),
                        **{c: "" if r[c] is None else fmt.fixed(r[c], d[c]) for c in ("Seq SS", "Adj SS", "Adj MS")},
                        "F": "" if r["F"] is None else f"{r['F']:.2f}", "P": "" if r["P"] is None else f"{r['P']:.3f}"})
        return pd.DataFrame(out)

    def response_title(self) -> str:
        return RESPONSE_TITLES[self.characteristic]

    def response_table(self) -> pd.DataFrame:
        return response_table(self.design, self.y)


def response_table(design, y) -> pd.DataFrame:
    """요인 수준별 특성값 평균, Delta(최대 − 최소), Rank(Delta 가 큰 순서, 1부터)."""
    coded = design.coded.reset_index(drop=True)
    y = np.asarray(y, dtype=float)
    max_lv = max(len(f.levels) for f in design.factors)
    means, deltas = {}, {}
    for L, f in zip(design.letters, design.factors):
        m = [float(np.mean(y[coded[L].values == k + 1])) for k in range(len(f.levels))]
        means[f.name] = m
        deltas[f.name] = max(m) - min(m)
    order = sorted(deltas, key=lambda k: -round(deltas[k], 10))
    rank = {k: i + 1 for i, k in enumerate(order)}
    rows = []
    for k in range(max_lv):
        rows.append({"Level": str(k + 1), **{n: (f"{m[k]:.2f}" if k < len(m) else "") for n, m in means.items()}})
    rows.append({"Level": "Delta", **{n: f"{v:.2f}" for n, v in deltas.items()}})
    rows.append({"Level": "Rank", **{n: str(rank[n]) for n in deltas}})
    return pd.DataFrame(rows)


def analyze_characteristic(design, y, characteristic: str = "sn", *, terms=None, sn_type: str | None = None) -> TaguchiAnalysis:
    """이미 계산한 런별 특성값 y 로 모형을 적합한다."""
    tl = parse_terms(design, terms) if terms is not None else [(L,) for L in design.letters]
    return TaguchiAnalysis(design, characteristic, np.asarray(y, dtype=float), tl, sn_type)


def analyze_taguchi(design, Y, *, characteristics=("sn", "mean"), sn_type: str = "larger", terms=None) -> dict:
    """반응 행렬 Y(런 × 잡음 조건·반복)로 특성마다 분석한다. 결과: {특성: TaguchiAnalysis}."""
    Y = np.atleast_2d(np.asarray(Y, dtype=float))
    if Y.shape[0] != len(design.coded):
        Y = Y.T
    if Y.shape[0] != len(design.coded):
        raise ValueError("반응 행 수가 런 수와 다릅니다.")
    return {c: analyze_characteristic(design, characteristic_values(Y, c, sn_type), c, terms=terms,
                                      sn_type=sn_type if c == "sn" else None) for c in characteristics}


def analyze_taguchi_worksheet(ws, responses: list[str], **kw) -> dict:
    Y = np.column_stack([ws.column(c).astype(float).values for c in responses])
    return analyze_taguchi(ws.design, Y, **kw)


def interaction_candidates(design) -> list[tuple[str, str]]:
    return list(combinations(design.letters, 2))


def predict_levels(a: TaguchiAnalysis, settings: dict) -> float:
    """요인 수준 설정(요인 이름 또는 문자 → 수준 값)에서의 예측값(Minitab 'Predict Taguchi Results').

    효과 코딩 모형이라 설정하지 않은 요인은 효과 0(그 요인 수준들의 평균)으로 본다."""
    d = a.design
    names = {f.name: L for L, f in zip(d.letters, d.factors)}
    fac = dict(zip(d.letters, d.factors))
    level_idx = {}
    for k, v in settings.items():
        L = names.get(k, k)
        if L not in fac:
            raise ValueError(f"요인이 아닙니다: {k!r}")
        vals = [_val(x) for x in fac[L].levels]
        if _val(v) not in vals:
            raise ValueError(f"{fac[L].name} 의 수준이 아닙니다: {v!r}")
        level_idx[L] = vals.index(_val(v)) + 1
    x = [1.0]
    for t in a.terms:
        per = []
        for L in t:
            n_lv = len(fac[L].levels)
            k = level_idx.get(L)
            per.append([0.0] * (n_lv - 1) if k is None else
                       [1.0 if k == j + 1 else (-1.0 if k == n_lv else 0.0) for j in range(n_lv - 1)])
        for combo in product(*[range(len(p)) for p in per]):
            x.append(float(np.prod([p[j] for p, j in zip(per, combo)])))
    return float(np.asarray(x) @ a.beta)
