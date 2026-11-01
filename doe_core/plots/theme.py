"""그래프 테마 — 시각화 지침의 기준 팔레트(검증 통과)와 표시 요소 규격.

- 범주 색은 고정 순서(파랑 → 주황 → 청록 → 노랑)로만 배정하고 순위로 다시 칠하지 않는다.
  라이트 2색·4색, 다크 2색 조합은 validate_palette.js 로 통과 확인(4색은 노랑·청록이 3:1 미만이라 직접 라벨 병행).
- 다크 모드는 같은 색상의 다크용 단계로 따로 정한다(자동 반전 아님).
- 막대 ≤ 24px·끝 4px 둥글게, 선 2px, 점 ≥ 8px, 격자는 1px 실선의 옅은 회색, 이중 y축 없음.
- 글자는 데이터 색을 쓰지 않고 본문/보조 글자 색만 쓴다.
"""
from __future__ import annotations

import plotly.graph_objects as go

FONT = "Pretendard, 'Noto Sans KR', 'Malgun Gothic', system-ui, sans-serif"

LIGHT = {
    "surface": "#fcfcfb", "text": "#0b0b0b", "text2": "#52514e", "grid": "#e8e7e3", "axis": "#c9c8c2",
    "muted": "#b4b3ad", "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"],
}
DARK = {
    "surface": "#1a1a19", "text": "#f0efec", "text2": "#c3c2b7", "grid": "#2f2f2d", "axis": "#4a4a46",
    "muted": "#5c5b57", "series": ["#3987e5", "#d95926", "#199e70", "#c98500"],
}

LINE_W = 2
MARKER = 9
BAR_MAX = 24


KEEP = "keep"          # 이 이름의 주석은 사용자 글자(요인 이름 등)라 영어 전환에서 바꾸지 않는다


def subtitle(*parts: str) -> str:
    """부제 조각을 ' · ' 로 잇는다. 빈 조각(고정값이 없을 때 등)은 빼서 끝에 ' ·' 가 남지 않게 한다."""
    return " · ".join(p for p in parts if p)


OVERLAY_ALL = "표시 범위 전체가 모든 반응의 범위 안입니다<br>하한·상한을 좁히면 경계선이 보입니다"
OVERLAY_NONE = "표시 범위에 모든 반응을 함께 만족하는 곳이 없습니다<br>범위를 넓히거나 다른 요인 값을 바꿔 보세요"


def overlay_note(fig: go.Figure, ok, inside, t: dict) -> go.Figure:
    """중첩 등고선도에서 경계선이 하나도 없을 때(표시 범위 전체가 만족 / 아무 데도 만족하지 않음) 그림 가운데 안내.

    기본 하한·상한이 데이터 최솟값·최댓값이면 보통 범위 전체가 만족해 빈 그림처럼 보이기 때문이다.
    ok: 모든 반응이 범위 안인 격자점, inside: 그릴 수 있는 격자점(혼합물은 삼각형 안).
    """
    import numpy as np
    ok, inside = np.asarray(ok, bool), np.asarray(inside, bool)
    if not inside.any():
        return fig
    if ok[inside].all():
        text = OVERLAY_ALL
    elif not ok[inside].any():
        text = OVERLAY_NONE
    else:
        return fig
    fig.add_annotation(x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, text=text, align="center",
                       font=dict(size=13, color=t["text"]), bgcolor=t["surface"], bordercolor=t["axis"],
                       borderwidth=1, borderpad=8)
    return fig


def lift_legend(fig: go.Figure, px: int) -> go.Figure:
    """범례를 그림 영역 위로 px 픽셀 더 올리고 위 여백을 늘린다(그림 바로 위의 기준선 값·소제목과 겹치지 않게)."""
    m = fig.layout.margin
    top, bottom = (m.t or 0) + px, (m.b or 0)
    plot_h = max((fig.layout.height or 450) - top - bottom, 60)
    fig.update_layout(margin=dict(t=top), legend=dict(y=1.02 + px / plot_h))
    return fig


def tokens(mode: str = "light") -> dict:
    return DARK if mode == "dark" else LIGHT


def title_text(ko: str, en: str | None = None) -> str:
    return ko if not en else f"{ko}<br><span style='font-size:12px'>{en}</span>"


def style(fig: go.Figure, mode: str = "light", *, title: str | None = None, en: str | None = None,
          height: int | None = None, showlegend: bool | None = None) -> go.Figure:
    t = tokens(mode)
    fig.update_layout(
        template="none",
        paper_bgcolor=t["surface"], plot_bgcolor=t["surface"],
        font=dict(family=FONT, size=13, color=t["text"]),
        title=dict(text=title, x=0.01, xanchor="left", xref="container", automargin=True, pad=dict(t=6),
                   font=dict(size=16, color=t["text"]),
                   subtitle=dict(text=en or "", font=dict(size=12, color=t["text2"]))) if title else None,
        margin=dict(l=64, r=24, t=(112 if showlegend is not False else 84) if title else 24, b=56),
        hoverlabel=dict(bgcolor=t["surface"], bordercolor=t["axis"], font=dict(family=FONT, color=t["text"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, xanchor="left", font=dict(color=t["text2"]),
                    bgcolor="rgba(0,0,0,0)"),
    )
    if height:
        fig.update_layout(height=height)
    if showlegend is not None:
        fig.update_layout(showlegend=showlegend)
    axis = dict(showgrid=True, gridcolor=t["grid"], gridwidth=1, griddash="solid", zeroline=False,
                linecolor=t["axis"], linewidth=1, showline=True, ticks="outside", tickcolor=t["axis"],
                tickfont=dict(color=t["text2"]), title_font=dict(color=t["text2"]))
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    return fig
