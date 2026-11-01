"""검정력 곡선 — Minitab 'Power Curve for …'(효과 크기 대 검정력, 반복·중앙점 조합마다 곡선, 계산한 점에 기호)."""
from __future__ import annotations

import plotly.graph_objects as go

from ..power import PowerResult, power_curve_data
from .theme import LINE_W, MARKER, style, tokens

KIND_EN = {"two_level": "2-Level Factorial Design", "pb": "Plackett-Burman Design", "gff": "General Full Factorial Design"}


def power_curve(res: PowerResult, mode: str = "light") -> go.Figure:
    t = tokens(mode)
    colors = t["series"]
    fig = go.Figure()
    curves = power_curve_data(res)
    color_of = {}
    for i, (name, xs, ys) in enumerate(curves[:8]):
        c = colors[i % len(colors)]
        color_of[name] = c
        fig.add_scatter(x=xs, y=ys, mode="lines", name=name, line=dict(color=c, width=LINE_W),
                        hovertemplate=f"{name}<br>효과 %{{x:.4g}}<br>검정력 %{{y:.3f}}<extra></extra>")
    for e, p, name in res.points:
        fig.add_scatter(x=[e], y=[p], mode="markers", showlegend=False,
                        marker=dict(size=MARKER, color=color_of.get(name, colors[0]), line=dict(color=t["surface"], width=2)),
                        hovertemplate=f"{name}<br>효과 %{{x:.4g}}<br>검정력 %{{y:.4f}}<extra></extra>")
    eff = "최대 차이" if res.kind == "gff" else "효과"
    eff_en = "Maximum Difference" if res.kind == "gff" else "Effect"
    legend = "반복" if res.kind == "gff" else "반복, 중앙점"
    style(fig, mode, title="검정력 곡선", en=f"Power Curve for {KIND_EN[res.kind]} · {legend}", height=420)
    fig.update_xaxes(title_text=f"{eff} ({eff_en})", rangemode="tozero")
    fig.update_yaxes(title_text="검정력 (Power)", range=[0, 1.02])
    return fig
