"""Minitab 출력 표시 형식.

문서 예제 6개(요인·반응표면·혼합물·선별 분석)에서 역추적한 규칙
- 계수표: SE Coef 를 유효숫자 3자리로 표시하고, Coef·Effect 는 같은 행 SE 와 같은 소수 자리.
  (56.0 / 21.0, -1.229 / 0.979, 2.658 / 0.678, 28.44 / 1.66, -5.81 / 1.10, 104.874 / 0.667)
- T-Value·F-Value 소수 2자리, P-Value 소수 3자리, VIF 소수 2자리.
- 분산분석표: Adj SS(·Seq SS) 열은 열의 최댓값(보통 Total) 기준 유효숫자 6자리, Adj MS 열도 열의 최댓값 기준 6자리.
  (460.478, 1447.60, 85179.2, 3924.94 / 113.068, 540.470, 38451.1, 560.597)
- 모형 요약: S 는 유효숫자 6자리(1.51005, 4.40228, 50.9634, 0.276960), R-sq 계열은 백분율 소수 2자리.
- 회귀식: 각 계수를 그 계수의 SE(비코드화 단위) 기준 위 계수표 규칙으로 표시.
"""
from __future__ import annotations

import math

MISSING = "*"


def decimals_for_sig(x: float, sig: int) -> int:
    """x 를 유효숫자 sig 자리로 보이게 하는 소수 자리 수(0 이상)."""
    if x is None or not math.isfinite(x) or x == 0:
        return max(0, sig - 1)
    return max(0, sig - 1 - math.floor(math.log10(abs(x))))


def fixed(x: float | None, d: int) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return MISSING
    s = f"{x:.{d}f}"
    return s


def by_se(value: float, se: float, sig: int = 3) -> str:
    """계수를 SE 의 유효숫자 sig 자리와 같은 소수 자리로."""
    if se is None or not math.isfinite(se):
        return fixed(value, 4)
    return fixed(value, decimals_for_sig(se, sig))


def se_text(se: float, sig: int = 3) -> str:
    if se is None or not math.isfinite(se):
        return MISSING
    return fixed(se, decimals_for_sig(se, sig))


def sig_text(x: float, sig: int = 6) -> str:
    if x is None or not math.isfinite(x):
        return MISSING
    return fixed(x, decimals_for_sig(x, sig))


def column_decimals(values, sig: int = 6) -> int:
    finite = [abs(v) for v in values if v is not None and math.isfinite(v)]
    return decimals_for_sig(max(finite), sig) if finite else 0


def t_text(t: float | None) -> str:
    return fixed(t, 2)


def p_text(p: float | None) -> str:
    return fixed(p, 3)


def pct_text(r: float | None) -> str:
    if r is None or not math.isfinite(r):
        return MISSING
    return f"{100 * r:.2f}%"
