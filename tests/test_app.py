"""Streamlit 화면 자동 검사(AppTest): 각 화면이 예외 없이 뜨고 핵심 흐름이 동작하는지."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet
from tests.helpers import SAMPLES

MAIN = Path(__file__).resolve().parents[1] / "app" / "main.py"


def run(page: str, ws=None) -> AppTest:
    """진입점(main.py)에서 내비게이션을 거쳐 해당 화면을 연다(페이지 링크가 동작하도록)."""
    at = AppTest.from_file(str(MAIN), default_timeout=90)
    if ws is not None:
        at.session_state["worksheet"] = ws
    at.run()
    if page != "home.py":
        at.switch_page(f"views/{page}")
        at.run()
    return at


def test_home_without_worksheet():
    at = run("home.py")
    assert not at.exception
    assert any("DOE Studio" in t.value for t in at.title)


def test_create_two_level_design_flow():
    at = run("create.py")
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    ws = at.session_state["worksheet"]
    assert ws.design.n_runs == 8
    assert any("Design Summary" in c.value for c in at.code)


@pytest.mark.parametrize("kind", ["Plackett-Burman", "일반 완전요인설계"])
def test_create_other_designs(kind):
    at = run("create.py")
    at.segmented_control[0].set_value(kind).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["worksheet"].design.n_runs > 0


def test_worksheet_page_add_column_and_modify():
    ws = Worksheet(create_two_level_design(4, 8, seed=1))
    at = run("worksheet.py", ws)
    assert not at.exception
    at.text_input[0].set_value("Yield")
    at.button[0].click().run()                          # 폼 제출 버튼
    assert not at.exception
    assert "Yield" in at.session_state["worksheet"].columns.columns


def test_analyze_page_with_insulation_example():
    p = SAMPLES / "InsulationProperties.MWX"
    if not p.exists():
        pytest.skip("InsulationProperties.MWX 없음")
    from doe_core.io.worksheet import load_mwx_worksheet
    ws = load_mwx_worksheet(p, ["Material", "InjPress", "InjTemp", "CoolTemp"])
    at = run("analyze.py", ws)
    assert not at.exception
    at.selectbox[0].set_value("Strength").run()
    at.multiselect[0].set_value(["MeasTemp"]).run()
    at.button[0].click().run()
    assert not at.exception
    a = at.session_state["analysis"]
    assert a.response == "Strength" and [t.name for t in a.terms][0] == "MeasTemp"
    assert len(at.dataframe) >= 3
    assert any("52.7 - 1.229 MeasTemp" in c.value for c in at.code)


def test_analyze_page_without_response_shows_hint():
    at = run("analyze.py", Worksheet(create_two_level_design(3, seed=0)))
    assert not at.exception
    assert any("반응 열이 없습니다" in i.value for i in at.info)


def test_create_response_surface_designs():
    at = run("create.py")
    at.segmented_control[0].set_value("반응표면 설계").run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    d = at.session_state["worksheet"].design
    assert type(d).__name__ == "ResponseSurfaceDesign" and d.kind == "ccd" and d.n_runs == 20
    at.segmented_control[1].set_value("Box-Behnken").run()
    at.button[0].click().run()
    assert not at.exception and at.session_state["worksheet"].design.kind == "bbd"


def test_analyze_and_optimize_seal_strength():
    p = SAMPLES / "SealStrength.MWX"
    if not p.exists():
        pytest.skip("SealStrength.MWX 없음")
    from doe_core.io.worksheet import load_mwx_worksheet
    ws = load_mwx_worksheet(p, ["HotBarT", "DwelTime", "HotBarP", "MatTemp"])
    at = run("analyze.py", ws)
    assert not at.exception and any("반응표면 설계 분석" in t.value for t in at.title)
    at.button[0].click().run()
    assert not at.exception
    assert any("-289.3 + 2.287 HotBarT" in c.value for c in at.code)
    at = run("optimize.py", ws)
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    res = at.session_state["opt"][1]
    assert 0 < res.D <= 1 and set(res.settings) == {"HotBarT", "DwelTime", "HotBarP", "MatTemp"}


def test_worksheet_add_axial_points():
    from doe_core.designs.common import Factor
    ws = Worksheet(create_two_level_design(2, factors=[Factor("T", 10, 20), Factor("P", 1, 2)], center_points=2, seed=0))
    at = run("worksheet.py", ws)
    assert not at.exception
    btn = [b for b in at.button if b.label == "축점 추가"][0]
    btn.click().run()
    assert not at.exception
    assert at.session_state["worksheet"].design.kind == "ccd"


# ---------------------------------------------------------------- 3단계 화면(혼합물·DSD·분할구·최적 설계)


@pytest.mark.parametrize("kind, type_name, runs", [("분할구 설계", "SplitPlotDesign", 32),
                                                   ("확정적 선별설계", "DefinitiveScreeningDesign", 13),
                                                   ("혼합물 설계", "MixtureDesign", 10)])
def test_create_stage3_designs(kind, type_name, runs):
    at = run("create.py")
    at.segmented_control[0].set_value(kind).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    d = at.session_state["worksheet"].design
    assert type(d).__name__ == type_name and d.n_runs == runs
    assert any("Design Summary" in c.value for c in at.code)


def test_create_mixture_extreme_vertices_with_process():
    at = run("create.py")
    at.segmented_control[0].set_value("혼합물 설계").run()
    at.segmented_control[1].set_value("극꼭지점 (Extreme vertices)").run()
    assert not at.exception
    next(n for n in at.number_input if "공정 변수" in n.label).set_value(1).run()   # 공정 변수 1개
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    d = at.session_state["worksheet"].design
    assert d.kind == "extreme_vertices" and len(d.process) == 1 and d.n_runs == 2 * 7


def _sample_ws(name, factors, **kw):
    p = SAMPLES / name
    if not p.exists():
        pytest.skip(f"{name} 없음")
    from doe_core.io.worksheet import load_mwx_worksheet
    return load_mwx_worksheet(p, factors, **kw)


def test_analyze_mixture_fondue():
    ws = _sample_ws("FondueRecipe.MWX", ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])
    at = run("analyze.py", ws)
    assert not at.exception and any("혼합물 설계 분석" in t.value for t in at.title)
    at.segmented_control[0].set_value("항 직접 선택").run()
    assert not at.exception
    at.multiselect[0].set_value(["A", "B", "C", "AB", "BC", "A*X1", "B*X1", "C*X1"]).run()
    at.button[0].click().run()
    assert not at.exception
    a = at.session_state["analysis"]
    assert a.coefficients_table()["Coef"].tolist()[:3] == ["104.874", "175.08", "-8.810"]
    assert any("Estimated Regression Coefficients for Flavor" in m.value for m in at.markdown)


def test_analyze_dsd_ultrasonic():
    ws = _sample_ws("ultrasonic_cleaner.MWX", ["Train", "Degas", "Burst", "Quiet", "Center", "Bandwidth", "Sweep"])
    at = run("analyze.py", ws)
    assert not at.exception and any("선별 설계 분석" in t.value for t in at.title)
    at.button[0].click().run()
    assert not at.exception
    assert any("I + 0.82 AA" in c.value for c in at.code)
    assert any("626.5 + 116.5 Train" in c.value for c in at.code)


def test_optimal_design_page_crystal():
    ws = _sample_ws("CrystalGrowth.MWX", ["A", "B", "C", "D"])
    at = run("optimal.py", ws)
    assert not at.exception
    at.number_input[0].set_value(20).run()
    at.button[0].click().run()
    assert not at.exception
    res = at.session_state["optimal"]
    assert [r + 1 for r in res.rows][:4] == [22, 23, 25, 27]
    assert any("Row number of selected design points: 22, 23, 25, 27" in c.value for c in at.code)
    [b for b in at.button if b.label == "지시자 열을 워크시트에 추가"][0].click().run()
    assert not at.exception
    assert at.session_state["worksheet"].column("OptPoint").sum() == 20
    at.segmented_control[0].set_value("설계 평가 (Evaluate)").run()
    at.selectbox[0].set_value("linear").run()
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["optimal"].task == "evaluate"


def test_analyze_split_plot_page():
    import numpy as np
    from doe_core.designs.split_plot import create_split_plot_design
    d = create_split_plot_design(3, 1, seed=1)
    ws = Worksheet(d)
    rng = np.random.default_rng(0)
    ws.add_column("Y", (5 + 2 * d.coded["A"] + d.coded["B"] + rng.normal(size=d.n_runs)).tolist(), order="worksheet")
    at = run("analyze.py", ws)
    assert not at.exception and any("분할구 설계 분석" in t.value for t in at.title)
    at.button[0].click().run()
    assert not at.exception
    a = at.session_state["analysis"]
    assert "WP Error" in [r.source for r in a.anova_rows()]
    assert "S(WP)" in a.summary_table().columns


def test_home_examples_and_mixture_optimize_notice():
    at = run("home.py")
    assert not at.exception
    ws = _sample_ws("FondueRecipe.MWX", ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])
    at = run("optimize.py", ws)
    assert not at.exception and any("혼합물 반응 최적화" in t.value for t in at.title)
    at.multiselect[0].set_value(["Flavor", "Quantity"]).run()
    [b for b in at.button if b.label == "최적화"][0].click().run()
    assert not at.exception
    _, _, _, res = at.session_state["mix_opt"]
    assert 0 < res.D <= 1 and abs(sum(res.settings[n] for n in ["Emmenthaler", "Gruyere", "Broth"]) - 1) < 1e-9


def test_mixture_panel_plots_and_predict():
    ws = _sample_ws("FondueRecipe.MWX", ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])
    at = run("analyze.py", ws)
    at.selectbox[0].set_value("Quantity").run()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.tabs) >= 5
    assert any("Fit" in df.value.columns for df in at.dataframe)               # 예측 탭의 예측표
    assert any("Centroid of vertices" in c.value for c in at.caption)
