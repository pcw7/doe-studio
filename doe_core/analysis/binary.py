"""이항 반응 분석 — Minitab 'Analyze Binary Response'(요인설계·반응표면·선별 설계, 로짓 연결).

문서(Example: FoodSpoilage, Coefficients table, Methods and formulas: goodness-of-fit)
- 반응: 사건/시행 형식(사건 수 열 + 시행 수 열) 또는 이항 열(행마다 0/1, 시행 1).
- 최대우도(로짓). Effect = 2 × Coef(2수준 항), 계수표 기본 열 Term | Effect | Coef | SE Coef | VIF,
  확장 표시는 95% CI · Z-Value · P-Value(Wald).
- Analysis of Variance(이탈도): Model, 각 항(Adj Dev = 그 항을 뺀 모형의 이탈도 − 현재 이탈도, 우도비 카이제곱), Error, Total.
  열 Source | DF | Adj Dev | Adj Mean | Chi-Square | P-Value. 그룹(Linear 등) 행은 없다.
- Model Summary: Deviance R-Sq = (D₀ − D)/D₀, Deviance R-Sq(adj) = (D₀ − D − (p − 1))/D₀, AIC = −2lnL + 2p,
  AICc = AIC + 2p(p + 1)/(n − p − 1), BIC = −2lnL + p·ln n (n = 행 수, p = 상수 포함 계수 수, lnL 은 이항 계수를 포함한
  완전 우도) — 문서 예제 값(97.95%, 76.75%, 105.98, 171.98, 114.48)의 관계로 확인.
- Goodness-of-Fit Tests: Deviance(DF = n − p), Pearson(Σ(y − mπ)²/(mπ(1 − π))), Hosmer-Lemeshow
  Ĉ = Σ(o_k − n'_k·π̄_k)²/(n'_k·π̄_k(1 − π̄_k)), DF = g − 2. 확률 순으로 10개 같은 크기 그룹을 시도.
- 오즈비: 연속 요인은 Unit of Change(코드화 단위 1 = 반폭)당 exp(계수), 범주형은 Level A 대 Level B. 교호작용·제곱 항에
  들어 있는 요인은 '*'.
- 회귀식: P(Event) = exp(Y')/(1 + exp(Y')), Y' = 비코드화 선형식.

문서에 없어 정한 것
- Hosmer-Lemeshow 그룹: 확률 오름차순으로 행(패턴)을 쌓아 누적 시행이 N/10 이상이 되면 그룹을 닫는다(행은 나누지 않음,
  남은 행은 마지막 그룹). 문서 예제(16행 × 약 500 시행)에서 DF 6(= 8그룹)이 나오는 규칙.
- 오즈비·CI 는 소수 4자리, Unit of Change 는 소수 1자리(정수가 아니면 그대로).
- 이항 열 형식에서도 적합도 검정은 행 단위(패턴으로 묶지 않음).
- 완전 분리(계수가 발산)면 오류.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import special, stats

from . import fmt
from .factorial import FactorialAnalysis, _rank
from .model import factorial_terms, rs_terms, term_matrix

Z95 = float(stats.norm.ppf(0.975))


def _deviance(y, m, p) -> float:
    mu = m * p
    with np.errstate(divide="ignore", invalid="ignore"):
        a = np.where(y > 0, y * np.log(y / mu), 0.0)
        b = np.where(m - y > 0, (m - y) * np.log((m - y) / (m - mu)), 0.0)
    return float(2 * np.sum(a + b))


def fit_logit(X: np.ndarray, y: np.ndarray, m: np.ndarray, *, max_iter: int = 200, tol: float = 1e-11):
    """(β, π) — 로짓 연결 이항 최대우도(IRLS)."""
    p0 = min(max(float(np.sum(y) / np.sum(m)), 1e-6), 1 - 1e-6)
    beta = np.zeros(X.shape[1])
    beta[0] = math.log(p0 / (1 - p0))
    for _ in range(max_iter):
        eta = X @ beta
        p = special.expit(eta)
        w = m * p * (1 - p)
        if np.any(w <= 1e-300):
            raise ValueError("완전 분리(어떤 설정에서 사건이 항상 또는 전혀 일어나지 않음)라 계수를 추정할 수 없습니다.")
        z = eta + (y - m * p) / w
        XtW = X.T * w
        new = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(new)) > 50:
            raise ValueError("완전 분리(계수가 발산)라 계수를 추정할 수 없습니다.")
        if np.max(np.abs(new - beta)) < tol:
            beta = new
            break
        beta = new
    else:
        raise ValueError("로지스틱 회귀가 수렴하지 않았습니다.")
    return beta, special.expit(X @ beta)


@dataclass
class BinaryAnalysis(FactorialAnalysis):
    """로짓 이항 회귀 결과. y·weights 는 수렴점의 작업 반응·IRLS 가중치(계수·SE·VIF·회귀식 재사용)."""
    events: np.ndarray = field(default=None, repr=False)
    trials: np.ndarray = field(default=None, repr=False)
    event_name: str = "Event"
    events_label: str = "Event"
    trials_label: str = "Trials"
    binary_format: bool = False
    event_value: str = ""

    is_binary = True

    # ---------------------------------------------------------- 기본 통계
    @property
    def df_error(self) -> int:                      # Wald 검정(정규) — 효과도 기준선도 z
        return 10 ** 9

    @property
    def df_resid(self) -> int:
        return self.n - self.p

    @property
    def mse(self) -> float:
        return 1.0

    @property
    def prob(self) -> np.ndarray:
        return special.expit(self.X @ self.beta)

    @property
    def response_label(self) -> str:
        return "Y'"

    @property
    def y_original(self) -> np.ndarray:
        """관측 비율(사건/시행)."""
        return self.events / self.trials

    def to_original(self, z):
        """선형 예측 → 사건 확률."""
        return special.expit(z)

    def deviance(self) -> float:
        return _deviance(self.events, self.trials, self.prob)

    def null_deviance(self) -> float:
        p0 = np.full(self.n, float(np.sum(self.events) / np.sum(self.trials)))
        return _deviance(self.events, self.trials, p0)

    def loglik(self) -> float:
        return float(np.sum(stats.binom.logpmf(self.events, self.trials, self.prob)))

    def _reduced_deviance(self, drop_terms: set[int]) -> float:
        keep = [j for j, ti in enumerate(self.col_term) if ti not in drop_terms]
        _, p = fit_logit(self.X[:, keep], self.events, self.trials)
        return _deviance(self.events, self.trials, p)

    # ---------------------------------------------------------- 표
    def method_table(self) -> pd.DataFrame:
        return pd.DataFrame([{"Method": "Link function", "Value": "Logit"},
                             {"Method": "Rows used", "Value": str(self.n)}])

    def response_table(self) -> pd.DataFrame:
        e, N = int(round(np.sum(self.events))), int(round(np.sum(self.trials)))
        if self.binary_format:
            return pd.DataFrame([{"Variable": self.events_label, "Value": f"{self.event_value} (Event)", "Count": str(e)},
                                 {"Variable": "", "Value": "Other", "Count": str(N - e)},
                                 {"Variable": "", "Value": "Total", "Count": str(N)}])
        return pd.DataFrame([{"Variable": self.events_label, "Value": "Event", "Count": str(e)},
                             {"Variable": "", "Value": "Non-event", "Count": str(N - e)},
                             {"Variable": self.trials_label, "Value": "Total", "Count": str(N)}])

    def coefficients_table(self, expanded: bool = False) -> pd.DataFrame:
        c = self.coefficients()
        rows = []
        for r in c.itertuples(index=False):
            se = r[3]
            d = {"Term": r[0], "Effect": "" if np.isnan(r[1]) else fmt.by_se(r[1], se), "Coef": fmt.by_se(r[2], se),
                 "SE Coef": fmt.se_text(se)}
            if expanded:
                d["95% CI"] = f"({fmt.by_se(r[2] - Z95 * se, se)}, {fmt.by_se(r[2] + Z95 * se, se)})"
                d["Z-Value"] = fmt.t_text(r[4])
                d["P-Value"] = fmt.p_text(r[5])
            d["VIF"] = "" if np.isnan(r[6]) else f"{r[6]:.2f}"
            rows.append(d)
        out = pd.DataFrame(rows)
        if not self.two_level:
            out = out.drop(columns="Effect")
        return out

    def summary(self) -> dict:
        D, D0 = self.deviance(), self.null_deviance()
        n, p = self.n, self.p
        m2ll = -2 * self.loglik()
        aic = m2ll + 2 * p
        return {"Deviance R-Sq": (D0 - D) / D0 if D0 > 0 else None,
                "Deviance R-Sq(adj)": max(0.0, (D0 - D - (p - 1)) / D0) if D0 > 0 else None,
                "AIC": aic, "AICc": aic + 2 * p * (p + 1) / (n - p - 1) if n - p - 1 > 0 else None,
                "BIC": m2ll + p * math.log(n)}

    def summary_table(self, expanded: bool = False) -> pd.DataFrame:
        s = self.summary()
        return pd.DataFrame([{"Deviance R-Sq": fmt.pct_text(s["Deviance R-Sq"]),
                              "Deviance R-Sq(adj)": fmt.pct_text(s["Deviance R-Sq(adj)"]),
                              "AIC": fmt.fixed(s["AIC"], 2), "AICc": fmt.fixed(s["AICc"], 2), "BIC": fmt.fixed(s["BIC"], 2)}])

    def anova_rows(self) -> list[dict]:
        D, D0 = self.deviance(), self.null_deviance()
        rows = []

        def add(src, df, dev, test=True):
            mean = dev / df if df else None
            chi = dev if test else None
            pv = float(stats.chi2.sf(dev, df)) if test and df else None
            rows.append({"Source": src, "DF": df, "Adj Dev": dev, "Adj Mean": mean, "Chi-Square": chi, "P-Value": pv})

        add("Model", self.p - 1, D0 - D)
        for ti, t in enumerate(self.terms):
            df = len(self._cols_of({ti}))
            add(t.name, df, max(self._reduced_deviance({ti}) - D, 0.0))
        add("Error", self.df_resid, D, test=False)
        rows.append({"Source": "Total", "DF": self.n - 1, "Adj Dev": D0, "Adj Mean": None, "Chi-Square": None,
                     "P-Value": None})
        return rows

    def anova_title(self) -> str:
        return "Analysis of Variance"

    def anova_table(self, seq_ss: bool = False) -> pd.DataFrame:
        rows = self.anova_rows()
        dev_dec = fmt.column_decimals([r["Adj Dev"] for r in rows])
        mean_dec = fmt.column_decimals([r["Adj Mean"] for r in rows])
        out = []
        for r in rows:
            out.append({"Source": r["Source"], "DF": str(r["DF"]), "Adj Dev": fmt.fixed(r["Adj Dev"], dev_dec),
                        "Adj Mean": "" if r["Adj Mean"] is None else fmt.fixed(r["Adj Mean"], mean_dec),
                        "Chi-Square": "" if r["Chi-Square"] is None else fmt.t_text(r["Chi-Square"]),
                        "P-Value": "" if r["P-Value"] is None else fmt.p_text(r["P-Value"])})
        return pd.DataFrame(out)

    def hosmer_lemeshow(self, groups: int = 10) -> tuple[float, int]:
        p, y, m = self.prob, self.events, self.trials
        order = np.argsort(p, kind="stable")
        target = float(np.sum(m)) / groups
        gid, acc, labels = 0, 0.0, np.empty(self.n, dtype=int)
        for i in order:
            labels[i] = gid
            acc += m[i]
            if acc >= target - 1e-9:
                gid, acc = gid + 1, 0.0
        if acc == 0.0:
            gid -= 1                                   # 마지막 그룹이 꽉 차서 끝난 경우
        g = gid + 1
        c = 0.0
        for k in range(g):
            sel = labels == k
            nk = float(np.sum(m[sel]))
            ok = float(np.sum(y[sel]))
            pk = float(np.sum(m[sel] * p[sel])) / nk
            denom = nk * pk * (1 - pk)
            if denom > 0:
                c += (ok - nk * pk) ** 2 / denom
        return c, g - 2

    def gof_table(self) -> pd.DataFrame:
        p, y, m = self.prob, self.events, self.trials
        D = self.deviance()
        pearson = float(np.sum((y - m * p) ** 2 / (m * p * (1 - p))))
        hl, hl_df = self.hosmer_lemeshow()
        rows = []
        for name, df, chi in [("Deviance", self.df_resid, D), ("Pearson", self.df_resid, pearson),
                              ("Hosmer-Lemeshow", hl_df, hl)]:
            pv = float(stats.chi2.sf(chi, df)) if df > 0 else None
            rows.append({"Test": name, "DF": str(df), "Chi-Square": fmt.t_text(chi),
                         "P-Value": fmt.p_text(pv) if pv is not None else fmt.MISSING})
        return pd.DataFrame(rows)

    # ---------------------------------------------------------- 오즈비
    def _in_higher_terms(self, letter: str) -> bool:
        return any(t.kind == "factor" and t.order > 1 and letter in t.letters for t in self.terms)

    def odds_continuous(self) -> pd.DataFrame:
        d = self.design
        rows = []
        cov = self.coef_cov()
        for L, f in zip(d.letters, d.factors):
            if not getattr(f, "is_numeric", False) or not hasattr(f, "low") or type(d).__name__ == "GeneralFullFactorialDesign":
                continue
            idx = [j for j, ti in enumerate(self.col_term) if ti >= 0 and self.terms[ti].letters == (L,)]
            if not idx:
                continue
            unit = (float(f.high) - float(f.low)) / 2
            unit_txt = f"{unit:.1f}" if abs(unit * 10 - round(unit * 10)) < 1e-9 else f"{unit:g}"
            if self._in_higher_terms(L):
                rows.append({"Term": f.name, "Unit of Change": unit_txt, "Odds Ratio": fmt.MISSING, "95% CI": "(*, *)"})
                continue
            b, se = float(self.beta[idx[0]]), float(math.sqrt(cov[idx[0], idx[0]]))
            rows.append({"Term": f.name, "Unit of Change": unit_txt, "Odds Ratio": f"{math.exp(b):.4f}",
                         "95% CI": f"({math.exp(b - Z95 * se):.4f}, {math.exp(b + Z95 * se):.4f})"})
        return pd.DataFrame(rows, columns=["Term", "Unit of Change", "Odds Ratio", "95% CI"])

    def odds_categorical(self) -> pd.DataFrame:
        """Level A 대 Level B 오즈비(범주형 = 텍스트 요인·일반 완전요인 요인)."""
        from ..designs.general_full import GeneralFullFactorialDesign
        d = self.design
        gff = isinstance(d, GeneralFullFactorialDesign)
        cov = self.coef_cov()
        rows = []
        for L, f in zip(d.letters, d.factors):
            if not gff and getattr(f, "is_numeric", True):
                continue
            idx = [j for j, ti in enumerate(self.col_term) if ti >= 0 and self.terms[ti].letters == (L,)]
            if not idx:
                continue
            rows.append({"Term": f.name, "Level A": "", "Level B": "", "Odds Ratio": "", "95% CI": ""})
            if self._in_higher_terms(L):
                rows.append({"Term": "", "Level A": "Any level", "Level B": "Any level", "Odds Ratio": fmt.MISSING,
                             "95% CI": "(*, *)"})
                continue
            levels = list(f.levels) if gff else [f.low, f.high]
            k = len(levels)
            # 수준별 선형 예측의 차이: 효과 코딩(gff) 또는 ±1(2수준)
            if gff:
                code = np.zeros((k, len(idx)))
                for i in range(k - 1):
                    code[i, i] = 1.0
                code[k - 1, :] = -1.0
            else:
                code = np.array([[-1.0], [1.0]])
            for a in range(k):
                for b in range(a):
                    vec = code[a] - code[b]
                    est = float(vec @ self.beta[idx])
                    se = float(math.sqrt(vec @ cov[np.ix_(idx, idx)] @ vec))
                    rows.append({"Term": "", "Level A": str(levels[a]), "Level B": str(levels[b]),
                                 "Odds Ratio": f"{math.exp(est):.4f}",
                                 "95% CI": f"({math.exp(est - Z95 * se):.4f}, {math.exp(est + Z95 * se):.4f})"})
        return pd.DataFrame(rows, columns=["Term", "Level A", "Level B", "Odds Ratio", "95% CI"])

    def equation(self) -> tuple[str, str] | None:
        base = super().equation()
        if base is None:
            return None
        title, text = base
        return title, f"P({self.event_name}) = exp(Y')/(1 + exp(Y'))\n{text}"


def analyze_binary(ws, *, events: str, trials: str | None = None, event_name: str = "Event", event_value=1,
                   order: int | None = 2, model: str | None = None, terms: list[str] | None = None,
                   include_blocks: bool | None = None) -> BinaryAnalysis:
    """사건/시행 형식(events + trials) 또는 이항 열 형식(events 열의 값 == event_value 이면 사건, 시행 1)."""
    from ..designs.definitive_screening import DefinitiveScreeningDesign
    from ..designs.mixture import MixtureDesign
    from ..designs.response_surface import ResponseSurfaceDesign
    from ..designs.split_plot import SplitPlotDesign
    d = ws.design
    if isinstance(d, (MixtureDesign, SplitPlotDesign)) or type(d).__name__ == "TaguchiDesign":
        raise ValueError("이항 반응 분석은 요인설계·반응표면·선별 설계에서 쓸 수 있습니다.")
    raw = ws.column(events)
    if trials:
        y = raw.astype(float).values
        m = ws.column(trials).astype(float).values
        binary = False
    else:
        vals = raw.values
        y = np.array([np.nan if (v is None or (isinstance(v, float) and np.isnan(v))) else
                      (1.0 if str(v) == str(event_value) or (_num(v) is not None and _num(v) == _num(event_value))
                       else 0.0) for v in vals])
        m = np.where(np.isfinite(y), 1.0, np.nan)
        binary = True
    ok = np.isfinite(y) & np.isfinite(m) & (m > 0)
    if np.any((y[ok] < 0) | (y[ok] > m[ok])):
        raise ValueError("사건 수는 0 이상, 시행 수 이하여야 합니다.")
    used = np.where(ok)[0]
    coded = d.coded.reset_index(drop=True).iloc[used].reset_index(drop=True)
    y, m = y[used], m[used]
    blocks_present = coded["Blocks"].nunique() > 1
    if isinstance(d, (ResponseSurfaceDesign, DefinitiveScreeningDesign)):
        tl = rs_terms(d, model=model or ("linear" if isinstance(d, DefinitiveScreeningDesign) else "full quadratic"),
                      terms=terms, include_blocks=include_blocks, blocks_present=blocks_present)
    else:
        tl = factorial_terms(d, order=order, terms=terms, include_blocks=include_blocks, include_center=False,
                             blocks_present=blocks_present, center_present=False)
    X = np.ones((len(y), 1))
    labels, col_term, kept, removed = ["Constant"], [-1], [], []
    for t in tl:
        M, labs = term_matrix(t, d, coded, {})
        cand = np.hstack([X, M])
        if _rank(cand) == cand.shape[1]:
            X = cand
            labels += labs
            col_term += [len(kept)] * M.shape[1]
            kept.append(t)
        else:
            removed.append(t)
    if X.shape[1] > len(y):
        raise ValueError("추정할 계수가 행 수보다 많습니다.")
    beta, p = fit_logit(X, y, m)
    w = m * p * (1 - p)
    z = X @ beta + (y - m * p) / w
    if binary and event_name == "Event":
        event_name = str(event_value)                    # 이항 열 형식: P(사건 값)
    return BinaryAnalysis(d, events, z, used, kept, removed, X, labels, col_term, {}, weights=w, events=y, trials=m,
                          event_name=event_name, events_label=events, trials_label=trials or "", binary_format=binary,
                          event_value=str(event_value))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
