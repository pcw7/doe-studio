"""검정력·표본 크기 — Minitab 'Stat > Power and Sample Size' 의 2-Level Factorial · Plackett-Burman · General Full Factorial.

문서(Methods and formulas, Example, All statistics)
- 2수준·PB: 오차 DF ν = 전체 관측 − 추정 모수, 전체 관측 = 반복 n × 꼭짓점 r + 중앙점(블록당 × 블록 수).
  추정 모수(2수준) = 반복당 꼭짓점 수 + 1(중앙점 항) + (블록 − 1) − 생략 항 수.
  추정 모수(PB) = (요인 수 + 1) + 1(중앙점 항) − 생략 주효과 수.
  λ = n·r·δ²/(4σ²), 검정력 = 1 − F(f_α; 1, ν, λ) (비중심 F, f_α = F(1, ν) 의 위쪽 α 점).
- 일반 완전요인: 수준이 가장 많은 요인(k 수준) 기준. k1 = k − 1, k2 = 전체 런 − (블록 − 1) − 모형 요인 항 DF 합 − 1,
  β = n·δ²/(2σ²)(n = 그 요인 한 수준의 표본 크기 = 전체 런/k, δ = 최대 차이), 검정력 = 1 − F(f_{1−α}; k1, k2, β).
  블록을 넣으면 반복마다 블록(블록 수 = 반복 수).
- 반복 수 풀기: 검정력이 목표 이상이 되는 가장 작은 정수 반복(Target Power · Actual Power). 효과 풀기: 검정력 = 목표인 효과.

검증: 문서 예제 4개(2수준 5요인 8꼭짓점, PB 10요인 12런, 일반 완전요인 3×3, 해석 페이지 표 5개)가 6자리까지 일치.

문서와 다른 점: 2수준 블록 예제(16꼭짓점, 블록 4, 블록당 중앙점 4 → 0.741569, 0.967699)는 '블록과 교락된 항'을 추정 모수에서
빼지 않아야 재현돼, 교락 항은 빼지 않는다. 표시 형식(문서 해석 페이지): Power·Actual Power 소수 6자리, 풀어 낸 효과는 유효숫자 6자리,
입력한 효과·목표 검정력은 입력 그대로, 풀어 낸 효과는 유효숫자 6자리이되 소수 7자리 이하(0.0153027, 0.0073261). 머리글 문구는 문서 예제 출력에서 옮김(일부 추정).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import optimize, stats

from .analysis import fmt


def _num_text(v: float) -> str:
    return f"{v:g}"


# ---------------------------------------------------------------- 공식


def two_level_df(*, corner_points: int, reps: int, center_points: int = 0, blocks: int = 1, omit: int = 0,
                 center_term: bool = True) -> tuple[int, int]:
    """(전체 런, 오차 DF) — 2수준 요인설계."""
    total = reps * corner_points + center_points * blocks
    params = corner_points + (1 if center_term and center_points > 0 else 0) + (blocks - 1) - omit
    return total, total - params


def pb_df(*, factors: int, runs: int, reps: int, center_points: int = 0, omit: int = 0,
          center_term: bool = True) -> tuple[int, int]:
    """(전체 런, 오차 DF) — Plackett-Burman."""
    total = reps * runs + center_points
    params = factors + 1 + (1 if center_term and center_points > 0 else 0) - omit
    return total, total - params


def f_power(effect: float, sigma: float, n_corner: int, nu: int, alpha: float = 0.05) -> float | None:
    """2수준·PB: 1 − F(f_α; 1, ν, λ), λ = N·δ²/(4σ²) (N = 꼭짓점 관측 수)."""
    if nu <= 0:
        return None
    lam = n_corner * effect ** 2 / (4 * sigma ** 2)
    f = stats.f.ppf(1 - alpha, 1, nu)
    if lam <= 0:                                   # 효과 0: 중심 F(scipy 비중심 F 는 λ = 0 에서 불안정)
        return float(stats.f.sf(f, 1, nu))
    return float(stats.ncf.sf(f, 1, nu, lam))


def gff_term_df(levels: list[int], order: int) -> int:
    """일반 완전요인 모형의 요인 항 DF 합(order 차 교호작용까지)."""
    total = 0
    for r in range(1, min(order, len(levels)) + 1):
        for S in combinations(levels, r):
            total += int(np.prod([L - 1 for L in S]))
    return total


def gff_power(delta: float, sigma: float, *, levels: list[int], reps: int, order: int, blocks: bool = False,
              alpha: float = 0.05) -> tuple[int, float | None]:
    """(전체 런, 검정력) — 일반 완전요인, 수준이 가장 많은 요인 기준."""
    k = max(levels)
    n1 = int(np.prod(levels)) * reps
    n2 = (reps - 1) if blocks else 0
    k2 = n1 - n2 - gff_term_df(levels, order) - 1
    if k2 <= 0:
        return n1, None
    n = n1 / k
    beta = n * delta ** 2 / (2 * sigma ** 2)
    f = stats.f.ppf(1 - alpha, k - 1, k2)
    if beta <= 0:
        return n1, float(stats.f.sf(f, k - 1, k2))
    return n1, float(stats.ncf.sf(f, k - 1, k2, beta))


# ---------------------------------------------------------------- 풀기


def _solve_reps(power_of, target: float, max_reps: int = 1000):
    for n in range(1, max_reps + 1):
        p = power_of(n)
        if p is not None and p >= target:
            return n, p
    raise ValueError("반복 1000회 안에서 목표 검정력에 이르지 못합니다.")


def _solve_effect(power_at, target: float) -> float:
    if power_at(1.0) is None:
        raise ValueError("오차 자유도가 없어 효과를 구할 수 없습니다.")
    hi = 1e-6
    while power_at(hi) < target:
        hi *= 2
        if hi > 1e12:
            raise ValueError("효과를 구할 수 없습니다.")
    return float(optimize.brentq(lambda e: power_at(e) - target, 0.0, hi, xtol=1e-14, rtol=1e-12))


@dataclass
class PowerResult:
    kind: str                         # "two_level" | "pb" | "gff"
    solve: str                        # "power" | "reps" | "effect"
    header: list[str]
    table: pd.DataFrame
    curves: list[dict] = field(default_factory=list)   # 그래프용: {label, reps, cp, power_at(effect)}
    points: list[tuple[float, float, str]] = field(default_factory=list)   # (효과, 검정력, 곡선 이름)


def _which(reps, effects, powers) -> str:
    given = [x is not None and len(x) > 0 for x in (reps, effects, powers)]
    if sum(given) != 2:
        raise ValueError("반복 수·효과·검정력 중 두 가지를 지정하세요.")
    return "power" if not given[2] else ("reps" if not given[0] else "effect")


def power_two_level(*, factors: int, corner_points: int, sigma: float, reps=None, effects=None, powers=None,
                    center_points=(0,), blocks: int = 1, omit: int = 0, center_term: bool = True,
                    alpha: float = 0.05) -> PowerResult:
    """Minitab 'Power and Sample Size for 2-Level Factorial Design'."""
    if corner_points & (corner_points - 1) or corner_points > 2 ** factors or corner_points < 4:
        raise ValueError("꼭짓점 수는 4 이상 2^요인 수 이하의 2의 거듭제곱이어야 합니다.")
    solve = _which(reps, effects, powers)

    def pw(n, cp, e):
        total, nu = two_level_df(corner_points=corner_points, reps=n, center_points=cp, blocks=blocks, omit=omit,
                                 center_term=center_term)
        return total, f_power(e, sigma, n * corner_points, nu, alpha)

    cp_col = "Center Points Per Block" if blocks > 1 else "Center Points"
    rows, curves, points = _generic_rows(solve, pw, reps, effects, powers, center_points, cp_col, "Effect")
    header = ["2-Level Factorial Design", f"α = {_num_text(alpha)}  Assumed standard deviation = {_num_text(sigma)}",
              f"Factors: {factors}  Base Design: {factors}, {corner_points}",
              f"Blocks: {'none' if blocks == 1 else blocks}"]
    if center_term and any(cp > 0 for cp in center_points):
        header.append("Including a term for center points in model.")
    if omit:
        header.append(f"Number of terms omitted from model: {omit}")
    return PowerResult("two_level", solve, header, rows, curves, points)


def power_pb(*, factors: int, runs: int, sigma: float, reps=None, effects=None, powers=None, center_points=(0,),
             omit: int = 0, center_term: bool = True, alpha: float = 0.05) -> PowerResult:
    """Minitab 'Power and Sample Size for Plackett-Burman Design'."""
    if runs % 4 or runs <= factors:
        raise ValueError("런 수는 4의 배수이고 요인 수보다 커야 합니다.")
    solve = _which(reps, effects, powers)

    def pw(n, cp, e):
        total, nu = pb_df(factors=factors, runs=runs, reps=n, center_points=cp, omit=omit, center_term=center_term)
        return total, f_power(e, sigma, n * runs, nu, alpha)

    res = _generic_rows(solve, pw, reps, effects, powers, center_points, "Center Points", "Effect")
    header = ["Plackett-Burman Design", f"α = {_num_text(alpha)}  Assumed standard deviation = {_num_text(sigma)}",
              f"Factors: {factors}  Design: {runs}"]
    if any(cp > 0 for cp in center_points):
        header.append(f"Center pts (total): {', '.join(str(c) for c in center_points)}")
        if center_term:
            header.append("Including a term for center points in model.")
    if omit:
        header.append(f"Number of main effect terms omitted from model: {omit}")
    return PowerResult("pb", solve, header, *res)


def power_gff(*, levels: list[int], sigma: float, reps=None, deltas=None, powers=None, order: int = 2,
              blocks: bool = False, alpha: float = 0.05) -> PowerResult:
    """Minitab 'Power and Sample Size for General Full Factorial Design'(최대 차이 δ)."""
    if len(levels) < 1 or any(L < 2 for L in levels):
        raise ValueError("요인마다 수준은 2 이상이어야 합니다.")
    solve = _which(reps, deltas, powers)

    def pw(n, cp, e):
        return gff_power(e, sigma, levels=levels, reps=n, order=order, blocks=blocks, alpha=alpha)

    rows, curves, points = _generic_rows(solve, pw, reps, deltas, powers, (None,), None, "Maximum Difference")
    header = ["General Full Factorial Design", f"α = {_num_text(alpha)}  Assumed standard deviation = {_num_text(sigma)}",
              f"Factors: {len(levels)}  Number of levels: {', '.join(str(L) for L in levels)}",
              f"Include terms in the model up through order: {order}"]
    if blocks:
        header.append("Include blocks in model.")
    return PowerResult("gff", solve, header, rows, curves, points)


def _generic_rows(solve, pw, reps, effects, powers, center_points, cp_col, eff_col):
    rows, curves, points = [], [], []
    for cp in center_points:
        lead = {cp_col: str(cp)} if cp_col else {}
        if solve == "power":
            for e in effects:
                for n in reps:
                    total, p = pw(n, cp, e)
                    rows.append({**lead, eff_col: _num_text(e), "Reps": str(n), "Total Runs": str(total),
                                 "Power": fmt.fixed(p, 6) if p is not None else fmt.MISSING})
                    if p is not None:
                        points.append((e, p, f"{n}" + (f", {cp}" if cp_col else "")))
            for n in reps:
                curves.append({"reps": n, "cp": cp, "f": (lambda e, n=n, cp=cp: pw(n, cp, e)[1])})
        elif solve == "reps":
            for e in effects:
                for target in powers:
                    n, p = _solve_reps(lambda n: pw(n, cp, e)[1], target)
                    rows.append({**lead, eff_col: _num_text(e), "Reps": str(n), "Total Runs": str(pw(n, cp, e)[0]),
                                 "Target Power": _num_text(target), "Actual Power": fmt.fixed(p, 6)})
                    points.append((e, p, f"{n}" + (f", {cp}" if cp_col else "")))
                    if not any(c["reps"] == n and c["cp"] == cp for c in curves):
                        curves.append({"reps": n, "cp": cp, "f": (lambda e, n=n, cp=cp: pw(n, cp, e)[1])})
        else:
            for n in reps:
                for target in powers:
                    e = _solve_effect(lambda e: pw(n, cp, e)[1], target)
                    rows.append({**lead, "Reps": str(n), "Total Runs": str(pw(n, cp, 1.0)[0]),
                                 "Power": _num_text(target),
                                 eff_col: fmt.fixed(e, min(fmt.decimals_for_sig(e, 6), 7))})
                    points.append((e, target, f"{n}" + (f", {cp}" if cp_col else "")))
                curves.append({"reps": n, "cp": cp, "f": (lambda e, n=n, cp=cp: pw(n, cp, e)[1])})
    return pd.DataFrame(rows), curves, points


def power_curve_data(res: PowerResult, n: int = 80) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """곡선마다 (이름, 효과, 검정력). 효과 범위는 점들의 최대 효과의 1.6배까지."""
    e_max = max([p[0] for p in res.points] + [1e-12]) * 1.6
    xs = np.linspace(0, e_max, n)
    out = []
    for c in res.curves:
        ys = np.array([c["f"](x) for x in xs], dtype=float)
        if np.any(~np.isfinite(ys)):
            continue
        name = f"{c['reps']}" + (f", {c['cp']}" if c["cp"] is not None else "")
        out.append((name, xs, ys))
    return out
