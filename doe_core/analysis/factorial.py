"""요인설계 분석 — Minitab 'Analyze Factorial Design' 의 적합·계수표·모형 요약·분산분석·회귀식.

계산 규칙(docs/spec/B_analysis_plots_optimizer.md 2~3절)
- 최소제곱. 계수는 코드화 단위(공변량은 원래 단위). Effect = 2 × Coef(2수준 요인 항만).
- 앞 항과 선형 종속인(완전 별칭) 항은 항 목록에서 뒤에 있는 것을 뺀다.
- Adj SS: 항(또는 그룹)을 뺀 모형의 SSE − 전체 모형 SSE. Model = SST − SSE. Seq SS: 입력 순서대로 추가할 때의 증가분.
- F = Adj MS / MSE, P = 1 − F_cdf. Lack-of-Fit F = MS_LOF / MS_PE.
- 오차 분할: 중앙점이 있는데 중앙점 항이 모형에 없으면 Curvature(DF 1)를 Error 아래에 둔다.
  반복(모형에 쓰인 요인·블록·공변량 값이 같은 런)이 있고 적합성 결여 DF > 0 이면 Lack-of-Fit / Pure Error 로 나눈다.
- 모형 요약: S = √MSE, R-sq, R-sq(adj), R-sq(pred) = 1 − PRESS/SST(음수면 0).
- VIF_j = [(X'X)⁻¹]_jj · Σ(x_j − x̄_j)².
- 회귀식: 계층 모형이면 비코드화 단위(숫자 요인 z = (x − m)/h 를 전개, 텍스트 요인은 ±1, 블록은 평균화되어 빠짐,
  Ct Pt 는 그대로). 비계층이면 코드화 단위.

문서에 없어 정한 것: Curvature 가 Error 아래에 있을 때 F 의 분모는 순수 오차(없으면 곡면성을 뺀 오차).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from ..designs.general_full import GeneralFullFactorialDesign
from ..designs.definitive_screening import DefinitiveScreeningDesign
from ..designs.definitive_screening import DefinitiveScreeningDesign
from ..designs.response_surface import ResponseSurfaceDesign
from . import fmt
from .model import Term, factorial_terms, is_hierarchical, names_by_letter, rs_terms, term_matrix

_EPS = 1e-10


def _sse(X: np.ndarray, y: np.ndarray) -> float:
    if X.shape[1] == 0:
        return float(np.sum(y ** 2))
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    return float(r @ r)


def _rank(X: np.ndarray) -> int:
    return int(np.linalg.matrix_rank(X, tol=1e-8 * max(1.0, np.abs(X).max()) * max(X.shape)))


@dataclass
class AnovaRow:
    source: str
    level: int                      # 0 = Model/Error/Total, 1 = 그룹·오차 성분, 2 = 개별 항
    df: int | None
    seq_ss: float | None = None
    adj_ss: float | None = None
    adj_ms: float | None = None
    f: float | None = None
    p: float | None = None


@dataclass
class FactorialAnalysis:
    design: object
    response: str
    y: np.ndarray
    used_rows: np.ndarray                 # design.coded 에서 분석에 쓴 행 위치
    terms: list[Term]
    removed_terms: list[Term]
    X: np.ndarray
    col_labels: list[str]                 # X 열 이름(첫 열 Constant)
    col_term: list[int]                   # X 열 → terms 인덱스(상수는 −1)
    covariates: dict[str, np.ndarray]
    beta: np.ndarray = field(init=False)
    cov_unscaled: np.ndarray = field(init=False)
    fitted: np.ndarray = field(init=False)
    resid: np.ndarray = field(init=False)
    hat: np.ndarray = field(init=False)

    def __post_init__(self):
        X, y = self.X, self.y
        self.cov_unscaled = np.linalg.inv(X.T @ X)
        self.beta = self.cov_unscaled @ X.T @ y
        self.fitted = X @ self.beta
        self.resid = y - self.fitted
        self.hat = np.einsum("ij,jk,ik->i", X, self.cov_unscaled, X)

    # ------------------------------------------------------------ 기본 통계량
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
        d = self.y - self.y.mean()
        return float(d @ d)

    @property
    def mse(self) -> float | None:
        return self.sse / self.df_error if self.df_error > 0 else None

    @property
    def two_level(self) -> bool:
        """2수준 요인설계·PB(효과·별칭·요인 그림 대상)."""
        return not isinstance(self.design, (GeneralFullFactorialDesign, ResponseSurfaceDesign,
                                            DefinitiveScreeningDesign))

    @property
    def is_rs(self) -> bool:
        """제곱 항을 쓸 수 있는 3수준 이상 설계(반응표면·확정적 선별설계): Effect 열 없음, 곡면성 행 없음."""
        return isinstance(self.design, (ResponseSurfaceDesign, DefinitiveScreeningDesign))

    @property
    def is_dsd(self) -> bool:
        return isinstance(self.design, DefinitiveScreeningDesign)

    def se_coef(self) -> np.ndarray:
        if self.mse is None:
            return np.full(self.p, np.nan)
        return np.sqrt(np.diag(self.cov_unscaled) * self.mse)

    def vif(self) -> np.ndarray:
        out = np.full(self.p, np.nan)
        for j in range(1, self.p):
            x = self.X[:, j]
            out[j] = self.cov_unscaled[j, j] * float(np.sum((x - x.mean()) ** 2))
        return out

    # ------------------------------------------------------------ 계수표
    def coefficients(self) -> pd.DataFrame:
        se = self.se_coef()
        with np.errstate(divide="ignore", invalid="ignore"):
            t = self.beta / se
        pv = 2 * stats.t.sf(np.abs(t), self.df_error) if self.df_error > 0 else np.full(self.p, np.nan)
        effect = np.full(self.p, np.nan)
        for j, ti in enumerate(self.col_term):
            if ti >= 0 and self.terms[ti].kind == "factor" and self.two_level:
                effect[j] = 2 * self.beta[j]
        return pd.DataFrame({"Term": self.col_labels, "Effect": effect, "Coef": self.beta, "SE Coef": se,
                             "T-Value": t, "P-Value": pv, "VIF": self.vif()})

    def coefficients_table(self) -> pd.DataFrame:
        """Minitab 'Coded Coefficients' 표(문자열)."""
        c = self.coefficients()
        rows = []
        for r in c.itertuples(index=False):
            se = r[3]
            rows.append({
                "Term": r[0],
                "Effect": "" if np.isnan(r[1]) else fmt.by_se(r[1], se),
                "Coef": fmt.by_se(r[2], se),
                "SE Coef": fmt.se_text(se),
                "T-Value": fmt.t_text(r[4]),
                "P-Value": fmt.p_text(r[5]),
                "VIF": "" if np.isnan(r[6]) else f"{r[6]:.2f}",
            })
        out = pd.DataFrame(rows)
        if not self.two_level:
            out = out.drop(columns="Effect")
        return out

    # ------------------------------------------------------------ 모형 요약
    def press(self) -> float | None:
        if np.any(self.hat > 1 - 1e-9):
            return None
        return float(np.sum((self.resid / (1 - self.hat)) ** 2))

    def summary(self) -> dict:
        r2 = 1 - self.sse / self.sst
        s = np.sqrt(self.mse) if self.mse is not None else None
        adj = max(0.0, 1 - self.mse / (self.sst / (self.n - 1))) if self.mse is not None else None
        press = self.press()
        pred = max(0.0, 1 - press / self.sst) if press is not None else None
        return {"S": s, "R-sq": r2, "R-sq(adj)": adj, "R-sq(pred)": pred, "PRESS": press}

    def summary_table(self) -> pd.DataFrame:
        s = self.summary()
        return pd.DataFrame([{"S": fmt.sig_text(s["S"]) if s["S"] is not None else fmt.MISSING,
                              "R-sq": fmt.pct_text(s["R-sq"]), "R-sq(adj)": fmt.pct_text(s["R-sq(adj)"]),
                              "R-sq(pred)": fmt.pct_text(s["R-sq(pred)"])}])

    # ------------------------------------------------------------ 분산분석
    def _cols_of(self, term_indexes: set[int]) -> list[int]:
        return [j for j, ti in enumerate(self.col_term) if ti in term_indexes]

    def _adj_ss(self, term_indexes: set[int]) -> float:
        drop = set(self._cols_of(term_indexes))
        keep = [j for j in range(self.p) if j not in drop]
        return _sse(self.X[:, keep], self.y) - self.sse

    def _seq_ss(self) -> dict[int, float]:
        """항별 순차 제곱합(입력 순서)."""
        out = {}
        prev = _sse(self.X[:, :1], self.y)
        for ti in range(len(self.terms)):
            cols = [0] + self._cols_of(set(range(ti + 1)))
            cur = _sse(self.X[:, cols], self.y)
            out[ti] = prev - cur
            prev = cur
        return out

    def _ftest(self, ss: float, df: int) -> tuple[float | None, float | None, float | None]:
        ms = ss / df
        if self.mse is None or self.mse <= 0:
            return ms, None, None
        f = ms / self.mse
        return ms, f, float(stats.f.sf(f, df, self.df_error))

    def _pure_error(self) -> tuple[float, int]:
        """모형에 쓰인 요인·블록·공변량 값이 같은 런끼리의 순수 오차."""
        coded = self.design.coded.iloc[self.used_rows].reset_index(drop=True)
        letters = sorted({L for t in self.terms if t.kind == "factor" for L in t.letters})
        key = coded[letters].copy() if letters else pd.DataFrame(index=coded.index)
        if any(t.kind == "blocks" for t in self.terms):
            key["_blk"] = coded["Blocks"].values
        if any(t.kind == "center" for t in self.terms):
            key["_ct"] = (coded[self.design.point_col].values == 0).astype(int)
        for t in self.terms:
            if t.kind == "covariate":
                key["_cov_" + t.name] = self.covariates[t.name]
        if key.shape[1] == 0:
            g = np.zeros(self.n, dtype=int)
        else:
            g = key.groupby(list(key.columns), sort=False).ngroup().values
        ss, df = 0.0, 0
        for gid in np.unique(g):
            yy = self.y[g == gid]
            ss += float(np.sum((yy - yy.mean()) ** 2))
            df += len(yy) - 1
        return ss, df

    def anova_rows(self) -> list[AnovaRow]:
        rows: list[AnovaRow] = []
        seq = self._seq_ss()
        model_df = self.p - 1
        model_ss = self.sst - self.sse
        ms, f, pv = self._ftest(model_ss, model_df) if model_df else (None, None, None)
        rows.append(AnovaRow("Model", 0, model_df, sum(seq.values()), model_ss, ms, f, pv))

        def term_df(ti):
            return len(self._cols_of({ti}))

        def add_group(label, idxs, show_members=True):
            if not idxs:
                return
            df = sum(term_df(i) for i in idxs)
            ss = self._adj_ss(set(idxs))
            ms, f, pv = self._ftest(ss, df)
            rows.append(AnovaRow(label, 1, df, sum(seq[i] for i in idxs), ss, ms, f, pv))
            if show_members:
                for i in idxs:
                    d = term_df(i)
                    s2 = self._adj_ss({i})
                    ms2, f2, p2 = self._ftest(s2, d)
                    rows.append(AnovaRow(self.terms[i].name, 2, d, seq[i], s2, ms2, f2, p2))

        kinds = [(i, t) for i, t in enumerate(self.terms)]
        add_group("Covariates", [i for i, t in kinds if t.kind == "covariate"])
        add_group("Blocks", [i for i, t in kinds if t.kind == "blocks"], show_members=False)
        add_group("Linear", [i for i, t in kinds if t.kind == "factor" and t.order == 1])
        add_group("Square", [i for i, t in kinds if t.kind == "factor" and t.is_square])
        top = max((t.order for t in self.terms if t.kind == "factor"), default=0)
        for r in range(2, top + 1):
            # 반응표면 분석 예제는 '2-Way Interaction'(단수), 요인설계 예제는 '2-Way Interactions'(복수)
            label = f"{r}-Way Interaction" if self.is_rs else f"{r}-Way Interactions"
            add_group(label, [i for i, t in kinds if t.kind == "factor" and t.order == r and not t.is_square])
        add_group("Curvature", [i for i, t in kinds if t.kind == "center"], show_members=False)

        # --- 오차와 그 분할
        dfe, sse = self.df_error, self.sse
        rows.append(AnovaRow("Error", 0, dfe, sse, sse, sse / dfe if dfe > 0 else None))
        sub: list[AnovaRow] = []
        curv_ss, curv_df = 0.0, 0
        coded = self.design.coded.iloc[self.used_rows]
        has_ct = self.design.point_col in coded and bool((coded[self.design.point_col] == 0).any()) and self.two_level
        if has_ct and not any(t.kind == "center" for t in self.terms) and dfe > 0:
            ct = (coded[self.design.point_col].values == 0).astype(float)[:, None]
            Xc = np.hstack([self.X, ct])
            if _rank(Xc) == self.p + 1:
                curv_ss, curv_df = sse - _sse(Xc, self.y), 1
        pe_ss, pe_df = self._pure_error()
        lof_df = dfe - pe_df - curv_df
        lof_ss = sse - pe_ss - curv_ss
        if curv_df:
            denom = (pe_ss / pe_df) if pe_df > 0 else ((sse - curv_ss) / (dfe - 1) if dfe > 1 else None)
            f = curv_ss / denom if denom else None
            p = float(stats.f.sf(f, 1, pe_df if pe_df > 0 else dfe - 1)) if f is not None else None
            sub.append(AnovaRow("Curvature", 1, 1, curv_ss, curv_ss, curv_ss, f, p))
        if pe_df > 0 and lof_df > 0:
            ms_lof, ms_pe = lof_ss / lof_df, pe_ss / pe_df
            f = ms_lof / ms_pe if ms_pe > 0 else None
            p = float(stats.f.sf(f, lof_df, pe_df)) if f is not None else None
            sub.append(AnovaRow("Lack-of-Fit", 1, lof_df, lof_ss, lof_ss, ms_lof, f, p))
            sub.append(AnovaRow("Pure Error", 1, pe_df, pe_ss, pe_ss, ms_pe))
        rows += sub
        rows.append(AnovaRow("Total", 0, self.n - 1, self.sst, self.sst))
        return rows

    def anova(self) -> pd.DataFrame:
        return pd.DataFrame([r.__dict__ for r in self.anova_rows()])

    def anova_table(self, seq_ss: bool = False) -> pd.DataFrame:
        """Minitab 'Analysis of Variance' 표(문자열). seq_ss=True 면 Seq SS 열 포함."""
        rows = self.anova_rows()
        ss_dec = fmt.column_decimals([r.adj_ss for r in rows])
        seq_dec = fmt.column_decimals([r.seq_ss for r in rows])
        ms_dec = fmt.column_decimals([r.adj_ms for r in rows])
        out = []
        for r in rows:
            d = {"Source": r.source, "DF": "" if r.df is None else str(r.df)}
            if seq_ss:
                d["Seq SS"] = "" if r.seq_ss is None else fmt.fixed(r.seq_ss, seq_dec)
            d["Adj SS"] = "" if r.adj_ss is None else fmt.fixed(r.adj_ss, ss_dec)
            d["Adj MS"] = "" if r.adj_ms is None else fmt.fixed(r.adj_ms, ms_dec)
            in_model = r.source not in ("Error", "Total", "Pure Error")
            d["F-Value"] = fmt.t_text(r.f) if r.f is not None else (fmt.MISSING if in_model and r.adj_ms is not None and self.df_error == 0 else "")
            d["P-Value"] = fmt.p_text(r.p) if r.p is not None else (fmt.MISSING if in_model and r.adj_ms is not None and self.df_error == 0 else "")
            out.append(d)
        return pd.DataFrame(out)

    # ------------------------------------------------------------ 회귀식
    def _uncoded_transform(self) -> tuple[list[str], np.ndarray]:
        """비코드화 단항식 이름 목록과 변환행렬 T(비코드화 계수 = T @ 코드화 계수)."""
        d = self.design
        names = names_by_letter(d)
        pos = {L: i for i, L in enumerate(d.letters)}
        fac = dict(zip(d.letters, d.factors))
        keys: list[tuple] = []
        entries: dict[tuple, dict[int, float]] = {}

        def add(key, j, w):
            if key not in entries:
                entries[key] = {}
                keys.append(key)
            entries[key][j] = entries[key].get(j, 0.0) + w

        for j, ti in enumerate(self.col_term):
            if ti < 0:
                add(("const",), j, 1.0)
                continue
            t = self.terms[ti]
            if t.kind == "covariate":
                add(("cov", t.name), j, 1.0)
            elif t.kind == "center":
                add(("ct",), j, 1.0)
            elif t.kind == "factor":
                # 각 위치의 z = (x - m)/h 를 곱해 전개한다(제곱 항처럼 같은 요인이 반복돼도 위치별로 처리)
                letters = list(t.letters)
                num_pos = [i for i, L in enumerate(letters) if fac[L].is_numeric]
                text = [L for L in letters if not fac[L].is_numeric]
                for r in range(len(num_pos) + 1):
                    for S in combinations(num_pos, r):
                        w = 1.0
                        for i in num_pos:
                            lo, hi = float(fac[letters[i]].low), float(fac[letters[i]].high)
                            m, h = (lo + hi) / 2, (hi - lo) / 2
                            w *= (1 / h) if i in S else (-m / h)
                        mono = tuple(sorted([letters[i] for i in S] + text, key=pos.__getitem__))
                        add(("const",) if not mono else ("fac", mono), j, w)
            # 블록은 평균화되어 식에서 빠진다

        def sort_key(k):
            kind = k[0]
            if kind == "const":
                return (0, 0, [])
            if kind == "cov":
                return (1, 0, [])
            if kind == "fac":
                m = k[1]
                rank = 0 if len(m) == 1 else (1 if len(m) == 2 and m[0] == m[1] else 1 + len(m))
                return (2, rank, [pos[L] for L in m])
            return (3, 0, [])

        cov_order = {t.name: i for i, t in enumerate(self.terms) if t.kind == "covariate"}
        keys.sort(key=lambda k: (sort_key(k), cov_order.get(k[1], 0) if k[0] == "cov" else 0))
        T = np.zeros((len(keys), self.p))
        for i, k in enumerate(keys):
            for j, w in entries[k].items():
                T[i, j] = w
        labels = []
        for k in keys:
            if k[0] == "const":
                labels.append("")
            elif k[0] == "cov":
                labels.append(k[1])
            elif k[0] == "ct":
                labels.append("Ct Pt")
            else:
                labels.append("*".join(names[L] for L in k[1]))
        return labels, T

    def equation(self) -> tuple[str, str] | None:
        """(제목, 식) — 일반 완전요인설계(범주형 다수준)는 None."""
        if isinstance(self.design, GeneralFullFactorialDesign):
            return None
        se = self.se_coef()
        if is_hierarchical(self.terms):
            labels, T = self._uncoded_transform()
            coef = T @ self.beta
            cov = T @ self.cov_unscaled @ T.T * (self.mse if self.mse is not None else np.nan)
            ses = np.sqrt(np.clip(np.diag(cov), 0, None))
            title = "Regression Equation in Uncoded Units"
        else:
            labels = ["" if j == 0 else lab for j, lab in enumerate(self.col_labels)]
            labels = [lab for j, lab in enumerate(labels) if not (self.col_term[j] >= 0 and self.terms[self.col_term[j]].kind == "blocks")]
            keep = [j for j in range(self.p) if not (self.col_term[j] >= 0 and self.terms[self.col_term[j]].kind == "blocks")]
            coef, ses = self.beta[keep], se[keep]
            title = "Regression Equation in Coded Units"
        parts = []
        for i, (lab, c, s) in enumerate(zip(labels, coef, ses)):
            txt = fmt.by_se(abs(c) if i else c, s)
            if i == 0:
                parts.append(txt if not lab else f"{txt} {lab}")
            else:
                sign = "-" if c < 0 else "+"
                parts.append(f"{sign} {txt} {lab}".rstrip())
        return title, f"{self.response} = " + " ".join(parts)


# ---------------------------------------------------------------- 진입점


def _prepare(design, y, covariates):
    covariates = {k: np.asarray(v, dtype=float) for k, v in (covariates or {}).items()}
    y = np.asarray(y, dtype=float)
    coded_all = design.coded.reset_index(drop=True)
    if len(y) != len(coded_all):
        raise ValueError(f"반응 길이({len(y)})가 런 수({len(coded_all)})와 다릅니다.")
    ok = np.isfinite(y)
    for v in covariates.values():
        ok &= np.isfinite(v)
    used = np.where(ok)[0]
    coded = coded_all.iloc[used].reset_index(drop=True)
    return coded, y[used], used, {k: v[used] for k, v in covariates.items()}


def _build(design, response, coded, yv, used, tl, cov) -> FactorialAnalysis:
    X = np.ones((len(yv), 1))
    labels, col_term, kept, removed = ["Constant"], [-1], [], []
    for t in tl:
        M, labs = term_matrix(t, design, coded, cov)
        cand = np.hstack([X, M])
        if _rank(cand) == X.shape[1] + M.shape[1]:
            X = cand
            labels += labs
            col_term += [len(kept)] * M.shape[1]
            kept.append(t)
        else:
            removed.append(t)
    if X.shape[1] > len(yv):
        raise ValueError("추정할 계수가 관측치보다 많습니다.")
    return FactorialAnalysis(design, response, yv, used, kept, removed, X, labels, col_term, cov)


def analyze_factorial(
    design,
    y,
    *,
    response: str = "Y",
    covariates: dict[str, np.ndarray] | None = None,
    order: int | None = 2,
    terms: list[str] | None = None,
    include_blocks: bool | None = None,
    include_center: bool | None = None,
    model: str | None = None,
) -> FactorialAnalysis:
    """design.coded 행 순서로 정렬된 반응 y 로 요인설계를 분석한다. 반응·공변량이 빈 행은 뺀다.

    반응표면 설계·확정적 선별설계가 들어오면 analyze_response_surface 로 넘긴다(order 대신 model 사용,
    기본은 반응표면 완전 2차, 확정적 선별설계 선형 — Minitab 'Analyze Screening Design' 예제의 Linear).
    """
    if isinstance(design, (ResponseSurfaceDesign, DefinitiveScreeningDesign)):
        if model is None:
            model = "linear" if isinstance(design, DefinitiveScreeningDesign) else "full quadratic"
        return analyze_response_surface(design, y, response=response, covariates=covariates, model=model,
                                        terms=terms, include_blocks=include_blocks)
    coded, yv, used, cov = _prepare(design, y, covariates)
    pt = design.point_col
    tl = factorial_terms(
        design, order=order, terms=terms, covariates=list(cov), include_blocks=include_blocks,
        include_center=include_center, blocks_present=coded["Blocks"].nunique() > 1,
        center_present=(not isinstance(design, GeneralFullFactorialDesign)) and bool((coded[pt] == 0).any()),
    )
    return _build(design, response, coded, yv, used, tl, cov)


def analyze_response_surface(
    design,
    y,
    *,
    response: str = "Y",
    covariates: dict[str, np.ndarray] | None = None,
    model: str = "full quadratic",
    terms: list[str] | None = None,
    include_blocks: bool | None = None,
) -> FactorialAnalysis:
    """반응표면 설계 분석(Minitab 'Analyze Response Surface Design'). 기본 완전 2차 모형."""
    coded, yv, used, cov = _prepare(design, y, covariates)
    tl = rs_terms(design, model=model, terms=terms, covariates=list(cov), include_blocks=include_blocks,
                  blocks_present=coded["Blocks"].nunique() > 1)
    return _build(design, response, coded, yv, used, tl, cov)


def analyze_worksheet(ws, response: str, *, covariates: list[str] | tuple[str, ...] = (), **kwargs):
    """워크시트의 반응 열과 공변량 열로 분석한다(혼합물 설계면 analyze_mixture)."""
    y = ws.column(response).astype(float).values
    from ..designs.mixture import MixtureDesign
    if isinstance(ws.design, MixtureDesign):
        from .mixture import analyze_mixture
        if covariates:
            raise ValueError("혼합물 분석에는 공변량을 쓸 수 없습니다.")
        return analyze_mixture(ws.design, y, response=response, **kwargs)
    cov = {c: ws.column(c).astype(float).values for c in covariates}
    return analyze_factorial(ws.design, y, response=response, covariates=cov, **kwargs)
