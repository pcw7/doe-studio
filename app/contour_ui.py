"""등고선도·표면도 탭 — 분석·산포 분석·이항 반응 화면이 함께 쓴다(값은 모형의 원래 단위: 반응·표준편차·확률)."""
from __future__ import annotations

import streamlit as st

from app.i18n import T
from app.state import show_plot
from doe_core.plots.contour_plots import contour_plot, default_hold, surface_plot


def numeric_letters(d) -> list[str]:
    return [L for L, f in zip(d.letters, d.factors) if getattr(f, "is_numeric", False) and hasattr(f, "low")]


def contour_tab(a, mode: str, prefix: str = "") -> None:
    """X·Y 축, 등고선 수, 나머지 요인의 고정값을 고르고 등고선도와 표면도를 그린다."""
    d = a.design
    names = dict(zip(d.letters, [f.name for f in d.factors]))
    nums = numeric_letters(d)
    if len(nums) < 2:
        st.info(T("연속 요인이 2개 이상이어야 등고선도를 그립니다.", "Contour plots need at least 2 continuous factors."))
        return
    c1, c2, c3 = st.columns(3)
    xL = c1.selectbox(T("X 축"), nums, format_func=lambda L: f"{L} ({names[L]})", key=f"{prefix}con_x")
    yL = c2.selectbox(T("Y 축"), [L for L in nums if L != xL], format_func=lambda L: f"{L} ({names[L]})",
                      key=f"{prefix}con_y")
    n_lv = c3.slider(T("등고선 수"), 2, 11, 7, key=f"{prefix}con_n")
    hold = {}
    others = [L for L in d.letters if L not in (xL, yL)]
    if others:
        st.markdown(T("**고정값 (Hold values)**"))
        defaults = default_hold(a, exclude=(xL, yL))
        cols = st.columns(min(4, len(others)))
        for i, L in enumerate(others):
            f = d.factors[d.letters.index(L)]
            with cols[i % len(cols)]:
                if getattr(f, "is_numeric", False) and hasattr(f, "low"):
                    hold[f.name] = st.number_input(f.name, value=float(defaults[f.name]), key=f"{prefix}hold_{L}")
                else:
                    opts = list(getattr(f, "levels", [f.low, f.high]))
                    hold[f.name] = st.selectbox(f.name, opts, key=f"{prefix}hold_{L}")
    try:
        show_plot(contour_plot(a, xL, yL, hold=hold, levels=n_lv, mode=mode))
        show_plot(surface_plot(a, xL, yL, hold=hold, mode=mode))
    except ValueError as err:
        st.info(str(err))
