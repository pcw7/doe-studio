"""반응 최적화기 검증.

정답 출처(Minitab 문서)
- ThermalEnergyTest(선형 모형 2개, Insolation Target 750, Heat Flux Target 200): Parameters 표 글자 단위 일치,
  종합 만족도 1. 문서 해(East 32.2129, South 34.9758, North 18.3831)의 Multiple Response Prediction 표 일치.
  D = 1 인 해는 무수히 많아 Minitab 과 같은 점을 찾을 필요는 없다.
- InsulationProperties 3반응(Strength 최대화, Density 최소화, Insulation 최대화, 2차 + 공변량):
  종합 만족도 0.7750, Formula2·InjTemp 100·CoolTemp 45, 문서 해(InjPress 98.4848)에서 Insulation 개별 만족도 0.85386.
  최적점 근처가 매우 평평해(InjPress 98.38 과 98.48 의 D 차이 1.6e−7) InjPress 는 0.2 이내로 비교한다.
- 만족도 함수: 구간별 정의를 직접 계산.
"""
import math

import numpy as np
import pytest

from doe_core.analysis.factorial import analyze_response_surface, analyze_worksheet
from doe_core.designs.common import Factor
from doe_core.designs.response_surface import create_ccd
from doe_core.io.mwx import read_mwx
from doe_core.io.worksheet import define_custom_response_surface, load_mwx_worksheet
from doe_core.optimize.optimizer import (
    ResponseGoal, composite, default_goal, desirability, evaluate, multiple_response_prediction, optimize,
    parameters_table, setting_table, solution_table,
)
from doe_core.optimize.predict import predict, response_prediction_row
from tests.helpers import SAMPLES, load_fixture, table


def _need(name):
    p = SAMPLES / name
    if not p.exists():
        pytest.skip(f"{name} 없음")
    return p


def test_desirability_functions():
    mx = ResponseGoal("Y", "maximize", lower=10, target=20, weight=2)
    assert desirability(5, mx) == 0 and desirability(25, mx) == 1 and math.isclose(desirability(15, mx), 0.25)
    mn = ResponseGoal("Y", "minimize", target=1, upper=3, weight=0.5)
    assert desirability(0.5, mn) == 1 and desirability(4, mn) == 0 and math.isclose(desirability(2, mn), 0.5 ** 0.5)
    tg = ResponseGoal("Y", "target", lower=0, target=10, upper=30)
    assert math.isclose(desirability(5, tg), 0.5) and math.isclose(desirability(20, tg), 0.5) and desirability(31, tg) == 0
    g = [ResponseGoal("a", "maximize", 0, 1, importance=1), ResponseGoal("b", "maximize", 0, 1, importance=3)]
    assert math.isclose(composite([0.5, 0.8], g), (0.5 * 0.8 ** 3) ** 0.25)
    assert composite([0.0, 1.0], g) == 0.0
    with pytest.raises(ValueError):
        ResponseGoal("Y", "maximize", 0, 1, weight=20)


@pytest.fixture(scope="module")
def thermal():
    th = define_custom_response_surface(read_mwx(_need("ThermalEnergyTest.MWX")), ["East", "South", "North"],
                                        point_type=None, std_order=None, run_order=None, blocks=None)
    a1 = analyze_worksheet(th, "Insolation", terms=["A", "B", "C"])
    a2 = analyze_worksheet(th, "Heat Flux", terms=["A", "B", "C"])
    return [a1, a2], [default_goal(a1, "target", target=750), default_goal(a2, "target", target=200)]


def test_thermal_parameters_and_doc_solution(thermal):
    fx = load_fixture("ufm__response-optimizer__example-with-regression-models")
    models, goals = thermal
    want = table(fx, "Parameters")
    got = parameters_table(models, goals)
    assert list(got.columns) == want["header"] and got.values.tolist() == want["rows"]
    # Heat Flux 는 Predict 예제와 같은 선형 모형이라 문서 해의 예측 행이 일치한다.
    # Insolation 은 Minitab 예제 파일에 저장된 모형의 항 구성이 문서에 없어(선형 모형으로는 문서 해에서 702.7) 비교하지 않는다.
    doc_point = {"East": 32.2129, "South": 34.9758, "North": 18.3831}
    pred = [t for t in fx["tables"] if "Fit" in t["header"]][0]
    hf = list(response_prediction_row("Heat Flux", predict(models[1], doc_point)).values())
    assert hf == pred["rows"][1]


def test_thermal_optimizer_reaches_targets(thermal):
    models, goals = thermal
    res = optimize(models, goals)
    assert res.D > 0.9999
    assert abs(res.fits["Insolation"] - 750) < 0.05 and abs(res.fits["Heat Flux"] - 200) < 0.01
    sol = solution_table(res, goals)
    assert list(sol.columns) == ["Solution", "East", "South", "North", "InsolationFit", "Heat FluxFit",
                                 "CompositeDesirability"]
    assert sol.iloc[0]["CompositeDesirability"] == "1" and sol.iloc[0]["InsolationFit"] == "750"


def test_insulation_three_responses():
    ws = load_mwx_worksheet(_need("InsulationProperties.MWX"), ["Material", "InjPress", "InjTemp", "CoolTemp"])
    models = [analyze_worksheet(ws, r, covariates=["MeasTemp"], order=2) for r in ["Strength", "Density", "Insulation"]]
    goals = [default_goal(models[0], "maximize"), default_goal(models[1], "minimize"), default_goal(models[2], "maximize")]
    # 기본 하한·목표·상한 = 데이터 최솟값·최댓값(문서: 19.2189 / 38.1821, 0.4351 / 1.60314, 13.2905 / 27.7156)
    assert round(goals[0].lower, 4) == 19.2189 and round(goals[0].target, 4) == 38.1821
    assert round(goals[1].target, 4) == 0.4351 and round(goals[1].upper, 5) == 1.60314
    res = optimize(models, goals)
    assert round(res.D, 4) == 0.7750
    assert res.settings["Material"] == "Formula2" and res.settings["InjTemp"] == 100 and res.settings["CoolTemp"] == 45
    assert abs(res.settings["InjPress"] - 98.4848) < 0.2
    assert res.covariates == {"MeasTemp": pytest.approx(21.4875)}
    doc = {"Material": "Formula2", "InjPress": 98.4848, "InjTemp": 100, "CoolTemp": 45}
    D, d, _ = evaluate(models, goals, doc)
    assert round(d["Insulation"], 5) == 0.85386 and round(D, 4) == 0.7750
    st = setting_table(res)
    assert st["Variable"].tolist() == ["Material", "InjPress", "InjTemp", "CoolTemp", "MeasTemp"]
    assert list(multiple_response_prediction(res).columns) == ["Response", "Fit", "SE Fit", "95% CI", "95% PI"]
    p = parameters_table(models, goals)
    assert p.iloc[0]["Upper"] == "" and p.iloc[1]["Lower"] == ""


def test_hold_and_response_surface_optimum():
    f = [Factor("Temp", 60, 80), Factor("Time", 10, 30)]
    d = create_ccd(2, factors=f, randomize=False)
    T, t = d.runs["Temp"].values, d.runs["Time"].values
    y = 100 - (T - 72) ** 2 / 10 - (t - 18) ** 2 / 5
    a = analyze_response_surface(d, y, response="Yield")
    g = [default_goal(a, "maximize", target=100)]          # 참 최댓값을 목표로(데이터 최댓값이면 d = 1 인 평평한 영역이 생김)
    res = optimize([a], g)
    assert abs(res.settings["Temp"] - 72) < 1e-3 and abs(res.settings["Time"] - 18) < 1e-3
    held = optimize([a], g, hold={"Temp": 65})
    assert held.settings["Temp"] == 65 and abs(held.settings["Time"] - 18) < 1e-3
    with pytest.raises(ValueError):
        default_goal(a, "target", target=95, lower=99, upper=100)
