"""산포 분석 화면 — Minitab 'Pre-Process Responses for Analyze Variability' · 'Analyze Variability'."""
import pandas as pd
import streamlit as st

from app.i18n import T, lang
from app.state import plot_mode, report_downloads, require_ws, show_plot, show_table
from app.contour_ui import contour_tab
from app.stepwise_ui import selection_details, stepwise_input
from doe_core.analysis.model import factorial_terms
from doe_core.analysis.alias import alias_lines, alias_title, factor_name_table, has_aliasing
from doe_core.analysis.effects import effects
from doe_core.analysis.variability import analyze_variability, repeat_std, replicate_std, store_preprocessed
from doe_core.designs.definitive_screening import DefinitiveScreeningDesign
from doe_core.designs.mixture import MixtureDesign
from doe_core.designs.response_surface import ResponseSurfaceDesign
from doe_core.designs.split_plot import SplitPlotDesign
from doe_core.plots.effects_plots import pareto_chart
from doe_core.plots.residual_plots import four_in_one

st.title(T("산포 분석", "Analyze variability"))
st.caption("Pre-Process Responses for Analyze Variability · Analyze Variability")
ws = require_ws()
d = ws.design
if isinstance(d, (ResponseSurfaceDesign, DefinitiveScreeningDesign, MixtureDesign, SplitPlotDesign)) or \
        type(d).__name__ == "TaguchiDesign":
    st.info(T("산포 분석은 요인설계(2수준·Plackett-Burman·일반 완전요인)에서 씁니다.",
              "Analyze Variability is available for factorial designs (2-level, Plackett-Burman, general full factorial)."))
    st.stop()
st.write(T("반복 측정의 **표준편차**가 요인에 따라 어떻게 달라지는지 ln(표준편차) 모형으로 분석합니다. "
           "먼저 표준편차 열을 만든 뒤(1) 분석합니다(2).",
           "Model how the **standard deviation** of repeated measurements depends on the factors, using ln(standard "
           "deviation). First create the standard deviation column (1), then analyze it (2)."))

numeric_cols = [c for c in ws.columns.columns if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 0]

# ---------------------------------------------------------------- 1. 전처리
with st.expander(T("1. 표준편차 준비 (Pre-Process Responses for Analyze Variability)",
                   "1. Pre-Process Responses for Analyze Variability"), expanded=True):
    MODE = {"replicates": ("반복 런 — 한 열에서 같은 요인 설정끼리 (Compute for replicates in each response column)",
                           "Compute for replicates in each response column"),
            "repeats": ("반복 측정 — 한 행의 여러 열 (Compute for repeat responses across rows)",
                        "Compute for repeat responses across rows")}
    mode = st.radio(T("표준편차 계산 방법", "How to compute the standard deviations"), list(MODE),
                    format_func=lambda m: T(*MODE[m]), key="var_mode")
    c1, c2, c3 = st.columns(3)
    if mode == "replicates":
        src = c1.selectbox(T("반응 열 (Response)"), numeric_cols, key="var_src") if numeric_cols else None
        base = src or "Y"
    else:
        src = c1.multiselect(T("반복 응답 열(2개 이상)", "Repeat responses across rows of"), numeric_cols, key="var_rep")
        base = src[0] if src else "Y"
    std_name = c2.text_input(T("표준편차 저장 열 (Store standard deviations in)"), f"StDev_{base}", key=f"var_std_{base}")
    cnt_name = c3.text_input(T("개수 저장 열 (Store counts in)"), f"Count_{base}", key=f"var_cnt_{base}")
    if st.button(T("계산해 워크시트에 저장", "Calculate and store"), key="var_pre"):
        try:
            sd, cnt = replicate_std(ws, src) if mode == "replicates" else repeat_std(ws, list(src))
            store_preprocessed(ws, sd, cnt, std_name.strip(), cnt_name.strip() or None)
            st.session_state["var_last"] = (std_name.strip(), cnt_name.strip())
            st.session_state["var_resp"] = std_name.strip()             # 새 열을 분석 대상으로 선택
            st.session_state["var_count"] = cnt_name.strip() or "-"
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(T("계산하지 못했습니다: ", "Could not calculate: ") + str(e))

# ---------------------------------------------------------------- 2. 분석
if not numeric_cols:
    st.stop()
last = st.session_state.get("var_last", (None, None))
with st.container(border=True):
    st.markdown(T("**2. 산포 분석 (Analyze Variability)**", "**2. Analyze Variability**"))
    c1, c2 = st.columns(2)
    std_opts = [c for c in numeric_cols]
    idx = std_opts.index(last[0]) if last[0] in std_opts else 0
    if st.session_state.get("var_resp") not in std_opts:
        st.session_state.pop("var_resp", None)
    if st.session_state.get("var_count") not in ["-"] + numeric_cols:
        st.session_state.pop("var_count", None)
    std_col = c1.selectbox(T("표준편차 열", "Response (standard deviations)"), std_opts, index=idx, key="var_resp")
    cnt_opts = ["-"] + numeric_cols
    cidx = cnt_opts.index(last[1]) if last[1] in cnt_opts else 0
    cnt_col = c2.selectbox(T("개수 열 (Counts) — 가중치 4/ψ′((n−1)/2)", "Counts — weights 4/ψ′((n−1)/2)"), cnt_opts,
                           index=cidx, key="var_count")
    k = len(d.letters)
    order = st.slider(T("모형에 포함되는 항의 최대 차수 (Include terms up through order)"), 1, k, min(2, k), key="var_order")
    alpha = st.number_input(T("유의 수준 α"), 0.001, 0.5, 0.05, step=0.01, format="%.3f", key="var_alpha")
    EST = {"ls": ("최소제곱 (Least squares)", "Least squares"), "ml": ("최대우도 (Maximum likelihood)", "Maximum likelihood")}
    est = st.radio(T("추정 방법 (Estimation method)", "Estimation method"), list(EST), horizontal=True,
                   format_func=lambda k: T(*EST[k]), key="var_est")
    st.caption(T("최소제곱의 p 값으로 항을 고르고 최대우도로 최종 계수를 추정하는 방법을 권합니다. 최대우도는 개수 열이 필요하고 "
                 "표준편차 0 인 런도 쓸 수 있으며, 모형 요약·분산분석표는 보이지 않습니다.",
                 "Use the least squares p-values to choose terms and maximum likelihood for the final coefficients. "
                 "Maximum likelihood needs a counts column, allows standard deviations of 0, and shows no model summary "
                 "or ANOVA table."))
    sw_opts = None
    with st.expander(T("단계적 선택 (Stepwise)", "Stepwise"), expanded=False):
        if est == "ml":
            st.caption(T("최대우도 추정에는 단계적 선택을 쓸 수 없습니다.", "Stepwise is not available with maximum likelihood."))
        else:
            sw_opts = stepwise_input(lambda: [t.name for t in factorial_terms(
                d, order=order, include_center=False, blocks_present=d.coded["Blocks"].nunique() > 1)], "vsw")
    run = st.button(T("분석", "Analyze"), type="primary", key="var_run")
if run:
    try:
        va = analyze_variability(ws, std_col, None if cnt_col == "-" else cnt_col, order=order, stepwise=sw_opts,
                                 method=est)
        st.session_state["variability"] = va
        st.session_state["var_alpha_used"] = va.selection.effects_alpha(alpha) if va.selection is not None else alpha
    except Exception as e:  # noqa: BLE001
        st.session_state.pop("variability", None)
        st.error(T("분석하지 못했습니다: ", "Could not analyze: ") + str(e))
a = st.session_state.get("variability")
if a is None:
    st.stop()
alpha = st.session_state.get("var_alpha_used", alpha)       # 단계적 선택이면 α to remove/enter

from doe_core.report import analysis_report  # noqa: E402
report_downloads(lambda figs: analysis_report(ws, a, alpha=alpha, figures=figs, lang=lang()),
                 f"rep_var_{id(a)}_{lang()}", T(f"{a.response}_산포분석보고서", f"{a.response}_variability_report"))
tab_tbl, tab_eff, tab_res, tab_con = st.tabs([T("결과표", "Tables"), T("효과도", "Effects"), T("잔차 그림", "Residuals"),
                                              T("등고선·표면도(표준편차)", "Contour & surface (standard deviation)")])
mode_plot = plot_mode()
with tab_tbl:
    st.markdown(T("**방법 (Method)**"))
    show_table(a.method_table())
    selection_details(a, lang() == "en")
    st.markdown(f"**{a.coefficients_title()}**")
    show_table(a.coefficients_table())
    st.caption(T("Ratio Effect = exp(Effect): 높은 수준의 표준편차가 낮은 수준의 몇 배인지.",
                 "Ratio Effect = exp(Effect): the ratio of the standard deviation at the high level to the low level."))
    if getattr(a, "is_ml", False):
        st.caption(T("최대우도 추정에서는 모형 요약과 분산분석표를 표시하지 않습니다(Minitab 과 같음). 유의성은 Z 값으로 봅니다.",
                     "With maximum likelihood, the model summary and ANOVA table are not shown (as in Minitab); use the "
                     "Z-values for significance."))
    else:
        st.markdown(f"**{a.summary_title()}**")
        show_table(a.summary_table())
        st.markdown(f"**{a.anova_title()}**")
        tbl = a.anova_table()
        tbl["Source"] = [(" " * r.level) + s for r, s in zip(a.anova_rows(), tbl["Source"])]
        show_table(tbl)
    eq = a.equation()
    if eq:
        st.markdown(f"**{eq[0]}**")
        st.code(eq[1], language=None, wrap_lines=True)
    if a.two_level and has_aliasing(a):
        st.markdown(f"**{alias_title(a)}**")
        c1, c2 = st.columns([1, 3])
        with c1:
            show_table(factor_name_table(a))
        with c2:
            st.code("\n".join(alias_lines(a)), language=None)
with tab_eff:
    if not a.two_level:
        st.info(T("효과도는 2수준 설계에서 그립니다.", "Effects plots are available for 2-level designs."))
    else:
        try:
            show_plot(pareto_chart(effects(a, alpha), mode_plot))
        except ValueError as err:
            st.info(str(err))
with tab_res:
    if getattr(a, "is_ml", False):
        st.info(T("잔차 그림은 최소제곱 추정에서 그립니다.", "Residual plots are drawn for least squares estimation."))
    elif a.df_error == 0:
        st.info(T("오차 자유도가 0 이라 잔차 그림을 그리지 않습니다.", "With 0 error DF, residual plots are not drawn."))
    else:
        show_plot(four_in_one(a, "regular", mode_plot))
with tab_con:
    st.caption(T("값은 표준편차(exp(Ln 모형))입니다.", "Values are standard deviations (exp of the Ln model)."))
    contour_tab(a, mode_plot, "var_")
