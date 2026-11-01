"""작업 이름 붙이기·이름 바꾸기·지우기와 내려받는 파일 이름 검증.

- 엔진: 워크시트 이름 다듬기(공백·길이)·저장 왕복(이름 없으면 'name' 키 없음)·설계 수정 뒤에도 유지,
  파일 이름에서 Windows 금지 글자 바꾸기, 자동 저장 이름 바꾸기(저장 시각·순서 그대로)·지우기.
- 화면: 시작 화면 목록의 '이름' → 입력 → 저장, '지우기' → 확인 → 지움(취소하면 그대로),
  워크시트 화면의 '작업 이름' 이 설명 줄·자동 저장·내려받는 파일 이름(.json·.csv·.xlsx)에 반영.
"""
from datetime import datetime, timedelta

import numpy as np
import pytest
from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage

from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.modify import replicate_design
from doe_core.io import autosave
from doe_core.io.worksheet import NAME_MAX, Worksheet, file_stem, worksheet_from_dict, worksheet_to_dict
from tests.test_app import run


@pytest.fixture
def folder(tmp_path, monkeypatch):
    d = tmp_path / "autosave"
    monkeypatch.setenv(autosave.ENV_DIR, str(d))
    monkeypatch.delenv(autosave.ENV_SWITCH, raising=False)
    return d


@pytest.fixture
def file_names(monkeypatch):
    """화면이 내려받기 버튼에 넘긴 파일 이름들."""
    names = []
    orig = MemoryMediaFileStorage.load_and_get_id

    def spy(self, path_or_data, mimetype, kind, filename=None):
        names.append(filename)
        return orig(self, path_or_data, mimetype, kind, filename)

    monkeypatch.setattr(MemoryMediaFileStorage, "load_and_get_id", spy)
    return names


def _ws(seed=1, name=""):
    ws = Worksheet(create_two_level_design(3, 8, center_points=3, seed=seed), name=name)
    ws.add_column("수율", np.arange(11) + 50.5)
    return ws


def test_worksheet_name_roundtrip():
    ws = _ws(name="  촉매   선별\n 1차 ")
    assert ws.name == "촉매 선별 1차"
    doc = worksheet_to_dict(ws)
    assert doc["name"] == "촉매 선별 1차"
    assert worksheet_from_dict(doc).name == "촉매 선별 1차"
    assert "name" not in worksheet_to_dict(_ws())                     # 이름 없는 파일은 예전 형식 그대로
    assert worksheet_from_dict(worksheet_to_dict(_ws())).name == ""
    assert ws.with_design(replicate_design(ws.design, 2)).name == "촉매 선별 1차"   # 설계 수정 뒤에도 유지
    assert len(Worksheet(ws.design, name="가" * 100).name) == NAME_MAX
    named = _ws(name="A")
    assert autosave.fingerprint(named) != autosave.fingerprint(_ws())  # 이름만 바꿔도 자동 저장된다


def test_file_stem():
    assert file_stem("용해도(g/L)_분석보고서", "x") == "용해도(g_L)_분석보고서"
    assert file_stem('a:b*?"<>|c.', "x") == "a_b_c"
    assert file_stem("촉매 선별 1차", "x") == "촉매 선별 1차"
    assert file_stem("  ", "doe_worksheet") == "doe_worksheet"
    assert file_stem("...", "doe") == "doe"
    assert len(file_stem("가" * 300, "x")) == 120


def test_rename_and_delete(folder):
    t0 = datetime(2026, 11, 1, 9, 0, 0)
    s1, s2 = autosave.new_slot(), autosave.new_slot()
    autosave.save(s1, _ws(1), now=t0)
    autosave.save(s2, _ws(2), now=t0 + timedelta(minutes=5))
    assert autosave.rename(s1, "  오래된   작업 ") == "오래된 작업"
    e2, e1 = autosave.recent()
    assert (e1.slot, e1.name, e1.saved_at) == (s1, "오래된 작업", t0)  # 저장 시각·순서는 그대로
    assert (e2.slot, e2.name) == (s2, "")
    assert autosave.load(s1).name == "오래된 작업"                   # 되살리면 이름도 따라온다
    assert autosave.rename(s1, "   ") == ""                         # 빈 이름 = 이름 지우기
    assert autosave.recent()[1].name == ""
    autosave.delete(s1)
    assert [e.slot for e in autosave.recent()] == [s2]
    autosave.delete(s1)                                             # 없는 칸 지우기는 조용히 넘어간다
    with pytest.raises(ValueError):
        autosave.rename("../evil", "x")


def _buttons(at, label):
    return [b for b in at.button if b.label == label]


def test_home_list_rename_and_delete(folder):
    t0 = datetime.now() - timedelta(hours=1)
    old, new = autosave.new_slot(), autosave.new_slot()
    autosave.save(old, _ws(1), now=t0)
    autosave.save(new, _ws(2), now=t0 + timedelta(minutes=5))
    at = run("home.py")
    assert not at.exception
    assert len(_buttons(at, "이어서 하기")) == len(_buttons(at, "이름")) == len(_buttons(at, "지우기")) == 2

    # 이름: 두 번째 줄(더 오래된 작업)에 이름을 붙인다
    at.button(key=f"as_name_{old}").click().run()
    assert not at.exception
    at.text_input(key=f"as_name_in_{old}").input("촉매 선별 1차").run()
    at.button(key=f"as_name_ok_{old}").click().run()
    assert not at.exception
    assert {e.slot: e.name for e in autosave.recent()} == {old: "촉매 선별 1차", new: ""}
    assert any("**촉매 선별 1차**" in m.value for m in at.markdown)
    assert any("이름을 '촉매 선별 1차'(으)로 바꿨습니다." in t.value for t in at.toast)
    assert not [w for w in at.text_input if w.key == f"as_name_in_{old}"]   # 입력 칸은 닫힌다

    # 이름 바꾸기 취소: 그대로
    at.button(key=f"as_name_{old}").click().run()
    at.text_input(key=f"as_name_in_{old}").input("바뀌면 안 됨").run()
    at.button(key=f"as_name_no_{old}").click().run()
    assert autosave.recent()[1].name == "촉매 선별 1차"

    # 지우기: 확인 전에는 지우지 않고, 취소하면 그대로, 확인하면 지운다
    at.button(key=f"as_del_{new}").click().run()
    assert not at.exception
    assert any("지우면 되살릴 수 없습니다" in w.value for w in at.warning)
    assert len(autosave.recent()) == 2
    at.button(key=f"as_del_no_{new}").click().run()
    assert len(autosave.recent()) == 2 and not at.warning
    at.button(key=f"as_del_{new}").click().run()
    at.button(key=f"as_del_ok_{new}").click().run()
    assert not at.exception
    assert [e.slot for e in autosave.recent()] == [old]
    assert len(_buttons(at, "이어서 하기")) == 1


def test_worksheet_name_input(folder, file_names):
    at = run("worksheet.py", _ws())
    assert not at.exception
    assert file_names[-3:] == ["doe_worksheet.json", "doe_worksheet.csv", "doe_worksheet.xlsx"]
    [box] = [w for w in at.text_input if (w.key or "").startswith("ws_name_")]
    box.input("  촉매 A/B  ").run()
    assert not at.exception
    assert at.session_state["worksheet"].name == "촉매 A/B"
    assert at.caption[0].value.startswith("**촉매 A/B** · 2수준 요인설계")
    assert file_names[-3:] == ["촉매 A_B.json", "촉매 A_B.csv", "촉매 A_B.xlsx"]
    assert autosave.recent()[0].name == "촉매 A/B"                   # 이름도 자동 저장된다
    # 시작 화면의 현재 워크시트 줄에도 이름
    at.switch_page("views/home.py").run()
    assert any("**촉매 A/B**" in s.value for s in at.success)


def test_home_list_english(folder):
    from tests.test_app_english import korean_left, run_en
    ws = Worksheet(create_two_level_design(3, 8, center_points=3, seed=1), name="Batch A")
    ws.add_column("Yield", np.arange(11) + 50.5)
    slot = autosave.new_slot()
    autosave.save(slot, ws)
    at = run_en("home.py")
    assert any("**Batch A**" in m.value for m in at.markdown)
    assert [b.label for b in at.button if b.key and b.key.endswith(slot)] == ["Continue", "Name", "Delete"]
    at.button(key=f"as_name_{slot}").click().run()
    assert not korean_left(at), korean_left(at)
    at.button(key=f"as_name_no_{slot}").click().run()
    at.button(key=f"as_del_{slot}").click().run()
    assert not at.exception
    assert not korean_left(at), korean_left(at)
