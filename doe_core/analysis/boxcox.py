"""Box-Cox 변환 — Minitab 분석 'Options > Box-Cox transformation' 과 'Method' 표.

문서(Methods and formulas: model information, Method table, Specify the options)
- 변환: λ ≠ 0 이면 Y^λ, λ = 0 이면 ln(Y). λ < 0 이면 반응의 순서를 지키려고 −1 을 곱한다(−Y^λ).
- 최적 λ: −2 ~ 2 에서 잔차 제곱합을 가장 작게 하는 값. 기본은 0.5 단위로 반올림한 λ(Rounded λ)를 쓴다.
- 반응은 모두 양수여야 한다. Method 표: Rounded λ, Estimated λ, 95% CI for λ.

문서에 없어 정한 것
- 잔차 제곱합은 기하평균 G 로 표준화한 W = (Y^λ − 1)/(λ·G^(λ−1)) (λ = 0 이면 G·ln Y)로 비교한다(서로 다른 λ 의
  척도를 맞추는 표준 Box-Cox. Minitab 관리도 Box-Cox 도 G 로 표준화한 W 를 쓴다).
- 95% CI: 프로파일 우도 n·ln(SSE(λ)/SSE(λ̂)) ≤ χ²₁(0.95). 구간 끝이 −2 ~ 2 안에서 정해지지 않으면 '*'.
- 최적 λ 는 분석에 지정한 모형(단계적 선택이면 후보 전체 모형)으로 찾는다. 그 모형을 적합할 수 없으면 오류.
- 분석 표·잔차·효과도는 변환한 단위, 예측·반응 최적화기·등고선은 원래 단위로 되돌린 값(단조 변환이라 구간 끝도 그대로 되돌림).
- 반응 이름 표기: ln(Y), Y^0.5, -Y^(-1) 꼴. Method 표의 Estimated λ 는 유효숫자 6자리, CI 는 소수 4자리.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import optimize, stats

from . import fmt

LAMBDA_RANGE = (-2.0, 2.0)


def transform(y, lam: float) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    if lam == 0:
        return np.log(y)
    if lam > 0:
        return y ** lam
    return -(y ** lam)


def inverse(z, lam: float) -> np.ndarray:
    """변환값을 원래 단위로. 되돌릴 수 없는 값(λ>0 에서 음수, λ<0 에서 0 이상)은 nan."""
    z = np.asarray(z, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        if lam == 0:
            return np.exp(z)
        if lam > 0:
            return np.where(z >= 0, np.abs(z) ** (1 / lam), np.nan)
        return np.where(z < 0, np.abs(z) ** (1 / lam), np.nan)


def response_label(name: str, lam: float) -> str:
    if lam == 0:
        return f"ln({name})"
    if lam == 1:
        return name
    if lam > 0:
        return f"{name}^{lam:g}"
    return f"-{name}^({lam:g})"


def round_lambda(lam: float) -> float:
    r = math.floor(lam * 2 + 0.5) / 2
    return 0.0 if r == 0 else r


def _standardized(y: np.ndarray, lam: float, g: float) -> np.ndarray:
    if abs(lam) < 1e-12:
        return g * np.log(y)
    return (y ** lam - 1) / (lam * g ** (lam - 1))


def _sse(X: np.ndarray, w: np.ndarray) -> float:
    beta, *_ = np.linalg.lstsq(X, w, rcond=None)
    r = w - X @ beta
    return float(r @ r)


def estimate_lambda(X: np.ndarray, y: np.ndarray, confidence: float = 0.95) -> tuple[float, tuple[float | None, float | None]]:
    """(최적 λ, (CI 하한, 상한)). X 는 상수 열을 포함한 모형 행렬."""
    y = np.asarray(y, dtype=float)
    if np.any(y <= 0):
        raise ValueError("Box-Cox 변환을 쓰려면 반응이 모두 양수여야 합니다.")
    g = float(np.exp(np.mean(np.log(y))))
    lo, hi = LAMBDA_RANGE

    def sse(lam):
        return _sse(X, _standardized(y, lam, g))

    grid = np.linspace(lo, hi, 401)
    vals = np.array([sse(v) for v in grid])
    k = int(np.argmin(vals))
    a, b = grid[max(k - 1, 0)], grid[min(k + 1, len(grid) - 1)]
    res = optimize.minimize_scalar(sse, bounds=(a, b), method="bounded", options={"xatol": 1e-9})
    lam = float(res.x) if res.fun <= vals[k] else float(grid[k])
    smin = sse(lam)
    n = len(y)
    chi = float(stats.chi2.ppf(confidence, 1))
    if smin <= 0:
        return lam, (None, None)

    def f(v):
        return n * math.log(sse(v) / smin) - chi

    left = optimize.brentq(f, lo, lam, xtol=1e-10) if lam > lo and f(lo) > 0 else None
    right = optimize.brentq(f, lam, hi, xtol=1e-10) if lam < hi and f(hi) > 0 else None
    return lam, (left, right)


@dataclass(frozen=True)
class BoxCox:
    """분석에 쓴 Box-Cox 변환."""
    lam: float                                   # 실제로 쓴 λ
    response: str                                # 원래 반응 이름
    estimated: float | None = None               # 최적 λ(Optimal 을 골랐을 때)
    ci: tuple[float | None, float | None] | None = None
    rounded: bool = True
    confidence: float = 0.95

    @property
    def label(self) -> str:
        return response_label(self.response, self.lam)

    def transform(self, y) -> np.ndarray:
        return transform(y, self.lam)

    def inverse(self, z) -> np.ndarray:
        return inverse(z, self.lam)

    def method_table(self) -> pd.DataFrame:
        """Minitab 'Method' 표."""
        if self.estimated is None:
            rows = [("Box-Cox transformation", f"λ = {self.lam:g}")]
        else:
            first = f"Rounded λ = {self.lam:g}" if self.rounded else f"Optimal λ = {fmt.sig_text(self.lam, 6)}"
            lo, hi = self.ci or (None, None)
            ci = f"({fmt.fixed(lo, 4)}, {fmt.fixed(hi, 4)})"
            c = int(round(self.confidence * 100))
            rows = [("Box-Cox transformation", first), ("Estimated λ", fmt.sig_text(self.estimated, 6)),
                    (f"{c}% CI for λ", ci)]
        return pd.DataFrame(rows, columns=["Method", "Value"])


def make_boxcox(spec, X: np.ndarray | None, y: np.ndarray, response: str, *, rounded: bool = True) -> BoxCox | None:
    """spec: None(변환 없음) / 'optimal' / λ 숫자. X 는 최적 λ 를 찾을 모형 행렬."""
    if spec is None:
        return None
    y = np.asarray(y, dtype=float)
    if np.any(y <= 0):
        raise ValueError("Box-Cox 변환을 쓰려면 반응이 모두 양수여야 합니다.")
    if spec == "optimal":
        if X is None:
            raise ValueError("최적 λ 를 찾을 모형을 적합할 수 없습니다. λ 를 직접 지정하세요.")
        est, ci = estimate_lambda(X, y)
        lam = round_lambda(est) if rounded else est
        return BoxCox(lam, response, est, ci, rounded)
    lam = float(spec)
    if not -5 <= lam <= 5:
        raise ValueError("λ 는 −5 ~ 5 사이로 지정하세요(보통 −2 ~ 2).")
    return BoxCox(lam, response)
