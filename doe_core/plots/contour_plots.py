"""등고선도·표면도·중첩 등고선도 — Minitab 'Contour Plot', 'Surface Plot', 'Overlaid Contour Plot'.

- 두 연속 요인을 축으로, 나머지 요인은 고정값(Hold): 연속 요인 기본 = 중점, 텍스트 요인 기본 = 낮은 수준,
  공변량 기본 = 평균. 축 범위는 설계점(축점 포함)의 최소~최대.
- 등고선 수준: 기본(자동 4~7개) / 개수(2~11) / 값 목록(2~11개). 영역 채우기 + 등고선 + 설계점 표시.
- 중앙점 항(Ct Pt)이 모형에 있으면 그리지 않는다(문서: Contour·Surface·Overlaid 사용 불가).
- 중첩 등고선도: 반응마다 Low/High. 모든 반응이 범위 안인 영역은 흰색(실현 가능), 나머지는 회색.
- 색: 연속 크기는 순차 팔레트(파랑 한 색, 밝음 → 어두움), 중첩 등고선의 반응별 선은 범주 색 고정 순서.
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from ..optimize.predict import _lookup, design_row
from .theme import LINE_W, MARKER, style, tokens

SEQ_BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
            "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]


def _check(a, x: str, y: str):
    if any(t.kind == "center" for t in a.terms):
        raise ValueError("중앙점 항이 모형에 있으면 등고선도·표면도를 그릴 수 없습니다. 중앙점 항을 빼고 다시 분석하세요.")
    d = a.design
    Lx, Ly = _lookup(a, x), _lookup(a, y)
    if Lx == Ly:
        raise ValueError("X 축과 Y 축은 서로 다른 요인이어야 합니다.")
    for L in (Lx, Ly):
        f = d.factors[list(d.letters).index(L)]
        if not getattr(f, "is_numeric", False) or not hasattr(f, "low"):
            raise ValueError(f"{f.name} 은 연속(숫자) 요인이 아니라 축으로 쓸 수 없습니다.")
    return Lx, Ly


def factor_range(a, letter: str) -> tuple[float, float]:
    d = a.design
    f = d.factors[list(d.letters).index(letter)]
    lo, hi = float(f.low), float(f.high)
    m, h = (lo + hi) / 2, (hi - lo) / 2
    c = d.coded[letter].astype(float)
    return m + h * float(c.min()), m + h * float(c.max())


def default_hold(a, exclude: tuple[str, ...] = ()) -> dict:
    out = {}
    for L, f in zip(a.design.letters, a.design.factors):
        if L in exclude:
            continue
        if hasattr(f, "levels"):
            out[f.name] = f.levels[0]
        elif f.is_numeric:
            out[f.name] = (float(f.low) + float(f.high)) / 2
        else:
            out[f.name] = f.low
    return out


def grid(a, x: str, y: str, hold: dict | None = None, n: int = 60, covariates: dict | None = None):
    """(xs, ys, Z) — Z[i, j] = (xs[j], ys[i]) 에서의 적합치."""
    Lx, Ly = _check(a, x, y)
    names = dict(zip(a.design.letters, [f.name for f in a.design.factors]))
    h = default_hold(a, exclude=(Lx, Ly))
    h.update(hold or {})
    xs = np.linspace(*factor_range(a, Lx), n)
    ys = np.linspace(*factor_range(a, Ly), n)
    Z = np.empty((n, n))
    for i, yv in enumerate(ys):
        for j, xv in enumerate(xs):
            s = dict(h)
            s[names[Lx]], s[names[Ly]] = xv, yv
            Z[i, j] = float(design_row(a, s, covariates) @ a.beta)
    return xs, ys, Z


def _hold_text(a, x, y, hold, covariates) -> str:
    Lx, Ly = _lookup(a, x), _lookup(a, y)
    h = default_hold(a, exclude=(Lx, Ly))
    h.update(hold or {})
    parts = [f"{k} = {v:g}" if isinstance(v, (int, float)) else f"{k} = {v}" for k, v in h.items()]
    for name, arr in a.covariates.items():
        v = (covariates or {}).get(name, float(np.mean(arr)))
        parts.append(f"{name} = {v:g}")
    return "고정값: " + ", ".join(parts) if parts else ""


def _levels(Z, levels):
    if levels is None:
        return None
    if isinstance(levels, int):
        if not 2 <= levels <= 11:
            raise ValueError("등고선 개수는 2~11 입니다.")
        lo, hi = float(np.min(Z)), float(np.max(Z))
        step = (hi - lo) / (levels + 1)
        return dict(start=lo + step, end=hi - step, size=step)
    vals = sorted(float(v) for v in levels)
    if not 2 <= len(vals) <= 11:
        raise ValueError("등고선 값은 2~11개입니다.")
    step = min(np.diff(vals)) if len(vals) > 1 else 1.0
    return dict(start=vals[0], end=vals[-1], size=step)


def contour_plot(a, x: str, y: str, *, hold: dict | None = None, levels=None, show_points: bool = True,
                 covariates: dict | None = None, mode: str = "light", n: int = 60) -> go.Figure:
    t = tokens(mode)
    xs, ys, Z = grid(a, x, y, hold, n, covariates)
    Lx, Ly = _lookup(a, x), _lookup(a, y)
    names = dict(zip(a.design.letters, [f.name for f in a.design.factors]))
    lv = _levels(Z, levels)
    fig = go.Figure(go.Contour(
        x=xs, y=ys, z=Z, colorscale=[[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)],
        contours=dict(showlabels=True, labelfont=dict(color=t["text"], size=11), coloring="fill", **(lv or {})),
        autocontour=lv is None, ncontours=7 if lv is None else None,
        line=dict(width=1, color=t["surface"]), colorbar=dict(title=dict(text=a.response, side="right"),
                                                             tickfont=dict(color=t["text2"])),
        hovertemplate=f"{names[Lx]} %{{x:.4g}}<br>{names[Ly]} %{{y:.4g}}<br>{a.response} %{{z:.4g}}<extra></extra>",
    ))
    if show_points:
        f = a.design
        fx, fy = f.factors[list(f.letters).index(Lx)], f.factors[list(f.letters).index(Ly)]
        cx = (float(fx.low) + float(fx.high)) / 2 + f.coded[Lx].astype(float) * (float(fx.high) - float(fx.low)) / 2
        cy = (float(fy.low) + float(fy.high)) / 2 + f.coded[Ly].astype(float) * (float(fy.high) - float(fy.low)) / 2
        pts = np.unique(np.column_stack([cx, cy]), axis=0)
        fig.add_scatter(x=pts[:, 0], y=pts[:, 1], mode="markers", name="설계점",
                        marker=dict(color=t["text"], size=MARKER - 2, symbol="circle-open", line=dict(width=1.5)),
                        hovertemplate="설계점 (%{x:.4g}, %{y:.4g})<extra></extra>")
    style(fig, mode, title=f"{a.response} 등고선도: {names[Ly]} vs {names[Lx]}",
          en=f"Contour Plot of {a.response} vs {names[Ly]}, {names[Lx]} · " + _hold_text(a, x, y, hold, covariates),
          height=520, showlegend=False)
    fig.update_xaxes(title_text=names[Lx], showgrid=False)
    fig.update_yaxes(title_text=names[Ly], showgrid=False)
    return fig


def surface_plot(a, x: str, y: str, *, hold: dict | None = None, covariates: dict | None = None,
                 mode: str = "light", n: int = 40) -> go.Figure:
    t = tokens(mode)
    xs, ys, Z = grid(a, x, y, hold, n, covariates)
    Lx, Ly = _lookup(a, x), _lookup(a, y)
    names = dict(zip(a.design.letters, [f.name for f in a.design.factors]))
    fig = go.Figure(go.Surface(
        x=xs, y=ys, z=Z, colorscale=[[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)],
        colorbar=dict(title=dict(text=a.response, side="right"), tickfont=dict(color=t["text2"])),
        hovertemplate=f"{names[Lx]} %{{x:.4g}}<br>{names[Ly]} %{{y:.4g}}<br>{a.response} %{{z:.4g}}<extra></extra>",
    ))
    style(fig, mode, title=f"{a.response} 표면도: {names[Ly]}, {names[Lx]}",
          en=f"Surface Plot of {a.response} · " + _hold_text(a, x, y, hold, covariates), height=560, showlegend=False)
    axis = dict(backgroundcolor=t["surface"], gridcolor=t["grid"], color=t["text2"])
    fig.update_layout(scene=dict(xaxis=dict(title=names[Lx], **axis), yaxis=dict(title=names[Ly], **axis),
                                 zaxis=dict(title=a.response, **axis)))
    return fig


def feasible_region(analyses: list, bounds: dict, x: str, y: str, hold: dict | None = None, n: int = 80,
                    covariates: dict | None = None):
    """(xs, ys, {반응: Z}, 실현 가능 마스크). bounds: {반응: (low, high)}."""
    base = analyses[0]
    zs, feasible = {}, None
    for a in analyses:
        if a.design is not base.design and list(a.design.letters) != list(base.design.letters):
            raise ValueError("중첩 등고선도의 모형들은 같은 설계를 써야 합니다.")
        xs, ys, Z = grid(a, x, y, hold, n, covariates)
        lo, hi = bounds[a.response]
        ok = (Z >= lo) & (Z <= hi)
        feasible = ok if feasible is None else feasible & ok
        zs[a.response] = Z
    return xs, ys, zs, feasible


def overlaid_contour_plot(analyses: list, bounds: dict, x: str, y: str, *, hold: dict | None = None,
                          covariates: dict | None = None, mode: str = "light", n: int = 80) -> go.Figure:
    t = tokens(mode)
    xs, ys, zs, feasible = feasible_region(analyses, bounds, x, y, hold, n, covariates)
    a0 = analyses[0]
    Lx, Ly = _lookup(a0, x), _lookup(a0, y)
    names = dict(zip(a0.design.letters, [f.name for f in a0.design.factors]))
    fig = go.Figure(go.Heatmap(x=xs, y=ys, z=np.where(feasible, np.nan, 1.0),
                               colorscale=[[0, t["muted"]], [1, t["muted"]]], showscale=False, opacity=0.55,
                               hoverinfo="skip"))
    for k, (resp, Z) in enumerate(zs.items()):
        color = t["series"][k % len(t["series"])]
        lo, hi = bounds[resp]
        for i, val in enumerate((lo, hi)):
            # 선 등고선은 line.color 가 아니라 색 척도로 칠해지므로 단색 척도를 준다
            fig.add_trace(go.Contour(x=xs, y=ys, z=Z, showscale=False, colorscale=[[0, color], [1, color]],
                                     contours=dict(coloring="lines", start=val, end=val, size=1, showlabels=True,
                                                   labelfont=dict(color=t["text"], size=11)),
                                     line=dict(width=LINE_W), name=f"{resp}: {lo:g} ~ {hi:g}",
                                     showlegend=i == 0, legendgroup=resp, hoverinfo="skip"))
    style(fig, mode, title=f"중첩 등고선도: {', '.join(zs)}",
          en="Overlaid Contour Plot · 흰 영역 = 모든 반응이 범위 안 · " + _hold_text(a0, x, y, hold, covariates),
          height=540)
    fig.update_xaxes(title_text=names[Lx], showgrid=False)
    fig.update_yaxes(title_text=names[Ly], showgrid=False)
    return fig
