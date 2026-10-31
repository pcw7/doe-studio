"""혼합물 예측·그래프 검증.

- 예측: statsmodels 의 예측(평균·SE·신뢰/예측 구간)과 같아야 한다.
- 반응 추적 그림: 문서 예제 해석(FondueRecipe Flavor, Cox 방향, 기준 혼합물 = 꼭지점 중심, Temperature 80)
  "Emmenthaler 가 늘면 맛 점수가 오르고, Gruyere 는 더 빠르게 오르며, Broth 가 늘면 내려간다".
- 등고선 격자: 삼각형 안의 값이 예측과 같고 밖은 비어 있다. 중첩 등고선의 실현 가능 마스크는 범위 조건과 같다.
"""
import numpy as np
import pytest
import statsmodels.api as sm

from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.mixture import analyze_mixture, feasible, mixture_rows, predict_mixture, reference_blend
from doe_core.designs.common import Factor
from doe_core.designs.mixture import Component, LinearConstraint, create_extreme_vertices, create_simplex_lattice
from doe_core.plots.mixture_plots import (
    Triangle, mixture_contour_plot, mixture_feasible_region, mixture_grid, mixture_overlaid_contour_plot,
    mixture_surface_plot, response_trace_plot, simplex_design_plot, trace_data,
)
from tests.helpers import SAMPLES

FONDUE = SAMPLES / "FondueRecipe.MWX"
DOC_TERMS = ["A", "B", "C", "AB", "BC", "A*X1", "B*X1", "C*X1"]


def fondue():
    if not FONDUE.exists():
        pytest.skip("FondueRecipe.MWX 없음")
    from doe_core.io.worksheet import load_mwx_worksheet
    return load_mwx_worksheet(FONDUE, ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])


def test_predict_matches_statsmodels():
    ws = fondue()
    a = analyze_worksheet(ws, "Flavor", terms=DOC_TERMS)
    p = predict_mixture(a, {"Emmenthaler": 0.375, "Gruyere": 0.125, "Broth": 0.5}, {"Temperature": 90})
    x0 = mixture_rows(a, [[0.375, 0.125, 0.5]], {"Temperature": 90})
    fr = sm.OLS(a.y, a.X).fit().get_prediction(x0).summary_frame(0.05).iloc[0]
    np.testing.assert_allclose([p.fit, p.se_fit, *p.ci, *p.pi],
                               [fr["mean"], fr["mean_se"], fr["mean_ci_lower"], fr["mean_ci_upper"],
                                fr["obs_ci_lower"], fr["obs_ci_upper"]], rtol=1e-9)
    # 설계점에서의 예측 = 적합치(공정 변수 실제 값으로)
    row = ws.design.coded.iloc[0]
    temp = ws.design.runs.iloc[0]["Temperature"]
    q = predict_mixture(a, {L: row[L] for L in ws.design.letters}, {"Temperature": temp})
    np.testing.assert_allclose(q.fit, a.fitted[0])
    # 양 단위 입력, 잘못된 입력
    d = create_simplex_lattice(3, 2, total=50.0, randomize=False)
    b = analyze_mixture(d, d.coded[d.letters].values @ [1.0, 2.0, 3.0], model="linear")
    np.testing.assert_allclose(predict_mixture(b, {"A": 25, "B": 25, "C": 0}, amounts=True).fit, 1.5)
    with pytest.raises(ValueError):
        predict_mixture(b, {"A": 0.5, "B": 0.4, "C": 0.2})
    with pytest.raises(ValueError):
        predict_mixture(b, {"A": 0.5, "B": 0.5})


def test_trace_matches_document_interpretation():
    ws = fondue()
    a = analyze_worksheet(ws, "Flavor", terms=DOC_TERMS)
    np.testing.assert_allclose(reference_blend(ws.design), [0.375, 0.125, 0.5])
    td = trace_data(a)                                                       # Cox, 기준 = 꼭지점 중심, 80도
    slope = {}
    for name, g in td.groupby("Component", sort=False):
        assert np.allclose(g[["Emmenthaler", "Gruyere", "Broth"]].sum(axis=1), 1)
        i = int(np.argmin(np.abs(g["Deviation"].values)))
        assert abs(g["Deviation"].iloc[i]) < 0.02
        slope[name] = np.polyfit(g["Deviation"].values[i - 2:i + 3], g["Fit"].values[i - 2:i + 3], 1)[0]
    assert slope["Emmenthaler"] > 0 and slope["Gruyere"] > slope["Emmenthaler"] and slope["Broth"] < 0
    # 기준 혼합물에서의 값 = 예측
    p = predict_mixture(a, {"Emmenthaler": 0.375, "Gruyere": 0.125, "Broth": 0.5})
    g = td[td["Component"] == "Broth"]
    np.testing.assert_allclose(np.interp(0, g["Deviation"], g["Fit"]), p.fit, rtol=1e-6)
    fig = response_trace_plot(a)
    assert len(fig.data) == 3 and "Temperature = 80" in fig.layout.title.subtitle.text


def test_trace_respects_constraints_and_piepel():
    comps = [Component("A", 0.2, 0.6), Component("B", 0.1, 0.5), Component("C", 0.1, 0.5)]
    d = create_extreme_vertices(3, components=comps, constraints=[LinearConstraint({"A": 1, "B": -1}, lower=0)],
                                randomize=False)
    rng = np.random.default_rng(1)
    P = d.coded[d.letters].values
    y = P @ [5.0, 2.0, 1.0] + 3 * P[:, 0] * P[:, 1] + rng.normal(scale=0.05, size=d.n_runs)
    a = analyze_mixture(d, y, model="quadratic")
    for direction in ("cox", "piepel"):
        td = trace_data(a, direction=direction)
        Pn = td[["A", "B", "C"]].values
        assert feasible(d, Pn, tol=1e-6).all()
    # 하한이 모두 0 이면 Piepel 방향 = Cox 방향
    d0 = create_simplex_lattice(3, 2, randomize=False)
    a0 = analyze_mixture(d0, d0.coded[d0.letters].values @ [1.0, 4.0, 2.0] + np.arange(d0.n_runs) * 0.01)
    c, p = trace_data(a0, direction="cox"), trace_data(a0, direction="piepel")
    np.testing.assert_allclose(c["Fit"], p["Fit"])
    with pytest.raises(ValueError):
        trace_data(a0, direction="other")


def test_contour_grid_and_overlaid():
    ws = fondue()
    a = analyze_worksheet(ws, "Flavor", terms=DOC_TERMS)
    tri, xs, ys, Z, Wg, inside = mixture_grid(a, n=41)
    assert np.isnan(Z[~inside]).all() and np.isfinite(Z[inside]).all()
    k = np.flatnonzero(inside.ravel())[200]
    P = tri.blends(Wg.reshape(-1, 3)[k][None, :])[0]
    np.testing.assert_allclose(Z.ravel()[k], predict_mixture(
        a, dict(zip(["Emmenthaler", "Gruyere", "Broth"], P))).fit)
    q = analyze_worksheet(ws, "Quantity", model="quadratic")
    bounds = {"Flavor": (80, 100), "Quantity": (1.5, 3)}
    tri, xs, ys, zs, ok = mixture_feasible_region([a, q], bounds, n=41)
    expect = (zs["Flavor"] >= 80) & (zs["Flavor"] <= 100) & (zs["Quantity"] >= 1.5) & (zs["Quantity"] <= 3)
    assert np.array_equal(ok, expect) and ok.any()
    for fig in (mixture_contour_plot(a, levels=5), mixture_surface_plot(a, mode="dark"),
                mixture_overlaid_contour_plot([a, q], bounds), simplex_design_plot(ws.design)):
        assert fig.layout.title.text


def test_triangle_with_more_components_and_lower_bounds():
    comps = [Component("A", 0.1, 1), Component("B", 0.2, 1), Component("C", 0.0, 1), Component("D", 0.1, 1)]
    from doe_core.designs.mixture import create_simplex_centroid
    d = create_simplex_centroid(4, components=comps, randomize=False)
    tri = Triangle(d, ["A", "B", "D"], hold={"C": 0.1})
    assert tri.S == pytest.approx(0.9) and tri.W == pytest.approx(0.9 - 0.4)
    corners = tri.blends(np.eye(3))
    np.testing.assert_allclose(corners.sum(axis=1), 1)
    np.testing.assert_allclose(corners[0], [0.6, 0.2, 0.1, 0.1])            # A 꼭지점: 나머지는 하한
    np.testing.assert_allclose(tri.weights(corners), np.eye(3), atol=1e-12)
    with pytest.raises(ValueError):
        Triangle(d, ["A", "A", "B"])
    fig = simplex_design_plot(d, ["A", "B", "D"], hold={"C": 0.1})
    assert fig.layout.title.text == "단순체 설계도"
    proc = create_simplex_lattice(3, 2, process=[Factor("T", 10, 20)], randomize=False)
    a = analyze_mixture(proc, np.arange(proc.n_runs, dtype=float), model="linear")
    assert "T = 20" in response_trace_plot(a, process={"T": 20}).layout.title.subtitle.text
