"""작업 자동 저장 — 브라우저를 새로 고치거나 닫아도, 서버를 다시 켜도 워크시트를 잃지 않게 한다.

워크시트가 바뀔 때마다 '작업 칸(slot)' 하나에 DOE Studio 워크시트 JSON 을 덮어쓴다. 새 설계를 만들거나 다른 파일을
불러오면 새 칸을 쓰고, 설계 수정(접기·반복·축점 등)과 값 입력은 같은 칸을 이어 쓴다. 가장 최근 KEEP 개만 남긴다.
저장 파일은 보통 워크시트 파일과 같은 형식이라 시작 화면의 파일 불러오기로도 열 수 있다('autosave' 키만 더 있다).
작업 이름은 워크시트의 'name' 키에 들어 있다. 목록에서 이름 바꾸기(rename)·지우기(delete)를 할 수 있다.

위치: 환경 변수 DOE_STUDIO_AUTOSAVE_DIR, 없으면 ~/.doe_studio/autosave.
끄기: DOE_STUDIO_AUTOSAVE=0 (여러 사람이 함께 쓰는 서버에 올릴 때 — 저장 폴더가 컴퓨터 하나에 하나라서다).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .worksheet import Worksheet, clean_name, worksheet_from_dict, worksheet_to_dict

ENV_DIR = "DOE_STUDIO_AUTOSAVE_DIR"
ENV_SWITCH = "DOE_STUDIO_AUTOSAVE"
KEEP = 20
_SLOT = re.compile(r"^[0-9a-f]{8,32}$")


def autosave_dir() -> Path | None:
    """저장 폴더. 자동 저장을 꺼 두었으면 None."""
    if os.environ.get(ENV_SWITCH, "1").strip().lower() in ("0", "off", "false", "no"):
        return None
    d = os.environ.get(ENV_DIR, "").strip()
    return Path(d) if d else Path.home() / ".doe_studio" / "autosave"


def new_slot() -> str:
    return uuid.uuid4().hex[:12]


def fingerprint(ws: Worksheet) -> str:
    """워크시트 내용의 지문 — 바뀌었을 때만 저장하려고 쓴다."""
    text = json.dumps(worksheet_to_dict(ws), ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _path(slot: str) -> Path | None:
    d = autosave_dir()
    if d is None:
        return None
    if not _SLOT.match(slot):
        raise ValueError(f"잘못된 자동 저장 이름: {slot!r}")
    return d / f"{slot}.json"


@dataclass
class AutosaveEntry:
    slot: str
    saved_at: datetime
    design_type: str           # design_to_dict 의 type (two_level, response_surface …)
    factors: list[str]
    n_runs: int
    columns: list[str]         # 비설계 열(반응·공변량)
    name: str = ""              # 사용자가 붙인 작업 이름


def save(slot: str, ws: Worksheet, *, now: datetime | None = None) -> Path | None:
    """워크시트를 slot 칸에 저장(임시 파일에 쓴 뒤 바꿔 넣는다). 꺼져 있으면 None."""
    path = _path(slot)
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = worksheet_to_dict(ws)
    doc["autosave"] = {"slot": slot, "saved_at": (now or datetime.now()).isoformat(timespec="seconds")}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    _prune(path.parent)
    return path


def _prune(d: Path) -> None:
    files = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[KEEP:]:
        try:
            p.unlink()
        except OSError:
            pass


def _entry(path: Path) -> AutosaveEntry:
    doc = json.loads(path.read_text(encoding="utf-8"))
    meta = doc.get("autosave", {})
    design = doc["design"]
    if "factors" in design:
        factors = [f["name"] for f in design["factors"]]
    else:                                            # 혼합물: 성분 + 공정 변수
        factors = [c["name"] for c in design.get("components", [])] + [f["name"] for f in design.get("process", [])]
    cols = [c for c in doc.get("columns", {}) if c != "StdOrder"]
    runs = len(next(iter(doc["coded"].values()), []))
    when = datetime.fromisoformat(meta["saved_at"]) if "saved_at" in meta else datetime.fromtimestamp(path.stat().st_mtime)
    return AutosaveEntry(path.stem, when, design.get("type", "?"), factors, runs, cols, clean_name(doc.get("name")))


def recent(limit: int = 5) -> list[AutosaveEntry]:
    """최근 저장 순서. 읽을 수 없는 파일은 건너뛴다."""
    d = autosave_dir()
    if d is None or not d.is_dir():
        return []
    out = []
    for p in d.glob("*.json"):
        if not _SLOT.match(p.stem):
            continue
        try:
            out.append(_entry(p))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    out.sort(key=lambda e: e.saved_at, reverse=True)
    return out[:limit]


def load(slot: str) -> Worksheet:
    path = _path(slot)
    if path is None:
        raise ValueError("자동 저장이 꺼져 있습니다.")
    return worksheet_from_dict(json.loads(path.read_text(encoding="utf-8")))


def rename(slot: str, name: str) -> str:
    """저장된 작업의 이름을 바꾼다(빈 이름이면 이름을 지운다). 저장 시각은 그대로 둬 목록 순서가 바뀌지 않는다.
    다듬은 이름을 돌려준다."""
    path = _path(slot)
    if path is None:
        raise ValueError("자동 저장이 꺼져 있습니다.")
    doc = json.loads(path.read_text(encoding="utf-8"))
    name = clean_name(name)
    if name:
        doc["name"] = name
    else:
        doc.pop("name", None)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return name


def delete(slot: str) -> None:
    """저장된 작업을 지운다(되살릴 수 없다). 없으면 아무 일도 하지 않는다."""
    path = _path(slot)
    if path is not None and path.exists():
        path.unlink()
