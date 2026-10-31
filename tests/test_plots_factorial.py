"""그래프 데이터·구성 검증(그림 자체는 브라우저로 육안 확인).

정답 출처: Minitab 문서 예제 'Cube Plot' — InsulationProperties 의 Insulation(2차 + 공변량 MeasTemp) 모형에서
CoolTemp 45, Formula2, InjTemp 100, InjPress 150 의 적합 평균 28.3558(최대).
"""
import numpy as np
import pytest

from doe_core.analysis.effects import effects
from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import load_mwx_worksheet
from doe_core.plots.effects_plots import half_normal_effects_chart, normal_effects_chart, pareto_chart
from doe_core.plots.factorial_plots import (
    cube_data, cube_plot, interaction_data, interaction_pairs, interaction_plot, main_effects_data, main_effects_plot,
)
from doe_core.plots.residual_plots import four_in_one, residual_data
from tests.helpers import SAMPLES

FACTORS = ["Material", "InjPress", "InjTemp", "CoolTemp"]


@pytest.fixture(scope="module")
def ws():
    p = SAMPLES / "InsulationProperties.MWX"
    if not p.exists():
        pytest.skip("InsulationProperties.MWX 없음")
    return load_mwx_worksheet(p, FACTORS)


def test_cube_plot_value_matches_doc(ws):
    a = analyze_worksheet(ws, "Insulation", covariates=["MeasTemp"], order=2)
    c = cube_data(a, list("ABCD"))
    assert len(c) == 16
    best = c.loc[c["Fitted Mean"].idxmax()]
    assert round(best["Fitted Mean"], 4) == 28.3558
    assert (best["Material"], best["InjPress"], best["InjTemp"], best["CoolTemp"]) == ("Formula2", "150", "100", "45")
    fig = cube_plot(a, list("ABCD"))
    texts = [tr.text[0] for tr in fig.data if tr.mode == "markers+text"]
    assert "28.3558" in texts and len(texts) == 16


def test_main_effects_and_interaction_data_match_means(ws):
    a = analyze_worksheet(ws, "Strength", terms=["A", "B", "C", "D", "CD"])
    me = main_effects_data(a).set_index(["Name", "Level"])["Fitted Mean"]
    assert round(me[("Material", "Formula1")], 3) == 26.269 and round(me[("CoolTemp", "45")], 3) == 27.674
    it = interaction_data(a, "C", "D").set_index(["X Level", "Trace Level"])["Fitted Mean"]
    assert round(it[("100", "45")], 3) == 30.726 and round(it[("85", "25")], 3) == 30.351
    assert interaction_pairs(a) == [("C", "D")]
    fig = main_effects_plot(a)
    assert len([tr for tr in fig.data if tr.mode == "lines+markers"]) == 4
    assert fig.layout.showlegend is False                                 # 계열 하나면 범례 없음
    fig2 = interaction_plot(a, "C", "D")
    assert len(fig2.data) == 2 and fig2.layout.showlegend is not False


def test_center_point_marker_in_main_effects():
    d = create_two_level_design(2, center_points=3, randomize=False)
    c = d.coded
    y = (5 + c.A + c.B + 2.0 * (c.CenterPt == 0)).astype(float).values
    a = analyze_factorial(d, y, order=2)
    fig = main_effects_plot(a)
    centers = [tr for tr in fig.data if tr.name == "중앙점 (Center)"]
    assert len(centers) == 2 and abs(centers[0].y[0] - 7.0) < 1e-9


def test_effects_charts_and_residuals(ws):
    a = analyze_worksheet(ws, "Strength", covariates=["MeasTemp"], order=2)
    e = effects(a)
    p = pareto_chart(e)
    bars = [tr for tr in p.data if tr.type == "bar"]
    assert sum(len(b.x) for b in bars) == 10
    assert all(b.marker.cornerradius == 4 for b in bars)
    assert p.layout.shapes[0].x0 == pytest.approx(e.reference)
    n = normal_effects_chart(e)
    sig = [tr for tr in n.data if tr.name and tr.name.startswith("유의함")][0]
    assert set(sig.text) == {"A", "B", "C", "D"}                            # 유의한 점만 라벨
    half_normal_effects_chart(e)
    rd = residual_data(a, "standardized")
    assert len(rd) == 16 and np.all(np.diff(rd.sort_values("Residual")["Normal Score"]) > 0)
    f4 = four_in_one(a)
    assert len(f4.layout.annotations) >= 4
    with pytest.raises(ValueError):
        residual_data(a, "studentized")


def test_dark_mode_uses_dark_tokens(ws):
    a = analyze_worksheet(ws, "Strength", order=1)
    fig = main_effects_plot(a, mode="dark")
    assert fig.layout.paper_bgcolor == "#1a1a19"
    assert fig.data[0].line.color == "#3987e5"
