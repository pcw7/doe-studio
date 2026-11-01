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


def test_report_downloads_on_analysis_page():
    ws = _sample_ws("InsulationProperties.MWX", ["Material", "InjPress", "InjTemp", "CoolTemp"])
    at = run("analyze.py", ws)
    at.selectbox[0].set_value("Strength").run()
    at.button[0].click().run()
    assert not at.exception
    next(c for c in at.checkbox if c.label == "그래프 포함").uncheck().run()
    next(b for b in at.button if b.label == "보고서 만들기").click().run()
    assert not at.exception
    a = at.session_state["analysis"]
    files = at.session_state[f"rep_an_{id(a)}_ko"]
    assert files["xlsx"][:2] == b"PK" and files["pdf"][:5] == b"%PDF-" and b"<!doctype html>" in files["html"]


def test_report_downloads_on_create_page():
    at = run("create.py")
    at.button[0].click().run()
    next(c for c in at.checkbox if c.label == "그래프 포함").uncheck().run()
    next(b for b in at.button if b.label == "보고서 만들기").click().run()
    assert not at.exception
    d = at.session_state["worksheet"].design
    assert at.session_state[f"rep_design_{id(d)}_ko"]["xlsx"][:2] == b"PK"


def test_taguchi_create_and_analyze_pages():
    at = run("create.py")
    at.segmented_control[0].set_value("Taguchi 설계").run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    d = at.session_state["worksheet"].design
    assert type(d).__name__ == "TaguchiDesign" and d.used_name == "L4(2^3)" and d.columns == [1, 2, 3]
    import numpy as np
    ws = at.session_state["worksheet"]
    rng = np.random.default_rng(0)
    ws.add_column("Y1", rng.normal(50, 2, d.n_runs), order="worksheet")
    ws.add_column("Y2", rng.normal(52, 2, d.n_runs), order="worksheet")
    at = run("analyze.py", ws)
    assert not at.exception and any("Taguchi 설계 분석" in t.value for t in at.title)
    at.button[0].click().run()
    assert not at.exception
    res = at.session_state["taguchi"][1]
    assert set(res) == {"sn", "mean"}
    assert any("Response Table for Signal to Noise Ratios" in m.value for m in at.markdown)


def test_analyze_page_stepwise():
    """단계적 선택: 여과율 2⁴ 무반복 실험, 4차까지 후보, 후진 제거(포화 모형 선제거) → 결과·세부 표·보고서."""
    import numpy as np
    from doe_core.analysis.stepwise import StepwiseOptions
    d = create_two_level_design(4, randomize=False)
    ws = Worksheet(d)
    y = [45, 71, 48, 65, 68, 60, 80, 65, 43, 100, 45, 104, 75, 86, 70, 96]
    ws.add_column("Filtration", np.array(y, dtype=float), order="std")
    at = run("analyze.py", ws)
    assert not at.exception
    at.slider[0].set_value(4).run()
    at.selectbox(key="sw_method").set_value("stepwise").run()
    assert not at.exception
    assert at.number_input(key="sw_ae_stepwise").value == 0.15
    at.button[0].click().run()
    assert not at.exception
    a = at.session_state["analysis"]
    assert [t.name for t in a.terms] == ["A", "C", "D", "A*C", "A*D"]
    assert at.session_state["alpha"] == 0.15
    assert any("α to enter = 0.15, α to remove = 0.15" in c.value for c in at.code)
    assert any("1단계: A 추가" in c.value for c in at.code)
    at.selectbox(key="sw_method").set_value("backward").run()
    at.button[0].click().run()
    assert not at.exception
    sel = at.session_state["analysis"].selection
    assert sel.method == "backward" and len(sel.pre_removed) == 4
    from doe_core.report import analysis_report
    rep = analysis_report(ws, at.session_state["analysis"], figures=False)
    assert StepwiseOptions(method="backward").alphas()[1] == 0.1
    assert rep is not None


def test_analyze_and_optimize_with_boxcox():
    """Box-Cox: 시추 속도 2⁴(Montgomery) — 분석 화면에서 최적 λ(반올림 0 → 로그), 최적화 화면은 원래 단위."""
    import numpy as np
    d = create_two_level_design(4, randomize=False)
    ws = Worksheet(d)
    y = [1.68, 1.98, 3.28, 3.44, 4.98, 5.70, 9.97, 9.07, 2.07, 2.44, 4.09, 4.53, 7.77, 9.43, 11.75, 16.30]
    ws.add_column("Rate", np.array(y), order="std")
    at = run("analyze.py", ws)
    at.selectbox(key="bc_analyze").set_value("optimal").run()
    at.slider[0].set_value(1).run()
    at.button[0].click().run()
    assert not at.exception
    a = at.session_state["analysis"]
    assert a.boxcox is not None and a.response_label == "ln(Rate)"
    assert any(c.value.startswith("ln(Rate) = ") for c in at.code)
    at = run("optimize.py", ws)
    at.selectbox(key="bc_optimize").set_value("0").run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    res = at.session_state["opt"][1]
    assert 1.0 < res.fits["Rate"] < 30.0                      # 원래 단위(로그 단위면 3 안팎)


def test_variability_page():
    """산포 분석: 반복 런 2회 2³ → 전처리(첫 런 행에 표준편차·개수) → 분석(가중 최소제곱) → 보고서."""
    import numpy as np
    d = create_two_level_design(3, replicates=3, seed=2)
    ws = Worksheet(d)
    rng = np.random.default_rng(3)
    ws.add_column("Strength", list(rng.normal(30, 2, len(d.coded))))
    at = run("variability.py", ws)
    assert not at.exception
    at.button(key="var_pre").click().run()
    assert not at.exception
    w = at.session_state["worksheet"]
    assert {"StDev_Strength", "Count_Strength"} <= set(w.columns.columns)
    assert w.columns["StDev_Strength"].notna().sum() == 8
    at.button(key="var_run").click().run()
    assert not at.exception
    a = at.session_state["variability"]
    assert a.response == "StDev_Strength" and a.n == 8 and a.weighted
    assert any("Ln(StDev_Strength)" in m.value for m in at.markdown)


def test_analyze_page_with_weights():
    import numpy as np
    d = create_two_level_design(3, replicates=2, randomize=False)
    ws = Worksheet(d)
    rng = np.random.default_rng(8)
    ws.add_column("Y", list(10 + rng.normal(0, 1, len(d.coded))))
    ws.add_column("W", list(rng.uniform(0.5, 2, len(d.coded))))
    at = run("analyze.py", ws)
    at.selectbox(key="weights_col").set_value("W").run()
    at.button[0].click().run()
    assert not at.exception
    a = at.session_state["analysis"]
    assert a.weighted and a.response == "Y"


def test_binary_page():
    """이항 반응: 사건/시행 형식 2⁴ → 분석 → 표·Pareto, 이항 열 형식도."""
    import numpy as np
    from tests.test_binary import _spoilage
    ws, y, m = _spoilage()
    at = run("binary.py", ws)
    assert not at.exception
    at.selectbox(key="bin_events").set_value("Spoilage").run()
    at.selectbox(key="bin_trials").set_value("Containers").run()
    at.button(key="bin_run").click().run()
    assert not at.exception
    a = at.session_state["binary"]
    assert a.n == 16 and a.p == 11
    assert any(c.value.startswith("P(Event) = exp(Y')") for c in at.code)
    from doe_core.report.builders import binary_report
    from doe_core.report import to_pdf
    assert to_pdf(binary_report(ws, a, figures=False))[:4] == b"%PDF"
    d = create_two_level_design(2, replicates=10, randomize=False)
    w2 = Worksheet(d)
    rng = np.random.default_rng(0)
    w2.add_column("Pass", list(rng.binomial(1, 0.4, len(d.coded)).astype(float)), order="std")
    at = run("binary.py", w2)
    at.radio(key="bin_form").set_value("binary").run()
    at.button(key="bin_run").click().run()
    assert not at.exception and at.session_state["binary"].binary_format


def test_optimize_page_with_variability_and_binary_models():
    """강건 설계: 평균(Y) 목표값 + 산포 모형(SdY) 최소화를 최적화 화면에서 함께."""
    from doe_core.analysis.variability import analyze_variability
    from tests.test_optimizer_models import _robust_ws
    ws = _robust_ws()
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(MAIN), default_timeout=90)
    at.session_state["worksheet"] = ws
    at.session_state["variability"] = analyze_variability(ws, "SdY", "NY", order=1)
    at.run()
    at.switch_page("views/optimize.py")
    at.run()
    assert not at.exception
    at.multiselect[0].set_value(["Y"]).run()
    at.checkbox(key="opt_extra_variability").check().run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    names, res = at.session_state["opt"]
    assert names == ["Y", "SdY"] and "SdY" in res.fits


def test_analyze_page_expanded_tables_and_storage():
    from tests.test_storage import _ws
    ws = _ws()
    at = run("analyze.py", ws)
    at.number_input(key="conf_level").set_value(90.0).run()
    at.button[0].click().run()
    assert not at.exception and at.session_state["confidence"] == pytest.approx(0.90)
    at.toggle(key="coef_expanded").set_value(True).run()
    assert not at.exception
    assert any("90% CI" in list(df.value.columns) for df in at.dataframe)
    at.multiselect(key="store_pick").set_value(["fits", "sres"]).run()
    at.button(key="store_btn").click().run()
    assert not at.exception
    assert {"FITS1", "SRES1"} <= set(at.session_state["worksheet"].columns.columns)


def test_power_page():
    """검정력·표본 크기: 워크시트 없이도 열린다. 2수준 예제(0.229…), 반복 수 풀기, PB, 일반 완전요인."""
    at = run("power.py")
    assert not at.exception
    at.number_input(key="pw_omit_two_level").set_value(2).run()
    at.button(key="pw_run").click().run()
    assert not at.exception
    res = at.session_state["power"]
    assert [round(float(v), 3) for v in res.table["Power"]] == [0.229, 0.533, 0.735, 0.858]
    at.text_input(key="pw_reps_two_level").set_value("").run()
    at.text_input(key="pw_pow_two_level").set_value("0.8").run()
    at.button(key="pw_run").click().run()
    assert not at.exception and at.session_state["power"].solve == "reps"
    at.segmented_control(key="pw_kind").set_value("gff").run()
    at.text_input(key="pw_reps_gff").set_value("").run()
    at.text_input(key="pw_pow_gff").set_value("0.9").run()
    at.checkbox(key="pw_gff_blocks").check().run()
    at.button(key="pw_run").click().run()
    assert not at.exception
    assert at.session_state["power"].table.values.tolist() == [["0.4", "2", "18", "0.9", "0.930521"]]


def test_variability_page_with_stepwise():
    import numpy as np
    d = create_two_level_design(3, replicates=3, seed=2)
    ws = Worksheet(d)
    rng = np.random.default_rng(3)
    sd = np.where(d.coded["A"].values > 0, 3.0, 1.0)
    ws.add_column("Strength", list(30 + rng.normal(0, 1, len(d.coded)) * sd))
    at = run("variability.py", ws)
    at.button(key="var_pre").click().run()
    at.selectbox(key="vsw_method").set_value("backward").run()
    at.button(key="var_run").click().run()
    assert not at.exception
    a = at.session_state["variability"]
    assert a.selection is not None and a.selection.method == "backward"
    assert any("Backward Elimination of Terms" in m.value for m in at.markdown)


def test_help_page():
    at = run("help.py")
    assert not at.exception
    assert any("도움말" in t.value for t in at.title)
    assert len(at.tabs) == 5 and len(at.expander) >= 5
