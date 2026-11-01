"""혼합물 분석의 단계적 선택 검증.

문서(Methods and formulas for stepwise in Analyze Mixture Design, term options 페이지): Stepwise·Forward·Backward,
Forced Terms, α to enter/remove, 포화 모형이면 Backward 진행 안 함. 정한 것: 성분 선형 항은 늘 모형(상수항 역할).
- statsmodels OLS(상수항 없음)로 따로 짠 단계적 선택과 단계별 모형 일치(FondueRecipe 세 반응에 잡음을 더한 데이터).
- 완전 적합(Flavor) 단계는 S = 0, SE·Cp·AICc·BIC 는 '*'.
"""
import numpy as np
import pytest
import statsmodels.api as sm

from doe_core.analysis.mixture import analyze_mixture, analyze_mixture_worksheet, term_matrix, component_values
from doe_core.analysis.stepwise import StepwiseOptions
from tests.helpers import SAMPLES

FONDUE = SAMPLES / "FondueRecipe.MWX"
needs = pytest.mark.skipif(not FONDUE.exists(), reason="FondueRecipe.MWX 없음")


def _ws():
    from doe_core.io.worksheet import load_mwx_worksheet
    return load_mwx_worksheet(FONDUE, ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])


def _naive(a_full, y, method, ae, ar):
    """a_full: 모든 후보 항으로 적합한 MixtureAnalysis. 성분 선형 항은 고정."""
    d = a_full.design
    coded = d.coded.reset_index(drop=True).iloc[a_full.used_rows].reset_index(drop=True)
    P = component_values(d, coded, a_full.units)
    cols = {t.short: term_matrix(t, d, coded, P)[0] for t in a_full.terms}
    order = [t.short for t in a_full.terms]
    linear = [t.short for t in a_full.terms if t.is_component_linear]

    def fit(model):
        X = np.hstack([cols[t] for t in order if t in model])
        return sm.OLS(y, X).fit()

    def pval(model, t):
        res = fit(model)
        inm = [x for x in order if x in model]
        return float(res.pvalues[inm.index(t)])

    model = set(order) if method == "backward" else set(linear)
    steps = [frozenset(model)]
    while True:
        if method in ("stepwise", "backward"):
            cand = [t for t in order if t in model and t not in linear]
            if cand:
                pv = {t: pval(model, t) for t in cand}
                worst = max(cand, key=lambda t: (round(pv[t], 12), order.index(t)))
                if pv[worst] > ar:
                    model.discard(worst)
                    steps.append(frozenset(model))
                    continue
        if method in ("stepwise", "forward"):
            outs = [t for t in order if t not in model]
            if outs:
                pv = {t: pval(model | {t}, t) for t in outs}
                best = min(outs, key=lambda t: (round(pv[t], 12), order.index(t)))
                if pv[best] < ae:
                    model.add(best)
                    steps.append(frozenset(model))
                    continue
        break
    return steps


@needs
@pytest.mark.parametrize("method", ["stepwise", "forward", "backward"])
@pytest.mark.parametrize("base", ["Flavor", "Quantity", "Burned"])
def test_matches_independent_no_intercept_ols(method, base):
    # 예제 반응은 모형에 거의 완전히 맞는 인공 데이터라 p 값이 수치 잡음이 된다 → 잡음을 더해 비교
    ws = _ws()
    rng = np.random.default_rng(4)
    yb = ws.column(base).astype(float).values
    response = f"{base}_noisy"
    ws.add_column(response, list(yb + rng.normal(0, 0.3 * np.std(yb), len(yb))), order="std")
    y = ws.column(response).astype(float).values
    opts = StepwiseOptions(method=method)
    a = analyze_mixture(ws.design, y, response=response, stepwise=opts)
    full = analyze_mixture(ws.design, y, response=response)
    r = a.selection
    mine = [frozenset(r.candidates[i].short for i in s.terms) for s in r.steps]
    assert mine == _naive(full, full.y, method, *opts.alphas())
    assert {t.short for t in a.terms} >= {"A", "B", "C"}                     # 성분 선형 항은 늘 포함
    t = r.details_table()
    assert t["Term"].iloc[0] == "Emmenthaler"                                 # 상수항 행 없음
    assert t[t["Term"] == "Emmenthaler"].iloc[0, 2] == ""                     # 성분 선형 항의 P 는 비움


@needs
def test_perfect_fit_and_forced_terms():
    ws = _ws()
    a = analyze_mixture_worksheet(ws, "Flavor", stepwise=StepwiseOptions(method="forward"))
    last = dict(zip(a.selection.details_table()["Term"], a.selection.details_table().iloc[:, -1]))
    assert last["S"] == "0.00000" and last["Mallows' Cp"] == "*" and last["AICc"] == "*"
    b = analyze_mixture_worksheet(ws, "Burned", stepwise=StepwiseOptions(method="backward", force=("AB",)))
    assert "AB" in [t.short for t in b.terms]
    with pytest.raises(ValueError):
        analyze_mixture_worksheet(ws, "Burned", stepwise=StepwiseOptions(method="forward_ic"))
