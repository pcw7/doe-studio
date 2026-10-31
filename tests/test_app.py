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
