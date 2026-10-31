"""확정적 선별설계(DSD) 생성·분석 검증.

정답 출처(Minitab 문서)
- 'Create Screening Design' 예제: 8요인 2반복 → 설계 요약표와 설계표(행 집합) 글자 단위 비교.
- 'Available definitive screening designs' 표: 요인 수별 런 수.
- 'Analyze Screening Design' 예제: ultrasonic_cleaner.MWX(7요인 17런), 반응 Power, 선형 모형 →
  계수표·모형 요약·분산분석표·회귀식·별칭 구조(up to order 2) 비교. 이 표본의 표준 순서로 생성 순서도 확인.
"""
import re
from collections import Counter
from itertools import combinations

import numpy as np
import pytest

from doe_core.analysis.alias import alias_lines, alias_title, factor_name_table
from doe_core.analysis.effects import effects
from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet
from doe_core.designs.common import Factor
from doe_core.designs.definitive_screening import (
    DSD_ORDERS, base_runs_for, conference_matrix, conference_order, create_definitive_screening,
)
from doe_core.designs.modify import randomize_design, replicate_design
from doe_core.designs.response_surface import create_box_behnken
from doe_core.io.worksheet import Worksheet, define_custom_dsd, load_mwx_worksheet, load_worksheet, save_worksheet
from tests.helpers import SAMPLES, load_fixture

CLEANER = SAMPLES / "ultrasonic_cleaner.MWX"
CLEANER_FACTORS = ["Train", "Degas", "Burst", "Quiet", "Center", "Bandwidth", "Sweep"]
needs_cleaner = pytest.mark.skipif(not CLEANER.exists(), reason="ultrasonic_cleaner.MWX 없음")


def by_header(fx, first: str, second: str | None = None):
    return next(t for t in fx["tables"] if t["header"][0] == first and (second is None or t["header"][1] == second))


def test_conference_matrices():
    for n in DSD_ORDERS:
        C = conference_matrix(n)
        assert np.array_equal(C.T @ C, (n - 1) * np.eye(n, dtype=int)), n
        assert np.all(np.diag(C) == 0) and np.all(np.abs(C[~np.eye(n, dtype=bool)]) == 1)
        assert np.all(C[0, 1:] == 1) and np.all(C[1:, 0] == 1)


def test_available_designs_table():
    fx = load_fixture("topic__factorial-and-screening-designs__available-definitive-screening-designs")
    for rng, runs in fx["tables"][0]["rows"]:
        lo, hi = map(int, rng.split("–"))
        for m in range(lo, hi + 1):
            assert base_runs_for(m) == int(runs), m
            assert base_runs_for(m, n_text=1) == int(runs) + 1                # 범주형 요인이 있으면 반복당 1런 추가
    with pytest.raises(ValueError):
        conference_order(49)
    with pytest.raises(ValueError):
        create_definitive_screening(1)


def test_example_8_factors_2_replicates():
    fx = load_fixture("screening__create-definitive-screening-design__example")
    d = create_definitive_screening(8, replicates=2, seed=11)
    summ = by_header(fx, "Factors:")
    assert d.summary_table().values.tolist() == [summ["header"], *summ["rows"]]
    dt = by_header(fx, "Run", "Blk")
    assert list(d.design_table().columns) == dt["header"]
    got = Counter(tuple(map(str, r[1:])) for r in d.design_table().values.tolist())
    assert got == Counter(tuple(r[1:]) for r in dt["rows"])
    assert sorted(d.design_table()["Run"]) == list(range(1, 35))
    assert d.total_center_points == 2 and set(d.coded["PtType"]) == {0, 2}


@needs_cleaner
def test_standard_order_matches_sample_7_factors():
    ws = load_mwx_worksheet(CLEANER, CLEANER_FACTORS)
    mine = create_definitive_screening(7, randomize=False)
    a = ws.design.coded.sort_values("StdOrder")
    b = mine.coded.sort_values("StdOrder")
    assert a[["StdOrder", "PtType", *a.columns[4:]]].values.tolist() == b[["StdOrder", "PtType", *b.columns[4:]]].values.tolist()
    assert ws.design.order == 8 and ws.design.base_runs == 17


def test_dsd_properties():
    for m in (4, 6, 7, 10, 13):
        d = create_definitive_screening(m, randomize=False)
        X = d.coded[d.letters].values.astype(float)
        assert len(X) == base_runs_for(m)
        assert np.allclose(X.T @ X, np.diag(np.diag(X.T @ X)))             # 주효과끼리 직교
        sq = X ** 2
        tw = np.column_stack([X[:, i] * X[:, j] for i, j in combinations(range(m), 2)])
        assert np.allclose(X.T @ sq, 0) and np.allclose(X.T @ tw, 0)       # 주효과 ⟂ 제곱·2요인 교호작용
        M = np.column_stack([np.ones(len(X)), X, sq])
        assert np.linalg.matrix_rank(M) == 1 + 2 * m                       # 상수 + 주효과 + 제곱 추정 가능
        pt = d.coded["PtType"].values
        assert set(pt[(X == 0).all(axis=1)]) == {0}
        assert np.all((pt == 2) == ((X == 0).any(axis=1) & ~(X == 0).all(axis=1)))


def test_text_factors_and_blocks():
    facs = [Factor("A", 1, 2), Factor("B", 1, 2), Factor("Cat", "x", "y", False), Factor("D", 0, 10),
            Factor("Supplier", "S1", "S2", False), Factor("F", 5, 6)]
    d = create_definitive_screening(6, factors=facs, replicates=4, n_blocks=2, seed=3)
    assert d.base_runs == 14 and d.n_runs == 56 and d.total_center_points == 8
    X = d.coded[d.letters].values.astype(float)
    assert not (X[:, [2, 4]] == 0).any()                                     # 텍스트 요인은 2수준만
    assert np.allclose(X.sum(axis=0), 0)
    rows = Counter(map(tuple, X.astype(int)))
    assert all(rows[tuple(-v for v in r)] == n for r, n in rows.items())    # 중앙점 2개까지 접힘 쌍 → 주효과 ⟂ 2차 항
    tw = np.column_stack([X[:, i] * X[:, j] for i, j in combinations(range(6), 2)] + [X ** 2])
    assert np.allclose(X.T @ tw, 0)
    num = [0, 1, 3, 5]
    assert np.allclose(X[:, num].T @ X[:, num], np.diag(np.diag(X[:, num].T @ X[:, num])))
    corr = np.corrcoef(X, rowvar=False)
    assert np.abs(corr[~np.eye(6, dtype=bool)]).max() < 0.2                  # 텍스트 요인 관련 상관은 작다
    assert set(d.runs["Cat"]) == {"x", "y"}
    assert d.coded.groupby("Blocks").size().tolist() == [28, 28]
    with pytest.raises(ValueError):
        create_definitive_screening(6, replicates=4, n_blocks=3)
    # 텍스트 요인 제곱은 모형에 넣지 않는다
    y = np.random.default_rng(0).normal(size=d.n_runs)
    a = analyze_factorial(d, y, model="linear+squares")
    assert [t.word for t in a.terms if t.is_square] == ["AA", "BB", "DD", "FF"]


def test_save_load_and_modify(tmp_path):
    d = create_definitive_screening(5, seed=4)
    ws = Worksheet(d)
    ws.add_column("Y", np.arange(d.n_runs, dtype=float))
    back = load_worksheet(save_worksheet(ws, tmp_path / "dsd.json"))
    assert back.design.summary() == d.summary() and back.design.coded.equals(d.coded)
    r = replicate_design(d)
    assert r.replicates == 2 and r.n_runs == 26 and r.total_center_points == 2
    assert randomize_design(d, seed=5).n_runs == 13
    # 확정적 선별설계가 아닌 데이터(3요인 Box-Behnken)는 DSD 로 정의하지 않는다
    bbd = create_box_behnken(3, randomize=False)
    with pytest.raises(ValueError):
        define_custom_dsd(bbd.runs, [f.name for f in bbd.factors])


@needs_cleaner
def test_example_analyze_screening_design_power():
    fx = load_fixture("screening__analyze-screening-design__example")
    ws = load_mwx_worksheet(CLEANER, CLEANER_FACTORS)
    a = analyze_worksheet(ws, "Power")                                       # DSD 기본 모형 = 선형
    for got, (h1, h2) in [(a.coefficients_table(), ("Term", "Coef")), (a.summary_table(), ("S", "R-sq")),
                          (a.anova_table(), ("Source", "DF"))]:
        want = by_header(fx, h1, h2)
        assert list(got.columns) == want["header"]
        assert got.values.tolist() == want["rows"]
    title, eq = a.equation()
    want_eq = " ".join(by_header(fx, "Power", "=")["header"])
    assert title == "Regression Equation in Uncoded Units"
    norm = lambda s: re.sub(r"\s+", " ", s.replace("+", " + ").replace(" - ", " - ")).strip()  # noqa: E731
    assert norm(eq) == norm(want_eq)                                          # 문서 원문은 'Center+ 0.70' 처럼 공백 누락
    assert alias_title(a) == "Alias Structure (up to order 2)"
    assert alias_lines(a) == [r[0] for r in by_header(fx, "Aliases")["rows"]]
    fn = by_header(fx, "Factor", "Name")
    assert factor_name_table(a).values.tolist() == fn["rows"]
    e = effects(a)                                                            # 문서: 가장 큰 주효과는 Train(A)·Quiet(D)
    assert e.standardized and e.table.loc[e.table["Significant"], "Name"].tolist() == ["Train", "Quiet"]
    # 제곱 항을 넣은 모형: Effect 열 없음, 곡면성 행 없음
    b = analyze_worksheet(ws, "Power", terms=["Train", "Quiet", "Quiet*Quiet", "Sweep*Sweep"])
    assert "Effect" not in b.coefficients_table().columns
    assert [r.source for r in b.anova_rows()][:4] == ["Model", "Linear", "Train", "Quiet"]
    assert "Curvature" not in [r.source for r in b.anova_rows()]
    lines = alias_lines(b)
    assert [ln.split()[0] for ln in lines] == ["I", "A", "D", "DD", "GG"]   # 모형에 넣은 제곱 항은 별칭 쪽에서 빠짐
    assert " DD" not in lines[0] and " GG" not in lines[0] and " AA" in lines[0]
