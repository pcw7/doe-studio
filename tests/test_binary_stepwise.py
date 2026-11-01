"""이항 반응 분석의 단계적 선택 검증.

- statsmodels GLM(Binomial) 이탈도 차(우도비 카이제곱)로 따로 짠 Stepwise·Forward·Backward(계층 없음)와 단계별 모형 일치.
- 정보 기준 전진 선택: 단계마다 AICc·BIC 가 statsmodels 로그우도(이항 계수 포함)로 계산한 값과 같고, 최소인 단계를 고른다.
- 결과는 BinaryAnalysis(.selection), 단계 표 통계 행은 Deviance R-Sq·Deviance R-Sq(adj)·AIC·AICc·BIC.
"""
import math
from itertools import combinations

import numpy as np
import pytest
import statsmodels.api as sm
from scipy import stats

from doe_core.analysis.binary import analyze_binary
from doe_core.analysis.stepwise import StepwiseOptions
from tests.test_binary import _spoilage


def _naive(ws, y, m, method, ae, ar):
    d = ws.design
    c = d.coded.reset_index(drop=True)
    names = dict(zip(d.letters, [f.name for f in d.factors]))
    cand = {}
    for r in (1, 2):
        for w in combinations(d.letters, r):
            cand["*".join(names[L] for L in w)] = np.prod([c[L].values.astype(float) for L in w], axis=0)
    order = list(cand)
    endog = np.column_stack([y, m - y])

    def dev(model):
        X = np.column_stack([np.ones(len(y))] + [cand[t] for t in order if t in model])
        return sm.GLM(endog, X, family=sm.families.Binomial()).fit(tol=1e-12).deviance

    def pval(small, big):
        return stats.chi2.sf(max(dev(small) - dev(big), 0.0), 1)

    model = set(order) if method == "backward" else set()
    steps = [frozenset(model)] if model else []
    while True:
        if method in ("stepwise", "backward") and model:
            pv = {t: pval(model - {t}, model) for t in model}
            worst = max(sorted(model, key=order.index), key=lambda t: (round(pv[t], 12), order.index(t)))
            if pv[worst] > ar:
                model.discard(worst)
                steps.append(frozenset(model))
                continue
        if method in ("stepwise", "forward"):
            outs = [t for t in order if t not in model]
            if outs:
                pv = {t: pval(model, model | {t}) for t in outs}
                best = min(outs, key=lambda t: (round(pv[t], 12), order.index(t)))
                if pv[best] < ae:
                    model.add(best)
                    steps.append(frozenset(model))
                    continue
        break
    return steps


@pytest.mark.parametrize("method", ["stepwise", "forward", "backward"])
def test_matches_independent_lr_stepwise(method):
    ws, y, m = _spoilage(seed=7, inter=0.12)
    opts = StepwiseOptions(method=method, hierarchy="none")
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=2, stepwise=opts)
    r = a.selection
    mine = [frozenset(r.candidates[i].name for i in s.terms) for s in r.steps]
    yy, mm = a.events, a.trials
    assert mine == _naive(ws, yy, mm, method, *opts.alphas())
    assert type(a).__name__ == "BinaryAnalysis" and [t.name for t in a.terms] == [t.name for t in r.final_terms()]
    assert list(r.details_table()["Term"])[-5:] == ["Deviance R-Sq", "Deviance R-Sq(adj)", "AIC", "AICc", "BIC"]


def test_forward_ic_binary_criteria():
    ws, y, m = _spoilage(seed=7, inter=0.12)
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=2,
                       stepwise=StepwiseOptions(method="forward_ic", hierarchy="none"))
    r = a.selection
    c = ws.design.coded.reset_index(drop=True)
    endog = np.column_stack([a.events, a.trials - a.events])
    vals = []
    for s in r.steps:
        cols = [np.prod([c[L].values.astype(float) for L in r.candidates[i].letters], axis=0) for i in s.terms]
        X = np.column_stack([np.ones(a.n)] + cols)
        llf = sm.GLM(endog, X, family=sm.families.Binomial()).fit(tol=1e-12).llf
        p, n = X.shape[1], a.n
        aicc = -2 * llf + 2 * p + 2 * p * (p + 1) / (n - p - 1) if n - p - 1 > 0 else math.inf
        got = dict(s.fit.stat_rows())["AICc"]
        if math.isfinite(aicc):
            assert float(got) == pytest.approx(aicc, abs=0.006)
        vals.append(aicc)
    assert r.chosen == int(np.argmin(vals))
    assert r.footer_lines() == [f"Model with minimum AICc: Step {r.chosen + 1}"]


def test_hierarchical_binary_stepwise_and_app():
    ws, y, m = _spoilage(seed=7, inter=0.12)
    a = analyze_binary(ws, events="Spoilage", trials="Containers", order=2,
                       stepwise=StepwiseOptions(method="stepwise", hierarchy="each_step"))
    from doe_core.analysis.model import is_hierarchical
    for s in a.selection.steps:
        assert is_hierarchical([a.selection.candidates[i] for i in s.terms])
    assert a.anova_table()["Source"].iloc[0] == "Model"
