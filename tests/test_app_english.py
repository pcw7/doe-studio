"""영어 화면 검사: 언어를 English 로 바꾸면 화면의 제목·소제목·버튼·입력 라벨·안내·탭에 한글이 남지 않아야 한다.

허용: 사이드바 언어 선택(언어 · Language / 한국어), 사용자가 입력한 값(요인 이름 등)."""
import re

import numpy as np
import pytest

from tests.helpers import SAMPLES
from tests.test_app import run

HANGUL = re.compile(r"[\uac00-\ud7a3]")
ALLOWED = {"언어 · Language", "한국어"}


def korean_left(at) -> list[str]:
    texts = []
    for coll in ("title", "subheader", "header", "markdown", "caption", "info", "warning", "error", "success"):
        texts += [e.value for e in getattr(at, coll)]
    for coll in ("button", "selectbox", "multiselect", "checkbox", "number_input", "text_input", "slider", "radio",
                 "segmented_control", "tabs", "expander"):
        for e in getattr(at, coll):
            texts.append(getattr(e, "label", "") or "")
            for opt in getattr(e, "options", []) or []:
                texts.append(str(opt))
    return [t for t in texts if t and HANGUL.search(t) and t not in ALLOWED]


def run_en(page, ws=None):
    from streamlit.testing.v1 import AppTest
    from tests.test_app import MAIN
    at = AppTest.from_file(str(MAIN), default_timeout=120)
    at.session_state["lang"] = "en"
    if ws is not None:
        at.session_state["worksheet"] = ws
    at.run()
    if page != "home.py":
        at.switch_page(f"views/{page}")
        at.run()
    assert not at.exception
    return at


def sample(name, factors, **kw):
    p = SAMPLES / name
    if not p.exists():
        pytest.skip(f"{name} 없음")
    from doe_core.io.worksheet import load_mwx_worksheet
    return load_mwx_worksheet(p, factors, **kw)


@pytest.mark.parametrize("kind", ["2수준 요인설계", "분할구 설계", "Plackett-Burman", "확정적 선별설계", "일반 완전요인설계",
                                  "반응표면 설계", "혼합물 설계"])
def test_create_page_english(kind):
    at = run_en("create.py")
    next(w for w in at.segmented_control if w.key != "lang").set_value(kind).run()   # 사이드바 언어 선택 제외
    at.button[0].click().run()
    assert not at.exception
    assert korean_left(at) == []


def test_home_and_worksheet_english():
    assert korean_left(run_en("home.py")) == []
    from doe_core.designs.factorial import create_two_level_design
    from doe_core.io.worksheet import Worksheet
    assert korean_left(run_en("worksheet.py", Worksheet(create_two_level_design(3, seed=1)))) == []


def test_analyze_pages_english():
    ws = sample("InsulationProperties.MWX", ["Material", "InjPress", "InjTemp", "CoolTemp"])
    at = run_en("analyze.py", ws)
    at.selectbox[0].set_value("Strength").run()
    at.button[0].click().run()
    assert not at.exception and korean_left(at) == []
    mix = sample("FondueRecipe.MWX", ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])
    at = run_en("analyze.py", mix)
    at.button[0].click().run()
    assert not at.exception and korean_left(at) == []


def test_optimize_and_optimal_english():
    ws = sample("SealStrength.MWX", ["HotBarT", "DwelTime", "HotBarP", "MatTemp"])
    at = run_en("optimize.py", ws)
    at.button[0].click().run()
    assert not at.exception and korean_left(at) == []
    mix = sample("FondueRecipe.MWX", ["Emmenthaler", "Gruyere", "Broth"], process=["Temperature"])
    at = run_en("optimize.py", mix)
    [b for b in at.button if b.label == "Optimize"][0].click().run()
    assert not at.exception and korean_left(at) == []
    crystal = sample("CrystalGrowth.MWX", ["A", "B", "C", "D"])
    at = run_en("optimal.py", crystal)
    at.button[0].click().run()
    assert not at.exception and korean_left(at) == []


def test_figures_and_reports_in_english():
    from app.i18n import english_of
    from doe_core.analysis.factorial import analyze_worksheet
    from doe_core.plots.lang import to_english
    from doe_core.plots.residual_plots import four_in_one
    from doe_core.report import analysis_report, to_html
    assert english_of("**요인 (Factors)**") == "**Factors**" and english_of("Plain (x)") is None
    ws = sample("InsulationProperties.MWX", ["Material", "InjPress", "InjTemp", "CoolTemp"])
    a = analyze_worksheet(ws, "Strength")
    fig = to_english(four_in_one(a))
    texts = [fig.layout.title.text, fig.layout.title.subtitle.text]
    texts += [x.text for x in fig.layout.annotations] + [fig.layout[k].title.text for k in fig.layout
                                                          if k.startswith(("xaxis", "yaxis")) and fig.layout[k].title.text]
    texts += [t.hovertemplate or "" for t in fig.data]
    assert not any(HANGUL.search(t or "") for t in texts), texts
    html = to_html(analysis_report(ws, a, lang="en"), plotlyjs="cdn")
    body = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    assert "Analysis report — Strength" in body and not HANGUL.search(body)
