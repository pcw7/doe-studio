"""Plackett-Burman 설계 생성 — Minitab 'Create Factorial Design > Plackett-Burman design' 에 해당.

Minitab 문서 "Plackett-Burman designs" 의 규칙
- 런 수 n 은 12~48 의 4의 배수. 8·16 런은 같은 해상도 이상의 2수준 요인설계가 있어 제공하지 않는다.
- 요인 수 k 는 2~47, k ≤ n − 1. k < n − 1 이면 처음 k 열만 쓴다.
- n ≠ 28: 생성열 하나를 순환 치환해 (n−1)×(n−1) 행렬을 만들고 마지막에 전부 − 인 행을 붙인다.
  열 j 는 생성열을 j 칸 아래로 민 것이다(문서 예제 9요인 12런으로 확인).
- n = 28: 문서의 9행 × 27열 블록을 9열씩 A|B|C 로 나눠 행 방향으로 순환 치환([A B C] → [C A B] → [B C A])하고
  전부 − 인 행을 붙인다. 문서 문장이 행/열 어느 쪽으로도 읽혀 네 해석 모두 직교임을 확인했고, 다른 런 수와 같은
  "한 칸씩 오른쪽" 규칙을 택했다(Minitab 실물 대조 전까지 미검증).
- n = 40: "20런 설계의 이중화". [[D20, +1, −D20], [D20, −1, D20]] 로 만들면 직교이고 첫 열이 문서의 생성열과 같다.
  문서의 40런 생성열은 38개 부호로, 가운데 '−' 하나가 빠진 오타다.
- 44런 생성열의 '+-' 는 두 부호로 나눠 읽는다(43개).
- 중앙점은 '반복당' 지정 수이고 텍스트 요인이 Q 개면 2^Q 배. 블록과 무관하다.
- 워크시트 C3 열 이름은 PtType(0 중앙점, 1 모서리점).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .common import Factor, assign_orders, center_point_rows, default_factors, factor_letters, sign_table, to_levels

PB_RUNS = (12, 20, 24, 28, 32, 36, 40, 44, 48)

_GENERATORS = {
    12: "+ + - + + + - - - + -",
    20: "+ + - - + + + + - + - + - - - - + + -",
    24: "+ + + + + - + - + + - - + + - - + - + - - - -",
    32: "- - - - + - + - + + + - + + - - - + + + + + - - + + - + - - +",
    36: "- + - + + + - - - + + + + + - + + + - - + - - - - + - + - + + - - + -",
    44: "+ + - - + - + - - + + + - + + + + + - - - + - + + + - - - - - + - - - + +- + - + + -",
    48: "+ + + + + - + + + + - - + - + - + + + - - + - - + + - + + - - - + - + - + + - - - - + - - - -",
}

_ROWS_28 = """
+ - + + + + - - - - + - - - + - - + + + - + - + + - +
+ + - + + + - - - - - + + - - + - - - + + + + - + + -
- + + + + + - - - + - - - + - - + - + - + - + + - + +
- - - + - + + + + - - + - + - - - + + - + + + - + - +
- - - + + - + + + + - - - - + + - - + + - - + + + + -
- - - - + + + + + - + - + - - - + - - + + + - + - + +
+ + + - - - + - + - - + - - + - + - + - + + - + + + -
+ + + - - - + + - + - - + - - - - + + + - + + - - + +
+ + + - - - - + + - + - - + - + - - - + + - + + + - +
"""


def _parse(s: str) -> list[int]:
    return [1 if t == "+" else -1 for t in s.replace("+-", "+ -").split()]


def _cyclic(g: list[int]) -> np.ndarray:
    m = len(g)
    ga = np.asarray(g, dtype=int)
    idx = (np.arange(m)[:, None] - np.arange(m)[None, :]) % m
    return np.vstack([ga[idx], -np.ones(m, dtype=int)])


def pb_matrix(n_runs: int) -> np.ndarray:
    """n_runs × (n_runs − 1) 의 ±1 행렬(표준 순서). 각 열의 합은 0 이고 열끼리 직교한다."""
    if n_runs not in PB_RUNS:
        raise ValueError(f"Plackett-Burman 런 수는 {PB_RUNS} 중 하나여야 합니다.")
    if n_runs in _GENERATORS:
        return _cyclic(_parse(_GENERATORS[n_runs]))
    if n_runs == 28:
        p = np.array([_parse(r) for r in _ROWS_28.strip().splitlines()], dtype=int)  # 9 × 27
        a, b, c = p[:, :9], p[:, 9:18], p[:, 18:]
        m = np.block([[a, b, c], [c, a, b], [b, c, a]])
        return np.vstack([m, -np.ones(27, dtype=int)])
    # 40: 20런 설계 이중화
    d20 = pb_matrix(20)
    one = np.ones((20, 1), dtype=int)
    return np.block([[d20, one, -d20], [d20, -one, d20]])


def default_runs(n_factors: int) -> int:
    """요인 수에 맞는 가장 작은 런 수(n > k)."""
    for n in PB_RUNS:
        if n > n_factors:
            return n
    raise ValueError("Plackett-Burman 설계는 최대 47요인까지입니다.")


@dataclass
class PlackettBurmanDesign:
    factors: list[Factor]
    letters: list[str]
    runs: pd.DataFrame                # StdOrder, RunOrder, PtType, Blocks, 요인열(실제 수준값), RunOrder 순
    coded: pd.DataFrame               # 같은 행 순서, 요인열은 −1/0/+1 코드(열 이름은 A,B,…)
    corner_runs: int                  # PB 런 수 n
    center_points_per_replicate: int
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
    def n_text_factors(self) -> int:
        return sum(not f.is_numeric for f in self.factors)

    @property
    def total_center_points(self) -> int:
        return int((self.runs["PtType"] == 0).sum())

    @property
    def base_runs(self) -> int:
        return self.n_runs // self.replicates

    def summary(self) -> dict:
        """Minitab 'Design Summary' 항목(순서 포함)."""
        return {
            "Factors": self.n_factors,
            "Replicates": self.replicates,
            "Base runs": self.base_runs,
            "Total runs": self.n_runs,
            "Base blocks": 1,
            "Total blocks": self.n_blocks,
            "Center points": self.total_center_points,
        }

    def summary_text(self) -> str:
        s = self.summary()
        lines = [
            "Design Summary",
            f"Factors: {s['Factors']}  Replicates: {s['Replicates']}",
            f"Base runs: {s['Base runs']}  Total runs: {s['Total runs']}",
            f"Base blocks: {s['Base blocks']}  Total blocks: {s['Total blocks']}",
        ]
        if s["Center points"]:
            lines.append(f"Center points: {s['Center points']}")
        if self.center_points_per_replicate and self.n_text_factors:
            lines.append("* NOTE * The number of centerpoints specified is doubled for each categorical factor. "
                         "For Q categorical factors, the result is 2^Q times as many centerpoints.")
        return "\n".join(lines)

    def design_table(self) -> pd.DataFrame:
        """Minitab 'Design Table (randomized)': Run, Blk, 요인 기호(+/−/0)."""
        tbl = pd.DataFrame(sign_table(self.coded, self.letters), columns=self.letters)
        tbl.insert(0, "Blk", self.coded["Blocks"].values)
        tbl.insert(0, "Run", self.coded["RunOrder"].values)
        return tbl


def create_plackett_burman_design(
    n_factors: int,
    n_runs: int | None = None,
    *,
    factors: list[Factor] | None = None,
    center_points: int = 0,
    replicates: int = 1,
    block_on_replicates: bool = False,
    randomize: bool = True,
    seed: int | None = None,
) -> PlackettBurmanDesign:
    """Minitab 'Create Plackett-Burman Design' 과 같은 설계를 만든다.

    center_points 는 '반복당 중앙점 수'. block_on_replicates=True 면 반복마다 블록을 나눈다.
    표준 순서는 반복 → (모서리점 생성 순서, 중앙점) 순이다(중앙점 위치는 문서에 없어 반복 끝에 둠).
    """
    if not 2 <= n_factors <= 47:
        raise ValueError("Plackett-Burman 설계의 요인 수는 2~47 이어야 합니다.")
    n_runs = default_runs(n_factors) if n_runs is None else n_runs
    if n_runs not in PB_RUNS:
        raise ValueError(f"런 수는 {PB_RUNS} 중 하나여야 합니다(8·16런은 2수준 요인설계를 쓰세요).")
    if n_factors > n_runs - 1:
        raise ValueError(f"{n_runs}런 설계는 최대 {n_runs - 1}요인까지 가능합니다.")
    if replicates < 1 or center_points < 0:
        raise ValueError("replicates ≥ 1, center_points ≥ 0 이어야 합니다.")
    if factors is None:
        factors = default_factors(n_factors)
    if len(factors) != n_factors:
        raise ValueError("factors 길이가 n_factors 와 다릅니다.")
    letters = factor_letters(n_factors)

    corner = pd.DataFrame(pb_matrix(n_runs)[:, :n_factors], columns=letters)
    corner["PtType"] = 1
    corner["_order"] = np.arange(n_runs)

    parts = []
    for r in range(replicates):
        block = r + 1 if block_on_replicates else 1
        c = corner.copy()
        c["Blocks"], c["_rep"] = block, r
        parts.append(c)
        for cp in center_point_rows(letters, factors, center_points):
            cp["PtType"], cp["Blocks"], cp["_rep"] = 0, block, r
            cp["_order"] = n_runs + np.arange(len(cp))
            parts.append(cp)
    coded = pd.concat(parts, ignore_index=True)

    coded = assign_orders(coded, ["Blocks", "_rep", "_order"], randomize=randomize, seed=seed)
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", *letters]]
    runs = to_levels(coded, letters, factors, "PtType")
    return PlackettBurmanDesign(
        factors=factors, letters=letters, runs=runs, coded=coded, corner_runs=n_runs,
        center_points_per_replicate=center_points, replicates=replicates,
        n_blocks=replicates if block_on_replicates else 1, seed=seed,
    )
