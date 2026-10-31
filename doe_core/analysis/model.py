"""모형 항과 설계행렬 — Minitab 'Analyze Factorial Design > Terms' 에 해당.

설계행렬 열 순서(문서 'Model information'): 상수 → 공변량 → 블록 → 요인(주효과) → 교호작용. 중앙점 항은 맨 뒤.
- 2수준·PB 요인: 코드값(−1/+1) 한 열. 교호작용은 구성 요인 열의 곱.
- 일반 완전요인의 범주형 요인: (수준 수 − 1) 열 효과 코딩(마지막 수준이 전부 −1).
- 블록: (블록 수 − 1) 열 효과 코딩(−1, 0, +1). 각 계수 = 블록 평균 − 전체 평균.
- 중앙점 항(Ct Pt): (0, 1) 코딩, 기준 수준은 요인점(=0), 중앙점에서 1.
- 공변량: 원래 단위 그대로 한 열.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product

import numpy as np
import pandas as pd

from ..designs.general_full import GeneralFullFactorialDesign

KIND_ORDER = {"covariate": 0, "blocks": 1, "factor": 2, "center": 3}


@dataclass(frozen=True)
class Term:
    kind: str                       # "covariate" | "blocks" | "factor" | "center"
    letters: tuple[str, ...] = ()   # 요인 항이면 구성 요인 문자
    name: str = ""                  # 출력 이름(Material*InjPress, MeasTemp, Blocks, Ct Pt)

    @property
    def order(self) -> int:
        return len(self.letters)

    @property
    def word(self) -> str:
        return "".join(self.letters)

    @property
    def is_square(self) -> bool:
        return len(self.letters) == 2 and self.letters[0] == self.letters[1]

    @property
    def group_rank(self) -> int:
        """정렬·분산분석 그룹 순서: 선형 0, 제곱 1, r차 교호작용 1 + r."""
        if self.order == 1:
            return 0
        if self.is_square:
            return 1
        return 1 + self.order


def names_by_letter(design) -> dict[str, str]:
    return dict(zip(design.letters, [f.name for f in design.factors]))


def factor_term(design, letters) -> Term:
    names = names_by_letter(design)
    order = {L: i for i, L in enumerate(design.letters)}
    letters = tuple(sorted(letters, key=order.__getitem__))
    return Term("factor", letters, "*".join(names[L] for L in letters))


def parse_term(spec: str, design) -> Term:
    """'AB', 'A*B', 'Material*InjPress' 같은 문자열을 요인 항으로."""
    names = names_by_letter(design)
    by_name = {v: k for k, v in names.items()}
    s = spec.strip()
    if "*" in s:
        parts = [p.strip() for p in s.split("*")]
        letters = [by_name.get(p, p) for p in parts]
    elif s in by_name:
        letters = [by_name[s]]
    elif all(ch in names for ch in s):
        letters = list(s)
    else:
        raise ValueError(f"항을 해석할 수 없습니다: {spec!r}")
    square = len(letters) == 2 and letters[0] == letters[1]
    if any(L not in names for L in letters) or (len(set(letters)) != len(letters) and not square):
        raise ValueError(f"항을 해석할 수 없습니다: {spec!r}")
    if square and not _allows_squares(design):
        raise ValueError(f"제곱 항은 반응표면 설계에서만 쓸 수 있습니다: {spec!r}")
    return factor_term(design, letters)


def _allows_squares(design) -> bool:
    from ..designs.response_surface import ResponseSurfaceDesign
    return isinstance(design, ResponseSurfaceDesign)


def sort_terms(terms: list[Term], design) -> list[Term]:
    pos = {L: i for i, L in enumerate(design.letters)}
    return sorted(terms, key=lambda t: (KIND_ORDER[t.kind], t.group_rank, [pos[L] for L in t.letters]))


def factorial_terms(
    design,
    *,
    order: int | None = 2,
    terms: list[str] | None = None,
    covariates: tuple[str, ...] | list[str] = (),
    include_blocks: bool | None = None,
    include_center: bool | None = None,
    blocks_present: bool = False,
    center_present: bool = False,
) -> list[Term]:
    """모형 항 목록. terms 를 주면 그 항만(요인 항), 아니면 order 차수까지의 모든 교호작용."""
    out = [Term("covariate", (), c) for c in covariates]
    if include_blocks is None:
        include_blocks = blocks_present
    if include_blocks and blocks_present:
        out.append(Term("blocks", (), "Blocks"))
    if terms is not None:
        out += [parse_term(t, design) for t in terms]
    else:
        k = len(design.letters)
        top = k if order is None else min(order, k)
        for r in range(1, top + 1):
            out += [factor_term(design, c) for c in combinations(design.letters, r)]
    if include_center is None:
        include_center = center_present
    if include_center and center_present:
        out.append(Term("center", (), "Ct Pt"))
    return sort_terms(out, design)


RS_MODELS = ("linear", "linear+squares", "linear+interactions", "full quadratic")


def rs_terms(
    design,
    *,
    model: str = "full quadratic",
    terms: list[str] | None = None,
    covariates: tuple[str, ...] | list[str] = (),
    include_blocks: bool | None = None,
    blocks_present: bool = False,
) -> list[Term]:
    """반응표면 모형 항. model: linear / linear+squares / linear+interactions / full quadratic(기본)."""
    out = [Term("covariate", (), c) for c in covariates]
    if include_blocks is None:
        include_blocks = blocks_present
    if include_blocks and blocks_present:
        out.append(Term("blocks", (), "Blocks"))
    if terms is not None:
        out += [parse_term(t, design) for t in terms]
    else:
        if model not in RS_MODELS:
            raise ValueError(f"모형은 {RS_MODELS} 중 하나여야 합니다.")
        L = list(design.letters)
        out += [factor_term(design, (a,)) for a in L]
        if model in ("linear+squares", "full quadratic"):
            out += [factor_term(design, (a, a)) for a in L]
        if model in ("linear+interactions", "full quadratic"):
            out += [factor_term(design, c) for c in combinations(L, 2)]
    return sort_terms(out, design)


def is_hierarchical(terms: list[Term]) -> bool:
    words = {t.letters for t in terms if t.kind == "factor"}
    for t in terms:
        if t.kind == "factor" and t.order > 1:
            for r in range(1, t.order):
                for sub in combinations(t.letters, r):
                    if sub not in words:
                        return False
    return True


# ---------------------------------------------------------------- 설계행렬


def _effect_coding(levels: np.ndarray, ids: list) -> np.ndarray:
    """수준 ids 의 효과 코딩: 앞 L−1 수준은 지시변수, 마지막 수준 행은 전부 −1."""
    cols = np.zeros((len(levels), len(ids) - 1))
    for j, v in enumerate(ids[:-1]):
        cols[levels == v, j] = 1.0
    cols[levels == ids[-1], :] = -1.0
    return cols


def factor_columns(design, coded: pd.DataFrame, letter: str) -> tuple[np.ndarray, list[str]]:
    """요인 하나의 설계행렬 열과 열 이름 접미사."""
    if isinstance(design, GeneralFullFactorialDesign):
        f = design.factors[design.letters.index(letter)]
        ids = list(range(1, f.n_levels + 1))
        return _effect_coding(coded[letter].values.astype(int), ids), [str(v) for v in f.levels[:-1]]
    return coded[letter].values.astype(float)[:, None], [""]


def term_matrix(term: Term, design, coded: pd.DataFrame, cov: dict[str, np.ndarray]) -> tuple[np.ndarray, list[str]]:
    """항 하나의 열들과 열 이름."""
    n = len(coded)
    if term.kind == "covariate":
        return np.asarray(cov[term.name], dtype=float)[:, None], [term.name]
    if term.kind == "blocks":
        ids = sorted(coded["Blocks"].unique())
        return _effect_coding(coded["Blocks"].values, ids), [f"Blocks {b}" for b in ids[:-1]]
    if term.kind == "center":
        return (coded[design.point_col].values == 0).astype(float)[:, None], ["Ct Pt"]
    parts = [factor_columns(design, coded, L) for L in term.letters]
    cols, labels = [], []
    for combo in product(*[range(p[0].shape[1]) for p in parts]):
        col = np.ones(n)
        for (mat, _), j in zip(parts, combo):
            col = col * mat[:, j]
        cols.append(col)
        suffix = " ".join(p[1][j] for p, j in zip(parts, combo) if p[1][j])
        labels.append(term.name + (f" {suffix}" if suffix else ""))
    return np.column_stack(cols), labels
