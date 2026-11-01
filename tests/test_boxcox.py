"""Box-Cox 변환 검증.

- 상수만 있는 모형: 최적 λ·95% CI 가 scipy.stats.boxcox(최대우도, χ² 프로파일 우도 구간)와 같아야 한다.
- 회귀 모형: 최적 λ 가 야코비안 형태 로그우도 −n/2·ln(SSE/n) + (λ−1)·Σln y 의 최대점과 같아야 한다(독립 계산).
- 문서 규칙: λ ≠ 0 이면 Y^λ, λ = 0 이면 ln Y, λ < 0 이면 −1 을 곱해 순서 유지, 0.5 단위 반올림, 반응은 양수.
- 교과서 예제: Montgomery 시추 속도 2⁴(B, C, D 모형) → 로그 변환(λ̂ ≈ −0.06, CI 가 0 포함, 반올림 λ = 0).
"""
import math

import numpy as np
import pytest
from scipy import optimize, stats

from doe_core.analysis.boxcox import estimate_lambda, inverse, response_label, round_lambda, transform
from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet
from doe_core.designs.factorial import create_two_level_design
from doe_core.optimize.optimizer import ResponseGoal, optimize as run_optimizer
from doe_core.optimize.predict import predict, prediction_table
from doe_core.plots.contour_plots import grid

DRILL = [1.68, 1.98, 3.28, 3.44, 4.98, 5.70, 9.97, 9.07, 2.07, 2.44, 4.09, 4.53, 7.77, 9.43, 11.75, 16.30]


def _drill():
    d = create_two_level_design(4, randomize=False)
    y = np.array([DRILL[int(i) - 1] for i in d.coded["StdOrder"]])
    return d, y


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_intercept_only_matches_scipy(seed):
    rng = np.random.default_rng(seed)
    y = rng.lognormal(1.0, 0.5, 40) + 0.5
    lam, (lo, hi) = estimate_lambda(np.ones((len(y), 1)), y)
    _, want, (wlo, whi) = stats.boxcox(y, alpha=0.05)
    assert lam == pytest.approx(want, abs=1e-6)
    assert lo == pytest.approx(wlo, abs=1e-5) and hi == pytest.approx(whi, abs=1e-5)


def test_regression_lambda_maximizes_jacobian_likelihood():
    d, y = _drill()
    a = analyze_factorial(d, y, terms=["B", "C", "D"])
    X, n = a.X, len(y)

    def nll(lam):
        z = np.log(y) if abs(lam) < 1e-12 else (y ** lam - 1) / lam
        beta, *_ = np.linalg.lstsq(X, z, rcond=None)
        sse = float(np.sum((z - X @ beta) ** 2))
        return n / 2 * math.log(sse / n) - (lam - 1) * float(np.sum(np.log(y)))

    want = optimize.minimize_scalar(nll, bounds=(-2, 2), method="bounded", options={"xatol": 1e-10}).x
    lam, (lo, hi) = estimate_lambda(X, y)
    assert lam == pytest.approx(want, abs=1e-6)
    chi = stats.chi2.ppf(0.95, 1)
    assert 2 * (nll(lo) - nll(lam)) == pytest.approx(chi, abs=1e-6)
    assert 2 * (nll(hi) - nll(lam)) == pytest.approx(chi, abs=1e-6)


def test_transform_rules():
    y = np.array([0.5, 1.0, 2.0, 4.0])
    assert np.allclose(transform(y, 0), np.log(y))
    assert np.allclose(transform(y, 0.5), np.sqrt(y))
    assert np.allclose(transform(y, -1), -1 / y)
    for lam in (-2, -1, -0.5, 0, 0.5, 1, 2):
        z = transform(y, lam)
        assert np.all(np.diff(z) > 0), lam                    # 순서 유지
        assert np.allclose(inverse(z, lam), y), lam
    assert np.isnan(inverse(-1.0, 0.5)) and np.isnan(inverse(0.5, -1))
    assert [round_lambda(v) for v in (-0.26, -0.24, 0.24, 0.26, 0.74, 1.3, -0.055)] == [-0.5, 0, 0, 0.5, 0.5, 1.5, 0]
    assert response_label("Y", 0) == "ln(Y)" and response_label("Y", 0.5) == "Y^0.5"
    assert response_label("Y", -1) == "-Y^(-1)" and response_label("Y", 1) == "Y"


def test_drill_example_log_transform():
    d, y = _drill()
    a = analyze_factorial(d, y, response="Rate", terms=["B", "C", "D"], boxcox="optimal")
    bc = a.boxcox
    assert bc.lam == 0 and bc.estimated == pytest.approx(-0.0551, abs=5e-4)
    assert bc.ci[0] < 0 < bc.ci[1]
    assert a.response_label == "ln(Rate)" and a.response == "Rate"
    assert np.allclose(a.y, np.log(y[a.used_rows])) and np.allclose(a.y_original, y[a.used_rows])
    assert bc.method_table().values.tolist() == [["Box-Cox transformation", "Rounded λ = 0"],
                                                 ["Estimated λ", "-0.0550763"],
                                                 ["95% CI for λ", "(-0.3015, 0.1881)"]]
    title, eq = a.equation()
    assert eq.startswith("ln(Rate) = ")
    # 예측은 원래 단위: exp(선형 예측), 구간 끝도 exp
    b = analyze_factorial(d, np.log(y), response="L", terms=["B", "C", "D"])
    p, q = predict(a, {"B": 1, "C": -1, "D": 1}), predict(b, {"B": 1, "C": -1, "D": 1})
    assert p.fit == pytest.approx(math.exp(q.fit))
    assert p.ci == pytest.approx((math.exp(q.ci[0]), math.exp(q.ci[1])))
    assert p.pi == pytest.approx((math.exp(q.pi[0]), math.exp(q.pi[1])))
    assert prediction_table(p)["SE Fit"].iloc[0] == "*"
    # 반올림하지 않으면 추정값 그대로
    c = analyze_factorial(d, y, terms=["B", "C", "D"], boxcox="optimal", boxcox_rounded=False)
    assert c.boxcox.lam == pytest.approx(-0.0550763, abs=1e-6)
    assert c.boxcox.method_table().iloc[0, 1].startswith("Optimal λ = ")


def test_fixed_lambda_and_errors():
    d, y = _drill()
    a = analyze_factorial(d, y, response="Rate", terms=["B", "C", "D"], boxcox=-0.5)
    assert a.boxcox.method_table().values.tolist() == [["Box-Cox transformation", "λ = -0.5"]]
    assert a.equation()[1].startswith("-Rate^(-0.5) = ")
    assert np.allclose(a.y, -(y ** -0.5))
    with pytest.raises(ValueError):
        analyze_factorial(d, y - 5, terms=["B", "C", "D"], boxcox="optimal")      # 음수 반응
    with pytest.raises(ValueError):
        analyze_factorial(d, y, order=4, boxcox="optimal")                         # 포화 모형: λ 추정 불가
    from doe_core.designs.split_plot import create_split_plot_design
    sp = create_split_plot_design(3, 1, randomize=False)
    with pytest.raises(ValueError):
        analyze_factorial(sp, np.arange(1, len(sp.coded) + 1, dtype=float), boxcox=0)


def test_optimizer_and_contour_use_original_units():
    d, y = _drill()
    a = analyze_factorial(d, y, response="Rate", terms=["B", "C", "D"], boxcox=0)
    res = run_optimizer([a], [ResponseGoal("Rate", "maximize", lower=2.0, target=16.0)])
    assert res.fits["Rate"] == pytest.approx(math.exp(float(np.sum(np.abs(a.beta)))), rel=1e-6)   # 모든 계수 양수 → 꼭짓점
    xs, ys, Z = grid(a, "B", "C", hold={"D": 1}, n=5)
    b0, bB, bC, bD = a.beta
    assert Z[0, 0] == pytest.approx(math.exp(b0 - bB - bC + bD))
    assert Z[-1, -1] == pytest.approx(math.exp(b0 + bB + bC + bD))


def test_worksheet_and_stepwise_combination():
    from doe_core.analysis.stepwise import StepwiseOptions
    from doe_core.io.worksheet import Worksheet
    d, y = _drill()
    ws = Worksheet(d)
    ws.add_column("Rate", y, order="std")
    a = analyze_worksheet(ws, "Rate", order=2, boxcox="optimal", stepwise=StepwiseOptions(method="backward"))
    assert a.boxcox is not None and a.selection is not None
    assert {t.name for t in a.terms} >= {"B", "C", "D"}
    from doe_core.report import analysis_report, to_xlsx
    from doe_core.report.xlsx import read_xlsx_cells
    cells = read_xlsx_cells(to_xlsx(analysis_report(ws, a, figures=False, lang="en")))
    flat = " ".join(str(v) for sheet in cells.values() for v in sheet.values())
    assert "Box-Cox transformation" in flat and "Estimated λ" in flat
