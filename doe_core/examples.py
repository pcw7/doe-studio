"""내장 예제 — Minitab 예제 파일(.MWX, 저장소에 넣지 않음)이 없어도 처음 쓰는 사람이 흐름을 따라 해 볼 수 있게 한다.

값은 정해 둔 '참 모형 + 잡음(고정 난수)'으로 계산한 **가상 데이터**다(실제 실험 결과가 아니다). 화학 연구실에서 흔한
세 가지 상황을 골랐다.

1. 반응 수율 선별: 온도·시간·촉매 2³ 완전요인 + 중앙점 3 → 곡면성이 유의하게 나온다(다음 단계: 축점 추가).
2. 반응 조건 최적화: 1 에 면 중심 축점 6개를 더한 중심합성설계 17런, 반응 수율·순도 두 개 → 다중 반응 최적화.
3. 용매 배합: 물·에탄올·아세톤 3성분 단순 중심 + 축점 10런, 용해도 → 혼합물 분석·삼각 등고선.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .designs.common import Factor
from .designs.factorial import create_two_level_design
from .designs.mixture import Component, create_simplex_centroid
from .designs.response_surface import add_axial_points
from .io.worksheet import Worksheet

FACTORS = [Factor("온도(°C)", 60, 80), Factor("시간(h)", 1, 3), Factor("촉매(wt%)", 0.5, 1.5)]


def _yield(a, b, c):
    return 75 + 6 * a + 3 * b + 4 * c - 2.5 * a * b - 3 * a * a - 2 * b * b - 1.5 * c * c


def _purity(a, b, c):
    return 97.5 - 1.2 * a + 0.4 * b - 0.8 * c - 0.5 * a * c - 0.6 * a * a


def _fill(ws: Worksheet, name: str, fn, sd: float, seed: int) -> None:
    coded = ws.design.coded.sort_values("StdOrder")
    rng = np.random.default_rng(seed)
    a, b, c = (coded[L].to_numpy(float) for L in ("A", "B", "C"))
    ws.add_column(name, np.round(fn(a, b, c) + rng.normal(0, sd, len(coded)), 1), order="std")


def reaction_screening() -> Worksheet:
    d = create_two_level_design(3, 8, factors=FACTORS, center_points=3, seed=20261101)
    ws = Worksheet(d)
    _fill(ws, "수율(%)", _yield, 0.4, 3)
    return ws


def reaction_optimization() -> Worksheet:
    d = create_two_level_design(3, 8, factors=FACTORS, center_points=3, seed=20261101)
    ws = Worksheet(add_axial_points(d, alpha="face"))
    _fill(ws, "수율(%)", _yield, 0.4, 3)
    _fill(ws, "순도(%)", _purity, 0.15, 3)
    return ws


def solvent_blend() -> Worksheet:
    comps = [Component("물"), Component("에탄올"), Component("아세톤")]
    d = create_simplex_centroid(3, components=comps, seed=20261101)
    coded = d.coded.sort_values("StdOrder")
    x1, x2, x3 = (coded[L].to_numpy(float) for L in d.letters)
    p = np.column_stack([x1, x2, x3])
    p = p / p.sum(axis=1, keepdims=True)                      # 비율(합 1)
    x1, x2, x3 = p.T
    y = 20 * x1 + 35 * x2 + 28 * x3 + 30 * x1 * x2 - 10 * x1 * x3 + 15 * x2 * x3
    rng = np.random.default_rng(4)
    ws = Worksheet(d)
    ws.add_column("용해도(g/L)", np.round(y + rng.normal(0, 0.3, len(coded)), 1), order="std")
    return ws


@dataclass(frozen=True)
class Example:
    key: str
    title_ko: str
    title_en: str
    desc_ko: str
    desc_en: str
    build: Callable[[], Worksheet]


EXAMPLES = [
    Example("screening", "반응 수율 선별", "Reaction yield screening",
            "온도·시간·촉매 2³ 완전요인 + 중앙점 3, 11런 · 반응: 수율. 분석하면 곡면성이 유의해 '축점 추가' 로 이어집니다.",
            "Temperature, time, catalyst: 2³ full factorial + 3 center points, 11 runs · response: yield. "
            "The analysis shows significant curvature, leading to 'Add axial points'.",
            reaction_screening),
    Example("optimization", "반응 조건 최적화", "Reaction optimization",
            "위 설계에 면 중심 축점 6개를 더한 중심합성설계 17런 · 반응: 수율·순도. 반응표면 분석과 다중 반응 최적화.",
            "The design above plus 6 face-centered axial points (central composite, 17 runs) · responses: yield, "
            "purity. Response surface analysis and multi-response optimization.",
            reaction_optimization),
    Example("blend", "용매 배합(혼합물)", "Solvent blend (mixture)",
            "물·에탄올·아세톤 단순 중심 + 축점 10런 · 반응: 용해도. 혼합물 분석·삼각 등고선·배합 최적화.",
            "Water, ethanol, acetone: simplex centroid + axial points, 10 runs · response: solubility. "
            "Mixture analysis, ternary contour plots and blend optimization.",
            solvent_blend),
]
