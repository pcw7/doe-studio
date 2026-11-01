"""작업 자동 저장 검증.

- 엔진: 저장 → 목록(최근 순·개수 제한) → 불러오기 왕복(설계·반응 열), 오래된 칸 정리(KEEP), 끄기(환경 변수), 잘못된 이름 거부,
  깨진 파일은 목록에서 건너뜀.
- 화면: 값을 넣은 세션이 끝나도(새로 고침 = 새 세션) 시작 화면에서 '이어서 하기' 로 같은 워크시트를 되살린다.
  새 설계는 새 칸, 설계 수정(축점 추가)은 같은 칸을 이어 쓴다.
"""
from datetime import datetime, timedelta

import numpy as np
import pytest

from doe_core.designs.factorial import create_two_level_design
from doe_core.io import autosave
from doe_core.io.worksheet import Worksheet
from tests.test_app import run


@pytest.fixture
def folder(tmp_path, monkeypatch):
    d = tmp_path / "autosave"
    monkeypatch.setenv(autosave.ENV_DIR, str(d))
    monkeypatch.delenv(autosave.ENV_SWITCH, raising=False)
    return d


def _ws(seed=1, y=True):
    ws = Worksheet(create_two_level_design(3, 8, center_points=3, seed=seed))
    if y:
        ws.add_column("수율", np.arange(11) + 50.5)
    return ws


def test_save_load_roundtrip(folder):
    ws = _ws()
    slot = autosave.new_slot()
    p = autosave.save(slot, ws)
    assert p == folder / f"{slot}.json" and p.exists()
    back = autosave.load(slot)
    assert back.table("run").equals(ws.table("run"))
    [e] = autosave.recent()
    assert (e.slot, e.design_type, e.n_runs, e.columns, e.factors) == (slot, "two_level", 11, ["수율"], ["A", "B", "C"])
    assert autosave.fingerprint(back) == autosave.fingerprint(ws)
    ws.add_column("순도", [1.0] * 11)
    assert autosave.fingerprint(ws) != autosave.fingerprint(back)


def test_recent_order_limit_and_prune(folder, monkeypatch):
    t0 = datetime(2026, 11, 1, 9, 0, 0)
    slots = [autosave.new_slot() for _ in range(6)]
    for i, s in enumerate(slots):
        autosave.save(s, _ws(seed=i + 1), now=t0 + timedelta(minutes=i))
    assert [e.slot for e in autosave.recent(3)] == slots[::-1][:3]
    monkeypatch.setattr(autosave, "KEEP", 4)
    autosave.save(slots[0], _ws(), now=t0 + timedelta(hours=1))      # 가장 최근으로 바뀌고 오래된 둘이 지워진다
    assert len(list(folder.glob("*.json"))) == 4
    assert autosave.recent(1)[0].slot == slots[0]
    (folder / "0123456789ab.json").write_text("{깨진 파일", encoding="utf-8")
    assert len(autosave.recent(10)) == 4


def test_switch_off_and_bad_slot(folder, monkeypatch):
    with pytest.raises(ValueError):
        autosave.save("../evil", _ws())
    monkeypatch.setenv(autosave.ENV_SWITCH, "0")
    assert autosave.autosave_dir() is None
    assert autosave.save(autosave.new_slot(), _ws()) is None
    assert autosave.recent() == []


def test_app_restores_after_reload(folder):
    ws = _ws()
    at = run("worksheet.py", ws)
    assert not at.exception
    [e] = autosave.recent()
    assert e.columns == ["수율"]
    first = e.slot
    # 축점 추가(설계 수정)는 같은 칸을 이어 쓴다
    at.session_state["worksheet"].add_column("순도", [99.0] * 11)
    at.run()
    assert [x.slot for x in autosave.recent()] == [first]
    assert autosave.recent()[0].columns == ["수율", "순도"]

    # 새로 고침 = 새 세션: 시작 화면에 '이어서 하기' 가 보이고 누르면 같은 워크시트
    at2 = run("home.py")
    assert not at2.exception
    btn = [b for b in at2.button if b.label.startswith("이어서 하기")]
    assert len(btn) == 1
    btn[0].click().run()
    assert not at2.exception
    back = at2.session_state["worksheet"]
    assert back.table("run").equals(at.session_state["worksheet"].table("run"))
    assert at2.session_state["autosave_slot"] == first


def test_new_design_gets_new_slot_modify_keeps_it(folder):
    at = run("create.py")
    at.button[0].click().run()                       # 새 설계
    assert not at.exception
    s1 = at.session_state["autosave_slot"]
    at.switch_page("views/worksheet.py").run()
    [axial] = [b for b in at.button if b.label == "축점 추가"]
    axial.click().run()                              # 설계 수정 → 같은 칸
    assert not at.exception
    assert at.session_state["autosave_slot"] == s1
    assert autosave.recent()[0].design_type == "response_surface"
    at.switch_page("views/create.py").run()
    at.button[0].click().run()                       # 다시 설계 생성 → 새 칸
    assert at.session_state["autosave_slot"] != s1
    assert len(autosave.recent(10)) == 2
