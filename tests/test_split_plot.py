"""2수준 분할구 설계 생성·분석 검증.

정답 출처
- 생성: Minitab 문서 'Create 2-Level Split-Plot Design' 예제(4요인, HTC 1, 완전 요인 2 전구 × 8 하위구, 전구 반복 2)
  → 설계 요약표, 설계표(Run | Blk | WP | A..D, 행 집합), 'Hard-to-change factors: A', 'Whole Plot Generators: A'.
- 분석: 문서에 숫자 예제가 없어 균형 분할구 고전 분산분석(전구 평균으로 직접 계산)과 statsmodels 혼합모형(REML)으로 검증.
"""
import json
from collections import Counter

import numpy as np
import pandas as pd
import pytest
import statsmodels.formula.api as smf

from doe_core.analysis.diagnostics import diagnostics
from doe_core.analysis.factorial import analyze_factorial
from doe_core.designs.common import Factor
from doe_core.designs.modify import randomize_design, replicate_design
from doe_core.designs.split_plot import available_split_plot, create_split_plot_design
from doe_core.io.worksheet import Worksheet, load_worksheet, save_worksheet
from tests.helpers import load_fixture


def test_example_create_split_plot():
    fx = load_fixture("factorial__create-factorial-design__create-2-level-split-plot__example")
    d = create_split_plot_design(4, 1, seed=7)                              # 기본: 완전 요인, 전구 반복 2
    summ, table = fx["tables"]
    assert d.summary_table().values.tolist() == [summ["header"], *summ["rows"]]
    assert list(d.design_table().columns) == table["header"]
    got = Counter(tuple(map(str, r[1:])) for r in d.design_table().values.tolist())
    assert got == Counter(tuple(r[1:]) for r in table["rows"])
    text = d.summary_text()
    assert "Hard-to-change factors: A" in text and "Whole Plot Generators: A" in text
    assert d.alias_text() == "All terms are free from aliasing."
    # 같은 전구의 런은 연속(전구 순서·전구 안 순서를 따로 랜덤화), 전구 안에서 HTC 요인은 고정
    wp_runs = d.coded.sort_values("RunOrder")["WP"].tolist()
    assert sum(a != b for a, b in zip(wp_runs, wp_runs[1:])) == 3
    assert (d.coded.groupby("WP")["A"].nunique() == 1).all()
    assert available_split_plot(4, 1)[-1].label == "Full factorial with 2 whole plots and 8 subplots"


def test_fractions_replicates_blocks():
    labels = [o.label for o in available_split_plot(5, 2)]
    assert labels == ["1/4 fraction with 4 whole plots and 2 subplots", "1/2 fraction with 4 whole plots and 4 subplots",
                      "Full factorial with 4 whole plots and 8 subplots"]
    d = create_split_plot_design(5, 2, 16, wp_replicates=1, randomize=False)
    assert d.generators == {"E": "ABCD"} and d.n_whole_plots == 4 and d.runs_per_whole_plot == 4
    assert "Design Generators: E = ABCD" in d.summary_text() and d.alias.resolution == 5
    r = create_split_plot_design(3, 1, wp_replicates=3, subplot_replicates=2, block_on_replicates=True, seed=1)
    assert r.n_runs == 48 and r.n_whole_plots == 6 and r.runs_per_whole_plot == 8 and r.n_blocks == 3
    assert (r.coded.groupby("Blocks")["WP"].nunique() == 2).all()
    assert (r.coded.groupby("WP")["Blocks"].nunique() == 1).all()
    for bad in [dict(n_factors=8, n_htc=1), dict(n_factors=3, n_htc=3)]:
        with pytest.raises(ValueError):
            create_split_plot_design(**bad)
    with pytest.raises(ValueError):
        create_split_plot_design(4, 1, 4)                                    # 하위구가 없는 런 수


def _simulate(d, seed=5):
    rng = np.random.default_rng(seed)
    c = d.coded
    wp = rng.normal(scale=2.0, size=int(c["WP"].max()) + 1)
    y = 10 + 3 * c["A"] + 2 * c["B"] - 1.5 * c["C"] + c["A"] * c["B"] + wp[c["WP"]] + rng.normal(scale=0.5, size=len(c))
    return y.values.astype(float)


def test_split_plot_anova_matches_classical():
    d = create_split_plot_design(4, 1, seed=3)
    y = _simulate(d)
    a = analyze_factorial(d, y, order=2)
    c = d.coded
    # 고전 분할구 분산분석: 전구 간 SS − A 의 SS = WP Error, 전구 안 SS − 하위구 효과 SS = SP Error
    grand = y.mean()
    wp_mean = pd.Series(y).groupby(c["WP"].values).transform("mean").values
    a_mean = pd.Series(y).groupby(c["A"].values).transform("mean").values
    ss_between = ((wp_mean - grand) ** 2).sum()
    ss_a = ((a_mean - grand) ** 2).sum()
    rows = {r.source: r for r in a.anova_rows()}
    np.testing.assert_allclose(rows["WP Error"].adj_ss, ss_between - ss_a)
    assert rows["WP Error"].df == 2 and rows["Error"].df == 32 - 4 - 9        # n − 전구 − 하위구 수준 계수
    np.testing.assert_allclose(rows["A"].adj_ss, ss_a)
    np.testing.assert_allclose(rows["A"].f, ss_a / rows["WP Error"].adj_ms)           # HTC 요인: 분모 = WP Error
    np.testing.assert_allclose(rows["B"].f, rows["B"].adj_ss / rows["Error"].adj_ms)   # ETC 요인: 분모 = SP Error
    np.testing.assert_allclose(rows["Model"].adj_ss + rows["Error"].adj_ss, rows["Total"].adj_ss)
    # 잔차는 전구 안에서 합이 0, 전구 잔차 = 전구 평균 − 고정효과 적합
    res = pd.Series(a.resid).groupby(c["WP"].values).sum()
    assert np.allclose(res, 0)
    assert np.allclose(a.whole_plot_residuals(), a.fitted - a.fitted_fixed)
    s = a.summary()
    np.testing.assert_allclose(s["S(WP)"], np.sqrt(rows["WP Error"].adj_ms))
    tot_wp = ss_a + rows["WP Error"].adj_ss
    np.testing.assert_allclose(s["R-sq(WP)"], 1 - rows["WP Error"].adj_ss / tot_wp)
    np.testing.assert_allclose(s["R-sq(SP)"], 1 - a.sse / (a.sst - tot_wp))
    assert list(a.summary_table().columns) == ["S", "R-sq", "R-sq(adj)", "R-sq(pred)", "S(WP)", "R-sq(SP)", "R-sq(WP)"]
    d2 = diagnostics(a)
    assert d2["Cook's D"].notna().all()


def test_split_plot_se_matches_mixed_model():
    d = create_split_plot_design(4, 1, wp_replicates=3, seed=4)
    y = _simulate(d, seed=8)
    a = analyze_factorial(d, y, order=1)
    df = d.coded[["WP", "A", "B", "C", "D"]].copy()
    df["y"] = y
    m = smf.mixedlm("y ~ A + B + C + D", df, groups=df["WP"]).fit(reml=True)
    np.testing.assert_allclose(a.beta, m.fe_params.values, rtol=1e-6)
    np.testing.assert_allclose(a.se_coef(), m.bse_fe.values, rtol=2e-3)
    c = a.coefficients()
    # HTC 요인 A 의 t 검정 자유도 = WP Error DF(전구 6 − 2 = 4), ETC 요인은 SP Error DF
    from scipy import stats
    t_a = c.loc[c["Term"] == "A", "T-Value"].iloc[0]
    np.testing.assert_allclose(c.loc[c["Term"] == "A", "P-Value"].iloc[0], 2 * stats.t.sf(abs(t_a), 4))
    assert a.df_wp == 4 and a.df_error == 48 - 6 - 3


def test_split_plot_save_randomize_and_text_factor(tmp_path):
    facs = [Factor("Oven", "low", "high", False), Factor("B", 1, 2), Factor("C", 10, 20)]
    d = create_split_plot_design(3, 1, factors=facs, seed=2)
    assert set(d.runs["Oven"]) == {"low", "high"} and "WP" in d.runs.columns
    ws = Worksheet(d)
    ws.add_column("Y", np.arange(d.n_runs, dtype=float))
    back = load_worksheet(save_worksheet(ws, tmp_path / "sp.json"))
    assert back.design.summary() == d.summary() and back.design.coded.equals(d.coded)
    r = randomize_design(d, seed=9)
    wp_runs = r.coded.sort_values("RunOrder")["WP"].tolist()
    assert sum(x != y for x, y in zip(wp_runs, wp_runs[1:])) == r.n_whole_plots - 1
    with pytest.raises(ValueError):
        replicate_design(d)
    a = analyze_factorial(back.design, back.column("Y").values, order=2)
    assert a.df_wp == 2 and "WP Error" in [x.source for x in a.anova_rows()]
