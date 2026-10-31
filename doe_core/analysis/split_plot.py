"""분할구 설계 분석 — Minitab 'Analyze Factorial Design' 의 분할구 처리.

문서 근거(docs/spec/B_analysis_plots_optimizer.md 2·3절 — 숫자 예제는 문서에 없음)
- 오차를 전구 오차(WP Error)와 하위구 오차(Error, SP)로 나눈다. 균형 분할구에서 바꾸기 어려운(HTC) 요인만으로 된
  항(과 블록)의 F 는 분모가 WP Error MS, 나머지 항은 하위구 오차 MS.
- 계수 SE: Cov(β) = (X'V⁻¹X)⁻¹, V = σ²_SP·I + σ²_WP·ZZ'(Z = 전구 지시행렬), σ²_SP = MSE(SP),
  균형 설계에서 σ²_WP = (MS_WP − MS_SP)/m(m = 전구당 런 수, 음수면 0).
- 모형 요약에 S(WP), R-sq(SP), R-sq(WP) 추가. R-sq(WP) = 1 − SS(WP Error)/SS Total(WP),
  SS Total(WP) = WP Error 와 HTC 요인만으로 된 항들의 SS 합, R-sq(SP) = 1 − SS(SP Error)/(SS Total − SS Total(WP)).
- 잔차: y − ŷ(고정효과 + 전구 항). 중앙점·가중치·단계적 선택 없음.

문서에 없어 정한 것
- 분산분석표: Model(DF = 고정 항 + WP Error) 아래에 그룹·항과 'WP Error' 행(F = MS_WP / MS_SP), 그 밑에 Error·Total.
  HTC 항과 ETC 항이 섞인 그룹의 F 는 하위구 오차를 분모로 쓴다. 하위구 오차를 적합성 결여·순수 오차로 나누지 않는다.
- S(WP) = √(WP Error MS). 열 순서 S, R-sq, R-sq(adj), R-sq(pred), S(WP), R-sq(SP), R-sq(WP).
- 계수 추정은 최소제곱(균형 설계에서 일반화 최소제곱과 같음).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from . import fmt
from .factorial import AnovaRow, FactorialAnalysis, _sse


@dataclass
class SplitPlotAnalysis(FactorialAnalysis):
    Z: np.ndarray = field(init=False)
    sse_fixed: float = field(init=False)
    rank_full: int = field(init=False)

    is_split_plot = True

    def __post_init__(self):
        super().__post_init__()
        coded = self.design.coded.iloc[self.used_rows]
        wp = coded["WP"].values
        ids = sorted(set(wp))
        self.Z = (wp[:, None] == np.array(ids)[None, :]).astype(float)
        self.sse_fixed = float(self.resid @ self.resid)
        full = np.hstack([self.X, self.Z])
        u, s, _ = np.linalg.svd(full, full_matrices=False)
        U = u[:, s > 1e-9 * s[0]]
        self.rank_full = U.shape[1]
        self.fitted_fixed = self.fitted.copy()
        self.fitted = U @ (U.T @ self.y)
        self.resid = self.y - self.fitted
        self.hat = (U ** 2).sum(axis=1)
        self._wp_cache = None

    # ------------------------------------------------------------ 오차 성분
    @property
    def p_resid(self) -> int:
        return self.rank_full

    @property
    def df_error(self) -> int:
        return self.n - self.rank_full

    @property
    def df_wp(self) -> int:
        return self.rank_full - self.p

    @property
    def ss_wp(self) -> float:
        return max(0.0, self.sse_fixed - self.sse)

    @property
    def ms_wp(self) -> float | None:
        return self.ss_wp / self.df_wp if self.df_wp > 0 else None

    @property
    def m(self) -> float:
        return self.n / self.Z.shape[1]

    def is_wp_term(self, ti: int) -> bool:
        t = self.terms[ti]
        if t.kind == "blocks":
            return True
        if t.kind == "factor":
            return set(t.letters) <= set(self.design.htc_letters)
        if t.kind == "covariate":
            v = self.covariates[t.name]
            return all(np.ptp(v[self.Z[:, j] > 0]) == 0 for j in range(self.Z.shape[1]))
        return False

    def coef_cov(self) -> np.ndarray:
        if self.mse is None:
            return np.full((self.p, self.p), np.nan)
        s2_sp = self.mse
        s2_wp = max(0.0, ((self.ms_wp or 0.0) - s2_sp) / self.m) if self.ms_wp is not None else 0.0
        V = s2_sp * np.eye(self.n) + s2_wp * (self.Z @ self.Z.T)
        Vi = np.linalg.pinv(V)
        return np.linalg.pinv(self.X.T @ Vi @ self.X)

    def se_coef(self) -> np.ndarray:
        return np.sqrt(np.clip(np.diag(self.coef_cov()), 0, None))

    def _col_df(self) -> np.ndarray:
        out = np.full(self.p, self.df_error)
        for j, ti in enumerate(self.col_term):
            if ti >= 0 and self.is_wp_term(ti):
                out[j] = self.df_wp
            elif ti < 0:
                out[j] = self.df_wp
        return out

    def coefficients(self) -> pd.DataFrame:
        c = super().coefficients()
        se = self.se_coef()
        with np.errstate(divide="ignore", invalid="ignore"):
            t = self.beta / se
        dfs = self._col_df()
        pv = np.array([2 * stats.t.sf(abs(tv), d) if d > 0 and np.isfinite(tv) else np.nan for tv, d in zip(t, dfs)])
        c["SE Coef"], c["T-Value"], c["P-Value"] = se, np.where(dfs > 0, t, np.nan), pv
        return c

    # ------------------------------------------------------------ 분산분석
    def _adj_ss(self, term_indexes: set[int]) -> float:
        drop = set(self._cols_of(term_indexes))
        keep = [j for j in range(self.p) if j not in drop]
        return max(0.0, _sse(self.X[:, keep], self.y) - self.sse_fixed)

    def _ftest_level(self, ss: float, df: int, wp: bool):
        ms = ss / df
        if wp:
            if self.ms_wp is None or self.ms_wp <= 0:
                return ms, None, None
            f = ms / self.ms_wp
            return ms, f, float(stats.f.sf(f, df, self.df_wp))
        return self._ftest(ss, df)

    def anova_rows(self) -> list[AnovaRow]:
        rows: list[AnovaRow] = []
        seq = self._seq_ss()
        model_df = self.p - 1 + self.df_wp
        model_ss = self.sst - self.sse
        ms, f, pv = self._ftest(model_ss, model_df) if model_df else (None, None, None)
        rows.append(AnovaRow("Model", 0, model_df, model_ss, model_ss, ms, f, pv))

        def add_group(label, idxs, show_members=True):
            if not idxs:
                return
            df = sum(len(self._cols_of({i})) for i in idxs)
            ss = self._adj_ss(set(idxs))
            wp = all(self.is_wp_term(i) for i in idxs)
            ms, f, pv = self._ftest_level(ss, df, wp)
            rows.append(AnovaRow(label, 1, df, sum(seq[i] for i in idxs), ss, ms, f, pv))
            if show_members:
                for i in idxs:
                    d = len(self._cols_of({i}))
                    s2 = self._adj_ss({i})
                    ms2, f2, p2 = self._ftest_level(s2, d, self.is_wp_term(i))
                    rows.append(AnovaRow(self.terms[i].name, 2, d, seq[i], s2, ms2, f2, p2))

        kinds = list(enumerate(self.terms))
        add_group("Covariates", [i for i, t in kinds if t.kind == "covariate"])
        add_group("Blocks", [i for i, t in kinds if t.kind == "blocks"], show_members=False)
        add_group("Linear", [i for i, t in kinds if t.kind == "factor" and t.order == 1])
        top = max((t.order for t in self.terms if t.kind == "factor"), default=0)
        for r in range(2, top + 1):
            add_group(f"{r}-Way Interactions", [i for i, t in kinds if t.kind == "factor" and t.order == r])
        if self.df_wp > 0:
            ms_wp = self.ms_wp
            f = ms_wp / self.mse if self.mse else None
            p = float(stats.f.sf(f, self.df_wp, self.df_error)) if f is not None else None
            rows.append(AnovaRow("WP Error", 1, self.df_wp, self.ss_wp, self.ss_wp, ms_wp, f, p))
        dfe, sse = self.df_error, self.sse
        rows.append(AnovaRow("Error", 0, dfe, sse, sse, sse / dfe if dfe > 0 else None))
        rows.append(AnovaRow("Total", 0, self.n - 1, self.sst, self.sst))
        return rows

    # ------------------------------------------------------------ 모형 요약
    def summary(self) -> dict:
        s = super().summary()
        seq = self._seq_ss()
        htc_ss = sum(seq[i] for i, t in enumerate(self.terms)
                     if t.kind == "factor" and set(t.letters) <= set(self.design.htc_letters))
        tot_wp = htc_ss + self.ss_wp
        tot_sp = self.sst - tot_wp
        s["S(WP)"] = float(np.sqrt(self.ms_wp)) if self.ms_wp is not None else None
        s["R-sq(SP)"] = 1 - self.sse / tot_sp if tot_sp > 0 else None
        s["R-sq(WP)"] = 1 - self.ss_wp / tot_wp if tot_wp > 0 else None
        return s

    def summary_table(self) -> pd.DataFrame:
        s = self.summary()
        tbl = super().summary_table()
        tbl["S(WP)"] = fmt.sig_text(s["S(WP)"]) if s["S(WP)"] is not None else fmt.MISSING
        tbl["R-sq(SP)"] = fmt.pct_text(s["R-sq(SP)"])
        tbl["R-sq(WP)"] = fmt.pct_text(s["R-sq(WP)"])
        return tbl

    def whole_plot_residuals(self) -> np.ndarray:
        """ŷ(고정효과 + 전구 항) − ŷ(고정효과만)."""
        return self.fitted - self.fitted_fixed
