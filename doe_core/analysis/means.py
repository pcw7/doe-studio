"""적합 평균 표 — Minitab 'Analyze Factorial Design > Options > Means table'.

요인 수준(또는 수준 조합)에서의 적합 평균과 SE. 나머지 요인은 코드값 0(평균), 공변량은 데이터 평균,
블록은 평균화(효과 코딩 0), 중앙점 항은 0(요인점)으로 둔다. SE Mean = √(x₀' Cov x₀).
표시: 수준 행 이름은 수준 값(교호작용은 공백으로 이어 씀), Fitted Mean 은 SE Mean 의 유효숫자 3자리와 같은 소수 자리.
문서 예제(InsulationProperties 축소 모형)의 Means 표를 그대로 재현한다.
"""
from __future__ import annotations

from itertools import product

import numpy as np
import pandas as pd

from ..designs.general_full import GeneralFullFactorialDesign
from . import fmt
from .model import Term, parse_term


def _level_label(v) -> str:
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return str(int(v)) if float(v).is_integer() else f"{v:g}"
    return str(v)


def _levels(design, letter: str):
    """(코드 상태, 표시 이름) 목록. 2수준: (−1, low), (+1, high). 일반 완전요인: 수준 번호."""
    f = design.factors[list(design.letters).index(letter)]
    if isinstance(design, GeneralFullFactorialDesign):
        return [(i + 1, _level_label(v)) for i, v in enumerate(f.levels)]
    return [(-1, _level_label(f.low)), (1, _level_label(f.high))]


def _x0(a, setting: dict[str, int]) -> np.ndarray:
    """설정(요인 문자 → 코드 상태)에서의 설계행렬 행."""
    x = np.zeros(a.p)
    x[0] = 1.0
    for j, ti in enumerate(a.col_term):
        if ti < 0:
            continue
        t = a.terms[ti]
        if t.kind == "covariate":
            x[j] = float(np.mean(a.covariates[t.name]))
        elif t.kind == "factor":
            # 이 열이 나타내는 수준 조합(일반 완전요인은 열마다 다름)을 계산
            x[j] = _factor_col_value(a, j, t, setting)
    return x


def _factor_col_value(a, j: int, t: Term, setting: dict[str, int]) -> float:
    d = a.design
    if not isinstance(d, GeneralFullFactorialDesign):
        val = 1.0
        for L in t.letters:
            val *= setting.get(L, 0)
        return val
    # 일반 완전요인: 이 항의 열들 중 몇 번째 열인지로 각 요인의 효과 코딩 열을 찾는다
    cols = [k for k, ti in enumerate(a.col_term) if ti >= 0 and a.terms[ti] == t]
    idx = cols.index(j)
    sizes = [d.factors[list(d.letters).index(L)].n_levels - 1 for L in t.letters]
    combo = []
    for s in reversed(sizes):
        combo.append(idx % s)
        idx //= s
    combo = list(reversed(combo))
    val = 1.0
    for L, cj, s in zip(t.letters, combo, sizes):
        if L not in setting:
            return 0.0
        lev = setting[L]                       # 1..L
        n_lev = s + 1
        code = 1.0 if lev == cj + 1 else (-1.0 if lev == n_lev else 0.0)
        val *= code
    return val


def means(a, which: str | list[str] = "model") -> pd.DataFrame:
    """적합 평균(숫자). which: 'model'(모형의 요인 항), 'main', 'main+2way', 또는 항 목록."""
    d = a.design
    if which == "model":
        terms = [t for t in a.terms if t.kind == "factor"]
    elif which == "main":
        terms = [t for t in a.terms if t.kind == "factor" and t.order == 1]
    elif which == "main+2way":
        terms = [t for t in a.terms if t.kind == "factor" and t.order <= 2]
    else:
        terms = [parse_term(s, d) for s in which]
    cov = a.cov_unscaled * (a.mse if a.mse is not None else np.nan)
    rows = []
    for t in terms:
        rows.append({"Term": t.name, "Level": "", "Fitted Mean": np.nan, "SE Mean": np.nan, "header": True})
        level_sets = [_levels(d, L) for L in t.letters]
        combos = list(product(*level_sets))
        # Minitab 순서: 첫 요인이 가장 빨리 바뀐다(85 25, 100 25, 85 45, 100 45)
        combos.sort(key=lambda c: [level_sets[i].index(c[i]) for i in reversed(range(len(c)))])
        for combo in combos:
            setting = {L: s for L, (s, _) in zip(t.letters, combo)}
            x0 = _x0(a, setting)
            rows.append({"Term": t.name, "Level": " ".join(lab for _, lab in combo),
                         "Fitted Mean": float(x0 @ a.beta), "SE Mean": float(np.sqrt(x0 @ cov @ x0)), "header": False})
    return pd.DataFrame(rows)


def means_table(a, which: str | list[str] = "model") -> pd.DataFrame:
    """Minitab 'Means' 표(문자열): Term | Fitted Mean | SE Mean. 항 이름 행 아래 수준 행."""
    m = means(a, which)
    out = []
    for r in m.itertuples(index=False):
        if r.header:
            out.append({"Term": r.Term, "Fitted Mean": "", "SE Mean": ""})
        else:
            out.append({"Term": r.Level, "Fitted Mean": fmt.by_se(r[2], r[3]), "SE Mean": fmt.se_text(r[3])})
    return pd.DataFrame(out, columns=["Term", "Fitted Mean", "SE Mean"])
