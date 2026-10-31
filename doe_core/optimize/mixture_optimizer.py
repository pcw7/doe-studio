"""혼합물 반응 최적화 — Minitab 'Stat > DOE > Mixture > Response Optimizer'.

만족도 함수·종합 만족도·출력표는 요인설계 최적화기(optimizer.py)와 같다. 다른 점은 탐색 영역이다.
- 성분 비율: 합 = 1, 성분 하한·상한, 선형 제약. 사용자 정의 설계(성분 범위를 모름)는 설계점 비율의 최솟값~최댓값을
  범위로 쓴다(요인설계 최적화기가 설계점 범위를 쓰는 것과 같은 원칙).
- 숫자 공정 변수: 낮은 수준~높은 수준 사이 연속, 텍스트 공정 변수: 수준 조합을 모두 시도.
- 고정(hold): 성분 이름(비율) 또는 공정 변수 이름을 값으로 고정할 수 있다. 성분을 고정하면 나머지 성분이 남은 합을 나눈다.

문서에 없어 정한 것: 탐색은 설계점·무작위 실현 가능점에서 시작한 SLSQP(등식·부등식 제약)이고, D = 0 인 곳에서는
범위를 벗어난 정도를 줄이는 보조 목적함수를 쓴다. 해의 성분 값은 비율로 표시한다.
"""
from __future__ import annotations

import itertools

import numpy as np
from scipy.optimize import minimize

from ..analysis.mixture import fast_rows, feasible, predict_mixture, process_coded
from .optimizer import OptimizationResult, ResponseGoal, _shortfall, _validate, composite, desirability

_EPS = 1e-9


def search_bounds(design) -> tuple[np.ndarray, np.ndarray]:
    """성분 비율의 탐색 하한·상한."""
    P = design.coded[design.letters].values.astype(float)
    if design.kind == "custom":
        return P.min(axis=0), P.max(axis=0)
    return np.array([c.lower for c in design.components]), np.array([c.upper for c in design.components])


def _inequalities(design, lo, hi):
    from ..designs.mixture import Component, _inequalities as ineq
    comps = [Component(c.name, float(a), float(b)) for c, a, b in zip(design.components, lo, hi)]
    return ineq(comps, design.letters, design.constraints)


def _random_feasible(G, h, lo, hi, n, rng, fixed: dict) -> np.ndarray:
    q = len(lo)
    out = []
    free = [i for i in range(q) if i not in fixed]
    rest = 1 - sum(fixed.values())
    for _ in range(200):
        Z = rng.dirichlet(np.ones(len(free)), size=4 * n) * rest
        P = np.zeros((len(Z), q))
        P[:, free] = Z
        for i, v in fixed.items():
            P[:, i] = v
        ok = np.all(P @ G.T <= h + 1e-9, axis=1)
        out += list(P[ok])
        if len(out) >= n:
            break
    return np.array(out[:n]) if out else np.zeros((0, q))


def optimize_mixture(analyses: list, goals: list[ResponseGoal], *, hold: dict | None = None, confidence: float = 0.95,
                     n_random: int = 60, seed: int = 0) -> OptimizationResult:
    """종합 만족도를 최대화하는 혼합물(성분 비율)과 공정 변수 설정."""
    if len(analyses) != len(goals) or not analyses:
        raise ValueError("반응 모형과 목표의 개수가 같아야 합니다.")
    for a, g in zip(analyses, goals):
        if a.response != g.response:
            raise ValueError(f"모형 반응({a.response})과 목표 반응({g.response})의 순서가 다릅니다.")
        _validate(g)
    d = analyses[0].design
    q = d.q
    names = [c.name for c in d.components]
    hold = dict(hold or {})
    fixed = {names.index(k): float(v) for k, v in hold.items() if k in names}
    proc_hold = {k: v for k, v in hold.items() if k not in names}
    lo, hi = search_bounds(d)
    G, h = _inequalities(d, lo, hi)
    if sum(fixed.values()) > 1 + 1e-9:
        raise ValueError("고정한 성분 비율의 합이 1 을 넘습니다.")

    num_proc = [f for f in d.process if f.is_numeric and f.name not in proc_hold]
    txt_proc = [f for f in d.process if not f.is_numeric and f.name not in proc_hold]
    k = len(num_proc)

    def unpack(v, combo):
        P = v[:q]
        z = np.clip(v[q:], -1, 1)
        proc = dict(proc_hold)
        for f, zz in zip(num_proc, z):
            lo_f, hi_f = float(f.low), float(f.high)
            proc[f.name] = (lo_f + hi_f) / 2 + zz * (hi_f - lo_f) / 2
        proc.update({f.name: lv for f, lv in zip(txt_proc, combo)})
        return P, proc

    rowfns = [fast_rows(a) for a in analyses]

    def evaluate(P, proc):
        zc = process_coded(d, proc)
        Z = np.array([[zc[X] for X in d.process_letters]]) if d.process else None
        fits, ds = {}, {}
        for a, g, fn in zip(analyses, goals, rowfns):
            y = float(fn(P[None, :], Z)[0] @ a.beta)
            fits[g.response] = y
            ds[g.response] = desirability(y, g)
        return composite([ds[g.response] for g in goals], goals), ds, fits

    def objective(v, combo):
        P, proc = unpack(v, combo)
        D, _, fits = evaluate(P, proc)
        if D > 0:
            return -D
        return 1.0 + sum(_shortfall(fits[g.response], g) for g in goals)

    cons = [{"type": "eq", "fun": lambda v: np.sum(v[:q]) - 1.0},
            {"type": "ineq", "fun": lambda v: h - G @ v[:q]}]
    cons += [{"type": "eq", "fun": (lambda v, i=i, val=val: v[i] - val)} for i, val in fixed.items()]
    bounds = [(0.0, 1.0)] * q + [(-1.0, 1.0)] * k

    rng = np.random.default_rng(seed)
    design_P = np.unique(d.coded[d.letters].values.astype(float).round(12), axis=0)
    starts_P = design_P[np.all(design_P @ G.T <= h + 1e-9, axis=1)] if not fixed else np.zeros((0, q))
    starts_P = np.vstack([starts_P, _random_feasible(G, h, lo, hi, n_random, rng, fixed)])
    if not len(starts_P):
        raise ValueError("성분 범위·제약을 모두 만족하는 혼합물이 없습니다.")
    zs = [np.zeros(k)] + [rng.uniform(-1, 1, k) for _ in range(3)] if k else [np.zeros(0)]

    best = None
    for combo in itertools.product(*[[f.low, f.high] for f in txt_proc]) if txt_proc else [()]:
        cand = [np.concatenate([p, z]) for p in starts_P for z in zs]
        scored = sorted(((objective(v, combo), v) for v in cand), key=lambda t: t[0])[:10]
        for _, v0 in scored:
            r = minimize(objective, v0, args=(combo,), method="SLSQP", bounds=bounds, constraints=cons,
                         options={"ftol": 1e-12, "maxiter": 500})
            v = r.x.copy()
            v[:q] = _repair(v[:q], lo, hi, fixed)
            P, _ = unpack(v, combo)
            if not feasible_box(P, G, h):
                v = v0
            val = objective(v, combo)
            if best is None or val < best[0] - 1e-12:
                best = (val, v, combo)
    _, v, combo = best
    P, proc = unpack(v, combo)
    P = np.round(np.where(np.abs(P) < 1e-10, 0.0, P), 12)       # 수치 잡음 정리(0.29999999999999716 → 0.3)
    D, ds, fits = evaluate(P, proc)
    settings = {n: float(x) for n, x in zip(names, P)}
    for f in d.process:
        val = proc[f.name]
        if f.is_numeric:
            lo_f, hi_f = float(f.low), float(f.high)
            val = lo_f if abs(val - lo_f) < 1e-7 * max(1, abs(lo_f)) else (hi_f if abs(val - hi_f) < 1e-7 * max(1, abs(hi_f)) else float(val))
        settings[f.name] = val
    blend = {n: settings[n] for n in names}
    proc_set = {f.name: settings[f.name] for f in d.process}
    preds = {g.response: predict_mixture(a, blend, proc_set, confidence=confidence) for a, g in zip(analyses, goals)}
    return OptimizationResult(settings, {}, fits, ds, D, preds)


def _repair(P: np.ndarray, lo: np.ndarray, hi: np.ndarray, fixed: dict, snap: float = 1e-6) -> np.ndarray:
    """SLSQP 해의 작은 제약 위반 정리: 범위로 자르고 경계 근처 값은 경계로, 남는 합은 나머지 성분에 나눈다."""
    P = np.clip(np.asarray(P, dtype=float), lo, hi)
    locked = np.zeros(len(P), bool)
    for i, v in fixed.items():
        P[i], locked[i] = v, True
    near_lo, near_hi = np.abs(P - lo) < snap, np.abs(P - hi) < snap
    P = np.where(near_lo & ~locked, lo, np.where(near_hi & ~locked, hi, P))
    locked |= near_lo | near_hi
    free = ~locked
    r = 1.0 - P.sum()
    if free.any() and abs(r) > 0:
        room = (hi - P) if r > 0 else (P - lo)
        room = np.where(free, np.maximum(room, 0), 0)
        if room.sum() > 0:
            P = P + np.sign(r) * room * min(1.0, abs(r) / room.sum())
    return P


def feasible_box(P: np.ndarray, G: np.ndarray, h: np.ndarray, tol: float = 1e-10) -> bool:
    return bool(np.all(G @ P <= h + tol) and abs(P.sum() - 1) < 1e-7 and np.all(P >= -tol))


__all__ = ["optimize_mixture", "search_bounds", "feasible", "feasible_box"]
