"""공통 pytest 픽스처.

tests/fixtures/minitab_docs/*.json 은 Minitab 공식 문서의 예제 페이지에서 자동 추출한 출력표다.
각 JSON: {url, title, steps, tables:[{heading, header, rows}], notes}
"""
import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "minitab_docs"


def load_fixture(name_fragment: str) -> dict:
    """파일명에 name_fragment 가 들어간 픽스처 하나를 읽는다. 여러 개면 오류."""
    hits = sorted(p for p in FIXTURE_DIR.glob("*.json") if name_fragment in p.name)
    if len(hits) != 1:
        raise FileNotFoundError(f"{name_fragment!r} 에 해당하는 픽스처가 {len(hits)}개: {hits}")
    return json.loads(hits[0].read_text(encoding="utf-8"))


def table(fx: dict, heading_fragment: str) -> dict:
    """픽스처에서 제목에 heading_fragment 가 들어간 표 하나를 돌려준다."""
    hits = [t for t in fx["tables"] if heading_fragment in t["heading"]]
    if len(hits) != 1:
        raise KeyError(f"{heading_fragment!r} 표가 {len(hits)}개: {[t['heading'] for t in fx['tables']]}")
    return hits[0]


@pytest.fixture
def minitab_fixture():
    return load_fixture
