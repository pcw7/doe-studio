"""반응 최적화기 — Minitab 'Response Optimizer'(만족도 함수로 여러 반응을 동시에 최적화).

문서 근거(docs/spec/B_analysis_plots_optimizer.md 5절)
- 목표: Maximize / Minimize / Target. Lower·Target·Upper, Weight(0.1~10, 만족도 함수 형상), Importance(0.1~10).
  기본값: Lower = 데이터 최솟값, Upper = 데이터 최댓값, Maximize 의 Target = 최댓값, Minimize 의 Target = 최솟값.
- 개별 만족도 d (Derringer–Suich, 문서의 구간 구조와 같음, 지수 r = Weight)
    Maximize: y < L → 0,  L ≤ y ≤ T → ((y − L)/(T − L))^r,  y > T → 1
    Minimize: y < T → 1,  T ≤ y ≤ U → ((U − y)/(U − T))^r,  y > U → 0
    Target  : L ≤ y ≤ T → ((y − L)/(T − L))^r,  T ≤ y ≤ U → ((U − y)/(U − T))^r,  그 밖 → 0
- 종합 만족도 D = (Π d_i^{w_i})^{1/W}, W = Σ w_i (w = Importance). Minitab 은 D 를 최대화한다.
- 요인설계의 공변량은 고정값(기본 = 평균), 블록은 평균화. 연속 요인 범위는 설계점(축점 포함)의 범위.
- 출력: Parameters, Solution, Multiple Response Prediction(Variable | Setting / Response | Fit | SE Fit | CI | PI).

문서에 없어 정한 것
- 탐색: 연속 요인은 코드화 공간 상자 안에서 격자·무작위 시작점 + Powell 국소 탐색, 텍스트 요인은 수준 조합을 모두 시도.
  D = 0 인 곳에서는 범위 밖으로 벗어난 정도를 줄이는 보조 목적함수로 이동한다. D = 1 인 해가 여럿이면 처음 찾은 해.
- 표시: Parameters 의 하한·상한 기본값은 데이터 값의 자릿수(유효숫자 6자리 이내), 지정 값은 그대로.
  Solution 은 유효숫자 6자리에서 끝의 0 을 지운다(32.2129, 750, 1).
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from ..analysis import fmt
from ..designs.general_full import GeneralFullFactorialDesign
from ..plots.contour_plots import factor_range
from .predict import design_row, predict, response_prediction_row

GOALS = ("maximize", "minimize", "target")


@dataclass
class ResponseGoal:
    response: str
    goal: str
    lower: float | None = None
    target: float | None = None
    upper: float | None = None
    weight: float = 1.0
    importance: float = 1.0
    _given: set = field(default_factory=set, repr=False)

    def __post_init__(self):
        if self.goal not in GOALS:
            raise ValueError(f"목표는 {GOALS} 중 하나입니다.")
        for nm in ("weight", "importance"):
            v = getattr(self, nm)
            if not 0.1 <= v <= 10:
                raise ValueError(f"{nm} 은 0.1~10 이어야 합니다.")


def default_goal(a, goal: str, *, target: float | None = None, lower: float | None = None,
                 upper: float | None = None, weight: float = 1.0, importance: float = 1.0) -> ResponseGoal:
    """데이터 최솟값·최댓값으로 빈 값을 채운 목표."""
    y = getattr(a, "y_original", a.y)
    lo_d, hi_d = float(np.min(y)), float(np.max(y))
    given = {k for k, v in (("lower", lower), ("target", target), ("upper", upper)) if v is not None}
    if goal == "maximize":
        g = ResponseGoal(a.response, goal, lower if lower is not None else lo_d, target if target is not None else hi_d,
                         None, weight, importance)
    elif goal == "minimize":
        g = ResponseGoal(a.response, goal, None, target if target is not None else lo_d,
                         upper if upper is not None else hi_d, weight, importance)
    else:
        if target is None:
            raise ValueError("목표값(Target) 을 지정해야 합니다.")
        g = ResponseGoal(a.response, goal, lower if lower is not None else lo_d, target,
                         upper if upper is not None else hi_d, weight, importance)
    g._given = given
    _validate(g)
    return g


def _validate(g: ResponseGoal):
    if g.goal == "maximize" and not g.lower < g.target:
        raise ValueError(f"{g.response}: 최대화는 Lower < Target 이어야 합니다.")
    if g.goal == "minimize" and not g.target < g.upper:
        raise ValueError(f"{g.response}: 최소화는 Target < Upper 이어야 합니다.")
    if g.goal == "target" and not g.lower < g.target < g.upper:
        raise ValueError(f"{g.response}: 목표값은 Lower < Target < Upper 이어야 합니다.")


def desirability(y: float, g: ResponseGoal) -> float:
    r = g.weight
    if g.goal == "maximize":
        if y <= g.lower:
            return 0.0
        return 1.0 if y >= g.target else ((y - g.lower) / (g.target - g.lower)) ** r
    if g.goal == "minimize":
        if y >= g.upper:
            return 0.0
        return 1.0 if y <= g.target else ((g.upper - y) / (g.upper - g.target)) ** r
    if y <= g.lower or y >= g.upper:
        return 0.0
    if y <= g.target:
        return ((y - g.lower) / (g.target - g.lower)) ** r
    return ((g.upper - y) / (g.upper - g.target)) ** r


def composite(ds: list[float], goals: list[ResponseGoal]) -> float:
    W = sum(g.importance for g in goals)
    if any(d <= 0 for d in ds):
        return 0.0
    return float(math.exp(sum(g.importance * math.log(d) for d, g in zip(ds, goals)) / W))


def _shortfall(y: float, g: ResponseGoal) -> float:
    """만족도가 0 인 쪽으로 벗어난 정도(정규화). 탐색 보조용."""
    span = (g.upper if g.upper is not None else g.target) - (g.lower if g.lower is not None else g.target)
    span = abs(span) or 1.0
    if g.goal in ("maximize", "target") and y <= g.lower:
        return (g.lower - y) / span + 1e-9
    if g.goal in ("minimize", "target") and y >= g.upper:
        return (y - g.upper) / span + 1e-9
    return 0.0


@dataclass
class OptimizationResult:
    settings: dict                   # 요인 이름 → 실제 단위 값(텍스트 요인은 수준 이름)
    covariates: dict                 # 공변량 이름 → 고정값
    fits: dict                       # 반응 → 적합치
    d: dict                          # 반응 → 개별 만족도
    D: float
    predictions: dict = field(default_factory=dict)   # 반응 → Prediction


def evaluate(analyses: list, goals: list[ResponseGoal], settings: dict, covariates: dict | None = None):
    """설정에서의 (D, {반응: d}, {반응: 적합치})."""
    fits, ds = {}, {}
    for a, g in zip(analyses, goals):
        y = float(design_row(a, settings, covariates) @ a.beta)
        if getattr(a, "boxcox", None) is not None:
            y = float(a.boxcox.inverse(y))                       # 원래 단위로
        fits[g.response] = y
        ds[g.response] = desirability(y, g) if math.isfinite(y) else 0.0
    return composite(list(ds.values()), goals), ds, fits


def optimize(analyses: list, goals: list[ResponseGoal], *, hold: dict | None = None, covariates: dict | None = None,
             confidence: float = 0.95, n_random: int = 60, seed: int = 0) -> OptimizationResult:
    """종합 만족도를 최대화하는 요인 설정을 찾는다. hold: 고정할 요인 {이름: 값}."""
    if len(analyses) != len(goals) or not analyses:
        raise ValueError("반응 모형과 목표의 개수가 같아야 합니다.")
    for a, g in zip(analyses, goals):
        if a.response != g.response:
            raise ValueError(f"모형 반응({a.response})과 목표 반응({g.response})의 순서가 다릅니다.")
        _validate(g)
    d0 = analyses[0].design
    hold = dict(hold or {})
    cov = {}
    for a in analyses:
        for name, arr in a.covariates.items():
            cov.setdefault(name, float((covariates or {}).get(name, np.mean(arr))))

    names = [f.name for f in d0.factors]
    cont, cont_rng, disc, disc_levels = [], [], [], []
    for L, f in zip(d0.letters, d0.factors):
        if f.name in hold:
            continue
        if isinstance(d0, GeneralFullFactorialDesign):
            disc.append(f.name)
            disc_levels.append(list(f.levels))
        elif f.is_numeric:
            cont.append(f.name)
            cont_rng.append(factor_range(analyses[0], L))
        else:
            disc.append(f.name)
            disc_levels.append([f.low, f.high])
    lo = np.array([r[0] for r in cont_rng])
    hi = np.array([r[1] for r in cont_rng])
    rng = np.random.default_rng(seed)

    def settings_of(z, combo):
        s = dict(hold)
        z = np.clip(z, 0, 1)
        z = np.where(z < 1e-9, 0.0, np.where(z > 1 - 1e-9, 1.0, z))      # 경계에 아주 가까우면 경계값으로
        vals = np.where(z == 0, lo, np.where(z == 1, hi, lo + (hi - lo) * z))
        s.update({n: float(v) for n, v in zip(cont, vals)})
        s.update(dict(zip(disc, combo)))
        return s

    def objective(z, combo):
        s = settings_of(z, combo)
        D, _, fits = evaluate(analyses, goals, s, cov)
        if D > 0:
            return -D
        return 1.0 + sum(_shortfall(fits[g.response], g) for g in goals)

    best = None
    k = len(cont)
    for combo in itertools.product(*disc_levels) if disc else [()]:
        if k == 0:
            val = objective(np.zeros(0), combo)
            if best is None or val < best[0]:
                best = (val, np.zeros(0), combo)
            continue
        grid_pts = list(itertools.product(*[np.linspace(0, 1, 3)] * k)) if k <= 5 else []
        starts = [np.array(p) for p in grid_pts] + [rng.random(k) for _ in range(n_random)]
        scored = sorted(((objective(z, combo), z) for z in starts), key=lambda t: t[0])[:8]
        for _, z0 in scored:
            res = minimize(objective, z0, args=(combo,), method="Powell", bounds=[(0, 1)] * k,
                           options={"xtol": 1e-10, "ftol": 1e-12, "maxiter": 20000})
            z = np.clip(res.x, 0, 1)
            val = objective(z, combo)
            if best is None or val < best[0] - 1e-12:
                best = (val, z, combo)
    _, z, combo = best
    s = settings_of(z, combo)
    D, ds, fits = evaluate(analyses, goals, s, cov)
    ordered = {n: s[n] for n in names}
    preds = {g.response: predict(a, ordered, covariates=cov, confidence=confidence) for a, g in zip(analyses, goals)}
    return OptimizationResult(ordered, cov, fits, ds, D, preds)


# ---------------------------------------------------------------- 출력표


def _data_decimals(values) -> int:
    best = 0
    for v in np.asarray(values, dtype=float):
        for d in range(0, 7):
            if abs(round(v, d) - v) < 1e-9 * max(1.0, abs(v)):
                best = max(best, d)
                break
        else:
            best = max(best, 6)
    return best


def _bound_text(v, a, given: bool) -> str:
    if v is None:
        return ""
    if given:
        return f"{v:g}"
    d = min(_data_decimals(getattr(a, "y_original", a.y)), fmt.decimals_for_sig(v, 6))
    return fmt.fixed(v, d)


def _trim(v: float) -> str:
    s = fmt.sig_text(float(v), 6)
    return s.rstrip("0").rstrip(".") if "." in s else s


def parameters_table(analyses: list, goals: list[ResponseGoal]) -> pd.DataFrame:
    """Parameters 표. 데이터 최솟값·최댓값으로 채운 하한·목표·상한은 열 안에서 가장 긴 소수 자리로 맞춘다
    (문서 예제: 568.55 와 같은 열의 181.5 → 181.50). 사용자가 지정한 값은 입력 그대로."""
    cols = {"Lower": "lower", "Target": "target", "Upper": "upper"}
    dec = {}
    for col, attr in cols.items():
        ds = [min(_data_decimals(getattr(a, "y_original", a.y)), fmt.decimals_for_sig(getattr(g, attr), 6))
              for a, g in zip(analyses, goals) if getattr(g, attr) is not None and attr not in g._given]
        dec[col] = max(ds) if ds else 0
    rows = []
    for g in goals:
        row = {"Response": g.response, "Goal": g.goal.capitalize()}
        for col, attr in cols.items():
            v = getattr(g, attr)
            row[col] = "" if v is None else (f"{v:g}" if attr in g._given else fmt.fixed(v, dec[col]))
        row.update({"Weight": f"{g.weight:g}", "Importance": f"{g.importance:g}"})
        rows.append(row)
    return pd.DataFrame(rows)


def solution_table(res: OptimizationResult, goals: list[ResponseGoal]) -> pd.DataFrame:
    row = {"Solution": "1"}
    for name, v in res.settings.items():
        row[name] = v if isinstance(v, str) else _trim(v)
    for g in goals:
        row[f"{g.response}Fit"] = _trim(res.fits[g.response])
    row["CompositeDesirability"] = _trim(res.D)
    return pd.DataFrame([row])


def setting_table(res: OptimizationResult) -> pd.DataFrame:
    rows = [{"Variable": k, "Setting": v if isinstance(v, str) else _trim(v)} for k, v in res.settings.items()]
    rows += [{"Variable": k, "Setting": _trim(v)} for k, v in res.covariates.items()]
    return pd.DataFrame(rows)


def multiple_response_prediction(res: OptimizationResult) -> pd.DataFrame:
    return pd.DataFrame([response_prediction_row(r, p) for r, p in res.predictions.items()])
