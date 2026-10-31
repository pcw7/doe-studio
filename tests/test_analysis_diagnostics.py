"""분석 진단·효과도·별칭·평균 검증.

정답 출처
- Minitab 문서 예제: InsulationProperties 의 부분 별칭 구조(공변량 MeasTemp), 별칭 해석 페이지의 부분요인·블록 설계 예,
  축소 모형(InjTemp*CoolTemp)의 Means 표, 효과 크기 순서(B 최대, BD 최소).
- 진단 측도는 statsmodels 의 영향력 측도와 대조. Lenth PSE 는 정의대로 손계산.
"""
import numpy as np
import pytest
from scipy import stats
from statsmodels.stats.outliers_influence import OLSInfluence
from statsmodels.regression.linear_model import OLS

from doe_core.analysis.alias import alias_lines, factor_name_table, has_aliasing
from doe_core.analysis.diagnostics import diagnostics, unusual_table
from doe_core.analysis.effects import effects, lenth_pse
from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet
from doe_core.analysis.means import means_table
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import load_mwx_worksheet
from tests.helpers import SAMPLES, load_fixture, table

FACTORS = ["Material", "InjPress", "InjTemp", "CoolTemp"]


@pytest.fixture(scope="module")
def insulation():
    p = SAMPLES / "InsulationProperties.MWX"
    if not p.exists():
        pytest.skip("InsulationProperties.MWX 없음")
    return load_mwx_worksheet(p, FACTORS)


def test_insulation_partial_alias_structure(insulation):
    fx = load_fixture("factorial__analyze-factorial-design__example")
    a = analyze_worksheet(insulation, "Strength", covariates=["MeasTemp"], order=2)
    names = [t for t in fx["tables"] if t["heading"] == "Alias Structure" and t["header"] == ["Factor", "Name"]][0]
    aliases = [t for t in fx["tables"] if t["heading"] == "Alias Structure" and t["header"] == ["Aliases"]][0]
    assert factor_name_table(a).values.tolist() == names["rows"]
    assert alias_lines(a) == [r[0] for r in aliases["rows"]]
    assert has_aliasing(a)


def test_alias_doc_examples_fraction_and_blocks():
    f = [Factor("Surgeon"), Factor("VAS"), Factor("Ibuprofen")]
    d = create_two_level_design(3, 4, factors=f, seed=0)                     # C = AB
    a = analyze_factorial(d, np.arange(4.0), order=1)
    assert alias_lines(a) == ["I + ABC", "A + BC", "B + AC", "C + AB"]
    # 반복 2 × 반복당 2블록(ABC) = 4블록: 블록이 ABC 와 별칭
    d2 = create_two_level_design(3, 8, factors=f, replicates=2, n_blocks=4, seed=1)
    y = np.random.default_rng(0).normal(size=d2.n_runs)
    a2 = analyze_factorial(d2, y, order=1)
    assert alias_lines(a2) == ["I", "Block 1 - ABC", "Block 2 + ABC", "Block 3 - ABC", "A", "B", "C"]


def test_full_factorial_without_covariate_has_no_aliasing(insulation):
    a = analyze_worksheet(insulation, "Strength", order=2)
    assert not has_aliasing(a)
    assert alias_lines(a)[:3] == ["I", "A", "B"]


def test_means_table_matches_doc(insulation):
    fx = load_fixture("factorial__analyze-factorial-design__asg__means-table")
    a = analyze_worksheet(insulation, "Strength", terms=["A", "B", "C", "D", "CD"])
    want = table(fx, "Means")
    got = means_table(a)
    assert list(got.columns) == want["header"]
    assert got.values.tolist() == want["rows"]


def test_effects_standardized_and_pareto_order(insulation):
    a = analyze_worksheet(insulation, "Strength", covariates=["MeasTemp"], order=2)
    e = effects(a)
    assert e.standardized and e.pareto_title == "Pareto Chart of the Standardized Effects"
    assert abs(e.reference - stats.t.ppf(0.975, 4)) < 1e-12
    par = e.pareto()
    assert par["Term"].iloc[0] == "B" and par["Term"].iloc[-1] == "BD"       # 문서: B 최대, BD 최소
    assert set(e.table[e.table["Significant"]]["Term"]) == {"A", "B", "C", "D"}
    assert "MeasTemp" not in set(e.table["Name"])
    # 정규 점수는 효과 크기 순서와 같은 순서
    t = e.table.sort_values("Standardized")
    assert t["Normal Score"].is_monotonic_increasing


def test_lenth_pse_and_unstandardized_effects():
    assert abs(lenth_pse([-0.5, 0.2, 0.3, 4, -6, 0.1, 0.4]) - 0.45) < 1e-12
    d = create_two_level_design(3, randomize=False)
    c = d.coded
    y = (20 + 4 * c.A - 3 * c.B + 0.2 * c.C + 0.1 * c.A * c.B - 0.15 * c.A * c.C + 0.05 * c.B * c.C + 0.12 * c.A * c.B * c.C).values
    a = analyze_factorial(d, y, order=3)
    assert a.df_error == 0
    e = effects(a)
    assert not e.standardized and e.pareto_title == "Pareto Chart of the Effects"
    eff = e.table.set_index("Term")["Effect"]
    assert abs(eff["A"] - 8) < 1e-9 and abs(eff["B"] + 6) < 1e-9
    pse = lenth_pse(eff.values)
    assert abs(e.pse - pse) < 1e-12 and abs(e.reference - stats.t.ppf(0.975, 7 / 3) * pse) < 1e-12
    assert set(e.table[e.table["Significant"]]["Term"]) == {"A", "B"}


def test_diagnostics_match_statsmodels(insulation):
    a = analyze_worksheet(insulation, "Strength", covariates=["MeasTemp"], order=2)
    infl = OLSInfluence(OLS(a.y, a.X).fit())
    d = diagnostics(a)
    np.testing.assert_allclose(d["HI"], infl.hat_matrix_diag, rtol=1e-9)
    np.testing.assert_allclose(d["Std Resid"], infl.resid_studentized_internal, rtol=1e-9)
    np.testing.assert_allclose(d["Del Resid"], infl.resid_studentized_external, rtol=1e-9)
    np.testing.assert_allclose(d["Cook's D"], infl.cooks_distance[0], rtol=1e-9)
    np.testing.assert_allclose(d["DFITS"], infl.dffits[0], rtol=1e-9)
    assert d["Obs"].tolist() == list(range(1, 17))
    # 문서 예제에는 이상 관측치 표가 없다
    assert unusual_table(a).empty


def test_unusual_observation_flags():
    d = create_two_level_design(3, center_points=3, randomize=False)
    c = d.coded
    y = (10 + c.A + c.B).astype(float).values + np.random.default_rng(3).normal(0, 0.1, d.n_runs)
    y[2] += 3.0                                                                   # 큰 잔차
    a = analyze_factorial(d, y, order=1)
    tbl = unusual_table(a)
    assert "3" in tbl["Obs"].tolist() and tbl.set_index("Obs").loc["3", ""].startswith("R")
    assert list(tbl.columns) == ["Obs", "Y", "Fit", "Resid", "Std Resid", ""]
