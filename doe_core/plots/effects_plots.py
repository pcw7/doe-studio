"""효과도: Pareto, 정규, 반정규 — Minitab 'Analyze Factorial Design > Graphs > Effects plots'.

- Pareto: |표준화 효과|(또는 |효과|)를 큰 순서로 가로 막대, 기준선(t 또는 ME)에 세로선과 값 라벨.
  막대 라벨은 요인 문자(A, B, AB …). 유의한 효과는 파랑, 나머지는 회색(범례 + 마우스 올림 정보로도 구분).
- 정규·반정규: x = 효과, y = 정규 점수(백분율 눈금). 적합선은 모든 효과가 0 일 때의 기대 위치
  (표준화: 표준편차 1, 비표준화: 표준편차 PSE). 유의한 점만 문자 라벨(모든 점에 라벨을 달지 않음).
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from scipy import stats

from ..analysis.effects import EffectsResult
from .theme import BAR_MAX, KEEP, LINE_W, MARKER, lift_legend, style, tokens

PERCENT_TICKS = [1, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99]


def _sig_label(e: EffectsResult) -> str:
    return f"유의함 (α = {e.alpha:g})"


def pareto_chart(e: EffectsResult, mode: str = "light") -> go.Figure:
    t = tokens(mode)
    p = e.pareto().iloc[::-1]                      # 가로 막대는 아래부터 그리므로 뒤집어 큰 것이 위로
    n = len(p)
    fig = go.Figure()
    for sig, name, color in ((True, _sig_label(e), t["series"][0]), (False, "유의하지 않음", t["muted"])):
        q = p[p["Significant"] == sig]
        if q.empty:
            continue
        fig.add_bar(
            x=q["Value"], y=q["Term"], orientation="h", name=name,
            marker=dict(color=color, cornerradius=4, line=dict(width=0)),
            customdata=np.stack([q["Name"]], axis=-1),
            hovertemplate="%{y} (%{customdata[0]})<br>%{x:.3f}<extra></extra>",
        )
    fig.add_vline(x=e.reference, line=dict(color=t["text2"], width=1.5))
    fig.add_annotation(x=e.reference, y=1, yref="paper", yanchor="bottom", text=f"{e.reference:.3f}",
                       showarrow=False, font=dict(color=t["text2"], size=12), xshift=4, xanchor="left")
    xlabel = "표준화 효과 (Standardized Effect)" if e.standardized else "효과 (Effect)"
    height = max(260, 34 * n + 150)
    style(fig, mode, title="효과의 Pareto 차트" if not e.standardized else "표준화 효과의 Pareto 차트",
          en=e.pareto_title, height=height)
    fig.update_layout(barmode="overlay", bargap=max(0.0, 1 - BAR_MAX / 34))
    if len(fig.data) > 1:
        lift_legend(fig, 22)
    _factor_name_box(fig, e, t)
    fig.update_xaxes(title_text=xlabel, rangemode="tozero")
    fig.update_yaxes(title_text="항 (Term)", categoryorder="array", categoryarray=list(p["Term"]), showgrid=False)
    return fig


def _factor_name_box(fig: go.Figure, e: EffectsResult, t: dict) -> None:
    """Pareto 오른쪽의 요인 문자 → 이름 표(이름이 문자와 다를 때만). 이름은 사용자 글자라 영어로 바꾸지 않는다."""
    one = e.table[e.table["Term"].str.len() == 1]
    pairs = [(L, str(n)) for L, n in zip(one["Term"], one["Name"]) if str(n) != L]
    if not pairs:
        return
    pairs.sort()
    width = min(260, 34 + 8 * max(len(n) for _, n in pairs))
    fig.update_layout(margin=dict(r=(fig.layout.margin.r or 24) + width))
    fig.add_annotation(x=1.02, y=1, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False,
                       align="left", text="요인 (Factor)", font=dict(size=12, color=t["text2"]))
    m = fig.layout.margin
    plot_h = max((fig.layout.height or 450) - (m.t or 0) - (m.b or 0), 60)
    fig.add_annotation(x=1.02, y=1 - 22 / plot_h, xref="paper", yref="paper", xanchor="left", yanchor="top",
                       showarrow=False,
                       align="left", name=KEEP, font=dict(size=12, color=t["text"]),
                       text="<br>".join(f"{L}&nbsp;&nbsp;{n}" for L, n in pairs))


def _prob_axis(fig: go.Figure, half: bool = False, row=None, col=None):
    if half:
        ticks = [10, 20, 30, 50, 70, 80, 90, 95, 98]
        vals = [stats.norm.ppf(0.5 + 0.5 * q / 100) for q in ticks]
    else:
        ticks = PERCENT_TICKS
        vals = [stats.norm.ppf(q / 100) for q in ticks]
    kw = dict(tickmode="array", tickvals=vals, ticktext=[str(q) for q in ticks], title_text="백분율 (Percent)")
    if row is None:
        fig.update_yaxes(**kw)
    else:
        fig.update_yaxes(row=row, col=col, **kw)


def normal_effects_chart(e: EffectsResult, mode: str = "light", half: bool = False) -> go.Figure:
    t = tokens(mode)
    tbl = e.table
    val_col = "Standardized" if e.standardized else "Effect"
    x = tbl[val_col].abs() if half else tbl[val_col]
    y = tbl["Half Normal Score"] if half else tbl["Normal Score"]
    sd = 1.0 if e.standardized else (e.pse or 1.0)
    fig = go.Figure()
    zmax = float(np.max(np.abs(y))) * 1.05
    zs = np.linspace(0 if half else -zmax, zmax, 50)
    fig.add_scatter(x=sd * zs, y=zs, mode="lines", name="효과 0 기준선", line=dict(color=t["text2"], width=1.5),
                    hoverinfo="skip")
    for sig, name, color, symbol in ((True, _sig_label(e), t["series"][0], "square"),
                                     (False, "유의하지 않음", t["muted"], "circle")):
        m = tbl["Significant"] == sig
        if not m.any():
            continue
        fig.add_scatter(
            x=x[m], y=y[m], mode="markers+text" if sig else "markers", name=name,
            text=tbl["Term"][m] if sig else None, textposition="middle right",
            textfont=dict(color=t["text"], size=12),
            marker=dict(color=color, size=MARKER, symbol=symbol, line=dict(color=t["surface"], width=2)),
            customdata=np.stack([tbl["Term"][m], tbl["Name"][m]], axis=-1),
            hovertemplate="%{customdata[0]} (%{customdata[1]})<br>효과 %{x:.3f}<extra></extra>",
        )
    if half:
        title, en = ("표준화 효과의 반정규 확률도", e.half_normal_title) if e.standardized else ("효과의 반정규 확률도", e.half_normal_title)
        xlabel = "|표준화 효과| (Absolute Standardized Effect)" if e.standardized else "|효과| (Absolute Effect)"
    else:
        title, en = ("표준화 효과의 정규 확률도", e.normal_title) if e.standardized else ("효과의 정규 확률도", e.normal_title)
        xlabel = "표준화 효과 (Standardized Effect)" if e.standardized else "효과 (Effect)"
    style(fig, mode, title=title, en=en, height=420)
    fig.update_xaxes(title_text=xlabel)
    _prob_axis(fig, half)
    return fig


def half_normal_effects_chart(e: EffectsResult, mode: str = "light") -> go.Figure:
    return normal_effects_chart(e, mode, half=True)
