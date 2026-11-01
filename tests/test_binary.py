"""이항 반응 분석 검증.

- 독립 구현 대조: statsmodels GLM(Binomial, logit) 과 계수·SE·이탈도·귀무 이탈도·Pearson·로그우도(이항 계수 포함) 일치,
  항별 Adj Dev = 그 항을 뺀 GLM 의 이탈도 차.
- 이항 열 형식(시행 1) 과 사건/시행 형식의 최대우도 계수가 같아야 한다.
- 문서 예제(FoodSpoilage, 원자료 없음)의 숫자 관계: D₀ = 47.1804, D = 0.9674, p = 11, n = 16, −2lnL = 83.98 일 때
  Model Summary 97.95% | 76.75% | 105.98 | 171.98 | 114.48, Deviance 검정 5 | 0.97 | 0.965, 분산분석표 표시 자리.
"""
import math

import numpy as np
import pytest
import statsmodels.api as sm
from scipy import stats

from doe_core.analysis.binary import analyze_binary
from doe_core.analysis.effects import effects
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet

FACTORS = [Factor("Preservative", "No", "Yes"), Factor("VacuumPress", 20, 40), Factor("ContaminationLevel", 15, 60),
           Factor("CoolTemp", 0, 10)]


def _spoilage(seed=1, inter=0.08):
    d = create_two_level_design(4, factors=FACTORS, randomize=False)
    c = d.coded.reset_index(drop=True)
    rng = np.random.default_rng(seed)
    eta = -2.74 + 0.22 * c["A"] + 0.13 * c["B"] + 0.15 * c["C"] - 0.055 * c["D"] + inter * c["C"] * c["D"]
    m = rng.integers(450, 550, len(c)).astype(float)
    y = rng.binomial(m.astype(int), 1 / (1 + np.exp(-eta))).astype(float)
    ws = Worksheet(d)
    order = np.argsort(c["StdOrder"].values)
    ws.add_column("Spoilage", list(y[order]), order="std")
    ws.add_column("Containers", list(m[order]), order="std")
    return ws, y, m


@pytest.mark.parametrize("seed", [1, 7])
def test_matches_statsmodels_glm(seed):
    ws, y, m = _spoilage(seed)
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=2)
    yy, mm = y[a.used_rows], m[a.used_rows]
    res = sm.GLM(np.column_stack([yy, mm - yy]), a.X, family=sm.families.Binomial()).fit(tol=1e-12)
    assert np.allclose(a.beta, res.params, atol=1e-9)
    assert np.allclose(a.se_coef(), res.bse, rtol=1e-6)
    assert a.deviance() == pytest.approx(res.deviance, abs=1e-8)
    assert a.null_deviance() == pytest.approx(res.null_deviance, abs=1e-8)
    assert a.loglik() == pytest.approx(res.llf, abs=1e-8)
    pearson = float(np.sum((yy - mm * a.prob) ** 2 / (mm * a.prob * (1 - a.prob))))
    assert pearson == pytest.approx(res.pearson_chi2, rel=1e-8)
    # 항별 Adj Dev = 그 항을 뺀 GLM 의 이탈도 차(우도비)
    rows = {r["Source"]: r for r in a.anova_rows()}
    keep = [j for j, ti in enumerate(a.col_term) if ti != 0]
    red = sm.GLM(np.column_stack([yy, mm - yy]), a.X[:, keep], family=sm.families.Binomial()).fit(tol=1e-12)
    assert rows["Preservative"]["Adj Dev"] == pytest.approx(red.deviance - res.deviance, abs=1e-7)
    assert rows["Model"]["Adj Dev"] == pytest.approx(res.null_deviance - res.deviance, abs=1e-8)
    assert rows["Error"]["DF"] == len(yy) - a.p and rows["Total"]["DF"] == len(yy) - 1
    # Wald Z·P
    c = a.coefficients()
    assert np.allclose(c["T-Value"], res.tvalues, rtol=1e-6)
    assert np.allclose(c["P-Value"], res.pvalues, atol=1e-8)


def test_binary_format_equals_event_trial_format():
    d1 = create_two_level_design(3, randomize=False)
    rng = np.random.default_rng(3)
    p = 1 / (1 + np.exp(-(0.2 + 0.8 * d1.coded["A"] - 0.5 * d1.coded["B"])))
    reps = 25
    d2 = create_two_level_design(3, replicates=reps, randomize=False)
    c2 = d2.coded.reset_index(drop=True)
    key = c2["A"].astype(str) + c2["B"].astype(str) + c2["C"].astype(str)
    pmap = dict(zip(d1.coded["A"].astype(str) + d1.coded["B"].astype(str) + d1.coded["C"].astype(str), p))
    yb = rng.binomial(1, key.map(pmap).values).astype(float)
    ws2 = Worksheet(d2)
    ws2.add_column("Pass", list(yb[np.argsort(c2["StdOrder"].values)]), order="std")
    b = analyze_binary(ws2, events="Pass", event_value=1, order=1)
    ws1 = Worksheet(d1)
    c1 = d1.coded.reset_index(drop=True)
    k1 = c1["A"].astype(str) + c1["B"].astype(str) + c1["C"].astype(str)
    ev = [float(yb[key.values == k].sum()) for k in k1]
    order = np.argsort(c1["StdOrder"].values)
    ws1.add_column("E", list(np.array(ev)[order]), order="std")
    ws1.add_column("N", [float(reps)] * 8, order="std")
    a = analyze_binary(ws1, events="E", trials="N", order=1)
    assert np.allclose(a.beta, b.beta, atol=1e-8)
    assert b.binary_format and b.response_table()["Value"].tolist()[0] == "1 (Event)"


def test_document_example_relations():
    ws, y, m = _spoilage()
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=2)
    assert (a.n, a.p) == (16, 11)
    a.deviance = lambda: 0.9674
    a.null_deviance = lambda: 47.1804
    a.loglik = lambda: -83.98 / 2
    assert a.summary_table().values.tolist() == [["97.95%", "76.75%", "105.98", "171.98", "114.48"]]
    assert a.gof_table().values.tolist()[0] == ["Deviance", "5", "0.97", "0.965"]
    rows = [{"Source": "Model", "DF": 10, "Adj Dev": 46.2130, "Adj Mean": 4.6213, "Chi-Square": 46.2130,
             "P-Value": float(stats.chi2.sf(46.2130, 10))},
            {"Source": "Preservative", "DF": 1, "Adj Dev": 22.6835, "Adj Mean": 22.6835, "Chi-Square": 22.6835,
             "P-Value": float(stats.chi2.sf(22.6835, 1))},
            {"Source": "VacuumPress", "DF": 1, "Adj Dev": 7.3313, "Adj Mean": 7.3313, "Chi-Square": 7.3313,
             "P-Value": float(stats.chi2.sf(7.3313, 1))},
            {"Source": "Error", "DF": 5, "Adj Dev": 0.9674, "Adj Mean": 0.9674 / 5, "Chi-Square": None, "P-Value": None},
            {"Source": "Total", "DF": 15, "Adj Dev": 47.1804, "Adj Mean": None, "Chi-Square": None, "P-Value": None}]
    a.anova_rows = lambda: rows
    t = a.anova_table().values.tolist()
    assert t[0] == ["Model", "10", "46.2130", "4.6213", "46.21", "0.000"]
    assert t[1] == ["Preservative", "1", "22.6835", "22.6835", "22.68", "0.000"]
    assert t[2] == ["VacuumPress", "1", "7.3313", "7.3313", "7.33", "0.007"]
    assert t[4] == ["Total", "15", "47.1804", "", "", ""]


def test_hosmer_lemeshow_groups_and_statistic():
    ws, y, m = _spoilage()
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=2)
    chi, df = a.hosmer_lemeshow()
    assert df == 6                                   # 16행 × 약 500 시행 → 8그룹(문서 예제와 같은 DF)
    # 독립 계산: 같은 그룹 규칙으로 2×g 표의 카이제곱
    p = a.prob
    order = np.argsort(p, kind="stable")
    target, groups, cur, acc = a.trials.sum() / 10, [], [], 0.0
    for i in order:
        cur.append(i)
        acc += a.trials[i]
        if acc >= target:
            groups.append(cur)
            cur, acc = [], 0.0
    if cur:
        groups.append(cur)
    want = 0.0
    for g in groups:
        n_k, o_k = a.trials[g].sum(), a.events[g].sum()
        pi = (a.trials[g] * p[g]).sum() / n_k
        want += (o_k - n_k * pi) ** 2 / (n_k * pi * (1 - pi))
    assert chi == pytest.approx(want) and df == len(groups) - 2


def test_odds_ratios_without_interactions():
    ws, y, m = _spoilage(inter=0.0)
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=1)
    cont = a.odds_continuous()
    se = a.se_coef()
    j = a.col_labels.index("VacuumPress")
    row = cont[cont["Term"] == "VacuumPress"].iloc[0]
    assert row["Unit of Change"] == "10.0" and row["Odds Ratio"] == f"{math.exp(a.beta[j]):.4f}"
    lo, hi = math.exp(a.beta[j] - 1.959963984540054 * se[j]), math.exp(a.beta[j] + 1.959963984540054 * se[j])
    assert row["95% CI"] == f"({lo:.4f}, {hi:.4f})"
    cat = a.odds_categorical()
    jp = a.col_labels.index("Preservative")
    assert cat.values.tolist()[1][1:3] == ["Yes", "No"]
    assert cat.values.tolist()[1][3] == f"{math.exp(2 * a.beta[jp]):.4f}"
    # 교호작용이 있으면 '*'
    b = analyze_binary(ws, events="Spoilage", trials="Containers", order=2)
    assert set(b.odds_continuous()["Odds Ratio"]) == {"*"}
    assert b.odds_categorical().values.tolist()[1] == ["", "Any level", "Any level", "*", "(*, *)"]


def test_equation_effects_and_errors():
    ws, y, m = _spoilage()
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=2)
    title, eq = a.equation()
    assert title == "Regression Equation in Uncoded Units"
    assert eq.startswith("P(Event) = exp(Y')/(1 + exp(Y'))\nY' = ")
    e = effects(a, 0.05)
    assert e.reference == pytest.approx(1.959964, abs=1e-5) and e.standardized
    assert a.method_table().values.tolist() == [["Link function", "Logit"], ["Rows used", "16"]]
    ws.add_column("Bad", [600.0] * 16, order="std")
    with pytest.raises(ValueError):
        analyze_binary(ws, events="Bad", trials="Containers")
    # 완전 분리
    d = create_two_level_design(2, replicates=3, randomize=False)
    w2 = Worksheet(d)
    w2.add_column("Y", list((d.coded["A"].values > 0).astype(float)[np.argsort(d.coded["StdOrder"].values)]),
                  order="std")
    with pytest.raises(ValueError):
        analyze_binary(w2, events="Y", event_value=1, order=1)
