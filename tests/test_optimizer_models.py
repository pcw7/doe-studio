"""반응 최적화기·예측·등고선에서 산포 모형(표준편차)과 이항 모형(확률)을 원래 단위로 쓰는지 검증(강건 설계).

- 산포 모형: 적합치 = exp(Ln 선형 예측), CI = exp(선형 예측 ± t·SE).
- 이항 모형: 확률 = expit(선형 예측), CI = expit(선형 예측 ± z·SE), SE Fit = π(1−π)·SE.
- 평균은 목표값, 표준편차는 최소화 → 산포가 작은 수준을 고른다.
"""
import math

import numpy as np
import pytest
from scipy import special, stats

from doe_core.analysis.binary import analyze_binary
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.variability import analyze_variability, replicate_std, store_preprocessed
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet
from doe_core.optimize.optimizer import ResponseGoal, optimize
from doe_core.optimize.predict import design_row, predict, prediction_table
from doe_core.plots.contour_plots import grid


def _robust_ws():
    """평균은 A 에, 산포는 C 에 달린 2³ × 4 반복."""
    d = create_two_level_design(3, replicates=4, randomize=False)
    c = d.coded.reset_index(drop=True)
    rng = np.random.default_rng(11)
    sd = np.exp(0.6 + 0.7 * c["C"].values)                    # C 높음 → 산포 큼
    y = 50 + 5 * c["A"].values + rng.normal(0, 1, len(c)) * sd
    ws = Worksheet(d)
    ws.add_column("Y", list(y[np.argsort(c["StdOrder"].values)]), order="std")
    s, n = replicate_std(ws, "Y")
    store_preprocessed(ws, s, n, "SdY", "NY")
    return ws


def test_variability_prediction_and_robust_optimization():
    ws = _robust_ws()
    mean = analyze_worksheet(ws, "Y", order=1)
    var = analyze_variability(ws, "SdY", "NY", order=1)
    settings = {"A": 0.3, "B": -1, "C": -1}
    p = predict(var, settings)
    x0 = design_row(var, settings)
    eta = float(x0 @ var.beta)
    se = float(np.sqrt(x0 @ var.coef_cov() @ x0))
    t = stats.t.ppf(0.975, var.df_error)
    assert p.fit == pytest.approx(math.exp(eta))
    assert p.ci == pytest.approx((math.exp(eta - t * se), math.exp(eta + t * se)))
    assert prediction_table(p)["95% PI"].iloc[0] == "(*, *)"
    res = optimize([mean, var], [ResponseGoal("Y", "target", lower=45, target=50, upper=55),
                                 ResponseGoal("SdY", "minimize", target=0.5, upper=8.0)])
    assert res.settings["C"] == pytest.approx(-1, abs=1e-3)              # 산포가 작은 수준
    assert res.fits["SdY"] == pytest.approx(float(np.exp(design_row(var, res.settings) @ var.beta)))
    assert res.fits["Y"] == pytest.approx(50, abs=0.5)


def test_binary_prediction_contour_and_optimizer():
    from tests.test_binary import _spoilage
    ws, y, m = _spoilage(inter=0.0)
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=1)
    s = {"Preservative": "Yes", "VacuumPress": 25, "ContaminationLevel": 20, "CoolTemp": 5}
    p = predict(a, s)
    x0 = design_row(a, s)
    eta = float(x0 @ a.beta)
    se = float(np.sqrt(x0 @ a.coef_cov() @ x0))
    z = stats.norm.ppf(0.975)
    assert p.fit == pytest.approx(special.expit(eta))
    assert p.se_fit == pytest.approx(p.fit * (1 - p.fit) * se)
    assert p.ci == pytest.approx((special.expit(eta - z * se), special.expit(eta + z * se)))
    xs, ys, Z = grid(a, "VacuumPress", "ContaminationLevel", hold={"Preservative": "No", "CoolTemp": 5}, n=4)
    assert np.all((Z > 0) & (Z < 1))
    res = optimize([a], [ResponseGoal("Spoilage", "minimize", target=0.02, upper=0.2)])
    corners = special.expit(a.X @ a.beta)                       # 주효과 모형: 최솟값은 꼭짓점
    assert res.fits["Spoilage"] == pytest.approx(float(np.min(corners)), rel=1e-6)
    assert res.settings["Preservative"] == "No" and res.settings["VacuumPress"] == pytest.approx(20, abs=1e-3)
