"""적합치와 진단 측도 — Minitab 'Fits and Diagnostics' 와 'Store statistics' 에 해당.

공식(표준 선형모형, 문서 'Fits and residuals', 'Diagnostic measures')
- 레버리지 h_i = X(X'X)⁻¹X' 의 대각원소, SE Fit = s·√h_i
- 표준화 잔차 = e_i / (s·√(1 − h_i))
- 삭제(외적 스튜던트화) 잔차 = e_i / (s_(i)·√(1 − h_i)), s_(i)² = (SSE − e_i²/(1 − h_i)) / (n − p − 1)
- Cook's D = (표준화 잔차² / p) · h_i / (1 − h_i),  DFITS = 삭제 잔차 · √(h_i / (1 − h_i))
- 이상 관측치: |표준화 잔차| > 2 → R, h_i > min(3p/n, 0.99) → X

표시 자릿수(문서에 없어 정함, 반응표면 예제로 추후 검증): 반응·Fit·Resid 는 그 행 SE Fit 의 유효숫자 3자리 기준 소수 자리,
Std Resid 는 소수 2자리. Obs 는 워크시트 행 번호(1부터).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import fmt


def diagnostics(a) -> pd.DataFrame:
    """관측치별 적합치·잔차·진단 측도(숫자)."""
    n, p = a.n, getattr(a, "p_resid", a.p)       # 분할구: 고정효과 + 전구 항의 계수(순위)
    h = a.hat
    e = a.resid
    label = getattr(a, "response_label", a.response)
    out = pd.DataFrame({"Obs": a.used_rows + 1, label: a.y, "Fit": a.fitted, "Resid": e, "HI": h})
    if a.mse is None:
        for c in ("SE Fit", "Std Resid", "Del Resid", "Cook's D", "DFITS"):
            out[c] = np.nan
        out["Flag"] = ""
        return out
    s = np.sqrt(a.mse)
    with np.errstate(divide="ignore", invalid="ignore"):
        std = e / (s * np.sqrt(1 - h))
        dfe1 = n - p - 1
        s_i2 = (a.sse - e ** 2 / (1 - h)) / dfe1 if dfe1 > 0 else np.full(n, np.nan)
        dele = e / (np.sqrt(s_i2) * np.sqrt(1 - h))
        cook = std ** 2 / p * h / (1 - h)
        dfits = dele * np.sqrt(h / (1 - h))
    out["SE Fit"] = s * np.sqrt(h)
    out["Std Resid"] = std
    out["Del Resid"] = dele
    out["Cook's D"] = cook
    out["DFITS"] = dfits
    lev_cut = min(3 * p / n, 0.99)
    flags = []
    for sr, hi in zip(std, h):
        f = ("R" if np.isfinite(sr) and abs(sr) > 2 else "") + (" X" if hi > lev_cut else "")
        flags.append(f.strip())
    out["Flag"] = flags
    return out[["Obs", label, "Fit", "SE Fit", "Resid", "Std Resid", "Del Resid", "HI", "Cook's D", "DFITS", "Flag"]]


def unusual_table(a) -> pd.DataFrame:
    """Minitab 'Fits and Diagnostics for Unusual Observations' 표(문자열). 이상 관측치가 없으면 빈 표."""
    d = diagnostics(a)
    d = d[d["Flag"] != ""]
    label = getattr(a, "response_label", a.response)
    rows = []
    for r in d.itertuples(index=False):
        se_fit = r[3]
        dec = fmt.decimals_for_sig(se_fit, 3)
        rows.append({"Obs": str(int(r[0])), label: fmt.fixed(r[1], dec), "Fit": fmt.fixed(r[2], dec),
                     "Resid": fmt.fixed(r[4], dec), "Std Resid": fmt.fixed(r[5], 2), "": r[10]})
    return pd.DataFrame(rows, columns=["Obs", label, "Fit", "Resid", "Std Resid", ""])


def unusual_legend(a) -> list[str]:
    flags = " ".join(diagnostics(a)["Flag"])
    out = []
    if "R" in flags:
        out.append("R  Large residual")
    if "X" in flags:
        out.append("X  Unusual X")
    return out
