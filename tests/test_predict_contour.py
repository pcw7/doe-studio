"""예측·등고선도·표면도·중첩 등고선도 검증.

정답 출처(Minitab 문서)
- Predict 예제: ThermalEnergyTest, Heat Flux = 389.2 + 2.12 East + 5.318 South - 24.13 North,
  East 35 / South 34 / North 16 → Fit 258.242, SE Fit 2.35414, 95% CI (253.393, 263.090), 95% PI (239.882, 276.601).
- Response Optimizer(Insulation 3반응) 예제의 Multiple Response Prediction 표:
  Material Formula2, InjPress 98.4848, InjTemp 100, CoolTemp 45, MeasTemp 21.4875 에서
  Strength 32.34 / 1.04 / (29.45, 35.22) / (27.25, 37.43) 등.
"""
import numpy as np
import pytest

from doe_core.analysis.factorial import analyze_factorial, analyze_response_surface, analyze_worksheet
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.response_surface import create_ccd
from doe_core.io.mwx import read_mwx
from doe_core.io.worksheet import define_custom_response_surface, load_mwx_worksheet
from doe_core.optimize.predict import (
    predict, prediction_table, response_prediction_row, settings_table,
)
from doe_core.plots.contour_plots import (
    contour_plot, factor_range, feasible_region, grid, overlaid_contour_plot, surface_plot,
)
from tests.helpers import SAMPLES


def _need(name):
    p = SAMPLES / name
    if not p.exists():
        pytest.skip(f"{name} 없음")
    return p


@pytest.fixture(scope="module")
def thermal():
    df = read_mwx(_need("ThermalEnergyTest.MWX"))
    return define_custom_response_surface(df, ["East", "South", "North"], point_type=None, std_order=None,
                                          run_order=None, blocks=None)


def test_predict_thermal_energy_example(thermal):
    a = analyze_worksheet(thermal, "Heat Flux", terms=["A", "B", "C"])
    assert a.equation()[1] == "Heat Flux = 389.2 + 2.12 East + 5.318 South - 24.13 North"
    p = predict(a, {"East": 35, "South": 34, "North": 16})
    tbl = prediction_table(p)
    assert tbl.values.tolist() == [["258.242", "2.35414", "(253.393, 263.090)", "(239.882, 276.601)"]]
    assert list(tbl.columns) == ["Fit", "SE Fit", "95% CI", "95% PI"]
    assert settings_table(a, {"East": 35, "South": 34, "North": 16}).values.tolist() == [
        ["East", "35"], ["South", "34"], ["North", "16"]]


def test_multiple_response_prediction_rows_insulation():
    ws = load_mwx_worksheet(_need("InsulationProperties.MWX"), ["Material", "InjPress", "InjTemp", "CoolTemp"])
    setting = {"Material": "Formula2", "InjPress": 98.4848, "InjTemp": 100, "CoolTemp": 45}
    want = {
        "Strength": ["32.34", "1.04", "(29.45, 35.22)", "(27.25, 37.43)"],
        "Density": ["0.6826", "0.0597", "(0.5167, 0.8484)", "(0.3899, 0.9753)"],
        "Insulation": ["25.608", "0.268", "(24.863, 26.352)", "(24.294, 26.921)"],
    }
    for resp, cells in want.items():
        a = analyze_worksheet(ws, resp, covariates=["MeasTemp"], order=2)
        row = response_prediction_row(resp, predict(a, setting))
        assert [row["Fit"], row["SE Fit"], row["95% CI"], row["95% PI"]] == cells, resp
    st = settings_table(a, setting)
    assert st.values.tolist() == [["Material", "Formula2"], ["InjPress", "98.4848"], ["InjTemp", "100"],
                                  ["CoolTemp", "45"], ["MeasTemp", "21.4875"]]


def test_contour_grid_matches_predict_and_ranges():
    f = [Factor("Temp", 60, 80), Factor("Time", 10, 30), Factor("Cat", 1, 3)]
    d = create_ccd(3, factors=f, seed=0)
    c = d.coded
    y = (50 + 3 * c.A - 2 * c.B + c.C - 2 * c.A ** 2 - c.B ** 2 + 0.5 * c.A * c.B).values
    a = analyze_response_surface(d, y, response="Yield")
    lo, hi = factor_range(a, "A")
    assert np.isclose(lo, 70 - 10 * d.alpha) and np.isclose(hi, 70 + 10 * d.alpha)
    xs, ys, Z = grid(a, "Temp", "Time", hold={"Cat": 2.5}, n=11)
    p = predict(a, {"Temp": xs[3], "Time": ys[7], "Cat": 2.5})
    assert np.isclose(Z[7, 3], p.fit)
    fig = contour_plot(a, "Temp", "Time", hold={"Cat": 2.5}, levels=5)
    assert fig.data[0].type == "contour" and fig.data[0].contours.coloring == "fill"
    assert "Cat = 2.5" in fig.layout.title.subtitle.text
    surface_plot(a, "Temp", "Time", mode="dark")
    with pytest.raises(ValueError):
        grid(a, "Temp", "Temp")
    with pytest.raises(ValueError):
        contour_plot(a, "Temp", "Time", levels=12)


def test_contour_refuses_center_point_term_and_text_axis():
    f = [Factor("A", 0, 10), Factor("M", "x", "y", numeric=False), Factor("C", 1, 2)]
    d = create_two_level_design(3, factors=f, center_points=3, seed=1)
    y = np.linspace(0, 1, d.n_runs) + (d.coded["CenterPt"] == 0).values
    a = analyze_factorial(d, y, order=1)                              # Ct Pt 포함
    with pytest.raises(ValueError, match="중앙점"):
        grid(a, "A", "C")
    b = analyze_factorial(d, y, order=1, include_center=False)
    with pytest.raises(ValueError, match="연속"):
        grid(b, "A", "M")
    xs, ys, Z = grid(b, "A", "C", hold={"M": "y"}, n=5)
    assert Z.shape == (5, 5)


def test_overlaid_contour_feasible_region(thermal):
    a1 = analyze_worksheet(thermal, "Insolation", terms=["A", "B", "C"])
    a2 = analyze_worksheet(thermal, "Heat Flux", terms=["A", "B", "C"])
    bounds = {"Insolation": (725, 775), "Heat Flux": (175, 225)}
    xs, ys, zs, ok = feasible_region([a1, a2], bounds, "South", "North", hold={"East": 31}, n=40)
    assert ok.any() and (~ok).any()
    i, j = np.argwhere(ok)[0]
    for a, (lo, hi) in zip([a1, a2], bounds.values()):
        fit = predict(a, {"East": 31, "South": xs[j], "North": ys[i]}).fit
        assert lo <= fit <= hi
    fig = overlaid_contour_plot([a1, a2], bounds, "South", "North", hold={"East": 31})
    names = {tr.name for tr in fig.data if tr.name}
    assert {"Insolation: 725 ~ 775", "Heat Flux: 175 ~ 225"} <= names
