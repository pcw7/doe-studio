"""화면 다듬기(taste-skill 무채색 장부 규칙, 색은 기존 유지) 검증.

- 글꼴: 내장 Pretendard(OFL)를 정적 파일로 내보내고 테마 글꼴로 쓴다. 강조색은 기존 #2a78d6 그대로.
- 제품 표시: 중앙점이 있는 2x2 요인설계 마크(로고·아이콘 SVG).
- 실험 진행 표시: 런 순서별 결과 입력 상태(다 입력·일부·아직).
- 표 높이: 행 높이를 고정하고 그 행 수로 높이를 계산(글자 크기를 바꿔도 표 아래 빈 줄이 없게).
"""
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from app.state import ROW_HEIGHT, run_states, table_height
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet

ROOT = Path(__file__).resolve().parents[1]


def test_theme_font_and_colour():
    cfg = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert cfg["server"]["enableStaticServing"] is True
    theme = cfg["theme"]
    assert theme["primaryColor"] == "#2a78d6"                        # 색은 기존 그대로
    assert theme["font"].startswith("Pretendard")
    assert theme["baseFontSize"] >= 15 and theme["headingFontSizes"][0] == "24px"
    [face] = theme["fontFaces"]
    assert face["family"] == "Pretendard"
    font = ROOT / face["url"]                                        # app/static/fonts/… (정적 파일 주소 = 경로)
    assert font.exists() and font.read_bytes()[:4] == b"wOF2"
    assert (font.parent / "Pretendard-OFL.txt").read_text(encoding="utf-8").count("SIL Open Font License") >= 1


def test_logo_marks_are_svg():
    for name in ("logo.svg", "mark.svg"):
        root = ET.parse(ROOT / "app" / "assets" / name).getroot()
        assert root.tag.endswith("svg") and root.get("aria-label") == "DOE Studio"
        circles = [e for e in root.iter() if e.tag.endswith("circle")]
        assert len(circles) == 5                                     # 네 모서리점 + 중앙점


def test_run_states():
    ws = Worksheet(create_two_level_design(2, 4, center_points=2, seed=3))
    assert set(run_states(ws)["state"]) == {"none"}                  # 반응 열이 없으면 모두 '아직'
    ws.add_column("수율", [50.0, np.nan, 52.0, np.nan, 49.0, 51.0])
    ws.add_column("순도", [99.0, 98.0, np.nan, np.nan, 97.0, 96.0])
    r = run_states(ws)
    assert list(r["RunOrder"]) == sorted(r["RunOrder"])
    assert list(r["state"]) == ["done", "part", "part", "none", "done", "done"]


def test_table_height_matches_rows():
    assert table_height(0) == ROW_HEIGHT + 1
    assert table_height(10) - table_height(9) == ROW_HEIGHT
