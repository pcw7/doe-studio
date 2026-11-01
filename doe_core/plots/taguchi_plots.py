"""Taguchi 그래프 — Minitab 'Main Effects Plot for SN ratios / Means'(수준별 특성값 평균, 전체 평균 가로선)."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..analysis.taguchi import CHARACTERISTICS, SN_TYPES, _val
from .theme import LINE_W, MARKER, style, tokens

KO = {"sn": "S/N 비", "mean": "평균", "std": "표준편차", "lnstd": "ln(표준편차)"}


def taguchi_main_effects_plot(a, mode: str = "light") -> go.Figure:
    """a: TaguchiAnalysis. 요인마다 수준 평균을 선으로, 전체 평균을 가는 가로선으로."""
    t = tokens(mode)
    d = a.design
    coded = d.coded.reset_index(drop=True)
    fig = make_subplots(rows=1, cols=len(d.factors), shared_yaxes=True, horizontal_spacing=0.04,
                        subplot_titles=[f.name for f in d.factors])
    grand = float(np.mean(a.y))
    for i, (L, f) in enumerate(zip(d.letters, d.factors), start=1):
        levels = [_val(v) for v in f.levels]
        means = [float(np.mean(a.y[coded[L].values == k + 1])) for k in range(len(f.levels))]
        fig.add_scatter(x=levels, y=means, mode="lines+markers", showlegend=False,
                        line=dict(color=t["series"][0], width=LINE_W),
                        marker=dict(color=t["series"][0], size=MARKER, line=dict(color=t["surface"], width=2)),
                        hovertemplate=f"{f.name} = %{{x}}<br>평균 %{{y:.4g}}<extra></extra>", row=1, col=i)
        fig.add_hline(y=grand, line=dict(color=t["text2"], width=1, dash="dot"), row=1, col=i)
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=levels, showgrid=False, row=1, col=i)
    en = f"Main Effects Plot for {CHARACTERISTICS[a.characteristic]}"
    if a.characteristic == "sn" and a.sn_type:
        en += f" · Signal-to-noise: {SN_TYPES[a.sn_type]}"
    style(fig, mode, title=f"{KO[a.characteristic]} 주효과도", en=en, height=380, showlegend=False)
    for ann in fig.layout.annotations:
        ann.font = dict(size=12, color=t["text2"])
    fig.update_yaxes(title_text=f"{KO[a.characteristic]} 평균 (Mean of {CHARACTERISTICS[a.characteristic]})",
                     row=1, col=1)
    return fig
