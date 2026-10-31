"""효과도(Pareto·정규·반정규) 통계 — Minitab 'Analyze Factorial Design > Graphs > Effects plots'.

문서 'Methods and formulas for the effects plots'
- 오차 DF ≥ 1: 표준화 효과(= T 값). Pareto 기준선 = t(1 − α/2, 오차 DF). 정규·반정규 그림은 p < α 인 효과를 유의로 표시.
  제목 'Pareto Chart of the Standardized Effects', 'Normal Plot of the Standardized Effects'.
- 오차 DF = 0: 비표준화 효과. Lenth PSE 와 ME = t(1 − α/2, 효과 수/3) × PSE. |효과| > ME 를 유의로 표시.
  제목 'Pareto Chart of the Effects', 'Normal Plot of the Effects'.
- Lenth PSE: s0 = 1.5 × median|효과|, PSE = 1.5 × median(|효과| < 2.5·s0 인 효과).
- 반정규 점의 누적분포 F(x) = 2Φ(x) − 1.

문서에 없어 정한 것: 정규 점수는 Blom 위치 (i − 3/8)/(m + 1/4), 반정규는 Φ⁻¹(0.5 + 0.5·위치).
효과도는 2수준 요인 항(열 1개)에만 그린다. 공변량·블록·중앙점 항은 제외.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


def lenth_pse(effects) -> float:
    a = np.abs(np.asarray(effects, dtype=float))
    s0 = 1.5 * np.median(a)
    small = a[a < 2.5 * s0]
    return float(1.5 * np.median(small)) if len(small) else float("nan")


def _blom(m: int) -> np.ndarray:
    return (np.arange(1, m + 1) - 3 / 8) / (m + 1 / 4)


@dataclass
class EffectsResult:
    table: pd.DataFrame        # Term(문자), Name, Effect, Standardized, P-Value, Significant, Normal Score, Half Normal Score
    standardized: bool         # True 면 표준화 효과 그림
    reference: float           # Pareto 기준선(t 또는 ME)
    pse: float | None
    alpha: float

    @property
    def pareto_title(self) -> str:
        return "Pareto Chart of the Standardized Effects" if self.standardized else "Pareto Chart of the Effects"

    @property
    def normal_title(self) -> str:
        return "Normal Plot of the Standardized Effects" if self.standardized else "Normal Plot of the Effects"

    @property
    def half_normal_title(self) -> str:
        return "Half Normal Plot of the Standardized Effects" if self.standardized else "Half Normal Plot of the Effects"

    def pareto(self) -> pd.DataFrame:
        """Pareto 막대 순서(큰 것부터): Term, Name, Value(절댓값)."""
        col = "Standardized" if self.standardized else "Effect"
        t = self.table.assign(Value=self.table[col].abs()).sort_values("Value", ascending=False)
        return t[["Term", "Name", "Value", "Significant"]].reset_index(drop=True)


def effects(a, alpha: float = 0.05) -> EffectsResult:
    """분석 결과에서 효과도 데이터를 만든다."""
    if not a.two_level:
        raise ValueError("효과도는 2수준 설계에서만 그립니다.")
    coefs = a.coefficients()
    rows = []
    for j, ti in enumerate(a.col_term):
        if ti >= 0 and a.terms[ti].kind == "factor":
            t = a.terms[ti]
            rows.append({"Term": t.word, "Name": t.name, "Effect": coefs["Effect"].iloc[j],
                         "Standardized": coefs["T-Value"].iloc[j], "P-Value": coefs["P-Value"].iloc[j]})
    tbl = pd.DataFrame(rows, columns=["Term", "Name", "Effect", "Standardized", "P-Value"])
    m = len(tbl)
    if m == 0:
        raise ValueError("효과를 계산할 요인 항이 없습니다.")
    if a.df_error >= 1:
        standardized, pse = True, None
        ref = float(stats.t.ppf(1 - alpha / 2, a.df_error))
        tbl["Significant"] = tbl["P-Value"] < alpha
        values = tbl["Standardized"].values
    else:
        standardized = False
        pse = lenth_pse(tbl["Effect"].values)
        ref = float(stats.t.ppf(1 - alpha / 2, m / 3) * pse)
        tbl["Significant"] = tbl["Effect"].abs() > ref
        values = tbl["Effect"].values
    pos = _blom(m)
    order = np.argsort(values, kind="stable")
    ns = np.empty(m)
    ns[order] = stats.norm.ppf(pos)
    order_abs = np.argsort(np.abs(values), kind="stable")
    hs = np.empty(m)
    hs[order_abs] = stats.norm.ppf(0.5 + 0.5 * pos)
    tbl["Normal Score"] = ns
    tbl["Half Normal Score"] = hs
    return EffectsResult(tbl, standardized, ref, pse, alpha)
