"""예측 — Minitab 'Predict'(적합 모형으로 새 설정의 적합치·SE Fit·신뢰구간·예측구간).

- 입력은 요인 이름(또는 문자) → 실제 단위 값. 숫자 요인은 z = (x − m)/h 로 코드화, 텍스트 요인은 수준 이름 → ±1,
  일반 완전요인은 수준 값 → 수준 번호. 블록은 평균화(효과 코딩 0), 중앙점 항(Ct Pt)은 모든 숫자 요인이 중점이면 1.
- 공변량은 값을 주면 그 값, 없으면 데이터 평균('Include covariates in prediction' 을 끄면 평균화와 같음).
- CI = Fit ± t(1 − α/2, 오차 DF)·SE Fit, PI = Fit ± t·√(SE Fit² + MSE).
- 표시: Minitab 'Predict' 출력은 각 값을 유효숫자 6자리(258.242, 2.35414, (253.393, 263.090)),
  반응 최적화기의 'Multiple Response Prediction' 은 SE Fit 유효숫자 3자리 기준(750.0, 34.3, (679.3, 820.7)).
  문서 예제(ThermalEnergyTest, InsulationProperties)와 일치한다.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from ..analysis import fmt
from ..analysis.means import _x0
from ..designs.general_full import GeneralFullFactorialDesign


@dataclass
class Prediction:
    fit: float
    se_fit: float
    ci: tuple[float, float]
    pi: tuple[float, float]
    settings: dict
    confidence: float


def _lookup(a, key: str) -> str:
    names = dict(zip([f.name for f in a.design.factors], a.design.letters))
    if key in names:
        return names[key]
    if key in a.design.letters:
        return key
    raise KeyError(f"요인 {key!r} 이 설계에 없습니다.")


def coded_setting(a, settings: dict) -> dict[str, float]:
    """실제 단위 설정 → 요인 문자별 코드값. 주지 않은 숫자 요인은 0(중점), 텍스트 요인은 낮은 수준."""
    d = a.design
    out = {}
    given = {_lookup(a, k): v for k, v in settings.items() if k not in a.covariates}
    for L, f in zip(d.letters, d.factors):
        if isinstance(d, GeneralFullFactorialDesign):
            v = given.get(L, f.levels[0])
            levels = [str(x) for x in f.levels]
            if str(v) not in levels and not (f.numeric and any(float(v) == float(x) for x in f.levels)):
                raise ValueError(f"{f.name} 의 수준이 아닙니다: {v!r}")
            idx = levels.index(str(v)) if str(v) in levels else [float(x) for x in f.levels].index(float(v))
            out[L] = idx + 1
        elif f.is_numeric:
            lo, hi = float(f.low), float(f.high)
            v = float(given.get(L, (lo + hi) / 2))
            out[L] = (v - (lo + hi) / 2) / ((hi - lo) / 2)
        else:
            v = given.get(L, f.low)
            if str(v) not in (str(f.low), str(f.high)):
                raise ValueError(f"{f.name} 의 수준이 아닙니다: {v!r} (가능: {f.low}, {f.high})")
            out[L] = -1.0 if str(v) == str(f.low) else 1.0
    return out


def design_row(a, settings: dict, covariates: dict | None = None) -> np.ndarray:
    coded = coded_setting(a, settings)
    numeric = [L for L, f in zip(a.design.letters, a.design.factors) if getattr(f, "is_numeric", False)]
    at_center = bool(numeric) and all(abs(coded[L]) < 1e-12 for L in numeric)
    cov = dict(covariates or {})
    cov.update({k: v for k, v in settings.items() if k in a.covariates})
    return _x0(a, coded, center=at_center, covariates=cov)


def predict(a, settings: dict, *, covariates: dict | None = None, confidence: float = 0.95) -> Prediction:
    x0 = design_row(a, settings, covariates)
    fit = float(x0 @ a.beta)
    if a.mse is None:
        nan = float("nan")
        return Prediction(fit, nan, (nan, nan), (nan, nan), dict(settings), confidence)
    se = float(np.sqrt(x0 @ a.coef_cov() @ x0))                     # 분할구는 전구 분산을 반영한 공분산
    t = float(stats.t.ppf(1 - (1 - confidence) / 2, a.df_error))
    spi = float(np.sqrt(se ** 2 + a.mse))
    return Prediction(fit, se, (fit - t * se, fit + t * se), (fit - t * spi, fit + t * spi), dict(settings), confidence)


def predict_many(a, rows: list[dict], **kw) -> list[Prediction]:
    return [predict(a, r, **kw) for r in rows]


def settings_table(a, settings: dict, covariates: dict | None = None) -> pd.DataFrame:
    """Minitab 'Settings' 표: Variable | Setting(주지 않은 요인은 중점·낮은 수준, 공변량은 평균)."""
    rows = []
    coded = coded_setting(a, settings)
    for L, f in zip(a.design.letters, a.design.factors):
        given = {_lookup(a, k): v for k, v in settings.items() if k not in a.covariates}
        if L in given:
            v = given[L]
        elif isinstance(a.design, GeneralFullFactorialDesign):
            v = f.levels[0]
        elif f.is_numeric:
            v = (float(f.low) + float(f.high)) / 2
        else:
            v = f.low
        rows.append({"Variable": f.name, "Setting": _fmt_setting(v)})
    cov = dict(covariates or {})
    for name, arr in a.covariates.items():
        v = settings.get(name, cov.get(name, float(np.mean(arr))))
        rows.append({"Variable": name, "Setting": _fmt_setting(v)})
    return pd.DataFrame(rows)


def _fmt_setting(v) -> str:
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return str(int(v)) if float(v).is_integer() else fmt.sig_text(float(v), 6).rstrip("0").rstrip(".")
    return str(v)


def prediction_table(p: Prediction) -> pd.DataFrame:
    """Minitab 'Prediction' 표(유효숫자 6자리): Fit | SE Fit | 95% CI | 95% PI."""
    c = int(round(p.confidence * 100))
    s6 = lambda v: fmt.sig_text(v, 6)  # noqa: E731
    return pd.DataFrame([{"Fit": s6(p.fit), "SE Fit": s6(p.se_fit), f"{c}% CI": f"({s6(p.ci[0])}, {s6(p.ci[1])})",
                          f"{c}% PI": f"({s6(p.pi[0])}, {s6(p.pi[1])})"}])


def response_prediction_row(response: str, p: Prediction) -> dict:
    """반응 최적화기 'Multiple Response Prediction' 행(SE Fit 유효숫자 3자리 기준)."""
    c = int(round(p.confidence * 100))
    by = lambda v: fmt.by_se(v, p.se_fit)  # noqa: E731
    return {"Response": response, "Fit": by(p.fit), "SE Fit": fmt.se_text(p.se_fit),
            f"{c}% CI": f"({by(p.ci[0])}, {by(p.ci[1])})", f"{c}% PI": f"({by(p.pi[0])}, {by(p.pi[1])})"}
