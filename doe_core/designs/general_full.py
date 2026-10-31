"""일반 완전요인설계 생성 — Minitab 'Create Factorial Design > General full factorial design' 에 해당.

문서 근거(docs/spec/A_factorial_create.md 1.6절, 예제 3요인 3수준 27런)
- Designs: 요인 이름, 요인별 수준 수, 반복 수, 반복 블록(Block on replicates).
- Factors: 이름(기본은 I 를 건너뛴 알파벳), 유형(Text/Numeric), 수준 값(라벨).
- 중앙점·접기·축점 없음. 워크시트 C3 열 이름은 PtType(전부 1).
- Design Summary: Factors/Replicates, Base runs/Total runs, Base blocks/Total blocks, Number of levels.
- Design Table: Run, Blk, 요인별 수준 번호(1, 2, 3, …).

문서에 없어 정한 것(사양서 4절 기록)
- 요인 수 2~15, 수준 수 2~100.
- 표준 순서는 첫 요인이 가장 빨리 바뀐다(2수준 Yates 순서와 같은 규칙).
- 숫자 요인의 기본 수준 값은 1, 2, …, L.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np
import pandas as pd

from .common import assign_orders, factor_letters


@dataclass
class GeneralFactor:
    name: str
    levels: list = field(default_factory=list)   # 수준 값(숫자 또는 텍스트). 비우면 n_levels 로 1..L
    n_levels: int | None = None
    numeric: bool | None = None                  # None 이면 수준 값으로 판단

    def __post_init__(self):
        if not self.levels:
            if self.n_levels is None:
                raise ValueError(f"요인 {self.name!r}: levels 또는 n_levels 가 필요합니다.")
            self.levels = list(range(1, self.n_levels + 1))
        self.n_levels = len(self.levels)
        if not 2 <= self.n_levels <= 100:
            raise ValueError(f"요인 {self.name!r}: 수준 수는 2~100 이어야 합니다.")
        if len(set(map(str, self.levels))) != self.n_levels:
            raise ValueError(f"요인 {self.name!r}: 수준 값이 중복됩니다.")
        if self.numeric is None:
            self.numeric = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in self.levels)
        if self.numeric and not all(isinstance(v, (int, float)) for v in self.levels):
            raise ValueError(f"요인 {self.name!r}: 숫자 요인의 수준 값은 숫자여야 합니다.")


@dataclass
class GeneralFullFactorialDesign:
    factors: list[GeneralFactor]
    letters: list[str]
    runs: pd.DataFrame          # StdOrder, RunOrder, PtType, Blocks, 요인열(실제 수준 값), RunOrder 순
    coded: pd.DataFrame         # 같은 행 순서, 요인열은 수준 번호 1..L(열 이름 A,B,…)
    replicates: int
    n_blocks: int
    seed: int | None = None

    @property
    def n_factors(self) -> int:
        return len(self.factors)

    @property
    def n_runs(self) -> int:
        return len(self.runs)

    @property
    def base_runs(self) -> int:
        return self.n_runs // self.replicates

    def summary(self) -> dict:
        return {
            "Factors": self.n_factors,
            "Replicates": self.replicates,
            "Base runs": self.base_runs,
            "Total runs": self.n_runs,
            "Base blocks": 1,
            "Total blocks": self.n_blocks,
            "Number of levels": ", ".join(str(f.n_levels) for f in self.factors),
        }

    def summary_text(self) -> str:
        s = self.summary()
        return "\n".join([
            "Design Summary",
            f"Factors: {s['Factors']}  Replicates: {s['Replicates']}",
            f"Base runs: {s['Base runs']}  Total runs: {s['Total runs']}",
            f"Base blocks: {s['Base blocks']}  Total blocks: {s['Total blocks']}",
            f"Number of levels: {s['Number of levels']}",
        ])

    def design_table(self) -> pd.DataFrame:
        """Minitab 'Design Table (randomized)': Run, Blk, 요인별 수준 번호."""
        tbl = self.coded[self.letters].copy()
        tbl.insert(0, "Blk", self.coded["Blocks"].values)
        tbl.insert(0, "Run", self.coded["RunOrder"].values)
        return tbl.reset_index(drop=True)


def create_general_full_factorial(
    factors: list[GeneralFactor] | list[int],
    *,
    replicates: int = 1,
    block_on_replicates: bool = False,
    randomize: bool = True,
    seed: int | None = None,
) -> GeneralFullFactorialDesign:
    """Minitab 'Create General Full Factorial Design' 과 같은 설계를 만든다.

    factors 는 GeneralFactor 목록 또는 요인별 수준 수 목록([3, 3, 2] 등. 이름은 A, B, C …, 수준 값 1..L).
    """
    if factors and all(isinstance(f, int) for f in factors):
        factors = [GeneralFactor(L, n_levels=k) for L, k in zip(factor_letters(len(factors)), factors)]
    if not 2 <= len(factors) <= 15:
        raise ValueError("일반 완전요인설계의 요인 수는 2~15 이어야 합니다.")
    if replicates < 1:
        raise ValueError("replicates ≥ 1 이어야 합니다.")
    letters = factor_letters(len(factors))

    # 첫 요인이 가장 빨리 바뀌는 표준 순서: product 는 마지막 요인이 가장 빨리 바뀌므로 뒤집어 만든다.
    combos = [tuple(reversed(c)) for c in product(*[range(1, f.n_levels + 1) for f in reversed(factors)])]
    base = pd.DataFrame(combos, columns=letters)
    base["PtType"] = 1
    base["_order"] = np.arange(len(base))

    parts = []
    for r in range(replicates):
        c = base.copy()
        c["Blocks"] = r + 1 if block_on_replicates else 1
        c["_rep"] = r
        parts.append(c)
    coded = pd.concat(parts, ignore_index=True)
    coded = assign_orders(coded, ["Blocks", "_rep", "_order"], randomize=randomize, seed=seed)
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", *letters]]

    runs = coded[["StdOrder", "RunOrder", "PtType", "Blocks"]].copy()
    for L, f in zip(letters, factors):
        values = np.array(f.levels, dtype=float if f.numeric else object)
        runs[f.name] = values[coded[L].values - 1]
    return GeneralFullFactorialDesign(
        factors=list(factors), letters=letters, runs=runs, coded=coded, replicates=replicates,
        n_blocks=replicates if block_on_replicates else 1, seed=seed,
    )
