"""그래프 부제·중첩 등고선 안내 검증(README 화면 캡처 중 발견).

- 고정값이 없을 때(요인 2개 등고선, 공정 변수 없는 3성분 혼합물) 부제 끝에 ' ·' 가 남지 않는다.
- 중첩 등고선도: 기본 하한(데이터 최솟값)처럼 표시 범위 전체가 만족하면 경계선이 없어 빈 그림처럼 보였다
  → 그림 가운데 안내. 아무 데도 만족하지 않을 때도 안내. 일부만 만족하면 안내 없음. 영어 전환도.
"""
import numpy as np
import pytest

from doe_core.analysis.factorial import analyze_worksheet
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.examples import reaction_optimization, solvent_blend
from doe_core.io.worksheet import Worksheet
from doe_core.plots.contour_plots import contour_plot, overlaid_contour_plot, surface_plot
from doe_core.plots.lang import to_english
from doe_core.plots.mixture_plots import mixture_contour_plot, mixture_overlaid_contour_plot, mixture_surface_plot
from doe_core.plots.theme import OVERLAY_ALL, OVERLAY_NONE, subtitle


def _sub(fig) -> str:
    return fig.layout.title.subtitle.text


def test_subtitle_joins_without_trailing_dot():
    assert subtitle("A", "", "B") == "A · B"
    assert subtitle("Contour Plot of Y", "") == "Contour Plot of Y"
    d = create_two_level_design(2, 4, factors=[Factor("온도", 60, 80), Factor("시간", 1, 3)], center_points=2, seed=1)
    ws = Worksheet(d)
    c = d.coded.sort_values("StdOrder")
    ws.add_column("Y", (70 + 3 * c["A"] + 2 * c["B"] + c["A"] * c["B"]).values + np.arange(len(c)) * 0.01, order="std")
    a = analyze_worksheet(ws, "Y", order=2, include_center=False)
    for fig in (contour_plot(a, "A", "B"), surface_plot(a, "A", "B")):
        assert not _sub(fig).rstrip().endswith("·")
    mix = solvent_blend()
    m = analyze_worksheet(mix, "용해도(g/L)")
    for fig in (mixture_contour_plot(m), mixture_surface_plot(m)):
        assert not _sub(fig).rstrip().endswith("·"), _sub(fig)


def _notes(fig):
    return [a.text for a in fig.layout.annotations if a.text in (OVERLAY_ALL, OVERLAY_NONE)]


@pytest.fixture(scope="module")
def rs_models():
    ws = reaction_optimization()
    return [analyze_worksheet(ws, c) for c in ws.columns.columns]


def test_overlaid_contour_note(rs_models):
    wide = {a.response: (float(np.min(a.y)), np.inf) for a in rs_models}          # 기본값: 데이터 최솟값 이상
    assert _notes(overlaid_contour_plot(rs_models, wide, "A", "B")) == [OVERLAY_ALL]
    part = {"수율(%)": (74.0, np.inf), "순도(%)": (97.5, np.inf)}                  # README 그림 조건: 일부만 만족
    assert _notes(overlaid_contour_plot(rs_models, part, "A", "B")) == []
    none = {"수율(%)": (200.0, np.inf), "순도(%)": (97.5, np.inf)}
    fig = overlaid_contour_plot(rs_models, none, "A", "B")
    assert _notes(fig) == [OVERLAY_NONE]
    en = to_english(fig)
    assert any("No point in the plotted region satisfies every response" in a.text for a in en.layout.annotations)
    assert not any("표시 범위" in a.text for a in en.layout.annotations)


def test_mixture_overlaid_contour_note():
    mix = solvent_blend()
    m = analyze_worksheet(mix, "용해도(g/L)")
    lo = float(np.min(m.y))
    assert _notes(mixture_overlaid_contour_plot([m], {m.response: (lo - 5, np.inf)})) == [OVERLAY_ALL]
    assert _notes(mixture_overlaid_contour_plot([m], {m.response: (30.0, np.inf)})) == []
    assert _notes(mixture_overlaid_contour_plot([m], {m.response: (500.0, np.inf)})) == [OVERLAY_NONE]
