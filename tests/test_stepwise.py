"""단계적 모형 선택 검증.

Minitab 문서에는 단계적 선택의 출력 숫자 예제가 없어 다음으로 검증한다.
- 독립 구현 대조: statsmodels OLS 로 따로 짠 Stepwise·Forward·Backward(계층 없음)와 단계마다 같은 모형인지.
- 정보 기준: 문서 공식(AICc = −2lnL + 2(p+1) + 2(p+1)(p+2)/(n−p−2), BIC = −2lnL + (p+1)·ln n)을 statsmodels
  로그우도로 다시 계산해 비교. Mallows' Cp 는 완전 모형에서 p 와 같아야 한다.
- 교과서 예제: Montgomery 여과율 2⁴ 무반복 실험(유의 효과 A, C, D, AC, AD). 포화 모형에서 ¼ = 4개 항을 Adj SS 가
  작은 순서로 계층을 지키며 먼저 뺀다(ABCD → ACD → ABC → BCD, 효과 크기로 손계산한 순서).
"""
import math

import numpy as np
import pytest
import statsmodels.api as sm

from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet, info_criteria
from doe_core.analysis.model import is_hierarchical
from doe_core.analysis.stepwise import StepwiseOptions
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import load_mwx_worksheet
from tests.helpers import SAMPLES

FILTRATION = [45, 71, 48, 65, 68, 60, 80, 65, 43, 100, 45, 104, 75, 86, 70, 96]


def _filtration():
    d = create_two_level_design(4, randomize=False)
    y = np.array([FILTRATION[int(i) - 1] for i in d.coded["StdOrder"]], dtype=float)
    return d, y


def _noisy_2_5(seed=3):
    d = create_two_level_design(5, randomize=False)
    c = d.coded
    rng = np.random.default_rng(seed)
    y = (50 + 6 * c["A"] - 4 * c["C"] + 2.5 * c["A"] * c["C"] + 1.2 * c["D"] + 1.0 * c["B"] * c["E"]
         + rng.normal(0, 2.0, len(c)))
    return d, y.values.astype(float)


def _naive(design, y, method, ae, ar):
    """statsmodels 로 짠 단순 단계적 선택(1자유도 항, 계층 없음). 단계마다 모형(항 이름 집합)."""
    c = design.coded.reset_index(drop=True)
    names = dict(zip(design.letters, [f.name for f in design.factors]))
    from itertools import combinations
    cand = {}
    for r in (1, 2):
        for w in combinations(design.letters, r):
            cand["*".join(names[L] for L in w)] = np.prod([c[L].values.astype(float) for L in w], axis=0)
    order = list(cand)

    def fit(model):
        cols = [cand[t] for t in order if t in model]
        X = np.column_stack([np.ones(len(y))] + cols)
        return sm.OLS(y, X).fit()

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
@pytest.mark.parametrize("seed", [3, 11])
def test_matches_independent_implementation(method, seed):
    d, y = _noisy_2_5(seed)
    opts = StepwiseOptions(method=method, hierarchy="none")
    a = analyze_factorial(d, y, order=2, stepwise=opts)
    r = a.selection
    mine = [frozenset(t.name for t in (r.candidates[i] for i in s.terms)) for s in r.steps]
    ae, ar = opts.alphas()
    assert mine == _naive(d, y, method, ae, ar)
    assert [t.name for t in a.terms] == [t.name for t in r.final_terms()]


def test_default_alphas_and_titles():
    assert StepwiseOptions(method="stepwise").alphas() == (0.15, 0.15)
    assert StepwiseOptions(method="forward").alphas() == (0.25, None)
    assert StepwiseOptions(method="backward").alphas() == (None, 0.1)
    d, y = _noisy_2_5()
    a = analyze_factorial(d, y, stepwise=StepwiseOptions(method="backward"))
    assert a.selection.title() == "Backward Elimination of Terms"
    assert a.selection.method_lines() == ["α to remove = 0.1"]
    a = analyze_factorial(d, y, stepwise=StepwiseOptions(method="stepwise", alpha_enter=0.1, alpha_remove=0.2))
    assert a.selection.title() == "Stepwise Selection of Terms"
    assert a.selection.method_lines() == ["α to enter = 0.1, α to remove = 0.2"]
    with pytest.raises(ValueError):
        StepwiseOptions(method="forward_ic", hierarchy="at_end")


def test_information_criteria_formulas():
    d, y = _noisy_2_5()
    a = analyze_factorial(d, y, order=2)
    res = sm.OLS(a.y, a.X).fit()
    n, p = a.n, a.p
    want_aicc = res.aic + 2 + 2 * (p + 1) * (p + 2) / (n - p - 2)        # statsmodels aic 는 σ 를 세지 않는다
    want_bic = res.bic + math.log(n)
    s = a.summary()
    assert s["AICc"] == pytest.approx(want_aicc, rel=1e-10)
    assert s["BIC"] == pytest.approx(want_bic, rel=1e-10)
    assert info_criteria(1.0, 10, 8)["AICc"] is None                    # n − p − 2 ≤ 0
    tbl = a.summary_table(expanded=True)
    assert list(tbl.columns) == ["S", "R-sq", "R-sq(adj)", "PRESS", "R-sq(pred)", "AICc", "BIC"]
    assert list(a.summary_table().columns) == ["S", "R-sq", "R-sq(adj)", "R-sq(pred)"]


def test_filtration_saturated_pre_removal_and_selection():
    d, y = _filtration()
    a = analyze_factorial(d, y, order=4, stepwise=StepwiseOptions(method="backward"))
    r = a.selection
    assert [t.name for t in r.pre_removed] == ["A*B*C*D", "A*C*D", "A*B*C", "B*C*D"]
    assert r.method_lines()[1] == "Terms removed from the saturated model: A*B*C*D, A*C*D, A*B*C, B*C*D"
    assert is_hierarchical(a.terms)
    # 계층 때문에 남는 항을 빼면 p ≤ 0.1
    tbl = a.coefficients_table()
    assert set(tbl["Term"]) >= {"A", "C", "D", "A*C", "A*D"}
    # 1단계(완전 모형)의 Mallows' Cp = p
    st = r.steps[0].fit.stats()
    assert st["Mallows' Cp"] == pytest.approx(r.steps[0].fit.p)
    # Stepwise·AICc 정보 기준은 교과서의 유의 효과를 고른다
    # (BIC 는 16런에서 오차 DF 가 거의 없는 큰 모형을 고른다 — 문서: 모수가 표본에 비해 많으면 AICc 모형이 더 작다)
    for opts in [StepwiseOptions(method="stepwise"), StepwiseOptions(method="forward_ic"),
                 StepwiseOptions(method="forward_ic", hierarchy="none")]:
        b = analyze_factorial(d, y, order=4, stepwise=opts)
        assert [t.name for t in b.terms] == ["A", "C", "D", "A*C", "A*D"], opts
    b = analyze_factorial(d, y, order=4, stepwise=StepwiseOptions(method="forward_ic", criterion="bic"))
    assert len(b.terms) > 5 and is_hierarchical(b.terms)


def test_hierarchy_each_step_and_at_end():
    d, y = _noisy_2_5(11)
    for method in ["stepwise", "forward", "backward"]:
        a = analyze_factorial(d, y, order=3, stepwise=StepwiseOptions(method=method, hierarchy="each_step"))
        for s in a.selection.steps:
            assert is_hierarchical([a.selection.candidates[i] for i in s.terms]), (method, s)
        b = analyze_factorial(d, y, order=3, stepwise=StepwiseOptions(method=method, hierarchy="at_end"))
        assert is_hierarchical(b.terms)
        last = b.selection.steps[-1]
        if last.note == "hierarchy":
            before = b.selection.steps[-2]
            assert not is_hierarchical([b.selection.candidates[i] for i in before.terms])
    # extra_terms: 고차 항이 하위 항과 함께 들어올 수 있다
    a = analyze_factorial(d, y, order=2, stepwise=StepwiseOptions(method="forward", hierarchy="each_step",
                                                                  extra_terms=True))
    assert is_hierarchical(a.terms)


def test_forward_information_criteria_picks_minimum():
    d, y = _noisy_2_5(3)
    for crit in ["aicc", "bic"]:
        a = analyze_factorial(d, y, order=2, stepwise=StepwiseOptions(method="forward_ic", criterion=crit,
                                                                      hierarchy="none"))
        r = a.selection
        key = {"aicc": "AICc", "bic": "BIC"}[crit]
        vals = []
        c = d.coded.reset_index(drop=True)
        for s in r.steps:
            cols = [np.prod([c[L].values.astype(float) for L in r.candidates[i].letters], axis=0) for i in s.terms]
            res = sm.OLS(a.y, np.column_stack([np.ones(a.n)] + cols)).fit()
            n, p = a.n, 1 + len(cols)
            want = (res.aic + 2 + 2 * (p + 1) * (p + 2) / (n - p - 2)) if key == "AICc" else res.bic + math.log(n)
            got = s.fit.stats()[key]
            assert got == pytest.approx(want, rel=1e-10)
            vals.append(got)
        finite = [v if v is not None else math.inf for v in vals]
        assert r.chosen == int(np.argmin(finite))
        best = finite[r.chosen]
        # 최솟값 뒤로 8단계 넘게 가지 않는다(완전 모형·오차 DF 1 로 먼저 멈출 수 있음)
        assert len(r.steps) - 1 - r.chosen <= 8
        assert r.steps[0].note == "start" and r.steps[0].terms == ()
        assert all(v >= best for v in finite)
        assert r.footer_lines() == [f"Model with minimum {key}: Step {r.chosen + 1}"]


def test_force_and_initial_terms():
    d, y = _noisy_2_5(3)
    a = analyze_factorial(d, y, order=2, stepwise=StepwiseOptions(method="backward", force=("B",)))
    assert "B" in [t.name for t in a.terms]
    a = analyze_factorial(d, y, order=2, stepwise=StepwiseOptions(method="stepwise", initial=("B*E",)))
    first = a.selection.steps[0]
    assert first.note == "start"
    assert {a.selection.candidates[i].name for i in first.terms} == {"B", "E", "B*E"}   # 계층으로 B, E 함께
    with pytest.raises(ValueError):
        analyze_factorial(d, y, order=2, stepwise=StepwiseOptions(method="stepwise", force=("Z",)))


def test_details_table_shape():
    d, y = _filtration()
    a = analyze_factorial(d, y, order=4, stepwise=StepwiseOptions(method="stepwise"))
    r = a.selection
    t = r.details_table()
    assert list(t.columns) == ["Term"] + [f"Step {k} {c}" for k in range(1, len(r.steps) + 1) for c in ("Coef", "P")]
    assert list(t["Term"])[-7:] == ["S", "R-sq", "R-sq(adj)", "R-sq(pred)", "Mallows' Cp", "AICc", "BIC"]
    assert t["Term"].iloc[0] == "Constant"
    notes = r.step_notes()
    assert notes[0].startswith("1단계: A 추가")
    assert r.step_notes(en=True)[0].startswith("Step 1: entered A")


def test_none_method_and_split_plot():
    d, y = _noisy_2_5()
    a = analyze_factorial(d, y, stepwise=StepwiseOptions(method="none"))
    assert a.selection is None
    from doe_core.designs.split_plot import create_split_plot_design
    sp = create_split_plot_design(3, 1, randomize=False)
    y = np.arange(len(sp.coded), dtype=float) ** 1.5
    assert analyze_factorial(sp, y, stepwise=StepwiseOptions(method="none")).selection is None
    with pytest.raises(ValueError):
        analyze_factorial(sp, y, stepwise=StepwiseOptions(method="backward"))


@pytest.mark.skipif(not (SAMPLES / "SealStrength.MWX").exists(), reason="SealStrength.MWX 없음")
def test_response_surface_backward():
    ws = load_mwx_worksheet(SAMPLES / "SealStrength.MWX", ["HotBarT", "DwelTime", "HotBarP", "MatTemp"])
    a = analyze_worksheet(ws, "Strength", stepwise=StepwiseOptions(method="backward"))
    assert is_hierarchical(a.terms)
    r = a.selection
    assert r.pre_removed == []
    # 계층으로 보호되지 않은 항은 모두 p ≤ 0.1
    c = a.coefficients()
    protected = {L for t in a.terms if t.order > 1 for L in t.letters}
    for t, p in zip(c["Term"][1:], c["P-Value"][1:]):
        tt = next(x for x in a.terms if x.name == t)
        if tt.order == 1 and tt.letters[0] in protected:
            continue
        assert p <= 0.1, t


@pytest.mark.skipif(not (SAMPLES / "ultrasonic_cleaner.MWX").exists(), reason="ultrasonic_cleaner.MWX 없음")
def test_dsd_supersaturated_forward_ic():
    ws = load_mwx_worksheet(SAMPLES / "ultrasonic_cleaner.MWX",
                            ["Train", "Degas", "Burst", "Quiet", "Center", "Bandwidth", "Sweep"])
    a = analyze_worksheet(ws, "Power", model="full quadratic", stepwise=StepwiseOptions(method="forward_ic"))
    r = a.selection
    assert len(r.candidates) == 7 + 7 + 21 and not r.full_estimable          # 후보가 런 수보다 많다
    assert a.df_error >= 1 and is_hierarchical(a.terms)
    names = [t.name for t in a.terms]
    assert "Train" in names and "Quiet" in names                              # 문서 해석: 가장 큰 주효과
    with pytest.raises(ValueError):
        analyze_worksheet(ws, "Power", model="full quadratic", stepwise=StepwiseOptions(method="backward"))


def test_details_table_slices_and_report():
    from doe_core.io.worksheet import Worksheet
    from doe_core.report import analysis_report, to_xlsx
    from doe_core.report.xlsx import read_xlsx_cells
    d, y = _noisy_2_5(3)
    ws = Worksheet(d)
    ws.add_column("Y", y, order="std")
    a = analyze_worksheet(ws, "Y", order=2, stepwise=StepwiseOptions(method="forward_ic", hierarchy="none"))
    r = a.selection
    n = len(r.steps)
    assert n > 5
    part = r.details_table(5, 5)
    assert list(part.columns)[1] == "Step 6 Coef"
    assert len(part.columns) == 1 + 2 * min(5, n - 5)
    rep = analysis_report(ws, a, figures=False)
    cells = read_xlsx_cells(to_xlsx(rep))
    flat = " ".join(str(v) for sheet in cells.values() for v in sheet.values())
    assert "Forward Selection of Terms" in flat and "Criterion: AICc" in flat
    assert f"Step {n} Coef" in flat and f"Model with minimum AICc: Step {r.chosen + 1}" in flat
