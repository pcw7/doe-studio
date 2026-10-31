"""설계 표시·수정 검증.

정답 출처(Minitab 문서)
- What is folding?: 3요인 4런(C=AB) 설계의 전체 접기·A 접기 결과 행, 5요인 정의관계 I + ABD + ACE + BCDE 의 접기 결과 I + BCDE.
- Replicate design: 2요인 + 중앙점 1(5런)에 반복 1회 추가 → StdOrder +5, RunOrder 6~10, Blocks 2.
- 접기의 성질: PB 를 전체 접기하면 주효과가 2요인 교호작용과 직교(해상도 IV).
"""
from collections import Counter
from itertools import combinations

import numpy as np
import pytest

from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.general_full import create_general_full_factorial
from doe_core.designs.modify import (
    display_design, fold_design, modify_factors, randomize_design, renumber_design, replicate_design,
)
from doe_core.designs.plackett_burman import create_plackett_burman_design


def rows(d, cols=None):
    cols = cols or d.letters
    return Counter(tuple(r) for r in d.coded[cols].values.tolist())


def test_fold_3_factor_half_fraction_matches_doc_rows():
    d = create_two_level_design(3, 4, randomize=False)          # C = AB
    assert rows(d) == Counter([(-1, -1, 1), (1, -1, -1), (-1, 1, -1), (1, 1, 1)])
    all_f = fold_design(d, "all")
    assert all_f.n_runs == 8
    added = [tuple(r) for r in all_f.coded.iloc[4:][list("ABC")].values.tolist()]
    assert added == [(1, 1, -1), (-1, 1, 1), (1, -1, 1), (-1, -1, -1)]   # 문서 표 5~8행
    assert all_f.alias.is_free and all_f.summary()["Folded on factors"] == "All"
    a_f = fold_design(d, "A")
    added = [tuple(r) for r in a_f.coded.iloc[4:][list("ABC")].values.tolist()]
    assert added == [(1, -1, 1), (-1, -1, -1), (1, 1, -1), (-1, 1, 1)]   # A 만 반전
    assert a_f.summary()["Folded on factors"] == "A"


def test_fold_defining_relation_rules_doc_example():
    d = create_two_level_design(5, 8, seed=0)                     # D = AB, E = AC
    assert d.alias.lines()[0] == "I + ABD + ACE + BCDE"
    for on in ("all", "A"):
        f = fold_design(d, on)
        assert f.alias.lines()[0] == "I + BCDE"
        assert f.alias.resolution == 4 and f.n_runs == 16
        assert "Defining Relation: I = BCDE" in f.summary_text()
        assert f.summary()["Design Generators"] == "D = AB, E = AC"   # 생성자는 접기 전 것
    fb = fold_design(d, "B")
    assert fb.alias.lines()[0] == "I + ACE"


def test_fold_errors_when_defining_relation_not_shortened():
    with pytest.raises(ValueError):
        fold_design(create_two_level_design(3, seed=0), "all")      # 완전요인: 정의관계 없음
    d = create_two_level_design(4, 8, seed=0)                       # I + ABCD (짝수)
    with pytest.raises(ValueError):
        fold_design(d, "all")
    assert fold_design(d, "A").alias.is_free                        # A 를 포함한 단어 제거
    with pytest.raises(ValueError):
        fold_design(create_general_full_factorial([2, 3], seed=0))
    with pytest.raises(ValueError):
        fold_design(fold_design(d, "A"), "B")                       # 두 번 접기


def test_fold_keeps_center_points_out_and_block_generators():
    d = create_two_level_design(5, 16, n_blocks=4, center_points=1, seed=2)   # E=ABCD, 블록 AB, AC
    f = fold_design(d, "all")
    assert f.n_runs == d.n_runs + 16                               # 모서리점만 복제
    assert (f.runs["CenterPt"] == 0).sum() == 4
    assert f.coded.groupby("Blocks").size().tolist() == [9, 9, 9, 9]
    for _, g in f.coded[f.coded["CenterPt"] == 1].groupby("Blocks"):
        assert (g.A * g.B).nunique() == 1 and (g.A * g.C).nunique() == 1
    assert f.alias.resolution is None and f.summary()["Block Generators"] == "AB, AC"


def test_fold_plackett_burman_makes_main_effects_clear_of_two_factor_interactions():
    d = create_plackett_burman_design(11, 12, center_points=2, seed=4)
    f = fold_design(d, "all")
    assert f.n_runs == 12 + 2 + 12 and f.summary()["Folded on factors"] == "All"
    assert f.summary()["Base runs"] == 26
    x = f.coded[f.coded["PtType"] == 1][f.letters].values
    for k in range(11):
        for i, j in combinations(range(11), 2):
            assert (x[:, k] * x[:, i] * x[:, j]).sum() == 0


def test_replicate_design_matches_doc_example():
    f = [Factor("Temperature", 25, 45), Factor("Pressure", 50, 150)]
    d = create_two_level_design(2, factors=f, center_points=1, seed=5)
    r = replicate_design(d)
    assert r.n_runs == 10 and r.replicates == 2 and r.n_blocks == 2
    top, bottom = r.coded.iloc[:5], r.coded.iloc[5:]
    assert (bottom["StdOrder"].values == top["StdOrder"].values + 5).all()
    assert bottom["RunOrder"].tolist() == [6, 7, 8, 9, 10]
    assert (bottom["Blocks"] == 2).all()
    assert r.runs.iloc[5:][["Temperature", "Pressure"]].values.tolist() == r.runs.iloc[:5][["Temperature", "Pressure"]].values.tolist()
    assert r.summary()["Center pts (total)"] == 2                   # 중앙점도 복제
    with pytest.raises(ValueError):
        replicate_design(d, 11)


def test_randomize_entire_and_just_block():
    d = replicate_design(create_two_level_design(3, center_points=1, seed=0), 2)   # 블록 3개 × 9런
    e = randomize_design(d, seed=8)
    assert sorted(e.coded["RunOrder"]) == list(range(1, 28))
    # 블록마다 RunOrder 가 연속 구간
    for _, g in e.coded.groupby("Blocks"):
        ro = sorted(g["RunOrder"])
        assert ro == list(range(ro[0], ro[0] + 9))
    j = randomize_design(d, block=2, seed=9)
    keep = d.coded[d.coded["Blocks"] != 2].set_index("StdOrder")["RunOrder"]
    after = j.coded[j.coded["Blocks"] != 2].set_index("StdOrder")["RunOrder"]
    assert after.sort_index().equals(keep.sort_index())
    assert sorted(j.coded[j.coded["Blocks"] == 2]["RunOrder"]) == list(range(10, 19))
    # 행 순서를 바꾸지 않는 옵션
    k = randomize_design(d, seed=1, display_in_run_order=False)
    assert k.coded["StdOrder"].tolist() == d.coded["StdOrder"].tolist()


def test_renumber_modify_factors_and_display():
    d = create_two_level_design(3, center_points=2, seed=3)
    shuffled = d.coded.sample(frac=1, random_state=0)
    from dataclasses import replace
    d2 = replace(d, coded=shuffled.reset_index(drop=True))
    rn = renumber_design(d2)
    assert rn.coded["RunOrder"].tolist() == list(range(1, 11))

    m = modify_factors(d, {"A": Factor("Temp", 150, 200), "B": Factor("Time", 10, 30)})
    assert [f.name for f in m.factors] == ["Temp", "Time", "C"]
    assert set(m.runs["Temp"]) == {150.0, 175.0, 200.0}
    assert m.coded.equals(d.coded)
    with pytest.raises(ValueError):
        modify_factors(d, {"A": Factor("Mat", "X", "Y", numeric=False)})   # 유형 변경 불가

    std = display_design(m, order="std")
    assert std["StdOrder"].tolist() == list(range(1, 11))
    coded = display_design(m, units="coded")
    assert set(coded["Temp"]) == {-1, 0, 1} and coded["RunOrder"].is_monotonic_increasing
