"""사용자 설계 정의(다수준) — Minitab 'Define Custom General Full Factorial Design' · 'Define Custom Taguchi Design'.

- 요인 열의 수준: 숫자 열은 값 오름차순, 텍스트 열은 글자 오름차순(수준 번호 1, 2, …).
- 일반 완전요인: 모든 수준 조합이 같은 횟수(반복 수)로 있어야 한다. 블록 열이 있으면 블록으로 쓴다.
- Taguchi: 런 수가 같은 카탈로그 배열의 열과 (같은 행 순서로) 그대로 일치하면 그 배열·열 번호를 쓰고, 아니면 데이터로 만든
  사용자 배열(L{런}(수준^개수))을 쓴다. 직교성(모든 열 쌍에서 수준 조합이 같은 횟수)은 is_orthogonal 로 알려 준다.
- 표준 순서·런 순서 열(StdOrder·RunOrder)이 있으면 쓰고, 없으면 행 순서. 나머지 열은 비설계 열.

문서에 없어 정한 것: 수준 정렬 규칙, 카탈로그 일치 판정(같은 행 순서·같은 수준 번호), 9수준 초과 요인은 Taguchi 로 정의 불가.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations

import numpy as np
import pandas as pd

from ..designs.common import factor_letters
from ..designs.general_full import GeneralFactor, GeneralFullFactorialDesign
from ..designs.taguchi import ARRAYS, TaguchiArray, TaguchiDesign

RESERVED = ("StdOrder", "RunOrder", "CenterPt", "PtType", "Blocks")


def _levels(x: pd.Series) -> tuple[list, np.ndarray]:
    """(수준 값 목록, 수준 번호 1..L)."""
    if x.isna().any():
        raise ValueError(f"요인 열 {x.name!r} 에 빈 칸이 있습니다.")
    if pd.api.types.is_numeric_dtype(x):
        vals = sorted({float(v) for v in x})
        levels = [int(v) if float(v).is_integer() else v for v in vals]
        idx = np.array([vals.index(float(v)) + 1 for v in x])
    else:
        vals = sorted({str(v) for v in x})
        levels = vals
        idx = np.array([vals.index(str(v)) + 1 for v in x])
    return levels, idx


def _orders(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    n = len(df)
    std = df["StdOrder"].astype(int).values if "StdOrder" in df else np.arange(1, n + 1)
    run = df["RunOrder"].astype(int).values if "RunOrder" in df else np.arange(1, n + 1)
    if len(set(std)) != n:
        raise ValueError("StdOrder 값이 겹칩니다.")
    return std, run


def _coded_frame(df, factors):
    letters = factor_letters(len(factors))
    facs, coded = [], {}
    for L, col in zip(letters, factors):
        levels, idx = _levels(df[col])
        if len(levels) < 2:
            raise ValueError(f"요인 {col!r} 의 수준이 하나뿐입니다.")
        facs.append(GeneralFactor(col, levels))
        coded[L] = idx
    return letters, facs, pd.DataFrame(coded)


def is_orthogonal(M: np.ndarray) -> bool:
    """모든 열이 수준 균형이고 모든 열 쌍에서 수준 조합이 같은 횟수."""
    n = M.shape[0]
    for j in range(M.shape[1]):
        c = Counter(M[:, j])
        if len(set(c.values())) != 1:
            return False
    for i, j in combinations(range(M.shape[1]), 2):
        c = Counter(zip(M[:, i], M[:, j]))
        li, lj = len(set(M[:, i])), len(set(M[:, j]))
        if len(c) != li * lj or len(set(c.values())) != 1 or n % (li * lj):
            return False
    return True


def is_full_factorial(M: np.ndarray) -> int | None:
    """모든 수준 조합이 같은 횟수면 그 횟수(반복 수), 아니면 None."""
    sizes = [len(set(M[:, j])) for j in range(M.shape[1])]
    c = Counter(map(tuple, M))
    if len(c) != int(np.prod(sizes)) or len(set(c.values())) != 1:
        return None
    return next(iter(c.values()))


def _extra(df, factors, std):
    used = set(factors) | set(RESERVED)
    extra = df[[c for c in df.columns if c not in used]].copy()
    extra.index = pd.Index(std, name="StdOrder")
    return extra


def define_custom_general_full(df: pd.DataFrame, factors: list[str]):
    """기존 데이터에서 일반 완전요인설계를 정의한다(모든 수준 조합이 같은 횟수)."""
    from .worksheet import Worksheet
    if not 1 <= len(factors) <= 15:
        raise ValueError("요인 수는 1~15 이어야 합니다.")
    df = df.reset_index(drop=True)
    letters, facs, M = _coded_frame(df, factors)
    reps = is_full_factorial(M.values)
    if reps is None:
        raise ValueError("일반 완전요인설계가 아닙니다: 모든 수준 조합이 같은 횟수로 있어야 합니다.")
    std, run = _orders(df)
    blocks = df["Blocks"].astype(int).values if "Blocks" in df else np.ones(len(df), dtype=int)
    coded = M.copy()
    coded.insert(0, "Blocks", blocks)
    coded.insert(0, "PtType", 1)
    coded.insert(0, "RunOrder", run)
    coded.insert(0, "StdOrder", std)
    d = GeneralFullFactorialDesign(facs, letters, pd.DataFrame(), coded, reps, int(len(set(blocks))))
    d.runs = d.rebuild_runs(coded)
    return Worksheet(d, _extra(df, factors, std))


def _catalog_match(M: np.ndarray) -> tuple[TaguchiArray, list[int]] | None:
    n, k = M.shape
    for arr in ARRAYS:
        if arr.runs != n:
            continue
        A = arr.matrix
        cols, used = [], set()
        for j in range(k):
            hit = next((c for c in range(A.shape[1]) if c not in used and np.array_equal(A[:, c], M[:, j])), None)
            if hit is None:
                break
            cols.append(hit + 1)
            used.add(hit)
        if len(cols) == k:
            return arr, cols
    return None


def define_custom_taguchi(df: pd.DataFrame, factors: list[str]):
    """기존 데이터에서 Taguchi(정적) 설계를 정의한다. 반환: (워크시트, 직교 여부)."""
    from .worksheet import Worksheet
    if not 1 <= len(factors) <= 50:
        raise ValueError("요인 수는 1~50 이어야 합니다.")
    df = df.reset_index(drop=True)
    letters, facs, M = _coded_frame(df, factors)
    if any(len(f.levels) > 9 for f in facs):
        raise ValueError("Taguchi 요인의 수준은 9개 이하여야 합니다.")
    Mv = M.values.astype(int)
    match = _catalog_match(Mv)
    if match:
        arr, cols = match
    else:
        cnt = Counter(len(f.levels) for f in facs)
        name = f"L{len(df)}(" + " ".join(f"{lv}^{cnt[lv]}" for lv in sorted(cnt)) + ")"
        arr = TaguchiArray(len(df), tuple(len(f.levels) for f in facs),
                           " ".join("".join(str(v) for v in row) for row in Mv), name)
        cols = list(range(1, len(facs) + 1))
    std, run = _orders(df)
    coded = M.copy()
    coded.insert(0, "Blocks", 1)
    coded.insert(0, "PtType", 1)
    coded.insert(0, "RunOrder", run)
    coded.insert(0, "StdOrder", std)
    d = TaguchiDesign(arr, cols, facs, pd.DataFrame(), coded)
    d.runs = d.rebuild_runs(coded)
    return Worksheet(d, _extra(df, factors, std)), is_orthogonal(Mv)


def multilevel_kind(df: pd.DataFrame, factors: list[str]) -> str | None:
    """중앙점 행을 뺀 뒤 3수준 이상인 요인이 있으면 'general_full'(완전 배치) 또는 'taguchi'(직교 부분 배치), 아니면 None."""
    sub = df[list(factors)].reset_index(drop=True)
    num = [c for c in factors if pd.api.types.is_numeric_dtype(sub[c])]
    if num:
        mid = {c: (float(sub[c].min()) + float(sub[c].max())) / 2 for c in num}
        center = np.all([np.isclose(sub[c].astype(float), mid[c]) for c in num], axis=0)
        if len(num) == len(factors):
            sub = sub[~center]
    if all(sub[c].nunique() <= 2 for c in factors):
        return None
    try:
        _, _, M = _coded_frame(df.reset_index(drop=True), factors)
    except ValueError:
        return None
    if is_full_factorial(M.values) is not None:
        return "general_full"
    return "taguchi" if is_orthogonal(M.values) else "general_full"
