"""분석 결과 저장과 모든 관측치 표 — Minitab 'Storage' · 'Fits and Diagnostics for All Observations'.

문서(Store statistics for Analyze Factorial Design)
- 저장 열 이름: 적합치 FITS, 잔차 RESI, 표준화 잔차 SRES, 삭제 잔차 TRES, 레버리지 HI, Cook 거리 COOK, DFITS DFIT.
  Box-Cox 변환이면 변환한 반응 BCRE, 원래 반응 단위의 적합치 BFIT. 같은 통계를 다시 저장하면 이름 끝 숫자가 커진다.
- 모든 관측치 표 열: Obs | 반응 | Fit | SE Fit | 95% CI | Resid | Std Resid | Del Resid | HI | Cook's D | DFITS.

문서에 없어 정한 것
- 분석에서 빠진 런(반응·공변량 결측, 가중치 0)의 저장 값은 결측. 계수(COEF)·효과(EFFE)·설계행렬(XMAT)·평균(SMEA)은
  런과 길이가 달라 저장하지 않는다.
- 모든 관측치 표의 표시: 반응·Fit·CI·Resid 는 그 행 SE Fit 의 유효숫자 3자리 기준(비정상 관측치 표와 같음),
  Std Resid·Del Resid 소수 2자리, HI·Cook's D·DFITS 유효숫자 6자리. CI = Fit ± t(1 − α/2, 오차 DF)·SE Fit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import fmt
from .diagnostics import diagnostics

STATS = {"fits": ("FITS", "Fit"), "resid": ("RESI", "Resid"), "sres": ("SRES", "Std Resid"),
         "tres": ("TRES", "Del Resid"), "hi": ("HI", "HI"), "cook": ("COOK", "Cook's D"), "dfit": ("DFIT", "DFITS")}
BOXCOX_STATS = {"bcre": "BCRE", "bfit": "BFIT"}


def _next_name(ws, base: str) -> str:
    taken = set(ws.columns.columns) | set(ws.design.runs.columns)
    k = 1
    while f"{base}{k}" in taken:
        k += 1
    return f"{base}{k}"


def store_statistics(ws, a, which: list[str]) -> list[str]:
    """선택한 통계를 워크시트 열로 저장하고 새 열 이름을 돌려준다. which: STATS·BOXCOX_STATS 의 키."""
    if getattr(a, "is_binary", False) or getattr(a, "is_mixture", False):
        raise ValueError("이 분석의 저장은 아직 지원하지 않습니다.")
    n_all = len(ws.design.coded)
    d = diagnostics(a)
    used = np.asarray(a.used_rows)
    order = np.argsort(ws.design.coded["StdOrder"].values)
    names = []
    for key in which:
        vals = np.full(n_all, np.nan)
        if key in STATS:
            base, col = STATS[key]
            vals[used] = d[col].values
        elif key in BOXCOX_STATS:
            if getattr(a, "boxcox", None) is None:
                raise ValueError("Box-Cox 변환을 쓴 분석에서만 저장할 수 있습니다.")
            base = BOXCOX_STATS[key]
            vals[used] = a.y if key == "bcre" else a.boxcox.inverse(a.fitted)
        else:
            raise ValueError(f"저장할 수 없는 통계: {key!r}")
        name = _next_name(ws, base)
        ws.add_column(name, list(vals[order]), order="std")
        names.append(name)
    return names


def fits_table(a, confidence: float = 0.95) -> pd.DataFrame:
    """Minitab 'Fits and Diagnostics for All Observations'(문자열)."""
    d = diagnostics(a)
    label = getattr(a, "response_label", a.response)
    c = int(round(confidence * 100))
    t = float(stats.t.ppf(1 - (1 - confidence) / 2, a.df_error)) if a.df_error and a.df_error > 0 else float("nan")
    rows = []
    for r in d.itertuples(index=False):
        obs, y, fit, se_fit, resid, std, dele, hi, cook, dfits = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]
        dec = fmt.decimals_for_sig(se_fit, 3) if np.isfinite(se_fit) else 4
        ci = (f"({fmt.fixed(fit - t * se_fit, dec)}, {fmt.fixed(fit + t * se_fit, dec)})"
              if np.isfinite(se_fit) and np.isfinite(t) else "(*, *)")
        rows.append({"Obs": str(int(obs)), label: fmt.fixed(y, dec), "Fit": fmt.fixed(fit, dec),
                     "SE Fit": fmt.se_text(se_fit), f"{c}% CI": ci, "Resid": fmt.fixed(resid, dec),
                     "Std Resid": fmt.fixed(std, 2), "Del Resid": fmt.fixed(dele, 2), "HI": fmt.sig_text(hi),
                     "Cook's D": fmt.sig_text(cook), "DFITS": fmt.sig_text(dfits)})
    return pd.DataFrame(rows)
