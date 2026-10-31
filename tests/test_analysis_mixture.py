"""혼합물 분석 검증.

정답 출처(Minitab 문서 'Analyze Mixture Design' 예제): FondueRecipe.MWX, 반응 Flavor, 성분 Emmenthaler·Gruyere·Broth
+ 공정 변수 Temperature, 비율 단위, 항 A B C AB BC A*X1 B*X1 C*X1. 계수표·모형 요약·분산분석표를 글자 단위로 비교.
나머지는 statsmodels 상수항 없는 OLS 와 교차 검증하거나 정의대로 계산해 비교한다.
"""
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from doe_core.analysis.diagnostics import diagnostics, unusual_table
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.mixture import MixtureAnalysis, analyze_mixture, component_terms, mixture_terms, parse_term
from doe_core.designs.common import Factor
from doe_core.designs.mixture import Component, create_extreme_vertices, create_simplex_centroid, create_simplex_lattice
from doe_core.io.worksheet import Worksheet, define_custom_mixture, load_mwx_worksheet, load_worksheet, save_worksheet
from doe_core.plots.residual_plots import four_in_one
from tests.helpers import SAMPLES, load_fixture

FONDUE = SAMPLES / "FondueRecipe.MWX"
DOC_TERMS = ["Emmenthaler", "Gruyere", "Broth", "AB", "BC", "A*X1", "B*X1", "C*X1"]
needs_fondue = pytest.mark.skipif(not FONDUE.exists(), reason="FondueRecipe.MWX 없음(python research/fetch_samples.py)")


def by_header(fx, first: str, second: str):
    return next(t for t in fx["tables"] if t["header"][:2] == [first, second])


def fondue_ws():
    return load_mwx_worksheet(FONDUE, ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])


@needs_fondue
def test_example_fondue_flavor():
    fx = load_fixture("mixtures__analyze-mixture-design__example")
    a = analyze_worksheet(fondue_ws(), "Flavor", terms=DOC_TERMS)
    assert isinstance(a, MixtureAnalysis)
    assert a.coefficients_title() == "Estimated Regression Coefficients for Flavor (component proportions)"
    assert a.anova_title() == "Analysis of Variance for Flavor (component proportions)"
    assert a.coefficients_note() == "Coefficients are calculated for coded process variables."
    for got, (h1, h2) in [(a.coefficients_table(), ("Term", "Coef")), (a.summary_table(), ("S", "R-sq")),
                          (a.anova_table(), ("Source", "DF"))]:
        want = by_header(fx, h1, h2)
        assert list(got.columns) == want["header"]
        assert got.values.tolist() == want["rows"]


@needs_fondue
def test_fondue_matches_statsmodels_and_diagnostics():
    ws = fondue_ws()
    a = analyze_worksheet(ws, "Flavor", terms=DOC_TERMS)
    ols = sm.OLS(a.y, a.X).fit()
    np.testing.assert_allclose(a.beta, ols.params, rtol=1e-10)
    np.testing.assert_allclose(a.se_coef(), ols.bse, rtol=1e-8)
    np.testing.assert_allclose(diagnostics(a)["Cook's D"], ols.get_influence().cooks_distance[0], rtol=1e-7)
    assert a.removed_terms == [] and [t.short for t in a.terms] == ["A", "B", "C", "AB", "BC", "A*X1", "B*X1", "C*X1"]
    four_in_one(a)                                                          # 잔차 그림이 혼합물 분석에도 그려짐
    assert list(unusual_table(a).columns)[:2] == ["Obs", "Flavor"]
    # 같은 데이터, 성분 이름으로 지정한 항
    b = analyze_worksheet(ws, "Flavor", terms=["Emmenthaler*Gruyere", "Gruyere*Broth", "Emmenthaler*Temperature",
                                                "Gruyere*Temperature", "Broth*Temperature"])
    np.testing.assert_allclose(b.beta, a.beta)


@needs_fondue
def test_fondue_default_model_and_perfect_fit():
    a = analyze_worksheet(fondue_ws(), "Flavor")                              # 기본: 2차 × 공정 변수 1차
    assert [t.short for t in a.terms] == ["A", "B", "C", "AB", "AC", "BC", "A*X1", "B*X1", "C*X1",
                                          "AB*X1", "AC*X1", "BC*X1"]
    # 이 데이터는 이 모형으로 오차 없이 맞는다 → 검정 통계량은 '*', 음수 제곱합 잡음 없음
    tbl = a.anova_table()
    assert (tbl.loc[tbl["Source"] == "Regression", "F-Value"] == "*").all()
    assert not tbl["Adj SS"].str.startswith("-").any()
    assert unusual_table(a).empty
    assert a.summary_table()["R-sq"].iloc[0] == "100.00%"


def test_parse_terms():
    d = create_simplex_centroid(3, components=[Component("Neroli"), Component("Rose"), Component("Tangerine")],
                                process=[Factor("Temp", 10, 20), Factor("Time", 1, 2)], randomize=False)
    shorts = {s: parse_term(s, d).short for s in
              ["A", "AB", "A*B", "ABC", "AABC", "ABBC", "AB(A-B)", "AB(A-B)2", "1/A", "A*X1", "AB*X1*X2",
               "Neroli*Rose", "Neroli*Rose*(-)", "Neroli*Rose*(-)^2", "Rose*Temp", "Neroli*Rose*Temp*Time",
               "A*A*B*C", "BA", "AB(B-A)"]}
    assert shorts["A*B"] == shorts["Neroli*Rose"] == shorts["BA"] == "AB"
    assert shorts["Neroli*Rose*(-)"] == shorts["AB(B-A)"] == "AB(A-B)"
    assert shorts["Neroli*Rose*(-)^2"] == "AB(A-B)2" and shorts["A*A*B*C"] == "AABC"
    assert shorts["Rose*Temp"] == "B*X1" and shorts["Neroli*Rose*Temp*Time"] == "AB*X1*X2"
    assert parse_term("AB(A-B)", d).name == "Neroli*Rose*(-)" and parse_term("1/C", d).name == "1/Tangerine"
    assert parse_term("AABC", d).name == "Neroli*Neroli*Rose*Tangerine"
    for bad in ["AA", "AAB", "X1", "Z", "AB(A-C)", "ABCD", "AAAB", "A*X1*X1"]:
        with pytest.raises(ValueError):
            parse_term(bad, d)


def test_model_term_counts():
    d3 = create_simplex_lattice(3, 4, randomize=False)
    counts = {m: len(component_terms(d3, m)) for m in
              ["linear", "quadratic", "special cubic", "full cubic", "special quartic", "full quartic"]}
    assert counts == {"linear": 3, "quadratic": 6, "special cubic": 7, "full cubic": 10, "special quartic": 9,
                      "full quartic": 15}                                    # 문서 'Model terms' 표(3성분)
    assert [t.short for t in component_terms(d3, "full quartic")][6:] == \
        ["AB(A-B)", "AC(A-C)", "BC(B-C)", "AABC", "ABBC", "ABCC", "AB(A-B)2", "AC(A-C)2", "BC(B-C)2"]
    d4 = create_simplex_lattice(4, 4, randomize=False)
    assert len(component_terms(d4, "special quartic")) == 4 + 6 + 12 + 1      # + ABCD
    # 격자 차수 4 설계(3성분 15점 + 중앙·축점)는 완전 4차 모형을 추정할 수 있다
    rng = np.random.default_rng(0)
    y = rng.normal(size=d3.n_runs)
    a = analyze_mixture(d3, y, model="full quartic")
    assert a.removed_terms == [] and a.p == 15
    ols = sm.OLS(a.y, a.X).fit()
    np.testing.assert_allclose(a.beta, ols.params, rtol=1e-8, atol=1e-8)
    # 공정 변수 차수 2: 성분 항 × (X1, X2, X1X2)
    dp = create_simplex_centroid(3, process=[Factor("T", 0, 1), Factor("P", 0, 1)], randomize=False)
    tl = mixture_terms(dp, model="linear", process_order=2)
    assert [t.short for t in tl] == ["A", "B", "C", "A*X1", "B*X1", "C*X1", "A*X2", "B*X2", "C*X2",
                                     "A*X1*X2", "B*X1*X2", "C*X1*X2"]
    assert [t.short for t in mixture_terms(dp, model="linear", process_order=0)] == ["A", "B", "C"]


def test_lack_of_fit_with_replicates():
    d = create_simplex_lattice(3, 2, replicates=2, randomize=False)              # 6점 × 2 + 중앙 2 + 축점 6
    rng = np.random.default_rng(1)
    P = d.coded[d.letters].values
    y = 10 * P[:, 0] + 20 * P[:, 1] + 5 * P[:, 2] + 30 * P[:, 0] * P[:, 1] + 40 * P[:, 0] * P[:, 1] * P[:, 2]
    y = y + rng.normal(scale=0.5, size=len(y))
    a = analyze_mixture(d, y, model="quadratic")
    rows = {r.source: r for r in a.anova_rows()}
    key = d.coded[d.letters].round(9).astype(str).agg("|".join, axis=1)
    pe = sum(((g - g.mean()) ** 2).sum() for _, g in pd.Series(y).groupby(key.values))
    assert rows["Pure Error"].df == len(y) - key.nunique()
    np.testing.assert_allclose(rows["Pure Error"].adj_ss, pe)
    np.testing.assert_allclose(rows["Lack-of-Fit"].adj_ss + rows["Pure Error"].adj_ss, a.sse)
    assert "Component Only" not in rows                                          # 공정 변수 없으면 제목 행 없음
    # 선형 그룹: DF q−1, Seq SS = 선형만의 회귀 SS, 그룹 합 = 회귀
    assert rows["Linear"].df == 2
    sse_lin = sm.OLS(y, P).fit().ssr
    np.testing.assert_allclose(rows["Linear"].seq_ss, a.sst - sse_lin)
    np.testing.assert_allclose(rows["Linear"].seq_ss + rows["Quadratic"].seq_ss, rows["Regression"].seq_ss)
    lin_mask = np.isin(a.anova()["source"], ["Linear", "Quadratic"])
    assert a.anova()[lin_mask]["df"].sum() == rows["Regression"].df


def test_units_pseudocomponents_and_amounts():
    comps = [Component("A", 0.2, 0.6), Component("B", 0.1, 0.5), Component("C", 0.1, 0.5)]
    d = create_extreme_vertices(3, components=comps, degree=2, randomize=False)
    rng = np.random.default_rng(2)
    P = d.coded[d.letters].values
    y = 3 * P[:, 0] + 7 * P[:, 1] + 2 * P[:, 2] + 9 * P[:, 0] * P[:, 2] + rng.normal(scale=0.1, size=d.n_runs)
    a = analyze_mixture(d, y, model="quadratic", units="proportions")
    b = analyze_mixture(d, y, model="quadratic", units="pseudocomponents")
    np.testing.assert_allclose(a.fitted, b.fitted, atol=1e-9)                   # 같은 모형 공간
    assert b.coefficients_title().endswith("(pseudo components)")
    Z = (P - [0.2, 0.1, 0.1]) / 0.6
    np.testing.assert_allclose(b.X[:, :3], Z)
    assert a.summary_table().equals(b.summary_table())
    # 총량 2 인 설계를 양 단위로 분석하면 선형 계수는 비율 계수 / 총량
    d2 = create_simplex_centroid(3, total=2.0, randomize=False)
    y2 = d2.coded[d2.letters].values @ [4.0, 6.0, 8.0] + rng.normal(scale=0.1, size=d2.n_runs)
    pa = analyze_mixture(d2, y2, model="linear", units="proportions")
    am = analyze_mixture(d2, y2, model="linear", units="amounts")
    np.testing.assert_allclose(am.beta, pa.beta / 2)
    assert am.coefficients_title().endswith("(component amounts)")


def test_inverse_terms():
    comps = [Component("A", 0.1, 0.8), Component("B", 0.1, 0.8), Component("C", 0.1, 0.8)]
    d = create_simplex_lattice(3, 3, components=comps, randomize=False)
    P = d.coded[d.letters].values
    y = 5 * P[:, 0] + 3 * P[:, 1] + 4 * P[:, 2] + 0.2 / P[:, 0] + np.random.default_rng(3).normal(scale=0.05, size=d.n_runs)
    a = analyze_mixture(d, y, model="linear", inverse=True)
    assert [t.short for t in a.terms] == ["A", "B", "C", "1/A", "1/B", "1/C"]
    assert [r.source for r in a.anova_rows()][1:3] == ["Linear", "Inverse"]
    np.testing.assert_allclose(a.beta, sm.OLS(a.y, a.X).fit().params, rtol=1e-8)
    with pytest.raises(ValueError):
        analyze_mixture(d, y, model="linear", inverse=True, units="pseudocomponents")
    with pytest.raises(ValueError):
        analyze_mixture(create_simplex_lattice(3, 3, randomize=False), y, model="linear", inverse=True)


def test_custom_mixture_blocks_and_save(tmp_path):
    d = create_simplex_lattice(3, 2, components=[Component("A", 0.1), Component("B"), Component("C")], replicates=2,
                               randomize=False)
    runs = d.runs.drop(columns=["PtType"]).copy()
    runs["Blocks"] = np.where(np.arange(d.n_runs) < d.n_runs // 2, 1, 2)
    runs["Amount A"], runs["Amount B"], runs["Amount C"] = runs["A"] * 50, runs["B"] * 50, runs["C"] * 50
    rng = np.random.default_rng(4)
    runs["Y"] = runs["A"] * 10 + runs["B"] * 12 + runs["C"] * 8 + (runs["Blocks"] == 2) * 1.5 + rng.normal(scale=0.2, size=len(runs))
    ws = define_custom_mixture(runs.drop(columns=["A", "B", "C"]), ["Amount A", "Amount B", "Amount C"],
                               lower={"Amount A": 5})
    dd = ws.design
    assert dd.kind == "custom" and dd.total == pytest.approx(50) and dd.components[0].lower == pytest.approx(0.1)
    assert set(dd.coded["PtType"]) == {1, 2, 0}                               # 점 유형 열이 없으면 만든다
    a = analyze_worksheet(ws, "Y", model="linear")
    assert a.terms[0].kind == "blocks" and a.col_labels[0] == "Blocks 1"
    srcs = [r.source for r in a.anova_rows()]
    assert srcs[:3] == ["Regression", "Blocks", "Linear"]
    np.testing.assert_allclose(a.beta, sm.OLS(a.y, a.X).fit().params, rtol=1e-8)
    assert "Design degree" not in dd.summary_text()
    back = load_worksheet(save_worksheet(ws, tmp_path / "mix.json"))
    b = analyze_worksheet(back, "Y", model="linear")
    assert b.anova_table().equals(a.anova_table())
    with pytest.raises(ValueError):
        define_custom_mixture(pd.DataFrame({"A": [0.5, 0.6], "B": [0.5, 0.5]}), ["A", "B"])
    with pytest.raises(ValueError):
        define_custom_mixture(pd.DataFrame({"A": [0.5, 0.6, 0.2], "B": [0.5, 0.4, 0.8], "T": [1, 2, 3]}),
                              ["A", "B"], process=["T"])


def test_analysis_errors():
    d = create_simplex_centroid(3, randomize=False)
    with pytest.raises(ValueError):
        analyze_mixture(d, np.ones(3))
    with pytest.raises(ValueError):
        analyze_mixture(d, np.arange(d.n_runs, dtype=float), model="cubic")
    with pytest.raises(ValueError):
        analyze_mixture(d, np.arange(d.n_runs, dtype=float), units="percent")
    y = np.arange(d.n_runs, dtype=float)
    y[0] = np.nan
    a = analyze_mixture(d, y, model="special cubic")                            # 결측 반응 행은 뺀다
    assert a.n == d.n_runs - 1 and a.p == 7
