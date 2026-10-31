"""혼합물 반응 최적화 검증: 해가 제약(합 1·성분 범위·선형 제약·고정값)을 지키고, 촘촘한 격자 탐색의 최댓값 이상인지."""
import numpy as np
import pytest

from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.mixture import analyze_mixture, feasible, predict_mixture
from doe_core.designs.common import Factor
from doe_core.designs.mixture import Component, LinearConstraint, create_extreme_vertices
from doe_core.optimize.mixture_optimizer import optimize_mixture, search_bounds
from doe_core.optimize.optimizer import composite, default_goal, desirability, solution_table
from tests.helpers import SAMPLES

FONDUE = SAMPLES / "FondueRecipe.MWX"
COMPS = ["Emmenthaler", "Gruyere", "Broth"]


def fondue_models():
    if not FONDUE.exists():
        pytest.skip("FondueRecipe.MWX 없음")
    from doe_core.io.worksheet import load_mwx_worksheet
    ws = load_mwx_worksheet(FONDUE, COMPS, process=["Temperature"])
    a = analyze_worksheet(ws, "Flavor", terms=["A", "B", "C", "AB", "BC", "A*X1", "B*X1", "C*X1"])
    q = analyze_worksheet(ws, "Quantity", model="quadratic", process_order=1)
    b = analyze_worksheet(ws, "Burned", model="quadratic", process_order=1)
    return ws, a, q, b


def grid_best(models, goals, design, temps):
    lo, hi = search_bounds(design)
    best = 0.0
    for A in np.linspace(lo[0], hi[0], 41):
        for B in np.linspace(lo[1], hi[1], 31):
            C = 1 - A - B
            if not lo[2] - 1e-9 <= C <= hi[2] + 1e-9:
                continue
            for T in temps:
                ds = [desirability(predict_mixture(m, dict(zip(COMPS, (A, B, C))), {"Temperature": T}).fit, g)
                      for m, g in zip(models, goals)]
                best = max(best, composite(ds, goals))
    return best


def test_single_response_flavor():
    ws, a, _, _ = fondue_models()
    g = [default_goal(a, "maximize")]
    r = optimize_mixture([a], g)
    assert r.settings["Temperature"] == 90.0                                  # 공정 변수 계수가 모두 양수
    np.testing.assert_allclose([r.settings[c] for c in COMPS], [0.3, 0.3, 0.4], atol=1e-9)
    assert r.D >= grid_best([a], g, ws.design, [80, 90]) - 1e-9
    assert solution_table(r, g)["Emmenthaler"].iloc[0] == "0.3"
    np.testing.assert_allclose(r.predictions["Flavor"].fit, r.fits["Flavor"])


def test_multiple_responses_and_hold():
    ws, a, q, b = fondue_models()
    goals = [default_goal(a, "maximize", lower=80, target=100), default_goal(q, "target", lower=1.5, target=2.25, upper=3),
             default_goal(b, "minimize", target=0.9, upper=1.5)]
    r = optimize_mixture([a, q, b], goals)
    P = np.array([r.settings[c] for c in COMPS])
    lo, hi = search_bounds(ws.design)
    assert abs(P.sum() - 1) < 1e-9 and np.all(P >= lo - 1e-9) and np.all(P <= hi + 1e-9)
    assert 80 <= r.settings["Temperature"] <= 90
    assert r.D >= grid_best([a, q, b], goals, ws.design, np.linspace(80, 90, 6)) - 1e-6
    h = optimize_mixture([a, q, b], goals, hold={"Temperature": 85, "Broth": 0.5})
    assert h.settings["Temperature"] == 85 and abs(h.settings["Broth"] - 0.5) < 1e-9
    with pytest.raises(ValueError):
        optimize_mixture([a, q], goals)
    with pytest.raises(ValueError):
        optimize_mixture([a], [default_goal(a, "maximize")], hold={"Broth": 0.7, "Gruyere": 0.5})


def test_constrained_design_with_text_process():
    comps = [Component("A", 0.2, 0.6), Component("B", 0.1, 0.5), Component("C", 0.1, 0.5)]
    d = create_extreme_vertices(3, components=comps, constraints=[LinearConstraint({"A": 1, "B": -1}, lower=0)],
                                degree=2, process=[Factor("Cat", "x", "y", False)], randomize=False)
    rng = np.random.default_rng(3)
    P = d.coded[d.letters].values
    x = d.coded["X1"].values
    y = P @ [2.0, 9.0, 1.0] + 2 * x * P[:, 1] + rng.normal(scale=0.05, size=d.n_runs)
    a = analyze_mixture(d, y, model="quadratic", process_order=1)
    r = optimize_mixture([a], [default_goal(a, "maximize")])
    Ps = np.array([[r.settings[c] for c in "ABC"]])
    assert feasible(d, Ps, tol=1e-7).all()                                   # A ≥ B 포함
    assert r.settings["Cat"] == "y"                                          # B 효과가 Cat=y 에서 커짐
    assert abs(Ps[0, 0] - Ps[0, 1]) < 1e-6                                   # B 를 키우면 A − B ≥ 0 에 걸린다
