"""분석 시 별칭 구조 — Minitab 'Analyze Factorial Design' 출력의 'Alias Structure'.

모형 항 X₁(상수·공변량·블록·요인 항·중앙점 항)에 대해, 모형 밖 요인 교호작용 X₂ 의 별칭 행렬
A = (X₁'X₁)⁻¹ X₁'X₂ 를 계산한다. 정규 부분요인이면 계수가 0 또는 ±1(완전 별칭), 공변량·중도 실패 런·PB 등에서는
1 이 아닌 계수(부분 별칭)가 나온다. InsulationProperties 예제의 부분 별칭 계수를 그대로 재현한다.

표시 규칙(문서 예제 3개)
- 행: I(상수), Block 1 …, 그리고 모형의 요인 항. 공변량·중앙점 항 행은 표시하지 않는다.
- 각 행: 항 다음에 X₂ 단어를 차수·알파벳 순으로, 계수는 소수 2자리. 0.00 으로 반올림되면 생략,
  절댓값이 1.00 이면 숫자 없이 부호만(`C + AB`).
- X₂ 범위: 요인 ≤ 7 이면 모든 교호작용, 8~10 은 3차까지, 11~15 는 2차까지(별칭표 기본값과 같음).
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

from ..designs.factorial import default_alias_order


def alias_matrix(a, max_order: int | None | str = "default"):
    """(행 이름 목록, X₂ 단어 목록, 계수 행렬). 행은 상수·블록·요인 항 열."""
    d = a.design
    letters = list(d.letters)
    k = len(letters)
    if max_order == "default":
        max_order = default_alias_order(k)
    top = k if max_order is None else min(max_order, k)
    in_model = {t.letters for t in a.terms if t.kind == "factor"}
    outside = [c for r in range(1, top + 1) for c in combinations(letters, r) if c not in in_model]
    coded = d.coded.iloc[a.used_rows]
    if outside:
        X2 = np.column_stack([np.prod([coded[L].values.astype(float) for L in w], axis=0) for w in outside])
        A = a.cov_unscaled @ a.X.T @ X2
    else:
        A = np.zeros((a.p, 0))
    names, rows = [], []
    block_no = 0
    for j, ti in enumerate(a.col_term):
        if ti < 0:
            names.append("I")
        else:
            t = a.terms[ti]
            if t.kind == "blocks":
                block_no += 1
                names.append(f"Block {block_no}")
            elif t.kind == "factor":
                names.append(t.word)
            else:
                continue
        rows.append(j)
    return names, ["".join(w) for w in outside], A[rows, :]


def alias_lines(a, max_order: int | None | str = "default") -> list[str]:
    names, words, A = alias_matrix(a, max_order)
    out = []
    for name, coefs in zip(names, A):
        parts = [name]
        for w, c in zip(words, coefs):
            r = round(float(c), 2)
            if r == 0:
                continue
            sign = "-" if r < 0 else "+"
            mag = abs(r)
            parts.append(f"{sign} {w}" if abs(mag - 1) < 1e-9 else f"{sign} {mag:.2f} {w}")
        out.append(" ".join(parts))
    return out


def has_aliasing(a, max_order: int | None | str = "default") -> bool:
    _, _, A = alias_matrix(a, max_order)
    return bool(np.any(np.round(A, 2) != 0))


def factor_name_table(a) -> pd.DataFrame:
    return pd.DataFrame({"Factor": list(a.design.letters), "Name": [f.name for f in a.design.factors]})
