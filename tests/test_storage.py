"""결과 저장(Storage)·확장 계수표·모든 관측치 표 검증.

- 저장 열 이름 FITS1·RESI1 …, 다시 저장하면 FITS2. 값은 진단 계산과 같고 분석에서 빠진 런은 결측.
- 확장 계수표의 신뢰구간 = statsmodels OLS conf_int, 모든 관측치 표의 CI = statsmodels get_prediction 의 평균 CI.
- 분할구는 계수마다 다른 자유도로 신뢰구간.
"""
import numpy as np
import pytest
import statsmodels.api as sm
from scipy import stats

from doe_core.analysis.diagnostics import diagnostics
from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet
from doe_core.analysis.storage import fits_table, store_statistics
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet


def _ws(seed=2, missing=True):
    d = create_two_level_design(3, replicates=2, randomize=True, seed=seed)
    c = d.coded.reset_index(drop=True)
    rng = np.random.default_rng(seed)
    y = 20 + 3 * c["A"] - 2 * c["B"] + c["A"] * c["C"] + rng.normal(0, 1, len(c))
    y = y.values.astype(float)
    if missing:
        y[3] = np.nan
    ws = Worksheet(d)
    ws.add_column("Y", list(y[np.argsort(c["StdOrder"].values)]), order="std")
    return ws


def _num(s):
    return float(s)


def test_store_statistics_names_and_values():
    ws = _ws()
    a = analyze_worksheet(ws, "Y", order=2)
    names = store_statistics(ws, a, ["fits", "resid", "sres", "tres", "hi", "cook", "dfit"])
    assert names == ["FITS1", "RESI1", "SRES1", "TRES1", "HI1", "COOK1", "DFIT1"]
    d = diagnostics(a)
    fits = ws.column("FITS1").values
    assert np.isnan(fits[3]) and np.allclose(fits[a.used_rows], d["Fit"].values)
    assert np.allclose(ws.column("TRES1").values[a.used_rows], d["Del Resid"].values)
    assert store_statistics(ws, a, ["fits"]) == ["FITS2"]
    with pytest.raises(ValueError):
        store_statistics(ws, a, ["bcre"])                     # Box-Cox 가 아니면 저장 불가


def test_store_boxcox_columns():
    ws = _ws(missing=False)
    a = analyze_worksheet(ws, "Y", order=1, boxcox=0)
    names = store_statistics(ws, a, ["bcre", "bfit"])
    assert names == ["BCRE1", "BFIT1"]
    assert np.allclose(ws.column("BCRE1").values, np.log(ws.column("Y").values))
    assert np.allclose(ws.column("BFIT1").values[a.used_rows], np.exp(a.fitted))


def test_expanded_coefficients_and_fits_ci_match_statsmodels():
    ws = _ws()
    a = analyze_worksheet(ws, "Y", order=2)
    res = sm.OLS(a.y, a.X).fit()
    for conf in (0.95, 0.90):
        t = a.coefficients_table(expanded=True, confidence=conf)
        col = f"{int(conf * 100)}% CI"
        assert list(t.columns) == ["Term", "Effect", "Coef", "SE Coef", col, "T-Value", "P-Value", "VIF"]
        ci = res.conf_int(alpha=1 - conf)
        for j, txt in enumerate(t[col]):
            lo, hi = (float(v) for v in txt.strip("()").split(", "))
            dec = len(t["Coef"].iloc[j].split(".")[1])
            assert lo == pytest.approx(ci[j, 0], abs=0.6 * 10 ** -dec)
            assert hi == pytest.approx(ci[j, 1], abs=0.6 * 10 ** -dec)
    ft = fits_table(a, 0.95)
    pr = res.get_prediction(a.X).conf_int(alpha=0.05)
    for j, txt in enumerate(ft["95% CI"]):
        lo, hi = (float(v) for v in txt.strip("()").split(", "))
        dec = len(ft["Fit"].iloc[j].split(".")[1])
        assert lo == pytest.approx(pr[j, 0], abs=0.6 * 10 ** -dec) and hi == pytest.approx(pr[j, 1], abs=0.6 * 10 ** -dec)
    assert list(ft.columns) == ["Obs", "Y", "Fit", "SE Fit", "95% CI", "Resid", "Std Resid", "Del Resid", "HI",
                                "Cook's D", "DFITS"]
    assert len(ft) == a.n
    # 기본 표는 그대로
    assert list(a.coefficients_table().columns) == ["Term", "Effect", "Coef", "SE Coef", "T-Value", "P-Value", "VIF"]


def test_split_plot_ci_uses_term_df():
    from doe_core.designs.split_plot import create_split_plot_design
    sp = create_split_plot_design(3, 1, randomize=False)
    rng = np.random.default_rng(4)
    y = 10 + 2 * sp.coded["A"].values + sp.coded["B"].values + rng.normal(0, 1, len(sp.coded))
    a = analyze_factorial(sp, y, order=2)
    dfs = a.coef_df()
    t = a.coefficients_table(expanded=True)
    c = a.coefficients()
    j = next(j for j, lab in enumerate(a.col_labels) if lab == "A")
    k = next(j for j, lab in enumerate(a.col_labels) if lab == "B")
    assert dfs[j] != dfs[k]
    for idx in (j, k):
        lo = float(t["95% CI"].iloc[idx].strip("()").split(", ")[0])
        want = c["Coef"].iloc[idx] - stats.t.ppf(0.975, dfs[idx]) * c["SE Coef"].iloc[idx]
        assert lo == pytest.approx(want, abs=0.01)
