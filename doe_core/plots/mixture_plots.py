"""혼합물 그래프 — Minitab 'Simplex Design Plot', 'Response Trace Plot', 혼합물 'Contour/Surface Plot',
'Overlaid Contour Plot(3 Components)'.

삼각 좌표: 세 축 성분(triplet)의 하한으로 정한 부분 단순체(L-유사성분 삼각형)를 그린다. 나머지 성분은 고정값(기본: 기준
혼합물의 값)이고 세 성분의 합은 S = 1 − 고정값 합. 꼭지점 i 의 비율 = L_i + (S − ΣL) (나머지 두 성분은 하한).
화면 좌표는 첫 성분이 위, 둘째가 왼쪽 아래, 셋째가 오른쪽 아래 꼭지점. 축 눈금은 실제 비율.

- 단순체 설계도: 설계점(서로 다른 혼합물, 점 유형별 기호)과 제약 영역(회색 채움, 3성분일 때).
- 반응 추적 그림: 기준 혼합물(기본 'Centroid of vertices' = 꼭지점 혼합물의 평균)에서 성분 하나를 바꿀 때의 적합치.
  Cox 방향: x_i = s_i + Δ, 나머지는 원래 비율대로 줄거나 늘어난다(x_j = s_j − Δ·s_j/(1 − s_i)).
  Piepel 방향: 같은 규칙을 유사성분 공간에서 적용. x 축은 성분 i 의 비율 편차 Δ. 성분 범위·선형 제약 안에서만 그린다.
  공정 변수는 기본으로 낮은 수준(문서 예제: Temperature 80).
- 등고선도·표면도: 삼각형 안의 격자에서 적합치. 등고선 색은 순차 파랑(밝음 → 어두움).
- 중첩 등고선도: 반응별 하한·상한 선, 모든 반응이 범위 안인 영역은 흰색, 나머지는 회색.

문서에 없어 정한 것: 삼각형을 부분 단순체로 확대하는 범위, 꼭지점 배치, 추적 그림의 Δ 표본 수.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ..analysis.mixture import feasible, mixture_rows, reference_blend
from .contour_plots import SEQ_BLUE
from .theme import LINE_W, MARKER, style, tokens

H = np.sqrt(3) / 2
DASHES = ["solid", "dash", "dot", "dashdot"]
PT_KO = {1: "꼭지점", 2: "모서리 중점", 3: "3성분 혼합", 0: "중심점", -1: "축점"}


# ---------------------------------------------------------------- 삼각 좌표


class Triangle:
    """세 축 성분의 부분 단순체와 화면 좌표 변환."""

    def __init__(self, design, triplet=None, hold: dict | None = None):
        d = design
        letters = list(d.letters)
        names = {c.name: L for L, c in zip(letters, d.components)}
        triplet = [names.get(t, t) for t in (triplet or letters[:3])]
        if len(set(triplet)) != 3 or any(t not in letters for t in triplet):
            raise ValueError("축 성분 세 개를 서로 다르게 고르세요.")
        self.design, self.idx = d, [letters.index(t) for t in triplet]
        self.triplet = triplet
        others = [i for i in range(d.q) if i not in self.idx]
        ref = reference_blend(d)
        hold = {names.get(k, k): float(v) for k, v in (hold or {}).items()}
        self.hold = {letters[i]: hold.get(letters[i], float(ref[i])) for i in others}
        self.S = 1.0 - sum(self.hold.values())
        lows = np.array([d.components[i].lower for i in self.idx])
        if lows.sum() >= self.S - 1e-9:
            lows = np.zeros(3)
        self.L = lows
        self.W = self.S - lows.sum()
        if self.W <= 1e-9:
            raise ValueError("고정값이 너무 커서 축 성분이 움직일 범위가 없습니다.")
        self.names = [d.components[i].name for i in self.idx]

    def blends(self, w: np.ndarray) -> np.ndarray:
        """무게중심 좌표 w(n × 3) → 전체 비율 행렬(n × q)."""
        w = np.atleast_2d(w)
        P = np.zeros((len(w), self.design.q))
        for j, i in enumerate(self.idx):
            P[:, i] = self.L[j] + w[:, j] * self.W
        for L, v in self.hold.items():
            P[:, self.design.letters.index(L)] = v
        return P

    def weights(self, P: np.ndarray) -> np.ndarray:
        P = np.atleast_2d(P)
        return (P[:, self.idx] - self.L) / self.W

    @staticmethod
    def xy(w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        w = np.atleast_2d(w)
        return 0.5 * w[:, 0] + w[:, 2], H * w[:, 0]

    @staticmethod
    def from_xy(x, y):
        w1 = y / H
        w3 = x - 0.5 * w1
        return np.stack([w1, 1 - w1 - w3, w3], axis=-1)

    def grid(self, n: int = 81):
        xs = np.linspace(0, 1, n)
        ys = np.linspace(0, H, n)
        X, Y = np.meshgrid(xs, ys)
        Wg = self.from_xy(X, Y)
        inside = np.all(Wg >= -1e-9, axis=-1)
        return xs, ys, Wg, inside

    def frame(self, fig: go.Figure, t: dict, *, ticks: int = 5, grid: bool = True, row=None, col=None) -> None:
        """삼각형 테두리·격자선(grid=False 면 테두리 눈금 표시만)·눈금(실제 비율)·꼭지점 이름."""
        corners = np.eye(3)
        cx, cy = self.xy(np.vstack([corners, corners[:1]]))
        kw = dict(row=row, col=col) if row else {}
        for k in range(1, ticks):
            f = k / ticks
            for j in range(3):
                a = np.zeros(3)
                a[j] = f
                b1, b2 = a.copy(), a.copy()
                o = [m for m in range(3) if m != j]
                b1[o[0]], b2[o[1]] = 1 - f, 1 - f
                if not grid:                              # 변에서 안쪽으로 짧은 눈금만
                    b2 = b1 + 0.03 * (b2 - b1) / max(np.abs(b2 - b1).max(), 1e-12)
                x, y = self.xy(np.vstack([b1, b2]))
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines",
                                         line=dict(color=t["grid"] if grid else t["axis"], width=1),
                                         hoverinfo="skip", showlegend=False), **kw)
        fig.add_trace(go.Scatter(x=cx, y=cy, mode="lines", line=dict(color=t["axis"], width=1.5), hoverinfo="skip",
                                 showlegend=False), **kw)
        # 눈금: 성분 j 의 값이 f 인 선이 변과 만나는 곳(시계 방향 다음 변)에 실제 비율
        for j in range(3):
            nxt = (j + 1) % 3
            xs, ys, txt = [], [], []
            for k in range(1, ticks):                     # 꼭지점(0·1)은 이름으로 대신
                f = k / ticks
                w = np.zeros(3)
                w[j], w[nxt] = f, 1 - f
                x, y = self.xy(w)
                xs.append(float(x[0]))
                ys.append(float(y[0]))
                txt.append(f"{self.L[j] + f * self.W:.3g}")
            off = {0: (-0.045, 0.0), 1: (0.0, -0.045), 2: (0.045, 0.0)}[j]
            fig.add_trace(go.Scatter(x=np.array(xs) + off[0], y=np.array(ys) + off[1], mode="text", text=txt,
                                     textfont=dict(size=10, color=t["text2"]), hoverinfo="skip", showlegend=False), **kw)
        labels = [(0.5, H + 0.06, self.names[0]), (-0.04, -0.07, self.names[1]), (1.04, -0.07, self.names[2])]
        for x, y, s in labels:
            fig.add_annotation(x=x, y=y, text=f"<b>{s}</b>", showarrow=False, font=dict(color=t["text"], size=13),
                               **({"row": row, "col": col} if row else {}))

    def region_polygon(self) -> np.ndarray | None:
        """3성분 설계의 제약 영역 꼭지점(무게중심 좌표, 둘레 순서). 성분이 3개가 아니면 None.

        사용자 정의 설계는 성분 범위를 모르는 경우가 많아 꼭지점(점 유형 1) 혼합물의 볼록 껍질을 쓴다.
        """
        d = self.design
        if d.q != 3:
            return None
        pt = d.coded[d.point_col].values
        if d.kind == "custom" and (pt == 1).sum() >= 3:
            V = np.unique(d.coded[d.letters].values[pt == 1].astype(float).round(12), axis=0)
        else:
            from ..designs.mixture import _inequalities, _vertices
            G, h = _inequalities(d.components, d.letters, d.constraints)
            V, _ = _vertices(G, h, 3)
        w = self.weights(V)
        x, y = self.xy(w)
        ang = np.arctan2(y - y.mean(), x - x.mean())
        return w[np.argsort(ang)]


def _mask_outside(fig: go.Figure, t: dict) -> None:
    """격자 가장자리의 계단 모양을 가리도록 삼각형 바깥을 바탕색으로 덮는다."""
    for xs, ys in [([-0.3, 0.0, 0.5, -0.3], [-0.001, -0.001, H, H + 0.3]), ([1.3, 1.0, 0.5, 1.3], [-0.001, -0.001, H, H + 0.3])]:
        fig.add_trace(go.Scatter(x=xs + [xs[0]], y=ys + [ys[0]], mode="lines", fill="toself", fillcolor=t["surface"],
                                 line=dict(width=0, color=t["surface"]), hoverinfo="skip", showlegend=False))


def _axes_off(fig: go.Figure) -> None:
    fig.update_xaxes(visible=False, range=[-0.12, 1.12])
    fig.update_yaxes(visible=False, range=[-0.14, H + 0.12], scaleanchor="x", scaleratio=1)


def _hold_text(tri: Triangle, process: dict | None, design) -> str:
    parts = [f"{design.components[design.letters.index(L)].name} = {v:.4g}" for L, v in tri.hold.items()]
    proc = dict(process or {})
    for f in design.process:
        parts.append(f"{f.name} = {proc.get(f.name, f.low)}")
    return ("고정값: " + ", ".join(parts)) if parts else ""


# ---------------------------------------------------------------- 단순체 설계도


def simplex_design_plot(design, triplet=None, *, hold: dict | None = None, mode: str = "light") -> go.Figure:
    t = tokens(mode)
    tri = Triangle(design, triplet, hold)
    fig = go.Figure()
    tri.frame(fig, t)
    poly = tri.region_polygon()
    if poly is not None:
        x, y = tri.xy(np.vstack([poly, poly[:1]]))
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", fill="toself", fillcolor=t["muted"], opacity=0.35,
                                 line=dict(color=t["muted"], width=1), name="설계 영역", hoverinfo="skip"))
    P = design.coded[design.letters].values.astype(float)
    pt = design.coded[design.point_col].values
    others = [design.letters.index(L) for L in tri.hold]
    keep = np.all(np.abs(P[:, others] - np.array(list(tri.hold.values()))) < 1e-9, axis=1) if others else \
        np.ones(len(P), bool)
    df = pd.DataFrame(P[keep], columns=design.letters)
    df["pt"] = pt[keep]
    g = df.groupby([*design.letters, "pt"]).size().reset_index(name="n")
    symbols = {1: "circle", 2: "square", 3: "diamond", 0: "star", -1: "triangle-up"}
    for k, (ptv, sub) in enumerate(sorted(g.groupby("pt"), key=lambda kv: (kv[0] <= 0, -kv[0]))):
        w = tri.weights(sub[design.letters].values)
        x, y = tri.xy(w)
        hover = ["<br>".join(f"{c.name} {r[L]:.4g}" for c, L in zip(design.components, design.letters))
                 + f"<br>런 {int(r['n'])}개" for _, r in sub.iterrows()]
        fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name=PT_KO.get(int(ptv), f"유형 {int(ptv)}"),
                                 marker=dict(size=MARKER + 2, symbol=symbols.get(int(ptv), "circle"),
                                             color=t["series"][k % len(t["series"])],
                                             line=dict(color=t["surface"], width=2)),
                                 text=hover, hovertemplate="%{text}<extra></extra>"))
    style(fig, mode, title="단순체 설계도", en="Simplex Design Plot · " + ", ".join(tri.names)
          + (" · " + _hold_text(tri, None, design).replace("고정값: ", "고정: ") if tri.hold else ""),
          height=560, showlegend=True)
    _axes_off(fig)
    return fig


# ---------------------------------------------------------------- 반응 추적 그림


def _direction(s: np.ndarray, i: int, delta: np.ndarray) -> np.ndarray:
    """Cox 방향: 성분 i 를 Δ 만큼 바꾸고 나머지는 비율을 유지하며 합 1."""
    P = np.repeat(s[None, :], len(delta), axis=0)
    rest = 1 - s[i]
    P[:, i] = s[i] + delta
    for j in range(len(s)):
        if j != i:
            P[:, j] = s[j] - delta * (s[j] / rest if rest > 0 else 0)
    return P


def trace_data(a, *, direction: str = "cox", reference=None, process: dict | None = None, n: int = 61) -> pd.DataFrame:
    """성분별 추적선: Component, Deviation(비율 편차), 성분 비율들, Fit."""
    d = a.design
    if direction not in ("cox", "piepel"):
        raise ValueError("추적 방향은 'cox' 또는 'piepel' 입니다.")
    s = reference_blend(d) if reference is None else np.asarray(reference, dtype=float)
    lo = np.array([c.lower for c in d.components])
    span = 1 - lo.sum()
    rows = []
    for i, comp in enumerate(d.components):
        grid = np.linspace(-1, 1, 2001)
        if direction == "cox":
            P = _direction(s, i, grid)
        else:                                         # 유사성분 공간의 Cox 방향
            r = (s - lo) / span
            Z = _direction(r, i, grid / span)
            P = lo + Z * span
        ok = feasible(d, P) & np.all(P >= -1e-12, axis=1)
        if not ok.any():
            continue
        zero = int(np.argmin(np.abs(grid)))
        if ok[zero]:
            lo_k, hi_k = zero, zero
            while lo_k > 0 and ok[lo_k - 1]:
                lo_k -= 1
            while hi_k < len(grid) - 1 and ok[hi_k + 1]:
                hi_k += 1
        else:
            idx = np.flatnonzero(ok)
            lo_k, hi_k = idx[0], idx[-1]
        dev = np.linspace(grid[lo_k], grid[hi_k], n)
        if direction == "cox":
            Pn = _direction(s, i, dev)
        else:
            r = (s - lo) / span
            Pn = lo + _direction(r, i, dev / span) * span
        fit = mixture_rows(a, Pn, process) @ a.beta
        df = pd.DataFrame(Pn, columns=[c.name for c in d.components])
        df.insert(0, "Deviation", Pn[:, i] - s[i])
        df.insert(0, "Component", comp.name)
        df["Fit"] = fit
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


def response_trace_plot(a, *, direction: str = "cox", reference=None, process: dict | None = None,
                        mode: str = "light") -> go.Figure:
    t = tokens(mode)
    data = trace_data(a, direction=direction, reference=reference, process=process)
    s = reference_blend(a.design) if reference is None else np.asarray(reference, dtype=float)
    fig = go.Figure()
    comps = list(dict.fromkeys(data["Component"]))
    for k, name in enumerate(comps):
        sub = data[data["Component"] == name]
        color = t["series"][k % len(t["series"])]
        dash = DASHES[(k // len(t["series"])) % len(DASHES)]
        fig.add_trace(go.Scatter(x=sub["Deviation"], y=sub["Fit"], mode="lines", name=name,
                                 line=dict(color=color, width=LINE_W, dash=dash),
                                 hovertemplate=f"{name}<br>편차 %{{x:.4g}}<br>{a.response} %{{y:.4g}}<extra></extra>"))
        last = sub.iloc[-1]
        fig.add_annotation(x=last["Deviation"], y=last["Fit"], text=name, showarrow=False, xanchor="left", xshift=6,
                           font=dict(color=t["text2"], size=12))
    fig.add_vline(x=0, line=dict(color=t["axis"], width=1, dash="dot"))
    ref_txt = ", ".join(f"{c.name} {v:.4g}" for c, v in zip(a.design.components, s))
    proc = dict(process or {})
    ptxt = ", ".join(f"{f.name} = {proc.get(f.name, f.low)}" for f in a.design.process)
    style(fig, mode, title=f"{a.response} 반응 추적 그림",
          en=f"Response Trace Plot · {'Cox' if direction == 'cox' else 'Piepel'} direction · 기준 혼합물 {ref_txt}"
          + (f" · {ptxt}" if ptxt else ""), height=480, showlegend=True)
    fig.update_xaxes(title_text="기준 혼합물에서의 편차 (비율)")
    fig.update_yaxes(title_text=f"적합치 {a.response}")
    fig.update_layout(margin=dict(r=90))
    return fig


# ---------------------------------------------------------------- 등고선·표면도


def mixture_grid(a, triplet=None, *, hold: dict | None = None, process: dict | None = None, n: int = 81):
    """(삼각형, xs, ys, Z, 무게중심 격자, 안쪽 마스크). 삼각형 밖은 NaN."""
    tri = Triangle(a.design, triplet, hold)
    xs, ys, Wg, inside = tri.grid(n)
    Z = np.full(inside.shape, np.nan)
    P = tri.blends(Wg[inside])
    Z[inside] = mixture_rows(a, P, process) @ a.beta
    return tri, xs, ys, Z, Wg, inside


def _customdata(tri: Triangle, Wg: np.ndarray, inside: np.ndarray) -> np.ndarray:
    cd = np.full(Wg.shape, np.nan)
    cd[inside] = (tri.blends(Wg[inside])[:, tri.idx])
    return cd


def _levels(Z, levels):
    if levels is None:
        return None
    lo, hi = float(np.nanmin(Z)), float(np.nanmax(Z))
    if isinstance(levels, int):
        if not 2 <= levels <= 11:
            raise ValueError("등고선 개수는 2~11 입니다.")
        step = (hi - lo) / (levels + 1)
        return dict(start=lo + step, end=hi - step, size=step)
    vals = sorted(float(v) for v in levels)
    step = min(np.diff(vals)) if len(vals) > 1 else 1.0
    return dict(start=vals[0], end=vals[-1], size=step)


def mixture_contour_plot(a, triplet=None, *, hold: dict | None = None, process: dict | None = None, levels=None,
                         show_points: bool = True, mode: str = "light", n: int = 81) -> go.Figure:
    t = tokens(mode)
    tri, xs, ys, Z, Wg, inside = mixture_grid(a, triplet, hold=hold, process=process, n=n)
    cd = _customdata(tri, Wg, inside)
    lv = _levels(Z, levels)
    nm = tri.names
    fig = go.Figure(go.Contour(
        x=xs, y=ys, z=Z, customdata=cd, connectgaps=False,
        colorscale=[[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)],
        contours=dict(coloring="fill", showlabels=True, labelfont=dict(color=t["text"], size=11), **(lv or {})),
        autocontour=lv is None, ncontours=7 if lv is None else None, line=dict(width=1, color=t["surface"]),
        colorbar=dict(title=dict(text=a.response, side="right"), tickfont=dict(color=t["text2"])),
        hovertemplate=f"{nm[0]} %{{customdata[0]:.4g}}<br>{nm[1]} %{{customdata[1]:.4g}}<br>{nm[2]} "
                      f"%{{customdata[2]:.4g}}<br>{a.response} %{{z:.4g}}<extra></extra>"))
    _mask_outside(fig, t)
    tri.frame(fig, t, grid=False)
    poly = tri.region_polygon()
    if poly is not None:
        x, y = tri.xy(np.vstack([poly, poly[:1]]))
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=t["text2"], width=1.5, dash="dash"),
                                 name="설계 영역", hoverinfo="skip", showlegend=False))
    if show_points:
        P = np.unique(a.design.coded[a.design.letters].values.astype(float).round(12), axis=0)
        others = [a.design.letters.index(L) for L in tri.hold]
        if others:
            P = P[np.all(np.abs(P[:, others] - np.array(list(tri.hold.values()))) < 1e-9, axis=1)]
        w = tri.weights(P)
        w = w[np.all(w >= -1e-9, axis=1)]
        x, y = tri.xy(w)
        fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="설계점", showlegend=False,
                                 marker=dict(color=t["text"], size=MARKER - 2, symbol="circle-open", line=dict(width=1.5)),
                                 hoverinfo="skip"))
    style(fig, mode, title=f"{a.response} 혼합물 등고선도",
          en=f"Mixture Contour Plot of {a.response} ({', '.join(nm)}) · " + _hold_text(tri, process, a.design),
          height=600, showlegend=False)
    _axes_off(fig)
    return fig


def _lattice(m: int):
    """삼각형 위 무게중심 격자(i + j + k = m)와 삼각형 면(꼭짓점 인덱스)."""
    pts, index = [], {}
    for i in range(m + 1):
        for j in range(m + 1 - i):
            index[(i, j)] = len(pts)
            pts.append((i / m, j / m, (m - i - j) / m))
    faces = []
    for i in range(m):
        for j in range(m - i):
            faces.append((index[(i, j)], index[(i + 1, j)], index[(i, j + 1)]))
            if i + j + 1 < m:
                faces.append((index[(i + 1, j)], index[(i + 1, j + 1)], index[(i, j + 1)]))
    return np.array(pts), np.array(faces)


def mixture_surface_plot(a, triplet=None, *, hold: dict | None = None, process: dict | None = None,
                         mode: str = "light", m: int = 40) -> go.Figure:
    t = tokens(mode)
    tri = Triangle(a.design, triplet, hold)
    w, faces = _lattice(m)
    P = tri.blends(w)
    z = mixture_rows(a, P, process) @ a.beta
    x, y = tri.xy(w)
    cd = P[:, tri.idx]
    nm = tri.names
    fig = go.Figure(go.Mesh3d(
        x=x, y=y, z=z, i=faces[:, 0], j=faces[:, 1], k=faces[:, 2], intensity=z, customdata=cd,
        colorscale=[[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)], flatshading=False,
        colorbar=dict(title=dict(text=a.response, side="right"), tickfont=dict(color=t["text2"])),
        hovertemplate=f"{nm[0]} %{{customdata[0]:.4g}}<br>{nm[1]} %{{customdata[1]:.4g}}<br>{nm[2]} "
                      f"%{{customdata[2]:.4g}}<br>{a.response} %{{z:.4g}}<extra></extra>"))
    zmin = float(np.min(z))
    cx, cy = tri.xy(np.vstack([np.eye(3), np.eye(3)[:1]]))
    fig.add_trace(go.Scatter3d(x=cx, y=cy, z=[zmin] * 4, mode="lines", line=dict(color=t["axis"], width=3),
                               hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter3d(x=cx[:3], y=cy[:3], z=[zmin] * 3, mode="text", text=[f"<b>{s}</b>" for s in nm],
                               textfont=dict(color=t["text"], size=13), hoverinfo="skip", showlegend=False))
    style(fig, mode, title=f"{a.response} 혼합물 표면도",
          en=f"Mixture Surface Plot of {a.response} · " + _hold_text(tri, process, a.design), height=600,
          showlegend=False)
    hidden = dict(showticklabels=False, title="", backgroundcolor=t["surface"], gridcolor=t["grid"], showgrid=False)
    fig.update_layout(scene=dict(xaxis=hidden, yaxis=hidden,
                                 zaxis=dict(title=a.response, backgroundcolor=t["surface"], gridcolor=t["grid"],
                                            color=t["text2"]),
                                 aspectmode="manual", aspectratio=dict(x=1, y=H, z=0.7)))
    return fig


def mixture_feasible_region(analyses: list, bounds: dict, triplet=None, *, hold: dict | None = None,
                            process: dict | None = None, n: int = 101):
    """(삼각형, xs, ys, {반응: Z}, 실현 가능 마스크)."""
    zs, ok, tri = {}, None, None
    for a in analyses:
        tri, xs, ys, Z, Wg, inside = mixture_grid(a, triplet, hold=hold, process=process, n=n)
        lo, hi = bounds[a.response]
        good = (Z >= lo) & (Z <= hi)
        ok = good if ok is None else ok & good
        zs[a.response] = Z
    return tri, xs, ys, zs, ok


def mixture_overlaid_contour_plot(analyses: list, bounds: dict, triplet=None, *, hold: dict | None = None,
                                  process: dict | None = None, mode: str = "light", n: int = 101) -> go.Figure:
    t = tokens(mode)
    tri, xs, ys, zs, ok = mixture_feasible_region(analyses, bounds, triplet, hold=hold, process=process, n=n)
    inside = ~np.isnan(next(iter(zs.values())))
    shade = np.where(inside & ~ok, 1.0, np.nan)
    fig = go.Figure(go.Heatmap(x=xs, y=ys, z=shade, colorscale=[[0, t["muted"]], [1, t["muted"]]], showscale=False,
                               opacity=0.55, hoverinfo="skip"))
    _mask_outside(fig, t)
    tri.frame(fig, t, grid=False)
    for k, (resp, Z) in enumerate(zs.items()):
        color = t["series"][k % len(t["series"])]
        lo, hi = bounds[resp]
        finite = [v for v in (lo, hi) if np.isfinite(v)]
        label = f"{resp}: {lo:g} ~ {hi:g}" if len(finite) == 2 else (f"{resp} ≥ {lo:g}" if np.isfinite(lo) else f"{resp} ≤ {hi:g}")
        for i, val in enumerate(finite):
            fig.add_trace(go.Contour(x=xs, y=ys, z=Z, showscale=False, colorscale=[[0, color], [1, color]],
                                     contours=dict(coloring="lines", start=val, end=val, size=1, showlabels=True,
                                                   labelfont=dict(color=t["text"], size=11)),
                                     line=dict(width=LINE_W), name=label, showlegend=i == 0, legendgroup=resp,
                                     hoverinfo="skip", connectgaps=False))
    a0 = analyses[0]
    style(fig, mode, title=f"혼합물 중첩 등고선도: {', '.join(zs)}",
          en="Overlaid Contour Plot · 회색이 아닌 영역 = 모든 반응이 범위 안 · " + _hold_text(tri, process, a0.design),
          height=620, showlegend=True)
    _axes_off(fig)
    return fig
