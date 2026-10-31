"""반응표면 설계(CCD·Box-Behnken·축점 추가) 생성 검증.

정답 출처(Minitab 문서)
- 'Summary of central composite designs' 표 44행: 런 수, 큐브·축·중앙점 수, 기본 α(소수 3자리), 블록 직교성.
- 'Summary of Box-Behnken designs' 표: 요인 3~7의 런 수와 블록 수.
- 예제: CCD 3요인 2블록 20런(α = 1.633), Box-Behnken 3요인 15런, Add axial points(3요인 반쪽 + 중앙점 3).
"""
from collections import Counter
from itertools import combinations

import numpy as np
import pytest

from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.response_surface import (
    BBD_CATALOG, CCD_CATALOG, CCD_ERRATA, add_axial_points, create_box_behnken, create_ccd,
)
from doe_core.io.worksheet import Worksheet, load_worksheet, save_worksheet
from tests.helpers import load_fixture, table


def quad_matrix(c: np.ndarray) -> np.ndarray:
    k = c.shape[1]
    cols = [np.ones(len(c))] + [c[:, i] for i in range(k)] + [c[:, i] ** 2 for i in range(k)]
    cols += [c[:, i] * c[:, j] for i, j in combinations(range(k), 2)]
    return np.column_stack(cols)


def blocks_orthogonal(d) -> bool:
    """블록 효과가 2차 모형 항과 직교: 블록마다 x_i, x_i x_j 합이 0 이고 x_i² 평균이 블록 사이에 같다."""
    c = d.coded
    L = d.letters
    sq_means = []
    for _, g in c.groupby("Blocks"):
        x = g[L].values.astype(float)
        if not np.allclose(x.sum(axis=0), 0):
            return False
        for i, j in combinations(range(len(L)), 2):
            if abs((x[:, i] * x[:, j]).sum()) > 1e-9:
                return False
        sq_means.append((x ** 2).sum(axis=0) / len(g))
    return bool(np.allclose(sq_means, sq_means[0], atol=1e-9))


@pytest.mark.parametrize("key", sorted(CCD_CATALOG))
def test_ccd_catalog_rows(key):
    e = CCD_CATALOG[key]
    assert e.runs == e.cube_runs + 2 * e.k + e.center
    if e.blocks > 1:
        assert e.center == e.cube_center + e.axial_center and e.cube_blocks == e.blocks - 1
    assert round(e.default_alpha, 3) == float(e.alpha_text)
    d = create_ccd(e.k, fraction=e.fraction, blocks=e.blocks, seed=1)
    assert d.n_runs == e.runs and d.coded["Blocks"].nunique() == e.blocks
    pc = d.point_counts()
    assert pc["cube"] == e.cube_runs and pc["axial"] == 2 * e.k and pc["center"] == e.center
    # 2차 모형 추정 가능
    X = quad_matrix(d.coded[d.letters].values.astype(float))
    assert np.linalg.matrix_rank(X) == X.shape[1]
    # 회전성 표시가 n 인 블록 설계는 직교 블록 α 를 쓴다 → 직교
    if e.blocks > 1 and not e.rotatable:
        assert blocks_orthogonal(d)


def test_ccd_errata_recorded():
    assert (3, "Full", 1) in CCD_ERRATA and CCD_CATALOG[(3, "Full", 1)].runs == 20


def test_ccd_example_3_factors_2_blocks():
    fx = load_fixture("create-central-composite-design__example")
    d = create_ccd(3, blocks=2, seed=3)
    s = d.summary()
    summ = table(fx, "Design Summary")
    exp = {}
    for r in [summ["header"], *summ["rows"]]:
        exp[r[0]], exp[r[2]] = r[1], r[3]
    for k, v in exp.items():
        assert str(s[k.rstrip(":")]) == v, k
    pts = table(fx, "Point Types")
    for r in [pts["header"], *pts["rows"]]:
        assert str(s[r[0].rstrip(":")]) == r[1]
    assert "α = 1.633" in d.summary_text() and "Two-level factorial: Full factorial" in d.summary_text()
    dt = table(fx, "Design Table")
    want = Counter((r[1], *r[2:]) for r in dt["rows"])
    mine = d.design_table()
    have = Counter((str(r[1]), *r[2:]) for r in mine.astype(str).values.tolist())
    assert have == want
    # 블록 1 = 큐브 + 중앙점 4, 블록 2 = 축점 + 중앙점 2
    assert d.coded.groupby("Blocks").size().tolist() == [12, 8]


def test_ccd_unblocked_rotatable_and_options():
    d = create_ccd(2, seed=0)
    assert d.n_runs == 13 and abs(d.alpha - 2 ** 0.5) < 1e-12
    assert d.coded.sort_values("StdOrder")["PtType"].tolist() == [1] * 4 + [-1] * 4 + [0] * 5   # 큐브 → 축 → 중앙
    f = create_ccd(3, alpha="face", center_points=4, randomize=False)
    assert f.alpha == 1 and f.point_counts()["center"] == 4 and set(np.unique(f.coded["A"])) == {-1.0, 0.0, 1.0}
    c = create_ccd(2, alpha=1.5, randomize=False)
    assert c.alpha == 1.5
    r = create_ccd(2, blocks=2, replicates=2, block_on_replicates=True, seed=0)
    assert r.n_blocks == 4 and r.n_runs == 28 and r.summary()["Base blocks"] == 2
    # 요인 수준을 축점 기준으로 정의: 축점 실제값이 입력한 저/고
    ax = create_ccd(2, factors=[Factor("T", 100, 200), Factor("P", 1, 3)], levels_define="axial", randomize=False)
    vals = ax.runs[ax.runs["PtType"] == -1]["T"]
    assert np.isclose(vals.min(), 100) and np.isclose(vals.max(), 200)
    cube = ax.runs[ax.runs["PtType"] == 1]["T"]
    assert np.isclose(cube.max() - 150, 50 / 2 ** 0.5)
    with pytest.raises(ValueError):
        create_ccd(4, fraction="Half")
    with pytest.raises(ValueError):
        create_ccd(2, factors=[Factor("A", "x", "y", numeric=False), Factor("B")])


def test_box_behnken_example_3_factors():
    fx = load_fixture("create-box-behnken-design__example")
    d = create_box_behnken(3, seed=5)
    assert d.summary()["Center points"] == 3 and "Center points: 3" in d.summary_text()
    dt = table(fx, "Design Table")
    want = Counter(tuple(r[2:]) for r in dt["rows"])
    have = Counter(tuple(str(v) for v in r) for r in d.design_table()[d.letters].values.tolist())
    assert have == want
    assert set(d.coded["PtType"]) == {0, 2}


@pytest.mark.parametrize("k", sorted(BBD_CATALOG))
def test_box_behnken_catalog(k):
    runs, blocks_opts, _ = BBD_CATALOG[k]
    for b in blocks_opts:
        d = create_box_behnken(k, blocks=b, seed=0)
        assert d.n_runs == runs and d.coded["Blocks"].nunique() == b
        x = d.coded[d.letters].values.astype(float)
        assert set(np.unique(x)) == {-1.0, 0.0, 1.0}
        assert not any((np.abs(row) == 1).all() for row in x)         # 모든 요인이 극단인 런 없음
        X = quad_matrix(x)
        assert np.linalg.matrix_rank(X) == X.shape[1]
        if b > 1:
            assert blocks_orthogonal(d)
    with pytest.raises(ValueError):
        create_box_behnken(k, blocks=4)


def test_add_axial_points_doc_example():
    f = [Factor("Pressure", 75, 150), Factor("Injection", 85, 100), Factor("Cooling", 25, 50)]
    d = create_two_level_design(3, 4, factors=f, center_points=3, seed=2)
    r = add_axial_points(d)
    ax = r.runs[r.runs["CenterPt"] == -1].sort_values("StdOrder")
    assert ax["StdOrder"].tolist() == list(range(8, 14)) and ax["RunOrder"].tolist() == list(range(8, 14))
    assert (ax["Blocks"] == 2).all()
    np.testing.assert_allclose(ax["Pressure"].round(3).tolist(), [59.467, 165.533, 112.5, 112.5, 112.5, 112.5])
    np.testing.assert_allclose(ax["Injection"].round(3).tolist(), [92.5, 92.5, 81.893, 103.107, 92.5, 92.5])
    np.testing.assert_allclose(ax["Cooling"].round(4).tolist(), [37.5, 37.5, 37.5, 37.5, 19.8223, 55.1777])
    assert r.kind == "ccd" and abs(r.alpha - 4 ** 0.25) < 1e-12 and r.point_col == "CenterPt"


def test_response_surface_worksheet_round_trip(tmp_path):
    d = create_ccd(3, blocks=2, seed=4)
    ws = Worksheet(d)
    ws.add_column("Y", np.linspace(0, 1, d.n_runs))
    back = load_worksheet(save_worksheet(ws, tmp_path / "rs.json"))
    assert back.design.summary() == d.summary()
    assert np.allclose(back.table()[["A", "B", "C", "Y"]].values, ws.table()[["A", "B", "C", "Y"]].values)
