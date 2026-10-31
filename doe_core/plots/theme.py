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
