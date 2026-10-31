"""요인설계 분석(적합·계수표·모형 요약·분산분석·회귀식) 검증.

정답 출처
- Minitab 문서 예제 "Analyze Factorial Design"(InsulationProperties.MWX, Strength, 2차 항 + 공변량 MeasTemp):
  Coded Coefficients, Model Summary, Analysis of Variance, Regression Equation in Uncoded Units 를 글자 단위로 비교.
- 같은 데이터의 공변량 없는 모형 2개(ANOVA 해석 페이지).
- 곡면성 제곱합 SS = nF·nC·(ȳF − ȳC)² / (nF + nC), 순수 오차 DF = c − 1 (Montgomery).
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from conftest import load_fixture, table
from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.general_full import GeneralFactor, create_general_full_factorial
from doe_core.io.worksheet import load_mwx_worksheet

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "minitab_samples"
INSULATION_FACTORS = ["Material", "InjPress", "InjTemp", "CoolTemp"]


@pytest.fixture(scope="module")
def insulation():
    p = SAMPLES / "InsulationProperties.MWX"
    if not p.exists():
        pytest.skip("InsulationProperties.MWX 없음 — python research/fetch_samples.py")
    return load_mwx_worksheet(p, INSULATION_FACTORS)


def as_rows(df: pd.DataFrame) -> list[list[str]]:
    return df.astype(str).values.tolist()


def test_insulation_example_matches_minitab_output(insulation):
    fx = load_fixture("factorial__analyze-factorial-design__example")
    a = analyze_worksheet(insulation, "Strength", covariates=["MeasTemp"], order=2)

    coef = table(fx, "Coded Coefficients")
    mine = a.coefficients_table()
    assert list(mine.columns) == coef["header"]
    assert as_rows(mine) == coef["rows"]

    summ = table(fx, "Model Summary")
    assert list(a.summary_table().columns) == summ["header"]
    assert as_rows(a.summary_table()) == summ["rows"]

    anova = table(fx, "Analysis of Variance")
    assert list(a.anova_table().columns) == anova["header"]
    assert as_rows(a.anova_table()) == anova["rows"]

    eq = table(fx, "Regression Equation in Uncoded Units")
    title, text = a.equation()
    assert title == "Regression Equation in Uncoded Units"
    want = "".join(eq["header"]).replace(" ", "")
    assert text.replace(" ", "") == want


def test_insulation_models_without_covariate(insulation):
    fx = load_fixture("factorial__analyze-factorial-design__asg__analysis-of-variance-table")
    full, reduced = [t for t in fx["tables"] if t["heading"].startswith("Analysis of Variance")]
    a = analyze_worksheet(insulation, "Strength", order=2)
    assert as_rows(a.anova_table()) == full["rows"]
    # 축소 모형: 문서 표는 SS 를 소수 2자리로 표시(다른 판의 출력으로 보임) → 숫자로 비교
    b = analyze_worksheet(insulation, "Strength", terms=["A", "B", "C", "D", "CD"])
    got = b.anova()
    for row in reduced["rows"]:
        r = got[got["source"] == row[0]].iloc[0]
        assert int(row[1]) == r["df"]
        assert abs(float(row[2]) - r["adj_ss"]) < 0.006
        if row[4]:
            assert abs(float(row[4]) - r["f"]) < 0.006 and abs(float(row[5]) - r["p"]) < 0.0006


def test_curvature_lack_of_fit_and_pure_error():
    d = create_two_level_design(3, center_points=4, randomize=False)
    c = d.coded
    rng = np.random.default_rng(0)
    y = 10 + 2 * c.A - 1.5 * c.B + 0.7 * c.A * c.B + 0.4 * c.A * c.B * c.C + 3 * (c.CenterPt == 0) + rng.normal(0, 0.3, len(c))
    y = y.values
    yF, yC = y[c.CenterPt == 1], y[c.CenterPt == 0]
    ss_curv = len(yF) * len(yC) * (yF.mean() - yC.mean()) ** 2 / (len(yF) + len(yC))

    # 중앙점 항이 모형에 없으면 Error 아래에 Curvature / Lack-of-Fit / Pure Error
    a = analyze_factorial(d, y, order=2, include_center=False).anova()
    err = a.set_index("source")
    assert err.loc["Curvature", "df"] == 1 and abs(err.loc["Curvature", "adj_ss"] - ss_curv) < 1e-9
    assert err.loc["Pure Error", "df"] == 3 and abs(err.loc["Pure Error", "adj_ss"] - ((yC - yC.mean()) ** 2).sum()) < 1e-9
    assert err.loc["Lack-of-Fit", "df"] == 1                       # ABC 항
    assert abs(err.loc["Error", "adj_ss"] - (err.loc["Curvature", "adj_ss"] + err.loc["Lack-of-Fit", "adj_ss"]
                                             + err.loc["Pure Error", "adj_ss"])) < 1e-9
    # 중앙점 항을 넣으면 Model 아래 Curvature, 계수 Ct Pt = ȳC − ȳF
    m = analyze_factorial(d, y, order=2)
    rows = m.anova().set_index("source")
    assert rows.loc["Curvature", "level"] == 1 and abs(rows.loc["Curvature", "adj_ss"] - ss_curv) < 1e-9
    coefs = m.coefficients().set_index("Term")
    assert abs(coefs.loc["Ct Pt", "Coef"] - (yC.mean() - yF.mean())) < 1e-9
    assert np.isnan(coefs.loc["Ct Pt", "Effect"]) and "Ct Pt" in m.equation()[1]


def test_aliased_terms_are_removed_later_first():
    d = create_two_level_design(4, 8, seed=1)                       # D = ABC: AB=CD, AC=BD, AD=BC
    y = np.arange(8, dtype=float)
    a = analyze_factorial(d, y, order=2)
    assert [t.name for t in a.removed_terms] == ["B*C", "B*D", "C*D"]
    assert [t.name for t in a.terms] == ["A", "B", "C", "D", "A*B", "A*C", "A*D"]
    assert a.df_error == 0
    tbl = a.coefficients_table()
    assert (tbl["T-Value"] == "*").all() and (tbl["P-Value"] == "*").all()
    assert a.summary_table().iloc[0]["S"] == "*"
    anova = a.anova_table()
    assert anova.set_index("Source").loc["Model", "F-Value"] == "*"


def test_blocks_effect_coding():
    d = create_two_level_design(3, 8, n_blocks=2, seed=2)            # 블록 생성자 ABC
    c = d.coded
    y = (5 + c.A + 2 * c.B + np.where(c.Blocks == 1, 1.5, -1.5)).astype(float).values
    a = analyze_factorial(d, y, order=2)
    co = a.coefficients().set_index("Term")
    assert abs(co.loc["Blocks 1", "Coef"] - (y[c.Blocks == 1].mean() - y.mean())) < 1e-9
    rows = a.anova().set_index("source")
    assert rows.loc["Blocks", "df"] == 1 and "Blocks" not in a.equation()[1]
    assert [t.kind for t in a.terms][0] == "blocks"


def test_general_full_factorial_effect_coding_against_cell_means():
    d = create_general_full_factorial([GeneralFactor("Solvent", ["MeOH", "EtOH", "IPA"]),
                                       GeneralFactor("Temp", [40, 60])], replicates=2, seed=3)
    c = d.coded
    rng = np.random.default_rng(1)
    base = {1: 10.0, 2: 12.0, 3: 15.0}
    y = np.array([base[a] + (1.0 if b == 2 else 0.0) for a, b in zip(c.A, c.B)]) + rng.normal(0, 0.2, len(c))
    a = analyze_factorial(d, y, order=2)
    tbl = a.coefficients_table()
    assert "Effect" not in tbl.columns
    assert list(tbl["Term"]) == ["Constant", "Solvent MeOH", "Solvent EtOH", "Temp 40", "Solvent*Temp MeOH 40",
                                 "Solvent*Temp EtOH 40"]
    co = a.coefficients().set_index("Term")
    grand = y.mean()
    assert abs(co.loc["Constant", "Coef"] - grand) < 1e-9
    assert abs(co.loc["Solvent MeOH", "Coef"] - (y[c.A == 1].mean() - grand)) < 1e-9
    rows = a.anova().set_index("source")
    assert rows.loc["Solvent", "df"] == 2 and rows.loc["Solvent*Temp", "df"] == 2
    # 완전 모형은 모든 셀 평균을 맞추므로 적합성 결여가 없고 오차 = 순수 오차(분할 행 없음)
    assert rows.loc["Error", "df"] == 6 and "Pure Error" not in rows.index
    assert a.equation() is None


def test_missing_responses_are_dropped():
    d = create_two_level_design(3, center_points=2, seed=4)
    y = np.linspace(1, 3, d.n_runs)
    y[[0, 5]] = np.nan
    a = analyze_factorial(d, y, order=1)
    assert a.n == d.n_runs - 2
    assert a.anova().set_index("source").loc["Total", "df"] == d.n_runs - 3
