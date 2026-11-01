"""워크시트 화면 편의 기능(실사용 점검 ④).

- 열 이름 바꾸기·삭제(설계 열·중복·빈 이름 거부), 분석·기억한 모형은 버림.
- 축점 추가 전 실제 값 미리보기(기본 α = F^¼ = 8^¼ → 온도 53.18~86.82, 면 중심 α = 1 → 60~80).
- 설계 수정 뒤 무엇이 바뀌었는지 안내(런 수 변화, 새 런의 빈 반응 칸).
"""
import numpy as np
import pytest

from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.response_surface import add_axial_points, axial_alpha, axial_preview
from doe_core.io.worksheet import Worksheet
from tests.test_app import run


def _ws():
    fac = [Factor("온도", 60, 80), Factor("시간", 1, 3), Factor("촉매", 0.5, 1.5)]
    ws = Worksheet(create_two_level_design(3, 8, factors=fac, center_points=3, seed=2))
    ws.add_column("수율", np.linspace(50, 80, 11))
    return ws


def test_rename_and_drop_column():
    ws = _ws()
    ws.add_column("순도", [99.0] * 11)
    ws.rename_column("수율", " 수율(%) ")
    assert list(ws.columns.columns) == ["수율(%)", "순도"]
    assert ws.column("수율(%)").notna().all()
    for bad in ("순도", "온도", "StdOrder", "  "):
        with pytest.raises(ValueError):
            ws.rename_column("수율(%)", bad)
    with pytest.raises(ValueError):
        ws.rename_column("없는열", "x")
    ws.drop_column("순도")
    assert list(ws.columns.columns) == ["수율(%)"]
    with pytest.raises(ValueError):
        ws.drop_column("순도")


def test_axial_preview_values():
    d = _ws().design
    assert axial_alpha(d) == pytest.approx(8 ** 0.25)
    p = axial_preview(d).set_index("Factor")
    assert p.loc["온도", "−α"] == pytest.approx(70 - 10 * 8 ** 0.25)
    assert p.loc["온도", "+α"] == pytest.approx(86.8179, abs=1e-4)
    assert p.loc["촉매", "−α"] == pytest.approx(0.1591, abs=1e-4)
    f = axial_preview(d, "face").set_index("Factor")
    assert (f["−α"] == f["Low"]).all() and (f["+α"] == f["High"]).all()
    assert axial_alpha(d, 1.2) == 1.2
    # add_axial_points 가 같은 α 를 쓰는지
    rs = add_axial_points(d)
    ax = rs.coded[rs.coded[rs.point_col] == -1]
    assert ax["A"].abs().max() == pytest.approx(8 ** 0.25)


def test_axial_points_notice_and_preview_on_page():
    at = run("worksheet.py", _ws())
    assert not at.exception
    assert any("−α" in df.value.columns for df in at.dataframe)          # 축점 미리보기 표
    [b] = [b for b in at.button if b.label == "축점 추가"]
    b.click().run()
    assert not at.exception
    assert at.session_state["worksheet"].design.n_runs == 17
    msg = " ".join(s.value for s in at.success)
    assert "축점 6개" in msg and "런 11개 → 17개" in msg and "비어 있으니" in msg
    at.run()
    assert not any("축점 6개" in s.value for s in at.success)              # 안내는 한 번만


def test_rename_and_delete_on_page():
    ws = _ws()
    at = run("worksheet.py", ws)
    [t] = [t for t in at.text_input if t.label == "새 이름"]
    t.input("수율(%)").run()
    [b] = [b for b in at.button if b.label == "이름 바꾸기"]
    b.click().run()
    assert not at.exception
    assert list(at.session_state["worksheet"].columns.columns) == ["수율(%)"]
    assert any("이름을 '수율(%)' 로 바꿨습니다" in s.value for s in at.success)
    [d] = [b for b in at.button if b.label == "열 삭제"]
    assert d.disabled                                                     # 확인 전에는 못 지움
    [c] = [c for c in at.checkbox if c.label == "삭제 확인"]
    c.check().run()
    [d] = [b for b in at.button if b.label == "열 삭제"]
    d.click().run()
    assert not at.exception
    assert list(at.session_state["worksheet"].columns.columns) == []
