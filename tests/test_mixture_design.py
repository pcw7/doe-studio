"""혼합물 설계 생성 검증.

정답 출처(Minitab 문서 'Create Mixture Design' 예제)
- 예제 1 단순 중심 3성분(10런: 꼭지점 3, 이중 혼합 3, 중심 1, 축점 3).
- 예제 2 단순 격자 3성분 차수 1(7런: 꼭지점 3, 중심 1, 축점 3).
- 예제 3 극꼭지점 3성분 + 공정 변수 1(18런): 성분 범위 A 0.2~0.6, B 0~0.3, C 0.4~0.6, 선형 제약 A − B ≥ 0,
  Temperature 80/90. 점 유형 표·성분 범위 표·선형 제약 표·설계표(행 집합)를 글자 단위로 비교.
"""
from collections import Counter
from math import comb

import numpy as np
import pytest

from doe_core.designs.common import Factor
from doe_core.designs.mixture import (
    Component, LinearConstraint, create_extreme_vertices, create_simplex_centroid, create_simplex_lattice, mix_letters,
)
from doe_core.io.worksheet import Worksheet, load_worksheet, save_worksheet
from tests.helpers import load_fixture, table


def as_set(d, decimals=4):
    return Counter((int(t), *np.round(r, decimals)) for t, r in zip(d.coded["PtType"], d.coded[d.letters].values))


def test_example_simplex_centroid_3():
    fx = load_fixture("create-mixture-design__example-for-simplex-centroid")
    d = create_simplex_centroid(3, components=[Component("Neroli"), Component("Rose"), Component("Tangerine")], seed=1)
    assert d.n_runs == 10 and "Design degree: 3" in d.summary_text() and "Mixture total: 1.00000" in d.summary_text()
    assert table(fx, "Number of Boundaries")["rows"] == d.boundaries_table().values.tolist()
    assert table(fx, "Number of Design Points")["rows"] == d.points_table().values.tolist()
    want = Counter((int(r[1]), *[round(float(x), 4) for x in r[2:]]) for r in table(fx, "Design Table")["rows"])
    assert as_set(d) == want
    np.testing.assert_allclose(d.coded[d.letters].sum(axis=1), 1.0)
    # 표준 순서: 꼭지점 A,B,C → 이중 혼합 AB, AC, BC → 중심 → 축점(문서 워크시트 예)
    std = d.coded.sort_values("StdOrder")
    assert std["PtType"].tolist() == [1, 1, 1, 2, 2, 2, 0, -1, -1, -1]
    assert std.iloc[4][d.letters].tolist() == [0.5, 0.0, 0.5]


def test_example_simplex_lattice_degree1():
    fx = load_fixture("create-mixture-design__example-for-simplex-lattice")
    d = create_simplex_lattice(3, 1, seed=2)
    assert d.n_runs == 7 and "Lattice degree: 1" in d.summary_text()
    assert table(fx, "Number of Design Points")["rows"] == d.points_table().values.tolist()
    want = Counter((int(r[1]), *[round(float(x), 4) for x in r[2:]]) for r in table(fx, "Design Table")["rows"])
    assert as_set(d) == want


def test_example_extreme_vertices_with_process_variable():
    fx = load_fixture("create-mixture-design__example-for-extreme-vertices")
    comps = [Component("Emmenthaler", 0.2, 0.6), Component("Gruyere", 0, 0.3), Component("Broth", 0.4, 0.6)]
    d = create_extreme_vertices(3, components=comps, constraints=[LinearConstraint({"A": 1, "B": -1, "C": 0}, lower=0)],
                                process=[Factor("Temperature", 80, 90)], seed=3)
    assert d.summary_text().splitlines()[1:3] == ["Components: 3  Design points: 18",
                                                   "Process variables: 1  Design degree: 1"]
    assert table(fx, "Number of Design Points")["rows"] == d.points_table().values.tolist()
    b = table(fx, "Bounds of Mixture Components")
    assert b["rows"][1:] == d.bounds_table().values.tolist()
    assert table(fx, "Linear Constraints")["rows"] == d.constraints_table().values.tolist()
    dt = table(fx, "Design Table")
    assert dt["header"] == list(d.design_table().columns)
    mine = Counter(tuple(map(str, r[1:])) for r in d.design_table().values.tolist())
    assert Counter(tuple(r[1:]) for r in dt["rows"]) == mine
    assert set(d.runs["Temperature"]) == {80.0, 90.0}
    # 경계 수: 기하학적으로 서로 다른 꼭지점·모서리(문서 표는 퇴화 꼭지점을 중복으로 세어 5·5)
    assert d.boundaries == [4, 4, 1]


def test_lattice_and_centroid_counts():
    for q in range(2, 6):
        d = create_simplex_centroid(q, axial=False, randomize=False)
        assert d.n_runs == 2 ** q - 1
    for q, m in [(3, 2), (3, 3), (4, 2), (4, 3)]:
        d = create_simplex_lattice(q, m, center=False, axial=False, randomize=False)
        assert d.n_runs == comb(q + m - 1, m)
        assert set(np.round(d.coded[d.letters].values.ravel() * m, 9)) <= set(range(m + 1))
    d33 = create_simplex_lattice(3, 3, randomize=False)                  # 중심이 이미 격자점 → 중앙점 중복 없음
    assert (d33.coded["PtType"] == 0).sum() == 1
    with pytest.raises(ValueError):
        create_simplex_lattice(9, 5)                                       # 차수 5 는 성분 8개까지
    assert mix_letters(20)[8] == "J" and "T" not in mix_letters(20)


def test_pseudocomponents_and_replicates():
    comps = [Component("A", 0.1, 1), Component("B", 0.2, 1), Component("C", 0.0, 1)]
    d = create_simplex_centroid(3, components=comps, axial=False, randomize=False)
    vtx = d.coded[d.coded["PtType"] == 1][d.letters].values
    np.testing.assert_allclose(sorted(map(tuple, vtx)), sorted([(0.8, 0.2, 0.0), (0.1, 0.9, 0.0), (0.1, 0.2, 0.7)]))
    r = create_simplex_lattice(3, 2, replicates=2, type_replicates={1: 3}, randomize=False)
    pt = r.points_table().set_index("Point Type")
    assert pt.loc["Replicates", "1"] == "6" and pt.loc["Replicates", "2"] == "2"


def test_extreme_vertices_degree_and_save(tmp_path):
    comps = [Component("A", 0.1, 0.5), Component("B", 0.2, 0.6), Component("C", 0.1, 0.4)]
    d1 = create_extreme_vertices(3, components=comps, center=False, axial=False, randomize=False)
    d2 = create_extreme_vertices(3, components=comps, degree=2, center=False, axial=False, randomize=False)
    nv = (d1.coded["PtType"] == 1).sum()
    assert (d2.coded["PtType"] == 2).sum() == nv                            # 다각형: 모서리 수 = 꼭지점 수
    G = d2.coded[d2.letters].values
    assert np.all(G >= np.array([0.1, 0.2, 0.1]) - 1e-9) and np.all(G <= np.array([0.5, 0.6, 0.4]) + 1e-9)
    ws = Worksheet(d2)
    ws.add_column("Y", np.arange(d2.n_runs, dtype=float))
    back = load_worksheet(save_worksheet(ws, tmp_path / "mix.json"))
    assert back.design.summary() == d2.summary() and back.design.points_table().equals(d2.points_table())
    with pytest.raises(ValueError):
        create_extreme_vertices(3, components=[Component("A", 0.5, 1), Component("B", 0.5, 1), Component("C", 0.1, 1)])
