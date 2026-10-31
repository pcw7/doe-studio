"""잔차 그림 — Minitab 'Graphs > Residual plots'(Four in one: 정규 확률도, 적합치 대비, 히스토그램, 관측 순서 대비).

잔차 종류: regular(일반) / standardized(표준화) / deleted(삭제). 정규 점수는 Blom 위치.
관측 순서는 워크시트 행 번호(Obs).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from ..analysis.diagnostics import diagnostics
from .effects_plots import _prob_axis
from .theme import LINE_W, MARKER, style, tokens

KINDS = {"regular": ("Resid", "잔차 (Residual)"), "standardized": ("Std Resid", "표준화 잔차 (Standardized Residual)"),
         "deleted": ("Del Resid", "삭제 잔차 (Deleted Residual)")}


def residual_data(a, kind: str = "regular") -> pd.DataFrame:
    if kind not in KINDS:
        raise ValueError(f"잔차 종류는 {list(KINDS)} 중 하나여야 합니다.")
    d = diagnostics(a)
    col = KINDS[kind][0]
    r = d[col].values
    m = len(r)
    pos = (np.arange(1, m + 1) - 3 / 8) / (m + 1 / 4)
    order = np.argsort(r, kind="stable")
    ns = np.empty(m)
    ns[order] = stats.norm.ppf(pos)
    return pd.DataFrame({"Obs": d["Obs"].values, "Fit": d["Fit"].values, "Residual": r, "Normal Score": ns})


def four_in_one(a, kind: str = "regular", mode: str = "light") -> go.Figure:
    t = tokens(mode)
    rd = residual_data(a, kind)
    label = KINDS[kind][1]
    fig = make_subplots(rows=2, cols=2, horizontal_spacing=0.12, vertical_spacing=0.18,
                        subplot_titles=("정규 확률도 (Normal Probability Plot)", "적합치 대비 (Versus Fits)",
                                        "히스토그램 (Histogram)", "관측 순서 대비 (Versus Order)"))
    pt = dict(color=t["series"][0], size=MARKER - 1, line=dict(color=t["surface"], width=2))
    hov = "관측치 %{customdata}<br>잔차 %{y:.4g}<extra></extra>"
    r = rd["Residual"].values
    fin = np.isfinite(r)
    # 1) 정규 확률도: x = 잔차, y = 정규 점수, 기준선 = 평균·표준편차의 정규분포
    if fin.sum() >= 2:
        mu, sd = float(np.mean(r[fin])), float(np.std(r[fin], ddof=1))
        zs = np.linspace(rd["Normal Score"].min() * 1.05, rd["Normal Score"].max() * 1.05, 30)
        fig.add_scatter(x=mu + sd * zs, y=zs, mode="lines", line=dict(color=t["text2"], width=1.5),
                        hoverinfo="skip", showlegend=False, row=1, col=1)
    fig.add_scatter(x=rd["Residual"], y=rd["Normal Score"], mode="markers", marker=pt, customdata=rd["Obs"],
                    hovertemplate="관측치 %{customdata}<br>잔차 %{x:.4g}<extra></extra>", showlegend=False, row=1, col=1)
    # 2) 적합치 대비
    fig.add_hline(y=0, line=dict(color=t["text2"], width=1), row=1, col=2)
    fig.add_scatter(x=rd["Fit"], y=rd["Residual"], mode="markers", marker=pt, customdata=rd["Obs"],
                    hovertemplate=hov, showlegend=False, row=1, col=2)
    # 3) 히스토그램
    fig.add_histogram(x=rd["Residual"], marker=dict(color=t["series"][0], line=dict(color=t["surface"], width=2)),
                      hovertemplate="%{x}<br>빈도 %{y}<extra></extra>", showlegend=False, row=2, col=1)
    # 4) 관측 순서 대비
    fig.add_hline(y=0, line=dict(color=t["text2"], width=1), row=2, col=2)
    fig.add_scatter(x=rd["Obs"], y=rd["Residual"], mode="lines+markers", marker=pt,
                    line=dict(color=t["series"][0], width=LINE_W), customdata=rd["Obs"], hovertemplate=hov,
                    showlegend=False, row=2, col=2)
    style(fig, mode, title=f"{a.response} 잔차 그림", en="Residual Plots for " + a.response, height=640,
          showlegend=False)
    for ann in fig.layout.annotations:
        ann.font = dict(size=12, color=t["text2"])
    fig.update_xaxes(title_text=label, row=1, col=1)
    _prob_axis(fig, row=1, col=1)
    fig.update_xaxes(title_text="적합치 (Fitted Value)", row=1, col=2)
    fig.update_yaxes(title_text=label, row=1, col=2)
    fig.update_xaxes(title_text=label, row=2, col=1)
    fig.update_yaxes(title_text="빈도 (Frequency)", row=2, col=1)
    fig.update_xaxes(title_text="관측 순서 (Observation Order)", row=2, col=2)
    fig.update_yaxes(title_text=label, row=2, col=2)
    fig.update_layout(bargap=0.04)
    return fig
