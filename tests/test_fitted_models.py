"""최적화·예측 화면이 분석 화면의 모형(Minitab 의 저장 모형)을 쓰는지 검증.

실사용 점검에서 최적화 화면이 분석 화면에서 줄인 모형을 무시하고 모든 반응을 '완전 2차'로 다시 적합하는 문제를 찾았다.
- 분석 화면에서 '분석' 을 누르면 반응별 모형이 기억된다.
- 항을 줄인 모형을 기억해 두면 최적화 해가 그 모형으로 직접 최적화한 해와 같고, 공통 모형(완전 2차)의 해와는 다르다.
- 중앙점 항(Ct Pt)이 있으면 같은 항으로 Ct Pt 만 빼고 다시 적합, 분석 뒤 값이 바뀌면 같은 설정으로 다시 적합,
  설계가 바뀌면(축점 추가) 기억한 모형은 쓰지 않는다.
"""
import numpy as np
import pytest

from app.fitted_models import _data_key
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.common import Factor
from doe_core.designs.modify import randomize_design
from doe_core.designs.response_surface import add_axial_points
from doe_core.io.worksheet import Worksheet
from doe_core.optimize.optimizer import default_goal, optimize
from tests.test_app import run


def _truth(c):
    a, b, k = c["A"], c["B"], c["C"]
    return 75 + 6 * a + 3 * b + 4 * k - 2.5 * a * b - 3 * a * a - 2 * b * b - 1.5 * k * k


def _ws(axial: bool):
    """실사용 점검 시나리오: 온도·시간·촉매 2³ + 중앙점 3 (axial=True 면 면 중심 축점 6개를 더한 17런)."""
    fac = [Factor("온도", 60, 80), Factor("시간", 1, 3), Factor("촉매", 0.5, 1.5)]
    d = create_two_level_design(3, 8, factors=fac, center_points=3, seed=7)
    if axial:
        d = add_axial_points(d, alpha="face")
    ws = Worksheet(d)
    rng = np.random.default_rng(3)
    coded = d.coded.sort_values("StdOrder")
    y = [_truth(r) + rng.normal(0, 0.4) for _, r in coded.iterrows()]
    ws.add_column("수율", y, order="std")
    return ws


def _store(at, ws, resp, a, kw):
    at.session_state["fitted_models"] = {resp: {"model": a, "kwargs": kw, "data": _data_key(ws, resp, kw)}}


def _optimize(at):
    [b] = [b for b in at.button if b.label == "최적화"]
    b.click().run()
    assert not at.exception
    return at.session_state["opt"][1]


def test_analyze_page_remembers_model():
    ws = _ws(axial=True)
    at = run("analyze.py", ws)
    [b] = [b for b in at.button if b.label == "분석"]
    b.click().run()
    assert not at.exception
    rec = at.session_state["fitted_models"]["수율"]
    assert rec["model"] is at.session_state["analysis"]
    assert rec["model"].design is ws.design


def test_optimizer_uses_reduced_model():
    ws = _ws(axial=True)
    kw = {"terms": ["A", "B", "C", "AA", "BB", "AB"], "include_blocks": True}
    reduced = analyze_worksheet(ws, "수율", **kw)
    at = run("optimize.py", ws)
    _store(at, ws, "수율", reduced, kw)
    at.run()
    assert not at.exception
    res = _optimize(at)
    want = optimize([reduced], [default_goal(reduced, "maximize")])
    for k, v in want.settings.items():
        assert res.settings[k] == pytest.approx(v, abs=1e-6)
    assert any("분석 화면의 모형" in str(df.value.to_dict()) for df in at.dataframe)
    full = analyze_worksheet(ws, "수율", model="full quadratic", include_center=False)
    other = optimize([full], [default_goal(full, "maximize")])
    assert abs(other.settings["촉매"] - res.settings["촉매"]) > 1e-3     # 공통 모형(완전 2차)과는 다른 해


def test_center_point_model_refit_without_ct_pt():
    ws = _ws(axial=False)
    kw = {"order": 2, "include_center": True}
    a = analyze_worksheet(ws, "수율", **kw)
    assert any(t.kind == "center" for t in a.terms)
    at = run("optimize.py", ws)
    _store(at, ws, "수율", a, kw)
    at.run()
    assert not at.exception
    text = str([df.value.to_dict() for df in at.dataframe])
    assert "Ct Pt" in text and "빼고" in text
    res = _optimize(at)
    want = analyze_worksheet(ws, "수율", order=2, include_center=False)
    ref = optimize([want], [default_goal(want, "maximize")])
    assert res.D == pytest.approx(ref.D, abs=1e-9)


def test_refit_when_data_changed_and_ignored_after_design_change():
    ws = _ws(axial=True)
    kw = {"terms": ["A", "B", "C", "AB"], "include_blocks": False}
    a = analyze_worksheet(ws, "수율", **kw)
    at = run("optimize.py", ws)
    _store(at, ws, "수율", a, kw)
    ws.add_column("수율", list(ws.table("run")["수율"] + 1.0))          # 분석 뒤 값 수정
    at.run()
    assert not at.exception
    assert "다시 적합" in str([df.value.to_dict() for df in at.dataframe])
    rec = at.session_state["fitted_models"]["수율"]
    assert rec["model"].y.mean() == pytest.approx(a.y.mean() + 1.0)
    # 설계가 바뀌면(랜덤화·반복 추가 등 새 설계 객체) 기억한 모형은 쓰지 않고 공통 모형
    at.session_state["worksheet"] = ws.with_design(randomize_design(ws.design, seed=11))
    at.run()
    assert not at.exception
    assert "공통 모형" in str([df.value.to_dict() for df in at.dataframe])


def test_mixture_optimizer_uses_analyzed_model():
    """혼합물: 분석 화면에서 선형 모형으로 분석하면 최적화도 그 모형(성분 선형항 + 공정 변수 항)을 쓴다."""
    from tests.test_app import _sample_ws
    ws = _sample_ws("FondueRecipe.MWX", ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])
    at = run("analyze.py", ws)
    at.selectbox[0].set_value("Flavor").run()
    [m] = [s for s in at.selectbox if s.label.startswith("성분 항")]
    m.set_value("linear").run()
    [b] = [b for b in at.button if b.label == "분석"]
    b.click().run()
    assert not at.exception
    a = at.session_state["analysis"]
    at.switch_page("views/optimize.py").run()
    assert not at.exception
    rows = [df.value for df in at.dataframe if "모형 항" in df.value.columns]
    assert rows and rows[0].iloc[0]["모형"] == "분석 화면의 모형"
    assert rows[0].iloc[0]["모형 항"] == ", ".join(t.name for t in a.terms)
