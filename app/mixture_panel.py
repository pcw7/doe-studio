"""혼합물 설계 분석 화면 — Minitab 'Analyze Mixture Design'(분석 화면에서 혼합물 설계일 때 그린다)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.state import plot_mode, show_plot, show_table, ws_caption
from doe_core.analysis.diagnostics import unusual_legend, unusual_table
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.mixture import MIX_MODELS, UNITS, component_terms, mixture_terms, process_words
from doe_core.plots.residual_plots import four_in_one

MIX_KO = {"linear": "선형 (Linear)", "quadratic": "2차 (Quadratic)", "special cubic": "특수 3차 (Special cubic)",
          "full cubic": "완전 3차 (Full cubic)", "special quartic": "특수 4차 (Special quartic)",
          "full quartic": "완전 4차 (Full quartic)"}
UNIT_KO = {"proportions": "비율 (Proportions)", "pseudocomponents": "유사성분 (Pseudocomponents)",
           "amounts": "양 (Amounts)"}


def _candidates(d, inverse_ok: bool) -> list:
    comp = component_terms(d, "full quartic" if d.q <= 5 else "special cubic", inverse=inverse_ok)
    out = list(comp)
    for w in process_words(d, len(d.process)):
        out += [type(t)(t.kind, t.comps, w, "") for t in comp]
    # 이름은 mixture_terms 가 다시 만든다(짧은 표기로 지정)
    return [t.short for t in out]


def render(ws) -> None:
    d = ws.design
    st.title("혼합물 설계 분석")
    st.caption("Analyze Mixture Design")
    st.caption(ws_caption(ws))
    numeric_cols = [c for c in ws.columns.columns
                    if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 1]
    if not numeric_cols:
        st.info("분석할 반응 열이 없습니다. **워크시트** 화면에서 반응 열을 추가하고 결과를 입력하세요.")
        st.page_link("views/worksheet.py", label="워크시트로 가기", icon=":material/table:")
        st.stop()
    inverse_ok = all(c.lower > 0 for c in d.components)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        response = c1.selectbox("반응 (Responses)", numeric_cols)
        units = c2.selectbox("성분 분석 단위 (Analyze Components in)", list(UNITS), format_func=UNIT_KO.get)
        mode = st.segmented_control("모형 항 (Terms)", ["모형 종류로 지정", "항 직접 선택"], default="모형 종류로 지정",
                                    required=True)
        kw: dict = {}
        if mode == "모형 종류로 지정":
            c3, c4, c5 = st.columns(3)
            kw["model"] = c3.selectbox("성분 항 (Include component terms for model)", list(MIX_MODELS), index=1,
                                       format_func=MIX_KO.get)
            if d.process:
                kw["process_order"] = c4.slider("공정 변수 항의 차수 (Include process variable terms up through order)",
                                                0, len(d.process), 1)
            kw["inverse"] = c5.checkbox("역항 포함 (Include inverse component terms)", False,
                                        disabled=not (inverse_ok and units == "proportions"),
                                        help="모든 성분의 하한이 0 보다 크고 비율 단위로 분석할 때만 쓸 수 있습니다.")
        else:
            cands = _candidates(d, inverse_ok and units == "proportions")
            default = [t.short for t in mixture_terms(d, model="quadratic")]
            kw["terms"] = st.multiselect("선택 항 (Selected Terms) — 성분 선형항은 항상 포함", cands,
                                         default=[t for t in default if t in cands])
        has_blocks = d.coded["Blocks"].nunique() > 1
        kw["include_blocks"] = st.checkbox("모형에 블록 포함 (Include blocks in the model)", value=has_blocks,
                                           disabled=not has_blocks)
        run = st.button("분석", type="primary")

    if run:
        try:
            st.session_state["analysis"] = analyze_worksheet(ws, response, units=units, **kw)
        except Exception as e:  # noqa: BLE001
            st.session_state.pop("analysis", None)
            st.error(f"분석하지 못했습니다: {e}")
    a = st.session_state.get("analysis")
    if a is None or not getattr(a, "is_mixture", False):
        st.stop()

    st.subheader(f"{a.response} 분석 결과")
    if a.removed_terms:
        st.warning("다음 항은 앞의 항과 선형 종속이라 모형에서 뺐습니다: " + ", ".join(t.name for t in a.removed_terms))
    tab_tbl, tab_res = st.tabs(["결과표", "잔차 그림"])
    with tab_tbl:
        st.markdown(f"**{a.coefficients_title()}**")
        show_table(a.coefficients_table())
        if a.coefficients_note():
            st.caption(a.coefficients_note())
        st.markdown("**모형 요약 (Model Summary)**")
        show_table(a.summary_table())
        st.markdown(f"**{a.anova_title()}**")
        tbl = a.anova_table()
        tbl["Source"] = [(" " * r.level) + s for r, s in zip(a.anova_rows(), tbl["Source"])]
        show_table(tbl)
        un = unusual_table(a)
        if not un.empty:
            st.markdown("**비정상적인 관측치에 대한 적합치 및 진단 (Fits and Diagnostics for Unusual Observations)**")
            show_table(un)
            st.caption(" · ".join(unusual_legend(a)))
    with tab_res:
        kind = st.segmented_control("잔차 종류", ["regular", "standardized", "deleted"], default="regular",
                                    required=True,
                                    format_func={"regular": "일반", "standardized": "표준화", "deleted": "삭제"}.get)
        if a.df_error == 0 and kind != "regular":
            st.info("오차 자유도가 0 이라 표준화·삭제 잔차를 계산할 수 없습니다.")
        else:
            show_plot(four_in_one(a, kind, plot_mode()))
    st.caption("혼합물 등고선도·반응 추적 그림·최적화는 다음 단계에서 지원합니다.")
