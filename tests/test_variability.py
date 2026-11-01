"""산포 분석·가중 회귀 검증.

정답 출처: Minitab 문서 예제 'Analyze Variability'(InsulationStrength.MWX, Std·N = 6, 2차까지, 최소제곱).
원자료(InsulationStrength.MWX)가 없어, 문서 표의 숫자로부터 같은 표가 나오는 런별 ln(Std) 를 만든다.
- 설계: InsulationProperties 와 같은 2⁴(Material 텍스트, InjPress 75–150, InjTemp 85–100, CoolTemp 25–45) — 문서 회귀식의
  비코드화 계수 비(−0.4959/−0.01322 = 37.5 등)로 범위를 확인.
- 가중치 w = 4/ψ'((6−1)/2) = 8.157… 로 모든 런이 같다 → Adj SS = 16·w·Coef² (문서 표에서 비가 일정한 것으로 확인).
- 각 계수는 문서의 Coef·Effect·Ratio Effect·Adj SS 표시를 모두 만족하는 값, 잔차는 모형 밖 ABCD 열 방향으로
  S = 0.549040 이 되게 둔다(직교 설계라 표의 모든 값이 계수와 SSE 로만 정해진다).
교과서·독립 검증: 가중 회귀를 statsmodels WLS 와 비교(계수·SE·SSE·R²), 가중치 공식.
"""
import math

import numpy as np
import pytest
import statsmodels.api as sm
from scipy import special, stats

from doe_core.analysis.alias import alias_lines, factor_name_table
from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet
from doe_core.analysis.variability import (analyze_variability, repeat_std, replicate_std, store_preprocessed,
                                           weights_from_counts)
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet
from tests.helpers import load_fixture, table

FACTORS = [Factor("Material", "Formula1", "Formula2"), Factor("InjPress", 75, 150), Factor("InjTemp", 85, 100),
           Factor("CoolTemp", 25, 45)]


def rows(df):
    return df.astype(str).values.tolist()


SSE = 1.507226                                       # S = 0.549040, Total = 67.0043 이 되는 오차 SS


def _ss_interval(crow, arow, w16, mse):
    """계수표(Coef·Effect·Ratio·T)와 분산분석표(Adj SS·Adj MS·F) 표시를 모두 만족하는 Adj SS 구간."""
    c = crow[3]
    se = math.sqrt(mse / w16)
    good = []
    for b in np.linspace(float(c) - 6e-5, float(c) + 6e-5, 12001):
        ss = w16 * b * b
        if (f"{b:.4f}" == c and f"{2 * b:.4f}" == crow[1] and f"{math.exp(2 * b):.4f}" == crow[2]
                and f"{b / se:.2f}" == crow[5] and f"{ss:.4f}" == arow[2] and f"{ss:.4f}" == arow[3]
                and f"{ss / mse:.2f}" == arow[4] and f"{2 * stats.t.sf(abs(b / se), 5):.3f}" == crow[6] == arow[5]):
            good.append(ss)
    assert good, crow
    return min(good), max(good)


def _insulation_strength():
    fx = load_fixture("analyze-variability__example")
    coef = table(fx, "Coded Coefficients")
    anova = {r[0]: r for r in table(fx, "Analysis of Variance")["rows"]}
    w = float(weights_from_counts([6])[0])
    d = create_two_level_design(4, factors=FACTORS, randomize=False)
    c = d.coded.reset_index(drop=True)
    letters = dict(zip([f.name for f in FACTORS], d.letters))
    w16, mse = 16 * w, SSE / 5
    rng = {r[0]: _ss_interval(r, anova[r[0]], w16, mse) for r in coef["rows"] if r[0] != "Constant"}
    sign = {r[0]: math.copysign(1.0, float(r[3])) for r in coef["rows"]}
    cols = {t: np.prod([c[letters[nm]].values.astype(float) for nm in t.split("*")], axis=0) for t in rng}
    abcd = np.prod([c[L].values.astype(float) for L in d.letters], axis=0)
    resid = abcd * math.sqrt(SSE / w16)
    groups = [(31.783785, [t for t in rng if "*" not in t]), (33.713245, [t for t in rng if "*" in t])]

    def worksheet(b0, ss):
        y = np.full(len(c), b0) + resid
        for t, v in ss.items():
            y = y + sign[t] * math.sqrt(v / w16) * cols[t]
        ws = Worksheet(d)
        order = np.argsort(c["StdOrder"].values)
        ws.add_column("Std", list(np.exp(y)[order]), order="std")
        ws.add_column("N", [6] * len(c), order="std")
        return ws

    # 그룹 합이 Linear 31.7838(MS 7.9459 → 31.78380 미만), 2-Way 33.7132, Model 65.4970, Total 67.0043 이 되도록
    # 각 항의 허용 구간 안에서 SS 를 고르고, 비코드화 회귀식 표시까지 맞는 조합을 고정 난수로 찾는다
    # (원자료가 없어 생기는 자유도: 교호작용 계수의 반올림 범위 안 차이가 회귀식의 마지막 자리를 바꾼다)
    mid = {t: sum(rng[t]) / 2 for t in rng}
    a0 = analyze_variability(worksheet(float(coef["rows"][0][3]), mid), "Std", "N", order=2)
    labels, T = a0._uncoded_transform()
    ses = np.sqrt(np.clip(np.diag(T @ (a0.cov_unscaled * mse) @ T.T), 0, None))
    import re
    want = [(s or "+", v) for s, v in re.findall(r"([+-]?)\s*(\d+\.\d+)", table(fx, "Regression Equation")["header"][2])]
    from doe_core.analysis import fmt
    gen = np.random.default_rng(0)
    pos = {lab: j for j, lab in enumerate(a0.col_labels)}
    for _ in range(50000):
        ss = {t: gen.uniform(*rng[t]) for t in rng}
        ok = True
        for target, group in groups:
            bal = max(group, key=lambda t: rng[t][1] - rng[t][0])
            ss[bal] = target - sum(ss[t] for t in group if t != bal)
            ok &= rng[bal][0] <= ss[bal] <= rng[bal][1]
        if not ok:
            continue
        b0 = gen.uniform(0.34235, 0.34241)                      # Coef 0.3424 이면서 T = 7.12
        beta = np.zeros(len(pos))
        beta[0] = b0
        for t, v in ss.items():
            beta[pos[t]] = sign[t] * math.sqrt(v / w16)
        u = T @ beta
        got = [("-" if x < 0 else "+", fmt.by_se(abs(x), s)) for x, s in zip(u, ses)]
        if got == want:
            return fx, worksheet(b0, ss)
    raise AssertionError("문서 표와 같은 표가 나오는 값을 찾지 못함")


def test_weights_formula():
    assert weights_from_counts([6])[0] == pytest.approx(4 / (math.pi ** 2 / 2 - 4 - 4 / 9))      # ψ'(2.5)
    assert weights_from_counts([6])[0] == pytest.approx(8.157310, abs=1e-6)
    assert np.isnan(weights_from_counts([1])[0])
    assert weights_from_counts([3])[0] == pytest.approx(4 / special.polygamma(1, 1.0))


def test_insulation_strength_example_matches_minitab():
    fx, ws = _insulation_strength()
    a = analyze_variability(ws, "Std", "N", order=2)
    assert rows(a.method_table()) == [["Estimation", "Least squares"]]
    assert table(fx, "Method")["header"] == ["Estimation", "Least squares"]
    for heading, title, mine in [("Coded Coefficients", a.coefficients_title(), a.coefficients_table()),
                                 ("Model Summary", a.summary_title(), a.summary_table()),
                                 ("Analysis of Variance", a.anova_title(), a.anova_table())]:
        want = table(fx, heading)
        assert want["heading"] == title
        assert list(mine.columns) == want["header"], heading
        assert rows(mine) == want["rows"], heading
    title, eq = a.equation()
    want = table(fx, "Regression Equation in Uncoded Units")
    assert title == "Regression Equation in Uncoded Units"
    assert eq.replace(" ", "") == "".join(want["header"]).replace(" ", "")
    names = [t for t in fx["tables"] if t["heading"] == "Alias Structure"]
    assert rows(factor_name_table(a)) == names[0]["rows"]
    assert [[x] for x in alias_lines(a)] == names[1]["rows"]


def test_weighted_regression_matches_statsmodels():
    rng = np.random.default_rng(5)
    d = create_two_level_design(3, replicates=2, randomize=False)
    c = d.coded.reset_index(drop=True)
    y = 10 + 2 * c["A"] - c["B"] + 0.5 * c["A"] * c["C"] + rng.normal(0, 1, len(c))
    w = rng.uniform(0.5, 3.0, len(c))
    a = analyze_factorial(d, y.values, order=2, weights=w)
    res = sm.WLS(a.y, a.X, weights=a.w).fit()
    assert np.allclose(a.beta, res.params) and np.allclose(a.se_coef(), res.bse)
    assert a.sse == pytest.approx(res.ssr) and a.summary()["R-sq"] == pytest.approx(res.rsquared)
    assert a.summary()["R-sq(adj)"] == pytest.approx(res.rsquared_adj)
    # 가중치 0 인 런은 빠진다, 음수는 오류
    w0 = w.copy()
    w0[0] = 0
    assert analyze_factorial(d, y.values, order=2, weights=w0).n == len(c) - 1
    with pytest.raises(ValueError):
        analyze_factorial(d, y.values, order=2, weights=-w)
    # 같은 가중치는 계수·T·P 가 가중치 없는 분석과 같고 SS 만 비례
    b = analyze_factorial(d, y.values, order=2, weights=np.full(len(c), 4.0))
    o = analyze_factorial(d, y.values, order=2)
    assert np.allclose(b.beta, o.beta) and np.allclose(b.se_coef(), o.se_coef())
    assert b.sse == pytest.approx(4 * o.sse)
    # 가중 −2lnL = n·ln(SSE/n) + n + n·ln(2π) − Σln w: 같은 가중치 4 면 n·ln4 − n·ln4 로 상쇄돼 가중치 없는 분석과 같다
    assert b.summary()["BIC"] == pytest.approx(o.summary()["BIC"], rel=1e-12)


def test_preprocess_repeats_and_replicates():
    d = create_two_level_design(2, replicates=3, randomize=True, seed=4)
    ws = Worksheet(d)
    rng = np.random.default_rng(1)
    vals = rng.normal(10, 1, len(d.coded))
    ws.add_column("Y", list(vals))                            # 런 순서
    sd, cnt = replicate_std(ws, "Y")
    store_preprocessed(ws, sd, cnt, "StdY", "CntY")
    c = d.coded.reset_index(drop=True)
    y = ws.column("Y").values
    got = ws.column("StdY").values
    for key, grp in c.groupby(["A", "B"]).groups.items():
        idx = list(grp)
        first = min(idx, key=lambda i: c.loc[i, "RunOrder"])
        assert got[first] == pytest.approx(np.std(y[idx], ddof=1))
        assert all(np.isnan(got[i]) for i in idx if i != first)
        assert ws.column("CntY").values[first] == 3
    a = analyze_variability(ws, "StdY", "CntY", order=2)
    assert a.n == 4 and a.weighted
    # 반복 열
    ws2 = Worksheet(create_two_level_design(2, randomize=False))
    for k in range(4):
        ws2.add_column(f"R{k}", list(rng.normal(5, 1 + k * 0.1, 4)), order="std")
    sd2, cnt2 = repeat_std(ws2, ["R0", "R1", "R2", "R3"])
    M = np.column_stack([ws2.column(f"R{k}").values for k in range(4)])
    assert np.allclose(sd2, M.std(axis=1, ddof=1)) and set(cnt2) == {4}
    with pytest.raises(ValueError):
        repeat_std(ws2, ["R0"])


def test_variability_rejects_other_designs_and_bad_values():
    fx, ws = _insulation_strength()
    ws.add_column("Bad", [-1.0] + [1.0] * 15, order="std")
    with pytest.raises(ValueError):
        analyze_variability(ws, "Bad")
    from doe_core.designs.response_surface import create_ccd
    rs = Worksheet(create_ccd(2, randomize=False))
    rs.add_column("S", list(np.linspace(1, 2, len(rs.design.coded))), order="std")
    with pytest.raises(ValueError):
        analyze_variability(rs, "S")
    # 가중치 열 이름으로 워크시트 분석
    a = analyze_worksheet(ws, "Std", order=1, weights="N")
    assert a.weighted and np.allclose(a.w, 6)
