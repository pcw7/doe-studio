"""반응표면 분석 검증.

정답 출처: Minitab 문서 예제 'Analyze Response Surface Design'(SealStrength.MWX, Strength, 완전 2차 모형)의
Coded Coefficients, Model Summary, Analysis of Variance, Regression Equation in Uncoded Units,
Fits and Diagnostics for Unusual Observations 를 글자 단위로 비교. 해석 문장: 가장 큰 효과는 HotBarT*DwelTime (AB).
교과서 검증: 잡음 없는 2차 함수 데이터에서 비코드화 회귀식이 원래 다항식을 그대로 복원.
"""
import numpy as np
import pytest

from doe_core.analysis.diagnostics import unusual_table
from doe_core.analysis.effects import effects
from doe_core.analysis.factorial import analyze_factorial, analyze_response_surface, analyze_worksheet
from doe_core.designs.common import Factor
from doe_core.designs.response_surface import create_box_behnken, create_ccd
from doe_core.io.worksheet import load_mwx_worksheet
from tests.helpers import SAMPLES, load_fixture, table

SEAL_FACTORS = ["HotBarT", "DwelTime", "HotBarP", "MatTemp"]


@pytest.fixture(scope="module")
def seal():
    p = SAMPLES / "SealStrength.MWX"
    if not p.exists():
        pytest.skip("SealStrength.MWX 없음")
    return load_mwx_worksheet(p, SEAL_FACTORS)


def rows(df):
    return df.astype(str).values.tolist()


def test_seal_strength_example_matches_minitab(seal):
    fx = load_fixture("response-surface__analyze-response-surface-design__example")
    d = seal.design
    assert d.kind == "ccd" and d.alpha == 2.0 and d.n_runs == 31
    assert [(f.low, f.high) for f in d.factors] == [(150, 200), (0.5, 1.0), (50, 150), (70, 110)]
    a = analyze_worksheet(seal, "Strength")
    for heading, mine in [("Coded Coefficients", a.coefficients_table()), ("Model Summary", a.summary_table()),
                          ("Analysis of Variance", a.anova_table()),
                          ("Fits and Diagnostics for Unusual Observations", unusual_table(a))]:
        want = table(fx, heading)
        assert list(mine.columns) == want["header"], heading
        assert rows(mine) == want["rows"], heading
    title, text = a.equation()
    eq = table(fx, "Regression Equation in Uncoded Units")
    assert title == "Regression Equation in Uncoded Units"
    assert text.replace(" ", "") == "".join(eq["header"]).replace(" ", "")


def test_seal_pareto_largest_is_ab(seal):
    a = analyze_worksheet(seal, "Strength")
    e = effects(a)
    assert e.standardized and e.pareto()["Term"].iloc[0] == "AB"
    assert set(e.table["Term"]) >= {"A", "AA", "AB", "CD"}


def test_quadratic_recovered_exactly_in_uncoded_units():
    f = [Factor("Temp", 60, 80), Factor("Time", 10, 30)]
    d = create_ccd(2, factors=f, randomize=False)
    T, t = d.runs["Temp"].values, d.runs["Time"].values
    y = 5 + 0.3 * T - 0.8 * t + 0.002 * T ** 2 + 0.01 * t ** 2 - 0.004 * T * t
    a = analyze_response_surface(d, y, response="Yield")
    labels, Tm = a._uncoded_transform()
    coef = dict(zip(labels, Tm @ a.beta))
    expect = {"": 5, "Temp": 0.3, "Time": -0.8, "Temp*Temp": 0.002, "Time*Time": 0.01, "Temp*Time": -0.004}
    for k, v in expect.items():
        assert abs(coef[k] - v) < 1e-9, k
    assert [t.name for t in a.terms] == ["Temp", "Time", "Temp*Temp", "Time*Time", "Temp*Time"]
    assert a.anova().set_index("source").index.tolist()[:8] == [
        "Model", "Linear", "Temp", "Time", "Square", "Temp*Temp", "Time*Time", "2-Way Interaction"]


def test_model_options_terms_and_blocks():
    d = create_ccd(3, blocks=2, seed=1)
    rng = np.random.default_rng(0)
    c = d.coded
    y = (10 + c.A - c.B + 0.5 * c.A ** 2 + 0.3 * c.A * c.C + np.where(c.Blocks == 1, 0.4, -0.4)).values + rng.normal(0, 0.05, d.n_runs)
    full = analyze_response_surface(d, y)
    assert [t.kind for t in full.terms][0] == "blocks" and full.anova().set_index("source").loc["Blocks", "df"] == 1
    lin = analyze_response_surface(d, y, model="linear")
    assert [t.word for t in lin.terms if t.kind == "factor"] == ["A", "B", "C"]
    sq = analyze_response_surface(d, y, model="linear+squares")
    assert [t.word for t in sq.terms if t.kind == "factor"] == ["A", "B", "C", "AA", "BB", "CC"]
    it = analyze_response_surface(d, y, model="linear+interactions")
    assert [t.word for t in it.terms if t.kind == "factor"] == ["A", "B", "C", "AB", "AC", "BC"]
    sel = analyze_response_surface(d, y, terms=["A", "B", "C", "AA", "A*C"])
    assert [t.word for t in sel.terms if t.kind == "factor"] == ["A", "B", "C", "AA", "AC"]
    assert analyze_factorial(d, y).terms == full.terms                      # 반응표면 설계는 자동으로 RS 분석
    with pytest.raises(ValueError):
        analyze_response_surface(d, y, model="cubic")


def test_box_behnken_analysis_and_lack_of_fit():
    d = create_box_behnken(3, seed=2)
    c = d.coded
    y = (20 + 2 * c.A + c.B - 1.5 * c.C ** 2 + 0.8 * c.A * c.B).values + np.random.default_rng(1).normal(0, 0.1, d.n_runs)
    a = analyze_response_surface(d, y)
    rows_ = a.anova().set_index("source")
    assert rows_.loc["Error", "df"] == 15 - 10
    assert rows_.loc["Pure Error", "df"] == 2 and rows_.loc["Lack-of-Fit", "df"] == 3
    assert "Effect" not in a.coefficients_table().columns
    with pytest.raises(ValueError):
        from doe_core.analysis.model import parse_term
        from doe_core.designs.factorial import create_two_level_design
        parse_term("AA", create_two_level_design(2, seed=0))          # 2수준 설계에는 제곱 항 없음
