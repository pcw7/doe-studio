"""Plackett-Burman 설계 생성 검증.

정답 출처
- Minitab 문서 예제 "Create Plackett-Burman Design": 9요인 12런 + 중앙점 3(픽스처의 Design Summary, Design Table).
  설계표는 Minitab 난수로 랜덤화된 것이므로 행 '집합'과 요약표를 비교한다.
- 모든 런 수(12~48)에 대해 열 직교성·균형(각 열 합 0)·마지막 표준 행 전부 −.
"""
from collections import Counter

import numpy as np
import pytest

from conftest import load_fixture, table
from doe_core.designs.common import Factor, factor_letters
from doe_core.designs.plackett_burman import PB_RUNS, create_plackett_burman_design, default_runs, pb_matrix


@pytest.mark.parametrize("n", PB_RUNS)
def test_pb_matrix_is_orthogonal_and_balanced(n):
    m = pb_matrix(n)
    assert m.shape == (n, n - 1)
    assert set(np.unique(m)) == {-1, 1}
    assert (m.sum(axis=0) == 0).all()
    assert np.array_equal(m.T @ m, n * np.eye(n - 1, dtype=int))
    assert (m[-1] == -1).all()


def test_pb_40_first_column_is_20_run_generator_doubled():
    # 문서의 40런 생성열은 20런 생성열을 두 번 이어 쓴 것(가운데 '−' 하나가 문서에서 빠짐)
    g20 = "++--++++-+-+----++-"
    first = "".join("+" if v > 0 else "-" for v in pb_matrix(40)[:-1, 0])
    assert first == g20 + "-" + g20


def test_example_9_factors_12_runs_3_center_points():
    fx = load_fixture("create-plackett-burman__example")
    d = create_plackett_burman_design(9, 12, center_points=3, seed=7)

    # Design Summary: 3행 × 4칸 + Center points
    summ = table(fx, "Design Summary")
    expected = {summ["header"][0]: summ["header"][1], summ["header"][2]: summ["header"][3]}
    for r in summ["rows"]:
        expected[r[0]] = r[1]
        expected[r[2]] = r[3]
    got = {f"{k}:": str(v) for k, v in d.summary().items()}
    for k, v in expected.items():
        assert got[k] == v, (k, got[k], v)
    assert d.summary()["Center points"] == 3
    assert "Center points: 3" in d.summary_text()

    # Design Table: 열 이름과 행 집합(+ 중앙점 3개)
    dt = table(fx, "Design Table")
    assert dt["header"] == ["Run", "Blk", *factor_letters(9)]
    want = Counter(tuple(r[2:]) for r in dt["rows"])
    mine = d.design_table()
    assert list(mine.columns) == dt["header"]
    have = Counter(tuple(r) for r in mine[factor_letters(9)].values.tolist())
    assert have == want
    assert mine["Run"].tolist() == list(range(1, 16))


def test_worksheet_columns_ptype_and_levels():
    f = [Factor("Temp", 150, 200), Factor("Cat", "X", "Y", numeric=False), Factor("Time", 10, 20)]
    d = create_plackett_burman_design(3, factors=f, center_points=2, randomize=False)
    assert list(d.runs.columns) == ["StdOrder", "RunOrder", "PtType", "Blocks", "Temp", "Cat", "Time"]
    # 텍스트 요인 1개 → 중앙점 2 × 2^1 = 4
    cp = d.runs[d.runs["PtType"] == 0]
    assert len(cp) == 4 and sorted(cp["Cat"]) == ["X", "X", "Y", "Y"]
    assert (cp["Temp"] == 175).all() and (cp["Time"] == 15).all()
    assert d.n_runs == 12 + 4
    assert (d.runs["RunOrder"] == d.runs["StdOrder"]).all()
    assert "2^Q times as many centerpoints" in d.summary_text()


def test_replicates_center_points_per_replicate_and_blocks():
    d = create_plackett_burman_design(5, 12, center_points=3, replicates=2, seed=1)
    s = d.summary()
    assert s["Base runs"] == 15 and s["Total runs"] == 30 and s["Center points"] == 6 and s["Total blocks"] == 1
    d2 = create_plackett_burman_design(5, 12, center_points=3, replicates=2, block_on_replicates=True, seed=1)
    assert d2.summary()["Total blocks"] == 2
    assert d2.coded.groupby("Blocks").size().tolist() == [15, 15]
    # 블록 안에서만 랜덤: RunOrder 순으로 블록 번호가 단조 증가
    assert d2.coded["Blocks"].is_monotonic_increasing


def test_default_runs_and_validation():
    assert default_runs(2) == 12 and default_runs(11) == 12 and default_runs(12) == 20
    assert default_runs(19) == 20 and default_runs(20) == 24 and default_runs(47) == 48
    with pytest.raises(ValueError):
        create_plackett_burman_design(12, 12)          # 12런은 최대 11요인
    with pytest.raises(ValueError):
        create_plackett_burman_design(5, 16)           # 16런 PB 없음
    with pytest.raises(ValueError):
        create_plackett_burman_design(48)              # 최대 47요인


def test_factor_letters_skip_i_and_extend_beyond_25():
    letters = factor_letters(30)
    assert letters[:10] == list("ABCDEFGHJK")
    assert "I" not in letters[:25] and letters[24] == "Z"
    assert letters[25:] == ["AA", "AB", "AC", "AD", "AE"]
    d = create_plackett_burman_design(47, seed=0)
    assert d.n_runs == 48 and len(set(d.letters)) == 47
