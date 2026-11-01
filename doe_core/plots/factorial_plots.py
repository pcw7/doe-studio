"""요인 그림 — Minitab 'Factorial Plots'(주효과도·교호작용도)와 'Cube Plot'.

모두 적합 평균(fitted means)을 쓴다. 나머지 요인은 코드값 0(평균), 공변량은 평균, 블록은 평균화.
- 주효과도: 요인마다 수준별 적합 평균을 선으로 잇고, 데이터 전체 평균에 기준선. 중앙점 항이 모형에 있으면 중앙점 적합 평균을 별도 점.
- 교호작용도: 요인 쌍마다 x = 첫 요인 수준, 선 = 둘째 요인 수준(범례 + 선 끝 직접 라벨).
- 입방체도: 2~3요인은 정육면체(2요인은 사각형) 하나, 4요인은 넷째 요인 수준별로 두 개. 꼭짓점에 적합 평균.
  문서 예제: InsulationProperties Insulation(2차 + 공변량)에서 CoolTemp 45, Formula2, InjTemp 100, InjPress 150 = 28.3558.
"""
from __future__ import annotations

from itertools import combinations, product

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..analysis import fmt
from ..analysis.means import _levels, fitted_at
from .theme import KEEP, LINE_W, MARKER, lift_legend, style, tokens


def _names(a) -> dict[str, str]:
    return dict(zip(a.design.letters, [f.name for f in a.design.factors]))


def _model_letters(a) -> list[str]:
    used = {L for t in a.terms if t.kind == "factor" for L in t.letters}
    return [L for L in a.design.letters if L in used]


# ---------------------------------------------------------------- 데이터


def main_effects_data(a, letters: list[str] | None = None) -> pd.DataFrame:
    letters = letters or _model_letters(a)
    names = _names(a)
    rows = []
    for L in letters:
        for i, (state, label) in enumerate(_levels(a.design, L)):
            m, se = fitted_at(a, {L: state})
            rows.append({"Factor": L, "Name": names[L], "Level": label, "Order": i, "Fitted Mean": m, "SE Mean": se})
    return pd.DataFrame(rows)


def center_fitted(a) -> float | None:
    if not any(t.kind == "center" for t in a.terms):
        return None
    return fitted_at(a, {}, center=True)[0]


def interaction_data(a, x: str, trace: str) -> pd.DataFrame:
    rows = []
    for (sx, lx), (st, lt) in product(_levels(a.design, x), _levels(a.design, trace)):
        m, se = fitted_at(a, {x: sx, trace: st})
        rows.append({"X Level": lx, "Trace Level": lt, "Fitted Mean": m, "SE Mean": se})
    return pd.DataFrame(rows)


def cube_data(a, letters: list[str]) -> pd.DataFrame:
    """꼭짓점별 적합 평균. letters 는 2~4개(2수준 설계)."""
    if not a.two_level:
        raise ValueError("입방체도는 2수준 설계에서만 그립니다.")
    if not 2 <= len(letters) <= 4:
        raise ValueError("입방체도는 요인 2~4개로 그립니다.")
    names = _names(a)
    rows = []
    for combo in product(*[_levels(a.design, L) for L in letters]):
        setting = {L: s for L, (s, _) in zip(letters, combo)}
        m, _ = fitted_at(a, setting)
        rows.append({**{names[L]: lab for L, (_, lab) in zip(letters, combo)},
                     **{f"_{L}": s for L, (s, _) in zip(letters, combo)}, "Fitted Mean": m})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 그림


def main_effects_plot(a, letters: list[str] | None = None, mode: str = "light") -> go.Figure:
    t = tokens(mode)
    data = main_effects_data(a, letters)
    facs = list(dict.fromkeys(data["Factor"]))
    names = _names(a)
    fig = make_subplots(rows=1, cols=len(facs), shared_yaxes=True, horizontal_spacing=0.04,
                        subplot_titles=[names[L] for L in facs])
    ct = center_fitted(a)
    grand = float(np.mean(a.y))
    facs_by = dict(zip(a.design.letters, a.design.factors))
    for i, L in enumerate(facs, start=1):
        q = data[data["Factor"] == L].sort_values("Order")
        cats = list(q["Level"])
        f = facs_by[L]
        mid = None
        if ct is not None and a.two_level:
            mid = fmt.fixed((float(f.low) + float(f.high)) / 2, 6).rstrip("0").rstrip(".") if f.is_numeric else "중앙"
            cats = [cats[0], mid, cats[-1]]
        fig.add_scatter(x=q["Level"], y=q["Fitted Mean"], mode="lines+markers", name="모서리점 (Corner)",
                        line=dict(color=t["series"][0], width=LINE_W),
                        marker=dict(color=t["series"][0], size=MARKER, line=dict(color=t["surface"], width=2)),
                        customdata=q["SE Mean"], showlegend=(i == 1 and mid is not None),
                        hovertemplate=f"{names[L]} = %{{x}}<br>적합 평균 %{{y:.4g}}<br>SE %{{customdata:.3g}}<extra></extra>",
                        row=1, col=i)
        if mid is not None:
            fig.add_scatter(x=[mid], y=[ct], mode="markers", name="중앙점 (Center)",
                            marker=dict(color=t["series"][1], size=MARKER, symbol="square",
                                        line=dict(color=t["surface"], width=2)),
                            showlegend=(i == 1), hovertemplate="중앙점 적합 평균 %{y:.4g}<extra></extra>", row=1, col=i)
        fig.add_hline(y=grand, line=dict(color=t["text2"], width=1), row=1, col=i)
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=cats, showgrid=False, row=1, col=i)
    style(fig, mode, title=f"{a.response} 주효과도", en=f"Main Effects Plot for {a.response} (Fitted Means)",
          height=380, showlegend=ct is not None and a.two_level)
    for ann in fig.layout.annotations:                   # 소제목 = 요인 이름(사용자 글자)
        ann.font = dict(size=12, color=t["text2"])
        ann.name = KEEP
    if ct is not None and a.two_level:
        lift_legend(fig, 22)
    fig.update_yaxes(title_text="적합 평균 (Fitted Mean)", row=1, col=1)
    return fig


def interaction_plot(a, x: str, trace: str, mode: str = "light") -> go.Figure:
    t = tokens(mode)
    names = _names(a)
    data = interaction_data(a, x, trace)
    fig = go.Figure()
    levels = list(dict.fromkeys(data["Trace Level"]))
    for k, lv in enumerate(levels):
        q = data[data["Trace Level"] == lv]
        color = t["series"][k % len(t["series"])]
        fig.add_scatter(x=q["X Level"], y=q["Fitted Mean"], mode="lines+markers", name=f"{names[trace]} {lv}",
                        line=dict(color=color, width=LINE_W),
                        marker=dict(color=color, size=MARKER, line=dict(color=t["surface"], width=2)),
                        hovertemplate=f"{names[x]} = %{{x}}<br>{names[trace]} = {lv}<br>적합 평균 %{{y:.4g}}<extra></extra>")
        if len(levels) <= 4:
            # 범주형 축에서 숫자처럼 보이는 범주 이름("100")은 숫자로 해석되므로 위치는 범주 순번으로 준다
            fig.add_annotation(x=len(q) - 1, y=q["Fitted Mean"].iloc[-1], text=f"{lv}", showarrow=False,
                               xanchor="left", xshift=10, font=dict(color=t["text"], size=12))
    style(fig, mode, title=f"{a.response} 교호작용도: {names[x]} × {names[trace]}",
          en=f"Interaction Plot for {a.response} (Fitted Means)", height=380)
    fig.update_xaxes(type="category", title_text=names[x], showgrid=False)
    fig.update_yaxes(title_text="적합 평균 (Fitted Mean)")
    fig.update_layout(margin=dict(r=72))
    return fig


def interaction_pairs(a) -> list[tuple[str, str]]:
    """모형에 있는 2요인 교호작용 쌍(없으면 모형 요인의 모든 쌍)."""
    pairs = [t.letters for t in a.terms if t.kind == "factor" and t.order == 2]
    return pairs or list(combinations(_model_letters(a), 2))


_PROJ = {"x": (1.0, 0.0), "y": (0.0, 1.0), "z": (0.42, 0.32)}


def cube_plot(a, letters: list[str], mode: str = "light") -> go.Figure:
    t = tokens(mode)
    data = cube_data(a, letters)
    names = _names(a)
    axes = letters[:3]
    split = letters[3] if len(letters) == 4 else None
    groups = [(None, data)] if split is None else [(lv, data[data[f"_{split}"] == s])
                                                    for s, lv in _levels(a.design, split)]
    fig = go.Figure()
    dec = fmt.decimals_for_sig(float(data["Fitted Mean"].abs().max()), 6)
    for gi, (lv, g) in enumerate(groups):
        ox = gi * 2.2

        def proj(c):
            px = ox + sum(_PROJ[k][0] * (1 if c[i] > 0 else 0) for i, k in enumerate(("x", "y", "z")[: len(axes)]))
            py = sum(_PROJ[k][1] * (1 if c[i] > 0 else 0) for i, k in enumerate(("x", "y", "z")[: len(axes)]))
            return px, py

        corners = list(product((-1, 1), repeat=len(axes)))
        for c1, c2 in combinations(corners, 2):
            if sum(a_ != b_ for a_, b_ in zip(c1, c2)) == 1:
                (x1, y1), (x2, y2) = proj(c1), proj(c2)
                fig.add_scatter(x=[x1, x2], y=[y1, y2], mode="lines", line=dict(color=t["axis"], width=1.5),
                                hoverinfo="skip", showlegend=False)
        for _, r in g.iterrows():
            c = tuple(int(r[f"_{L}"]) for L in axes)
            px, py = proj(c)
            label = ", ".join(f"{names[L]} {r[names[L]]}" for L in letters)
            fig.add_scatter(x=[px], y=[py], mode="markers+text", text=[fmt.fixed(r["Fitted Mean"], dec)],
                            textposition="top center", textfont=dict(color=t["text"], size=12),
                            marker=dict(color=t["series"][0], size=MARKER, line=dict(color=t["surface"], width=2)),
                            hovertemplate=f"{label}<br>적합 평균 %{{y:.6g}}<extra></extra>".replace("%{y:.6g}", fmt.fixed(r["Fitted Mean"], dec)),
                            showlegend=False)
        # 축 라벨(낮음·높음 수준과 요인 이름)
        lv0 = _levels(a.design, axes[0])
        fig.add_annotation(x=ox, y=-0.12, text=str(lv0[0][1]), showarrow=False, font=dict(color=t["text2"], size=11))
        fig.add_annotation(x=ox + 1, y=-0.12, text=str(lv0[1][1]), showarrow=False, font=dict(color=t["text2"], size=11))
        fig.add_annotation(x=ox + 0.5, y=-0.24, text=names[axes[0]], showarrow=False, font=dict(color=t["text"], size=12))
        lv1 = _levels(a.design, axes[1])
        fig.add_annotation(x=ox - 0.08, y=0, text=str(lv1[0][1]), showarrow=False, xanchor="right", font=dict(color=t["text2"], size=11))
        fig.add_annotation(x=ox - 0.08, y=1, text=str(lv1[1][1]), showarrow=False, xanchor="right", font=dict(color=t["text2"], size=11))
        fig.add_annotation(x=ox - 0.3, y=0.5, text=names[axes[1]], showarrow=False, textangle=-90, font=dict(color=t["text"], size=12))
        if len(axes) == 3:
            lv2 = _levels(a.design, axes[2])
            zx, zy = _PROJ["z"]
            fig.add_annotation(x=ox + 1 + zx * 0.5 + 0.08, y=zy * 0.5 - 0.02, text=f"{names[axes[2]]}", showarrow=False,
                               xanchor="left", font=dict(color=t["text"], size=12))
            fig.add_annotation(x=ox + 1 + 0.06, y=-0.03, text=str(lv2[0][1]), showarrow=False, xanchor="left", font=dict(color=t["text2"], size=11))
            fig.add_annotation(x=ox + 1 + zx + 0.06, y=zy - 0.03, text=str(lv2[1][1]), showarrow=False, xanchor="left", font=dict(color=t["text2"], size=11))
        if split is not None:
            fig.add_annotation(x=ox + 0.7, y=1.55, text=f"{names[split]} = {lv}", showarrow=False, font=dict(color=t["text"], size=13))
    style(fig, mode, title=f"{a.response} 입방체도", en=f"Cube Plot (Fitted Means) for {a.response}",
          height=420, showlegend=False)
    fig.update_xaxes(visible=False, showgrid=False)
    fig.update_yaxes(visible=False, showgrid=False, scaleanchor="x", scaleratio=1)
    return fig
