"""Taguchi 설계 분석 화면 — Minitab 'Analyze Taguchi Design' + 'Predict Taguchi Results'."""
from __future__ import annotations

from itertools import combinations

import pandas as pd
import streamlit as st

from app.i18n import T, lang
from app.state import plot_mode, report_downloads, show_plot, show_table, ws_caption
from doe_core.analysis.taguchi import CHARACTERISTICS, SN_TYPES, _val, analyze_taguchi_worksheet, predict_levels
from doe_core.plots.taguchi_plots import taguchi_main_effects_plot

SN_KO = {"larger": "클수록 좋음 (Larger is better)", "smaller": "작을수록 좋음 (Smaller is better)",
         "nominal": "망목 특성 (Nominal is best: 10·log10(ȳ²/s²))", "nominal_s": "망목 특성 (Nominal is best: −10·log10(s²))"}
CHAR_KO = {"sn": "S/N 비 (Signal to Noise ratios)", "mean": "평균 (Means)", "std": "표준편차 (Standard deviations)",
           "lnstd": "ln 표준편차 (Natural log of standard deviations)"}


def render(ws) -> None:
    d = ws.design
    st.title(T("Taguchi 설계 분석", "Analyze Taguchi design"))
    st.caption("Analyze Taguchi Design (static)")
    st.caption(ws_caption(ws))
    numeric_cols = [c for c in ws.columns.columns
                    if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 1]
    if not numeric_cols:
        st.info(T("분석할 반응 열이 없습니다. **워크시트** 화면에서 잡음 조건·반복마다 반응 열을 추가하고 결과를 입력하세요.",
                  "There is no response to analyze. On the **Worksheet** page add one response column per noise "
                  "condition or replicate and enter results."))
        st.page_link("views/worksheet.py", label=T("워크시트로 가기"), icon=":material/table:")
        st.stop()
    letters_name = dict(zip(d.letters, [f.name for f in d.factors]))
    with st.container(border=True):
        c1, c2 = st.columns(2)
        responses = c1.multiselect(T("반응 데이터 열 (Response data are in)"), numeric_cols, default=numeric_cols)
        chars = c2.multiselect(T("적합할 특성 (Fit linear model for)"), list(CHARACTERISTICS), default=["sn", "mean"],
                               format_func=lambda c: T(CHAR_KO[c]))
        c3, c4 = st.columns(2)
        sn_type = c3.selectbox(T("S/N 비 (Signal to Noise Ratio)"), list(SN_TYPES),
                               format_func=lambda s: T(SN_KO[s], SN_TYPES[s]))
        pairs = [f"{a}{b}" for a, b in combinations(d.letters, 2)]
        inter = c4.multiselect(T("교호작용 (Interactions)"), pairs,
                               format_func=lambda w: f"{w} ({letters_name[w[0]]}*{letters_name[w[1]]})")
        run = st.button(T("분석", "Analyze"), type="primary")
    if run:
        try:
            st.session_state["taguchi"] = (tuple(responses), analyze_taguchi_worksheet(
                ws, responses, characteristics=tuple(chars), sn_type=sn_type, terms=[*d.letters, *inter]))
        except Exception as e:  # noqa: BLE001
            st.session_state.pop("taguchi", None)
            st.error(T("분석하지 못했습니다: ", "Could not analyze: ") + str(e))
    res = st.session_state.get("taguchi")
    if not res or res[0] != tuple(responses):
        st.stop()
    analyses = res[1]
    from doe_core.report.builders import taguchi_report
    report_downloads(lambda figs: taguchi_report(ws, analyses, figures=figs, lang=lang()),
                     f"rep_tg_{id(analyses)}_{lang()}", T("Taguchi_분석보고서", "taguchi_analysis_report"))
    tabs = st.tabs([T(CHAR_KO[c]) for c in analyses] + [T("예측", "Predict")])
    mode = plot_mode()
    for tab, (c, a) in zip(tabs, analyses.items()):
        with tab:
            st.markdown(f"**{a.coefficients_title()}**")
            show_table(a.coefficients_table())
            st.markdown(T("**모형 요약 (Model Summary)**"))
            show_table(a.summary_table())
            st.markdown(f"**{a.anova_title()}**")
            show_table(a.anova_table())
            st.markdown(f"**{a.response_title()}**" + (f" — {SN_TYPES[a.sn_type]}" if c == "sn" else ""))
            show_table(a.response_table())
            show_plot(taguchi_main_effects_plot(a, mode))
    with tabs[-1]:
        st.write(T("요인 수준을 고르면 각 특성의 예측값을 계산합니다(Predict Taguchi Results).",
                   "Choose factor levels to predict each characteristic (Predict Taguchi Results)."))
        cols = st.columns(min(4, len(d.factors)))
        settings = {f.name: cols[i % len(cols)].selectbox(f.name, [_val(v) for v in f.levels], key=f"tg_pred_{f.name}")
                    for i, f in enumerate(d.factors)}
        rows = [{T("특성", "Characteristic"): CHARACTERISTICS[c], T("예측값", "Prediction"): f"{predict_levels(a, settings):.4f}"}
                for c, a in analyses.items()]
        show_table(pd.DataFrame(rows))
