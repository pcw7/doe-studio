"""Taguchi 설계 — Minitab 'Create Taguchi Design'(정적 설계).

문서 근거(docs/spec/C_rsm_mixture_optimal.md 7절, 카탈로그 21종 + 예제)
- 설계 종류: 2수준(2~31요인), 3수준(2~13), 4수준(2~5), 5수준(2~6), 혼합 수준(2·3, 2·4, 2·8, 3·6).
  배열 표기 L(런 수)(수준^요인 수). 수준 값 기본 1, 2, …(실제 값 입력 가능). 런 순서는 랜덤화하지 않는다.
- 출력: Taguchi Array L8(2^4), Factors, Runs, 'Columns of L8(2^7) array: 1 2 4 7', 설계(요인 열) 표.
- 예제: L8 에 4요인 → 배열의 1, 2, 4, 7 열.

문서에 없어 정한 것(기본 열 배정)
- 2수준 정규 배열(L4, L8, L16, L32): 열 번호의 이진수가 곧 기본 요인 곱(1 = A, 2 = B, 3 = AB, 4 = C …, 문서 배열로 확인)이므로
  2수준 요인설계 카탈로그의 기본 생성자 설계를 그대로 쓴다(4요인 L8 → 1 2 4 7, 문서와 같음).
- L27: 기본 열 1·2·5 다음 3요인 조합 열 9·10·12·13, 그다음 2요인 조합 열(표준 선형도, 배열에서 확인).
- 그 밖의 배열(L9, L12, L16(4^5), L25, 혼합 수준): 해당 수준의 열을 앞에서부터. 혼합 수준은 배열의 열 순서대로 요인 문자를 붙인다.
- 열을 직접 지정할 수도 있다(columns).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .common import factor_letters
from .general_full import GeneralFactor
from .taguchi_arrays import ARRAYS_RAW


# 문서 카탈로그의 배열 이름(ARRAYS_RAW 와 같은 순서). 혼합 수준의 수준 순서는 문서 표기를 따른다.
ARRAY_NAMES = ["L4(2^3)", "L8(2^7)", "L8(2^4 4^1)", "L9(3^4)", "L12(2^11)", "L16(2^15)", "L16(2^12 4^1)",
               "L16(2^9 4^2)", "L16(2^6 4^3)", "L16(2^3 4^4)", "L16(4^5)", "L16(8^1 2^8)", "L18(2^1 3^7)",
               "L18(6^1 3^6)", "L25(5^6)", "L27(3^13)", "L32(2^31)", "L32(2^1 4^9)", "L36(2^11 3^12)",
               "L36(2^3 3^13)", "L54(2^1 3^25)"]


def _level_order(name: str) -> list[int]:
    return [int(p.split("^")[0]) for p in name[name.index("(") + 1:-1].split()]


@dataclass(frozen=True)
class TaguchiArray:
    runs: int
    levels: tuple[int, ...]           # 열별 수준 수
    rows: str
    name: str = ""

    @property
    def matrix(self) -> np.ndarray:
        return np.array([[int(c) for c in r] for r in self.rows.split()], dtype=int)

    @property
    def level_counts(self) -> dict[int, int]:
        return dict(Counter(self.levels))


ARRAYS: list[TaguchiArray] = [TaguchiArray(r, lv, rows, nm) for (r, lv, rows), nm in zip(ARRAYS_RAW, ARRAY_NAMES)]
TYPES = {
    "2-level": (2,), "3-level": (3,), "4-level": (4,), "5-level": (5,),
    "mixed 2-3": (2, 3), "mixed 2-4": (2, 4), "mixed 2-8": (2, 8), "mixed 3-6": (3, 6),
}
_L27_ORDER = [1, 2, 5, 9, 10, 12, 13, 3, 4, 6, 7, 8, 11]


def array_by_name(name: str) -> TaguchiArray:
    key = name.replace(" ", "")
    for a in ARRAYS:
        if a.name.replace(" ", "") == key:
            return a
    raise ValueError(f"Taguchi 배열이 없습니다: {name!r}")


def available_taguchi(kind: str, counts: dict[int, int]) -> list[TaguchiArray]:
    """요인 수(수준별)를 담을 수 있는 배열. kind: TYPES 의 키, counts: {수준 수: 요인 수}."""
    if kind not in TYPES:
        raise ValueError(f"설계 종류는 {list(TYPES)} 중 하나입니다.")
    want = TYPES[kind]
    if set(counts) - set(want) or sum(counts.values()) < 2:
        raise ValueError("요인 수(수준별)가 설계 종류와 맞지 않거나 2개보다 적습니다.")
    out = []
    for a in ARRAYS:
        lc = a.level_counts
        if set(lc) != set(want):
            continue
        if all(lc.get(lv, 0) >= n for lv, n in counts.items()):
            out.append(a)
    return sorted(out, key=lambda a: (a.runs, a.name))


def default_columns(arr: TaguchiArray, counts: dict[int, int]) -> list[int]:
    """기본 열 배정(1부터, 요인 순서). 수준별 요인 수는 counts."""
    if set(arr.levels) == {2} and arr.runs in (4, 8, 16, 32):
        from .catalog import CATALOG
        from .words import LETTERS
        k = counts[2]
        q = int(np.log2(arr.runs))
        if k <= q:
            return [1 << b for b in range(k)]
        entry = CATALOG.get((k, arr.runs))
        if entry is not None:
            cols = [1 << b for b in range(q)]
            for _, word in sorted(entry.generators.items(), key=lambda kv: LETTERS.index(kv[0])):
                cols.append(sum(1 << LETTERS.index(ch) for ch in word))
            return cols
        return list(range(1, k + 1))
    if arr.runs == 27 and set(arr.levels) == {3}:
        return _L27_ORDER[: counts[3]]
    out, used = [], Counter()
    for j, lv in enumerate(arr.levels, 1):          # 배열의 열 순서대로 수준별로 필요한 만큼
        if used[lv] < counts.get(lv, 0):
            out.append(j)
            used[lv] += 1
    return out


@dataclass
class TaguchiDesign:
    array: TaguchiArray
    columns: list[int]                # 쓰는 배열 열(1부터, 요인 순서)
    factors: list[GeneralFactor]
    runs: pd.DataFrame
    coded: pd.DataFrame               # StdOrder, RunOrder, PtType, Blocks, A… (수준 번호 1, 2, …)
    replicates: int = 1
    n_blocks: int = 1
    seed: int | None = None
    point_col: str = "PtType"
    folded_on = None

    @property
    def letters(self) -> list[str]:
        return factor_letters(len(self.factors))

    @property
    def n_runs(self) -> int:
        return len(self.coded)

    @property
    def used_name(self) -> str:
        """설계 요약의 'Taguchi Array' 표기 — 쓰는 요인만 센다(예: L8(2^4))."""
        cnt = Counter(self.array.levels[c - 1] for c in self.columns)
        order = [x for x in _level_order(self.array.name) if cnt[x]]
        return f"L{self.array.runs}(" + " ".join(f"{x}^{cnt[x]}" for x in order) + ")"

    def rebuild_runs(self, coded: pd.DataFrame) -> pd.DataFrame:
        runs = coded[["StdOrder", "RunOrder", self.point_col, "Blocks"]].copy()
        for L, f in zip(self.letters, self.factors):
            runs[f.name] = [f.levels[int(v) - 1] for v in coded[L].values]
        return runs

    def summary(self) -> dict:
        return {"Taguchi Array": self.used_name, "Factors": len(self.factors), "Runs": self.n_runs}

    def summary_table(self) -> pd.DataFrame:
        s = self.summary()
        return pd.DataFrame([["Taguchi Array", s["Taguchi Array"]], ["Factors:", str(s["Factors"])],
                             ["Runs:", str(s["Runs"])]])

    def columns_text(self) -> str:
        return f"Columns of {self.array.name} array: " + " ".join(map(str, self.columns))

    def summary_text(self) -> str:
        s = self.summary()
        return "\n".join(["Taguchi Design", "Design Summary", f"Taguchi Array  {s['Taguchi Array']}",
                          f"Factors:  {s['Factors']}", f"Runs:     {s['Runs']}", "", self.columns_text()])

    def design_table(self) -> pd.DataFrame:
        """요인 열 표(수준 값). Minitab 워크시트의 C1, C2 … 에 해당."""
        return self.runs[[f.name for f in self.factors]].reset_index(drop=True)


def create_taguchi_design(
    array: TaguchiArray | str,
    factors: list[GeneralFactor] | None = None,
    *,
    columns: list[int] | None = None,
    n_factors: dict[int, int] | int | None = None,
) -> TaguchiDesign:
    """Taguchi 정적 설계. factors 를 주지 않으면 n_factors({수준 수: 개수} 또는 개수)로 A, B, … 와 수준 1, 2, … 를 만든다."""
    arr = array_by_name(array) if isinstance(array, str) else array
    if factors is None:
        if isinstance(n_factors, int):
            if len(set(arr.levels)) != 1:
                raise ValueError("혼합 수준 배열은 수준별 요인 수를 {수준 수: 개수} 로 주세요.")
            n_factors = {arr.levels[0]: n_factors}
        if not n_factors:
            raise ValueError("요인 또는 요인 수를 주세요.")
        cols = columns or default_columns(arr, n_factors)
        letters = factor_letters(len(cols))
        factors = [GeneralFactor(L, list(range(1, arr.levels[c - 1] + 1))) for L, c in zip(letters, cols)]
    counts = Counter(len(f.levels) for f in factors)
    if columns is None:
        cols = default_columns(arr, dict(counts))
        # 요인 순서를 배정된 열의 수준에 맞춘다(혼합 수준): 같은 수준끼리 입력 순서 유지
        by_level = {lv: [f for f in factors if len(f.levels) == lv] for lv in counts}
        ordered = [by_level[arr.levels[c - 1]].pop(0) for c in cols]
        factors = ordered
    else:
        cols = list(columns)
    if len(cols) != len(factors) or len(set(cols)) != len(cols):
        raise ValueError("열 수가 요인 수와 다르거나 같은 열을 두 번 썼습니다.")
    for c, f in zip(cols, factors):
        if not 1 <= c <= len(arr.levels):
            raise ValueError(f"{arr.name} 에는 {c} 열이 없습니다.")
        if arr.levels[c - 1] != len(f.levels):
            raise ValueError(f"{f.name} 의 수준 수({len(f.levels)})가 {c} 열의 수준 수({arr.levels[c - 1]})와 다릅니다.")
    M = arr.matrix[:, [c - 1 for c in cols]]
    letters = factor_letters(len(factors))
    coded = pd.DataFrame(M, columns=letters)
    n = arr.runs
    coded.insert(0, "Blocks", 1)
    coded.insert(0, "PtType", 1)
    coded.insert(0, "RunOrder", np.arange(1, n + 1))
    coded.insert(0, "StdOrder", np.arange(1, n + 1))
    d = TaguchiDesign(arr, cols, list(factors), pd.DataFrame(), coded)
    d.runs = d.rebuild_runs(coded)
    return d
