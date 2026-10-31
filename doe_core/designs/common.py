"""설계 생성기들이 공유하는 요소: 요인 정의, 요인 이름, 중앙점 행, 표준 순서·런 순서 부여, 실제 수준값 변환.

워크시트 열 규약(Minitab 과 동일)
  C1 StdOrder, C2 RunOrder, C3 CenterPt(2수준 요인설계) 또는 PtType(PB·일반 완전요인 등), C4 Blocks, C5~ 요인열
점 유형 코드: 1 모서리점, 0 중앙점(축점 −1 등은 반응표면에서 사용)
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd

# Minitab 요인 문자: I 를 건너뛴 A~Z (25자)
FACTOR_ALPHABET = "ABCDEFGHJKLMNOPQRSTUVWXYZ"


@dataclass
class Factor:
    name: str
    low: float | str = -1
    high: float | str = 1
    numeric: bool = True

    @property
    def is_numeric(self) -> bool:
        return self.numeric and isinstance(self.low, (int, float)) and isinstance(self.high, (int, float))


def factor_letters(n: int) -> list[str]:
    """요인 n 개의 문자 이름. 25개까지는 A~Z(I 제외).

    25개를 넘을 때의 Minitab 규칙은 문서에 없다. 여기서는 같은 알파벳의 두 글자 조합(AA, AB, …)을 이어 붙인다.
    """
    out = list(FACTOR_ALPHABET[:n])
    if n > len(FACTOR_ALPHABET):
        two = (a + b for a in FACTOR_ALPHABET for b in FACTOR_ALPHABET)
        out += [next(two) for _ in range(n - len(FACTOR_ALPHABET))]
    return out


def default_factors(n: int) -> list[Factor]:
    return [Factor(L) for L in factor_letters(n)]


def center_point_rows(letters: list[str], factors: list[Factor], count: int) -> list[pd.DataFrame]:
    """중앙점 count 개를 텍스트 요인 수준 조합(2^Q)마다 만든다. 숫자 요인은 0(코드), 텍스트 요인은 ±1."""
    if count <= 0:
        return []
    numeric = [f.is_numeric for f in factors]
    if not any(numeric):
        raise ValueError("모든 요인이 텍스트이면 중앙점을 추가할 수 없습니다.")
    text_letters = [L for L, isnum in zip(letters, numeric) if not isnum]
    frames = []
    for combo in product((-1, 1), repeat=len(text_letters)):
        cp = pd.DataFrame({L: [0] * count for L in letters})
        for L, v in zip(text_letters, combo):
            cp[L] = v
        frames.append(cp)
    return frames


def assign_orders(coded: pd.DataFrame, sort_keys: list[str], *, randomize: bool, seed: int | None) -> pd.DataFrame:
    """표준 순서(StdOrder)와 런 순서(RunOrder)를 매기고 RunOrder 순으로 정렬해 돌려준다.

    - StdOrder: sort_keys(첫 키는 Blocks) 순으로 1부터.
    - RunOrder: 블록 안에서만 랜덤화하고 블록은 번호 순서대로. randomize=False 면 StdOrder 와 같다.
    """
    coded = coded.sort_values(sort_keys, kind="stable").reset_index(drop=True)
    coded.insert(0, "StdOrder", np.arange(1, len(coded) + 1))
    rng = np.random.default_rng(seed)
    run_order = np.empty(len(coded), dtype=int)
    pos = 0
    for b in sorted(coded["Blocks"].unique()):
        idx = np.where(coded["Blocks"].values == b)[0]
        perm = rng.permutation(idx) if randomize else idx
        run_order[perm] = np.arange(pos + 1, pos + len(idx) + 1)
        pos += len(idx)
    coded.insert(1, "RunOrder", run_order)
    return coded.sort_values("RunOrder").reset_index(drop=True)


def to_levels(coded: pd.DataFrame, letters: list[str], factors: list[Factor], point_col: str) -> pd.DataFrame:
    """코드값(−1/0/+1) 워크시트를 실제 수준값 워크시트로 바꾼다. 숫자 요인의 0 은 (low+high)/2."""
    runs = coded[["StdOrder", "RunOrder", point_col, "Blocks"]].copy()
    for L, f in zip(letters, factors):
        c = coded[L].values
        if f.is_numeric:
            mid = (float(f.low) + float(f.high)) / 2
            runs[f.name] = np.where(c == -1, float(f.low), np.where(c == 1, float(f.high), mid))
        else:
            runs[f.name] = np.where(c == -1, f.low, f.high)
    return runs


def sign_table(coded: pd.DataFrame, letters: list[str]) -> list[list[str]]:
    """설계표(Design Table)용 기호: + / - / 0."""
    sym = {1: "+", -1: "-", 0: "0"}
    return [[sym[int(v)] for v in row] for row in coded[letters].values.tolist()]
