"""설계 표시·수정 — Minitab 'Stat > DOE > Display Design / Modify Design' 에 해당(요인설계 계열).

지원 설계: TwoLevelDesign(2수준 요인), PlackettBurmanDesign, GeneralFullFactorialDesign.
모든 함수는 원본을 바꾸지 않고 새 설계 객체를 돌려준다.

문서 근거(docs/spec/A_factorial_create.md 3.8, 6절)
- Fold design: 2수준 요인·PB 만 가능(일반 완전요인 불가). 모서리점을 복제해 아래에 붙이고 접는 요인의 부호를 바꾼다.
  "Each replicate or fold adds runs equal to the number of corner points in the base design" → 중앙점은 복제하지 않는다.
  전체 접기는 정의관계의 홀수 길이 단어를, 한 요인 접기는 그 요인을 포함한 단어를 없앤다.
  정의관계가 줄지 않으면(반복만 추가되는 경우) 오류. 블록 설계는 같은 블록 생성자로 새 런의 블록을 정한다.
- Replicate design: 중앙점 포함 모든 런을 복제(최대 10회). 추가 반복은 새 블록 번호, StdOrder·RunOrder 는 이어서.
  순서가 원본과 같으므로 다시 랜덤화해야 한다.
- Randomize design: 전체(블록 안 런 랜덤화 + 블록 순서 랜덤화) 또는 한 블록만(블록 순서 유지).
- Renumber design: RunOrder 를 현재 행 순서대로 1..n.
- Modify factors: 이름·수준(low/high) 변경. 코드값은 그대로 두고 실제값 워크시트만 다시 만든다.
- Display design: 런 순서/표준 순서, 코드화/비코드화 단위.
- Add axial points 는 결과가 중심합성(반응표면) 설계가 되므로 반응표면 단계에서 구현한다.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from .common import Factor
from .factorial import TwoLevelDesign, alias_structure, block_numbers
from .general_full import GeneralFullFactorialDesign
from .plackett_burman import PlackettBurmanDesign
from .words import word_from_str, word_len

MAX_ADDED_REPLICATES = 10


def _letters(d) -> list[str]:
    return list(d.letters)


def _finish(d, coded: pd.DataFrame, **changes):
    """코드값 워크시트를 바꾼 새 설계 객체를 만든다(실제값 워크시트도 다시 생성)."""
    coded = coded.reset_index(drop=True)
    new = replace(d, coded=coded, runs=pd.DataFrame(), **changes)
    new.runs = new.rebuild_runs(coded)
    return new


# ---------------------------------------------------------------- 접기


def _block_numbers(d: TwoLevelDesign, rows: pd.DataFrame, source_blocks: np.ndarray) -> np.ndarray:
    """접은 런의 블록 번호: 블록 생성자가 있으면 같은 생성자로 다시 계산, 없으면 원래 런의 블록을 그대로 쓴다."""
    gens = d.block_generators
    if not gens:
        return source_blocks
    in_rep = block_numbers(rows, gens)
    per_rep = 1 << len(gens)
    rep_offset = (source_blocks - 1) // per_rep * per_rep
    return in_rep + rep_offset


def fold_design(d: TwoLevelDesign | PlackettBurmanDesign, on: str = "all") -> TwoLevelDesign | PlackettBurmanDesign:
    """설계를 접는다. on="all" 이면 모든 요인, 요인 문자(A, B, …)면 그 요인만 부호를 바꾼다."""
    if not isinstance(d, (TwoLevelDesign, PlackettBurmanDesign)):
        raise ValueError("접기는 2수준 요인설계와 Plackett-Burman 설계에만 할 수 있습니다.")
    if d.folded_on:
        raise ValueError("이미 접은 설계입니다.")
    letters = _letters(d)
    if on != "all" and on not in letters:
        raise ValueError(f"접을 요인 {on!r} 이 설계에 없습니다. 가능한 요인: {letters}")
    flip = letters if on == "all" else [on]

    new_alias = None
    if isinstance(d, TwoLevelDesign):
        if on == "all":
            keep = [w for w in d.alias.defining if word_len(w) % 2 == 0]
        else:
            bit = word_from_str(on)
            keep = [w for w in d.alias.defining if not (w & bit)]
        if len(keep) == len(d.alias.defining):
            raise ValueError("접어도 정의관계가 줄지 않습니다(반복만 추가됨). 이런 경우 설계를 만들지 않습니다.")
        new_alias = alias_structure(d.n_factors, keep, [word_from_str(w) for w in d.block_generators])

    coded = d.coded
    corners = coded[coded[d.point_col] == 1].sort_values("StdOrder")
    folded = corners.copy()
    for L in flip:
        folded[L] = -folded[L]
    if isinstance(d, TwoLevelDesign):
        folded["Blocks"] = _block_numbers(d, folded, corners["Blocks"].values)
    folded["StdOrder"] = coded["StdOrder"].max() + np.arange(1, len(folded) + 1)
    folded["RunOrder"] = coded["RunOrder"].max() + np.arange(1, len(folded) + 1)
    out = pd.concat([coded, folded], ignore_index=True)
    changes = {"folded_on": on}
    if new_alias is not None:
        changes["alias"] = new_alias
    return _finish(d, out, **changes)


# ---------------------------------------------------------------- 반복 추가


def replicate_design(d, n_add: int = 1):
    """워크시트의 모든 런(중앙점 포함)을 n_add 번 복제해 새 블록으로 붙인다."""
    if not 1 <= n_add <= MAX_ADDED_REPLICATES:
        raise ValueError(f"추가할 반복 수는 1~{MAX_ADDED_REPLICATES} 이어야 합니다.")
    from .split_plot import SplitPlotDesign
    if isinstance(d, SplitPlotDesign):
        raise ValueError("분할구 설계의 반복은 설계를 만들 때 전구 반복·하위구 반복으로 지정합니다.")
    base = d.coded
    n = len(base)
    max_block = int(base["Blocks"].max())
    parts = [base]
    for k in range(1, n_add + 1):
        c = base.copy()
        c["StdOrder"] = base["StdOrder"] + k * n
        c["RunOrder"] = n * k + np.arange(1, n + 1)
        c["Blocks"] = base["Blocks"] + k * max_block
        parts.append(c)
    out = pd.concat(parts, ignore_index=True)
    return _finish(d, out, replicates=d.replicates * (n_add + 1), n_blocks=int(out["Blocks"].nunique()))


# ---------------------------------------------------------------- 랜덤화·번호


def randomize_design(d, *, block: int | None = None, seed: int | None = None, display_in_run_order: bool = True):
    """런 순서를 다시 랜덤화한다.

    block=None: 각 블록 안의 런을 섞고 블록 순서도 섞는다(Randomize entire design).
    block=b   : 블록 b 의 런만 섞고, 그 블록이 차지하던 RunOrder 자리는 유지한다(Randomize just block).
    display_in_run_order=False 면 RunOrder 열만 바꾸고 행 순서는 그대로 둔다.
    """
    from .split_plot import SplitPlotDesign, randomize_split_plot
    if isinstance(d, SplitPlotDesign):
        if block is not None:
            raise ValueError("분할구 설계는 설계 전체만 다시 랜덤화합니다(전구 순서·전구 안 런 순서).")
        return randomize_split_plot(d, seed)
    rng = np.random.default_rng(seed)
    coded = d.coded.copy()
    run_order = coded["RunOrder"].values.copy()
    blocks = coded["Blocks"].values
    if block is None:
        block_ids = np.array(sorted(set(blocks)))
        pos = 0
        for b in rng.permutation(block_ids):
            idx = np.where(blocks == b)[0]
            run_order[rng.permutation(idx)] = np.arange(pos + 1, pos + len(idx) + 1)
            pos += len(idx)
    else:
        idx = np.where(blocks == block)[0]
        if not len(idx):
            raise ValueError(f"블록 {block} 이 없습니다.")
        slots = np.sort(run_order[idx])
        run_order[rng.permutation(idx)] = slots
    coded["RunOrder"] = run_order
    if display_in_run_order:
        coded = coded.sort_values("RunOrder")
    return _finish(d, coded, seed=seed)


def renumber_design(d):
    """RunOrder 를 현재 워크시트 행 순서대로 1..n 으로 다시 매긴다."""
    coded = d.coded.copy()
    coded["RunOrder"] = np.arange(1, len(coded) + 1)
    return _finish(d, coded)


# ---------------------------------------------------------------- 요인 수정


def modify_factors(d: TwoLevelDesign | PlackettBurmanDesign, changes: dict[str, Factor]):
    """요인 이름·수준을 바꾼다. changes 의 키는 요인 문자(A, B, …) 또는 현재 요인 이름.

    요인 유형(숫자↔텍스트)은 바꿀 수 없다(Minitab 과 같음). 코드값은 그대로 두고 실제값만 다시 만든다.
    """
    if isinstance(d, GeneralFullFactorialDesign):
        raise ValueError("일반 완전요인설계의 수준 변경은 아직 지원하지 않습니다.")
    letters = _letters(d)
    factors = list(d.factors)
    for key, new in changes.items():
        if key in letters:
            i = letters.index(key)
        else:
            names = [f.name for f in factors]
            if key not in names:
                raise ValueError(f"요인 {key!r} 이 설계에 없습니다.")
            i = names.index(key)
        if new.is_numeric != factors[i].is_numeric:
            raise ValueError(f"요인 {factors[i].name!r} 의 유형(숫자/텍스트)은 바꿀 수 없습니다.")
        factors[i] = new
    if len({f.name for f in factors}) != len(factors):
        raise ValueError("요인 이름이 중복됩니다.")
    new_d = replace(d, factors=factors)
    new_d.runs = new_d.rebuild_runs(d.coded)
    return new_d


# ---------------------------------------------------------------- 설계 표시


def display_design(d, *, order: str = "run", units: str = "uncoded") -> pd.DataFrame:
    """워크시트를 런 순서(order="run") 또는 표준 순서("std"), 비코드화("uncoded") 또는 코드화("coded") 단위로 돌려준다.

    코드화 단위에서 요인 열 이름은 실제 요인 이름을 쓴다(2수준·PB 는 −1/0/+1, 일반 완전요인은 수준 번호).
    """
    if order not in ("run", "std") or units not in ("uncoded", "coded"):
        raise ValueError("order 는 'run'/'std', units 는 'uncoded'/'coded' 이어야 합니다.")
    if units == "uncoded":
        df = d.runs.copy()
    else:
        df = d.coded.rename(columns=dict(zip(_letters(d), [f.name for f in d.factors]))).copy()
    key = "RunOrder" if order == "run" else "StdOrder"
    return df.sort_values(key).reset_index(drop=True)
