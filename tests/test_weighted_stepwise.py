"""가중 회귀·산포 분석의 단계적 선택 검증.

- statsmodels WLS 로 따로 짠 Stepwise·Forward·Backward(계층 없음)와 단계마다 같은 모형.
- 단계 표의 마지막 단계 통계(R², AICc, BIC)가 최종 가중 분석의 모형 요약과 같다(−2lnL 의 −Σln w 포함).
- 산포 분석(16런 무반복 2⁴, 4차까지 = 포화)에서 Backward 는 ¼ = 4개 항을 먼저 빼고 진행, 결과는 VariabilityAnalysis.
"""
from itertools import combinations

import numpy as np
import pytest
import statsmodels.api as sm

from doe_core.analysis.factorial import analyze_factorial
from doe_core.analysis.stepwise import StepwiseOptions
from doe_core.analysis.variability import analyze_variability
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet


def _data(seed):
    d = create_two_level_design(5, randomize=False)
    c = d.coded
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.3, 3.0, len(c))
    y = (50 + 6 * c["A"] - 4 * c["C"] + 2.5 * c["A"] * c["C"] + 1.2 * c["D"] + 1.0 * c["B"] * c["E"]).values
    y = y + rng.normal(0, 2.0, len(c)) / np.sqrt(w)
    return d, y.astype(float), w


def _naive(design, y, w, method, ae, ar):
    c = design.coded.reset_index(drop=True)
    names = dict(zip(design.letters, [f.name for f in design.factors]))
    cand = {}
    for r in (1, 2):
        for word in combinations(design.letters, r):
            cand["*".join(names[L] for L in word)] = np.prod([c[L].values.astype(float) for L in word], axis=0)
    order = list(cand)

    def fit(model):
        X = np.column_stack([np.ones(len(y))] + [cand[t] for t in order if t in model])
        return sm.WLS(y, X, weights=w).fit()

    model = set(order) if method == "backward" else set()
    steps = [frozenset(model)] if model else []
    while True:
        if method in ("stepwise", "backward") and model:
            res = fit(model)
            inm = [t for t in order if t in model]
            pv = dict(zip(inm, res.pvalues[1:]))
            worst = max(inm, key=lambda t: pv[t])
            if pv[worst] > ar:
                model.discard(worst)
                steps.append(frozenset(model))
                continue
        if method in ("stepwise", "forward"):
            best, bp = None, 1.0
            for t in order:
                if t in model:
                    continue
                res = fit(model | {t})
                p = float(res.pvalues[1 + [x for x in order if x in model | {t}].index(t)])
                if best is None or p < bp:
                    best, bp = t, p
            if best is not None and bp < ae:
                model.add(best)
                steps.append(frozenset(model))
                continue
        break
    return steps


@pytest.mark.parametrize("method", ["stepwise", "forward", "backward"])
@pytest.mark.parametrize("seed", [3, 8])
def test_weighted_stepwise_matches_wls(method, seed):
    d, y, w = _data(seed)
    opts = StepwiseOptions(method=method, hierarchy="none")
    a = analyze_factorial(d, y, order=2, stepwise=opts, weights=w)
    r = a.selection
    mine = [frozenset(r.candidates[i].name for i in s.terms) for s in r.steps]
    assert mine == _naive(d, y, w, method, *opts.alphas())
    assert a.weighted
    last = r.steps[-1].fit.stats()
    s = a.summary()
    for k in ("R-sq", "R-sq(adj)", "R-sq(pred)", "AICc", "BIC"):
        assert last[k] == pytest.approx(s[k], rel=1e-9), k


def test_variability_saturated_backward():
    d = create_two_level_design(4, randomize=False)
    c = d.coded
    rng = np.random.default_rng(6)
    sd = np.exp(0.5 + 0.6 * c["A"].values - 0.4 * c["B"].values * c["A"].values + rng.normal(0, 0.1, len(c)))
    ws = Worksheet(d)
    order = np.argsort(c["StdOrder"].values)
    ws.add_column("Std", list(sd[order]), order="std")
    ws.add_column("N", [5] * len(c), order="std")
    a = analyze_variability(ws, "Std", "N", order=4, stepwise=StepwiseOptions(method="backward"))
    assert type(a).__name__ == "VariabilityAnalysis" and a.weighted
    assert len(a.selection.pre_removed) == 4 and a.selection.title() == "Backward Elimination of Terms"
    names = [t.name for t in a.terms]
    assert "A" in names and "A*B" in names
    assert a.coefficients_title() == "Coded Coefficients for Ln(Std)"
    b = analyze_variability(ws, "Std", "N", order=2, stepwise=StepwiseOptions(method="stepwise"))
    assert b.selection is not None and "A" in [t.name for t in b.terms]
