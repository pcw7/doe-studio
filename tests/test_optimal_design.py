"""최적 설계(Select Optimal Design) 검증.

정답 출처(Minitab 문서 'Select Optimal Design' 예제 3개, CrystalGrowth 4요인 2블록 CCD 30런)
- 선택: 30 → 20점, 완전 2차 + 블록. 선택 순서(행 번호)와 통계량 6개를 글자 단위로 비교.
- 증강: 문서 워크시트의 OptPoint(20점)를 −1 로 보호하고 25점으로. 행 번호·통계량 비교.
- 평가: OptPoint 20점을 선형 모형으로 평가. 통계량 비교.
"""
import numpy as np
import pytest

from doe_core.analysis.factorial import analyze_factorial
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.general_full import GeneralFactor, create_general_full_factorial
from doe_core.designs.mixture import create_simplex_lattice
from doe_core.designs.optimal import (
    _gfmt, augment_optimal_design, candidate_matrix, evaluate_design, optimal_subset, select_optimal_design,
)
from doe_core.io.worksheet import Worksheet, load_mwx_worksheet
from tests.helpers import SAMPLES, load_fixture

CRYSTAL = SAMPLES / "CrystalGrowth.MWX"
needs_crystal = pytest.mark.skipif(not CRYSTAL.exists(), reason="CrystalGrowth.MWX 없음")
# 문서 예제 2·3 의 워크시트 OptPoint 열(1 인 행)
OPT_ROWS = [1, 3, 4, 6, 8, 9, 10, 13, 15, 16, 17, 19, 22, 23, 24, 25, 26, 27, 28, 30]


def fx(name):
    return load_fixture(f"factorial__select-optimal-design__example-of-{name}-an-optimal-design")


def crystal():
    return load_mwx_worksheet(CRYSTAL, ["A", "B", "C", "D"]).design


def opt_indicator(sign=1):
    ind = np.zeros(30)
    ind[[r - 1 for r in OPT_ROWS]] = sign
    return ind


def doc_block(lines, first):
    """문서 단계 목록에서 출력 블록(first 줄부터 행 번호 두 줄까지)."""
    i = lines.index(first)
    j = next(k for k in range(i, len(lines)) if lines[k].startswith("Row number"))
    return lines[i:j + 2]


def full(t):
    return [t["header"], *t["rows"]]


def mine_block(r):
    rows = r.rows_text().split("\n")
    return [*r.header_lines(), "Specified Design" if r.task == "evaluate" else "Optimal Design",
            rows[0], rows[1].strip()]


@needs_crystal
def test_example_select_20_of_30():
    f = fx("selecting")
    r = select_optimal_design(crystal(), 20)
    assert mine_block(r) == doc_block(f["steps"], "Response surface design selected according to D-optimality")
    assert r.statistics_table().values.tolist() == full(f["tables"][0])
    ind = r.indicator()
    assert ind.sum() == 20 and set(ind) <= {0, 1}


@needs_crystal
def test_example_augment_to_25():
    f = fx("augmenting")
    r = augment_optimal_design(crystal(), opt_indicator(-1), 25)
    assert mine_block(r) == doc_block(f["steps"], "Response surface design augmented according to D-optimality")
    assert r.statistics_table().values.tolist() == full(f["tables"][-1])
    assert r.rows[:20] == [x - 1 for x in OPT_ROWS]                         # 보호한 점은 그대로 앞에


@needs_crystal
def test_example_evaluate_linear():
    f = fx("evaluating")
    r = evaluate_design(crystal(), opt_indicator(1), model="linear")
    assert r.header_lines() == ["Evaluation of Specified Response Surface Design",
                                "Number of design points in optimal design: 20", "Model terms: Block, A, B, C, D"]
    rows = r.rows_text().split("\n")
    assert [rows[0], rows[1].strip()] == f["notes"][2:4]
    assert r.statistics_table().values.tolist() == full(f["tables"][0])
    # 같은 20점을 완전 2차 모형으로 평가하면 예제 1 의 최적 설계와 같은 D·A 값(동등한 D-최적 설계)
    fq = evaluate_design(crystal(), opt_indicator(1))
    assert _gfmt(fq.statistics["D-optimality"]) == "2.73819E+18"


@needs_crystal
def test_improvement_methods_and_subset():
    d = crystal()
    seq = select_optimal_design(d, 20, improve=None)
    exc = select_optimal_design(d, 20)
    fed = select_optimal_design(d, 20, improve="fedorov")
    assert seq.statistics["D-optimality"] < exc.statistics["D-optimality"] * (1 + 1e-9)
    assert fed.statistics["D-optimality"] >= exc.statistics["D-optimality"] * (1 - 1e-9)
    assert fed.improve_method == "Fedorov" and "exchanged" not in " ".join(fed.header_lines())
    two = select_optimal_design(d, 22, n_exchange=2)
    assert "Number of design points exchanged is 2" in two.header_lines()
    sub = optimal_subset(d, exc.rows)
    assert sub.n_runs == 20 and list(sub.coded["StdOrder"]) == list(range(1, 21))
    ws = Worksheet(d)
    ws.add_column("OptPoint", exc.indicator(), order="worksheet")
    assert ws.table("worksheet")["OptPoint"].sum() == 20
    y = np.random.default_rng(0).normal(size=20)
    a = analyze_factorial(sub, y)                                            # 고른 설계로 완전 2차 분석 가능
    assert a.df_error == 4
    with pytest.raises(ValueError):
        select_optimal_design(d, 10)                                         # 항 16개보다 적음
    with pytest.raises(ValueError):
        evaluate_design(d, np.r_[np.ones(10), np.zeros(20)])                 # 10점으로 2차 모형 불가
    with pytest.raises(ValueError):
        augment_optimal_design(d, np.full(30, 0.5), 25)


def test_factorial_and_distance():
    d = create_two_level_design(4, 16, randomize=False)
    F, labels = candidate_matrix(d, order=2)
    assert labels == ["A", "B", "C", "D", "AB", "AC", "AD", "BC", "BD", "CD"] and F.shape == (16, 11)
    r = select_optimal_design(d, 12, order=2)
    assert r.kind_label == "Factorial" and r.header_lines()[0] == "Factorial design selected according to D-optimality"
    assert r.statistics["D-optimality"] > 0 and r.n_points == 12
    dist = select_optimal_design(d, 8, criterion="distance", order=1)
    Z = d.coded[d.letters].values[dist.rows]
    assert len({tuple(z) for z in Z}) == 8                                   # 거리 기반은 반복 없음
    assert dist.rows[0] == int(np.argmax((d.coded[d.letters].values ** 2).sum(axis=1)))
    g = create_general_full_factorial([GeneralFactor("A", [1, 2, 3]), GeneralFactor("B", ["x", "y"])], randomize=False)
    with pytest.raises(ValueError):
        select_optimal_design(g, 4, criterion="distance")


def test_mixture_quadratic_d_optimal_is_lattice():
    d = create_simplex_lattice(3, 2, randomize=False)                        # 꼭지점 3 + 모서리 중점 3 + 중심 + 축점 3
    r = select_optimal_design(d, 6, model="quadratic")
    pt = d.coded["PtType"].values[r.rows]
    assert sorted(pt) == [1, 1, 1, 2, 2, 2]                                  # Scheffé 2차의 D-최적 = {3,2} 격자
    assert r.header_lines()[0] == "Mixture design selected according to D-optimality"
    assert r.terms == ["A", "B", "C", "AB", "AC", "BC"]
    dist = select_optimal_design(d, 4, criterion="distance", model="linear")
    assert d.coded["PtType"].values[dist.rows[0]] == 1                       # 순수 성분에서 시작


def test_number_format():
    assert [_gfmt(v) for v in (10.22924, 2.738188573441e18, 47267840.0, 0.8, 1.0, 0.3205814, 123456789.0)] == \
        ["10.2292", "2.73819E+18", "47267840", "0.8", "1", "0.320581", "123456789"]
