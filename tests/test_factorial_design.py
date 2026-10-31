"""2수준 요인설계 생성 엔진 검증.

정답 출처
- Minitab 문서 "Design generators for 2-level designs" 표 50행(카탈로그 자체): 생성자로부터 계산한 해상도와
  블록 포함 해상도가 표의 값과 전부 일치해야 한다.
- Minitab 문서 예제: 6요인 16런 1/4(해상도 IV, E=ABC F=BCD), 5요인 16런 1/2 블록 4(E=ABCD, 블록 생성자 AB AC).
"""
import numpy as np
import pytest

from doe_core.designs.catalog import CATALOG, CATALOG_ERRATA, available_designs, lookup
from doe_core.designs.factorial import (
    Factor,
    alias_structure,
    create_two_level_design,
    resolution_of,
    resolution_with_blocks_of,
    word_from_str,
)


def test_catalog_size_and_fraction_labels():
    assert len(CATALOG) == 49  # 문서 표 50행 중 (5,16) 중복 1행 제외
    assert lookup(6, 16).fraction == "1/4"
    assert lookup(5, 16).fraction == "1/2"
    assert lookup(4, 16).fraction == "full"
    assert [e.n_runs for e in available_designs(6)] == [8, 16, 32, 64]


def test_every_catalog_resolution_matches_generators():
    for (k, n), e in CATALOG.items():
        if e.is_full:
            assert resolution_of({}) is None
            continue
        assert resolution_of(e.generators) == e.resolution, (k, n, e.generators)


# Minitab 문서 표의 오류: 13요인 128런 행은 12요인 128런 행의 블록 지정을 그대로 복사해 두었다.
# 생성자(M=ACEF, N=ABC …)가 달라 2블록은 해상도 III(문서는 IV), 8·16블록은 블록이 주효과와 교락된다.
def test_catalog_block_specs_validated_against_generators():
    assert CATALOG_ERRATA == {
        (13, 128, 2): (4, 3, "corrected"),
        (13, 128, 8): (3, 2, "dropped"),
        (13, 128, 16): (3, 2, "dropped"),
    }
    for (k, n), e in CATALOG.items():
        for nb, spec in e.blocks.items():
            assert resolution_with_blocks_of(e.generators_for(nb), list(spec.generators)) == spec.resolution_with_blocks


EXPECTED_6F_16RUN_ALIAS = """I + ABCE + ADEF + BCDF
A + BCE + DEF + ABCDF
B + ACE + CDF + ABDEF
C + ABE + BDF + ACDEF
D + AEF + BCF + ABCDE
E + ABC + ADF + BCDEF
F + ADE + BCD + ABCEF
AB + CE + ACDF + BDEF
AC + BE + ABDF + CDEF
AD + EF + ABCF + BCDE
AE + BC + DF + ABCDEF
AF + DE + ABCD + BCEF
BD + CF + ABEF + ACDE
BF + CD + ABDE + ACEF
ABD + ACF + BEF + CDE
ABF + ACD + BDE + CEF""".splitlines()


def test_example_6_factor_quarter_fraction():
    d = create_two_level_design(6, 16, seed=1)
    s = d.summary()
    assert s["Factors"] == 6 and s["Runs"] == 16 and s["Base Design"] == "6, 16"
    assert s["Resolution"] == "IV" and s["Fraction"] == "1/4" and s["Blocks"] == 1
    assert s["Center pts (total)"] == 0 and s["Replicates"] == 1
    assert s["Design Generators"] == "E = ABC, F = BCD"
    assert d.alias.lines() == EXPECTED_6F_16RUN_ALIAS
    # 문서에 실린 6개 런이 설계에 들어 있어야 한다(순서는 랜덤화로 달라질 수 있음)
    shown = [(1, -1, -1, -1, 1, -1), (-1, 1, 1, -1, -1, -1), (-1, -1, -1, -1, -1, -1),
             (-1, -1, -1, 1, -1, 1), (-1, -1, 1, -1, 1, 1), (1, 1, -1, 1, -1, -1)]
    rows = {tuple(r) for r in d.coded[list("ABCDEF")].values.tolist()}
    assert all(tuple(x) for x in shown) and set(shown) <= rows
    assert len(rows) == 16
    # 생성자 관계 E=ABC, F=BCD 가 모든 런에서 성립
    c = d.coded
    assert (c.A * c.B * c.C == c.E).all() and (c.B * c.C * c.D == c.F).all()


EXPECTED_5F_16RUN_4BLOCK_ALIAS = """I + ABCDE
Blk1 = AB + CDE
Blk2 = AC + BDE
Blk3 = BC + ADE
A + BCDE
B + ACDE
C + ABDE
D + ABCE
E + ABCD
AD + BCE
AE + BCD
BD + ACE
BE + ACD
CD + ABE
CE + ABD
DE + ABC""".splitlines()


def test_example_5_factor_half_fraction_4_blocks():
    d = create_two_level_design(5, 16, n_blocks=4, seed=3)
    s = d.summary()
    assert s["Resolution with blocks"] == "III" and s["Fraction"] == "1/2" and s["Blocks"] == 4
    assert s["Design Generators"] == "E = ABCD" and s["Block Generators"] == "AB, AC"
    assert d.alias.lines() == EXPECTED_5F_16RUN_4BLOCK_ALIAS
    assert "Blocks are confounded with two-way interactions" in d.summary_text()
    # 블록마다 4런, 블록 안에서 AB·AC 부호가 일정
    c = d.coded
    assert c.groupby("Blocks").size().tolist() == [4, 4, 4, 4]
    for _, g in c.groupby("Blocks"):
        assert (g.A * g.B).nunique() == 1 and (g.A * g.C).nunique() == 1
    # StdOrder 는 블록 순, RunOrder 도 블록 순(블록 안에서만 랜덤)
    by_std = c.sort_values("StdOrder")
    assert by_std["Blocks"].is_monotonic_increasing
    by_run = c.sort_values("RunOrder")
    assert by_run["Blocks"].is_monotonic_increasing


def test_full_factorial_no_aliasing_and_center_points_and_replicates():
    f = [Factor("Temp", 150, 200), Factor("Time", 30, 60), Factor("Cat", 1, 3)]
    d = create_two_level_design(3, factors=f, center_points=2, replicates=2, seed=0)
    assert d.alias_text().endswith("All terms are free from aliasing.")
    # Minitab: 중앙점은 블록당 지정 수이며 반복을 늘려도 늘지 않는다 → 8×2 + 2 = 18
    assert d.n_runs == 18
    assert (d.runs["CenterPt"] == 0).sum() == 2
    cp = d.runs[d.runs["CenterPt"] == 0]
    assert (cp["Temp"] == 175).all() and (cp["Time"] == 45).all() and (cp["Cat"] == 2).all()
    assert set(d.runs["Temp"].unique()) == {150.0, 175.0, 200.0}
    # 직교성: 모서리점의 각 요인 열 합은 0
    corners = d.coded[d.coded["CenterPt"] == 1]
    assert (corners[list("ABC")].sum() == 0).all()


def test_text_factor_levels_and_randomize_off():
    f = [Factor("Material", "Formula1", "Formula2", numeric=False), Factor("Press", 75, 150)]
    d = create_two_level_design(2, factors=f, randomize=False)
    assert (d.runs["RunOrder"] == d.runs["StdOrder"]).all()
    assert d.runs["Material"].tolist() == ["Formula1", "Formula2", "Formula1", "Formula2"]
    assert d.runs["Press"].tolist() == [75, 75, 150, 150]


def test_specify_generators_and_errors():
    d = create_two_level_design(5, 8, generators={"D": "AB", "E": "AC"}, seed=0)
    assert d.alias.resolution == 3
    with pytest.raises(ValueError):
        create_two_level_design(6, 12)
    with pytest.raises(ValueError):
        create_two_level_design(3, 4, n_blocks=2)  # 카탈로그: No blocking
    with pytest.raises(ValueError):  # 모든 요인이 텍스트면 중앙점 불가
        create_two_level_design(2, factors=[Factor("A", "x", "y", numeric=False), Factor("B", "p", "q", numeric=False)], center_points=1)


def test_alias_structure_direct_api():
    a = alias_structure(4, [word_from_str("DABC")])
    assert a.lines() == ["I + ABCD", "A + BCD", "B + ACD", "C + ABD", "D + ABC", "AB + CD", "AC + BD", "AD + BC"]
    assert a.resolution == 4


def test_center_points_with_text_factor_are_multiplied_per_level_combination():
    # Minitab: 텍스트 요인 Q 개면 중앙점은 텍스트 수준 조합마다 추가되어 2^Q 배. 블록마다 적용.
    f = [Factor("A", 0, 10), Factor("B", "absent", "present", numeric=False), Factor("C", 0.2, 0.3)]
    d = create_two_level_design(3, factors=f, center_points=3, seed=0)
    cp = d.runs[d.runs["CenterPt"] == 0]
    assert len(cp) == 6 and d.summary()["Center pts (total)"] == 6
    assert sorted(cp["B"].tolist()) == ["absent"] * 3 + ["present"] * 3
    assert (cp["A"] == 5).all() and (cp["C"] == 0.25).all()
    assert "2^Q times as many centerpoints" in d.summary_text()


def test_blocks_from_replicates_without_generators():
    # 블록 수 = 반복 수 → 반복이 곧 블록, 블록 생성자 없음, 해상도 유지, 중앙점은 블록마다
    d = create_two_level_design(4, 8, replicates=2, n_blocks=2, center_points=1, seed=0)
    s = d.summary()
    assert s["Blocks"] == 2 and s["Replicates"] == 2 and "Block Generators" not in s
    assert s["Resolution"] == "IV" and s["Center pts (total)"] == 2 and d.n_runs == 18
    assert d.coded.groupby("Blocks").size().tolist() == [9, 9]
    # 블록 수 4 = 반복 2 × 블록 생성자 1개(AB)
    d2 = create_two_level_design(4, 8, replicates=2, n_blocks=4, seed=0)
    assert d2.summary()["Block Generators"] == "AB" and d2.coded["Blocks"].nunique() == 4


def test_resolution_iii_note_and_alias_default_order_cap():
    d = create_two_level_design(5, 8, seed=0)
    assert "Some main effects are confounded with two-way interactions" in d.summary_text()
    # 11요인 이상은 기본으로 2차 교호작용까지만 표시하고 제목에 (up to order 2)
    d11 = create_two_level_design(11, 32, seed=0)
    txt = d11.alias_text()
    assert txt.startswith("Alias Structure (up to order 2)")
    body = txt.splitlines()[2:]  # I 줄 제외
    assert all(all(len(w) <= 2 for w in line.split(" + ")) for line in body)
    # 전부 표시 옵션
    assert d11.alias_text(max_order=None).startswith("Alias Structure\n")
