"""공통 pytest 설정. 픽스처 읽기 함수는 tests/helpers.py 에 있다."""
import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _autosave_to_temp(tmp_path_factory):
    """화면 테스트가 작업 자동 저장을 사용자 폴더(~/.doe_studio)가 아니라 임시 폴더에 쓰게 한다."""
    old = os.environ.get("DOE_STUDIO_AUTOSAVE_DIR")
    os.environ["DOE_STUDIO_AUTOSAVE_DIR"] = str(tmp_path_factory.mktemp("autosave"))
    yield
    if old is None:
        os.environ.pop("DOE_STUDIO_AUTOSAVE_DIR", None)
    else:
        os.environ["DOE_STUDIO_AUTOSAVE_DIR"] = old
