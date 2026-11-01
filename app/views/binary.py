"""이항 반응 분석 화면 — Minitab 'Analyze Binary Response'(요인설계·반응표면·선별 설계)."""
import pandas as pd
import streamlit as st

from app.i18n import T, lang
from app.state import plot_mode, report_downloads, require_ws, show_plot, show_table, ws_caption
from doe_core.analysis.alias import alias_lines, alias_title, factor_name_table, has_aliasing
from doe_core.analysis.binary import analyze_binary
from doe_core.analysis.effects import effects
from doe_core.analysis.model import RS_MODELS
from doe_core.designs.definitive_screening import DefinitiveScreeningDesign
from doe_core.designs.mixture import MixtureDesign
from doe_core.designs.response_surface import ResponseSurfaceDesign
from doe_core.designs.split_plot import SplitPlotDesign
from doe_core.plots.effects_plots import pareto_chart

st.title(T("이항 반응 분석", "Analyze binary response"))
st.caption("Analyze Binary Response (logit)")
ws = require_ws()
st.caption(ws_caption(ws))
d = ws.design
if isinstance(d, (MixtureDesign, SplitPlotDesign)) or type(d).__name__ == "TaguchiDesign":
    st.info(T("이항 반응 분석은 요인설계·반응표면·선별 설계에서 씁니다.",
              "Analyze Binary Response is available for factorial, response surface and screening designs."))
    st.stop()
st.write(T("합격/불합격, 불량 발생 여부처럼 **두 가지 결과**를 로지스틱 회귀(로짓)로 분석합니다. 런마다 사건 수와 시행 수를 "
           "적거나(사건/시행 형식), 런마다 결과 값 하나를 적습니다(이항 열 형식).",
           "Analyze **two-outcome** responses (pass/fail, defect or not) with logistic regression (logit). Enter the number "
           "of events and trials for each run (event/trial format), or one outcome per run (binary format)."))
cols = list(ws.columns.columns)
numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 0]
if not cols:
    st.info(T("분석할 열이 없습니다. **워크시트** 화면에서 결과 열을 추가하세요.",
              "There is no column to analyze. Add a result column on the **Worksheet** page."))
    st.page_link("views/worksheet.py", label=T("워크시트로 가기"), icon=":material/table:")
    st.stop()
is_dsd = isinstance(d, DefinitiveScreeningDesign)
is_rs = isinstance(d, ResponseSurfaceDesign) or is_dsd

with st.container(border=True):
    FORMAT = {"trial": ("사건/시행 형식 (Response in event/trial format)", "Response in event/trial format"),
              "binary": ("이항 열 형식 (Response in binary response format)", "Response in binary response format")}
    form = st.radio(T("반응 형식", "Response format"), list(FORMAT), format_func=lambda f: T(*FORMAT[f]),
                    horizontal=True, key="bin_form")
    c1, c2, c3 = st.columns(3)
    if form == "trial":
        events = c1.selectbox(T("사건 수 열 (Number of events)"), numeric_cols, key="bin_events")
        trials = c2.selectbox(T("시행 수 열 (Number of trials)"), [c for c in numeric_cols if c != events],
                              key="bin_trials")
        event_name = c3.text_input(T("사건 이름 (Event name)"), "Event", key="bin_name")
        event_value = 1
    else:
        events = c1.selectbox(T("반응 열 (Response)"), cols, key="bin_resp")
        vals = sorted({str(v) for v in ws.columns[events].dropna().tolist()}) if events else []
        event_value = c2.selectbox(T("사건 값 (Response event)"), vals, index=len(vals) - 1 if vals else 0,
                                   key="bin_value")
        trials, event_name = None, "Event"
    if is_rs:
        ko = {"linear": "선형 (Linear)", "linear+squares": "선형 + 제곱 (Linear + squares)",
              "linear+interactions": "선형 + 교호작용 (Linear + interactions)", "full quadratic": "완전 2차 (Full quadratic)"}
        model = st.selectbox(T("포함할 항 (Include the following terms)"), list(RS_MODELS), index=0 if is_dsd else 3,
                             format_func=lambda m: T(ko[m]), key="bin_model")
        order = None
    else:
        model = None
        order = st.slider(T("모형에 포함되는 항의 최대 차수 (Include terms up through order)"), 1, len(d.letters),
                          min(2, len(d.letters)), key="bin_order")
    alpha = st.number_input(T("유의 수준 α"), 0.001, 0.5, 0.05, step=0.01, format="%.3f", key="bin_alpha")
    run = st.button(T("분석", "Analyze"), type="primary", key="bin_run")
if run:
    try:
        ev = event_value
        try:
            ev = float(ev)
        except (TypeError, ValueError):
            pass
        st.session_state["binary"] = analyze_binary(ws, events=events, trials=trials, event_name=event_name or "Event",
                                                    event_value=ev, order=order, model=model)
    except Exception as e:  # noqa: BLE001
        st.session_state.pop("binary", None)
        st.error(T("분석하지 못했습니다: ", "Could not analyze: ") + str(e))
a = st.session_state.get("binary")
if a is None:
    st.stop()

from doe_core.report.builders import binary_report  # noqa: E402
report_downloads(lambda figs: binary_report(ws, a, alpha=alpha, figures=figs, lang=lang()),
                 f"rep_bin_{id(a)}_{lang()}", T(f"{a.response}_이항반응분석보고서", f"{a.response}_binary_report"))
if a.removed_terms:
    st.warning(T("다음 항은 앞의 항과 완전히 별칭이라 모형에서 뺐습니다: ",
                 "These terms are completely aliased with earlier terms and were removed: ")
               + ", ".join(t.name for t in a.removed_terms))
tab_tbl, tab_eff = st.tabs([T("결과표", "Tables"), T("효과도", "Effects")])
with tab_tbl:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(T("**방법 (Method)**"))
        show_table(a.method_table())
    with c2:
        st.markdown(T("**반응 정보 (Response Information)**"))
        show_table(a.response_table())
    st.markdown(T("**코드화된 계수 (Coded Coefficients)**"))
    expanded = st.toggle(T("확장 표 (95% CI·Z·P)", "Expanded table (95% CI, Z, P)"), key="bin_expanded")
    show_table(a.coefficients_table(expanded=expanded))
    oc, ocat = a.odds_continuous(), a.odds_categorical()
    if not oc.empty:
        st.markdown(T("**연속 예측변수의 오즈비 (Odds Ratios for Continuous Predictors)**"))
        show_table(oc)
    if not ocat.empty:
        st.markdown(T("**범주형 예측변수의 오즈비 (Odds Ratios for Categorical Predictors)**"))
        show_table(ocat)
        st.caption(T("Level A 의 Level B 에 대한 오즈비. 교호작용 항에 든 예측변수는 계산하지 않습니다('*').",
                     "Odds ratio for level A relative to level B. Not calculated for predictors in interaction terms (*)."))
    st.markdown(T("**모형 요약 (Model Summary)**"))
    show_table(a.summary_table())
    st.markdown(T("**적합도 검정 (Goodness-of-Fit Tests)**"))
    show_table(a.gof_table())
    st.markdown(T("**분산 분석 (Analysis of Variance)**"))
    show_table(a.anova_table())
    eq = a.equation()
    if eq:
        st.markdown(T(f"**회귀 방정식 ({eq[0]})**", f"**{eq[0]}**"))
        st.code(eq[1], language=None, wrap_lines=True)
    if a.two_level and has_aliasing(a):
        st.markdown(T(f"**별칭 구조 ({alias_title(a)})**", f"**{alias_title(a)}**"))
        c1, c2 = st.columns([1, 3])
        with c1:
            show_table(factor_name_table(a))
        with c2:
            st.code("\n".join(alias_lines(a)), language=None)
with tab_eff:
    if not (a.two_level or a.is_rs):
        st.info(T("효과도는 2수준 설계와 반응표면 설계에서 그립니다.",
                  "Effects plots are available for 2-level and response surface designs."))
    else:
        try:
            show_plot(pareto_chart(effects(a, alpha), plot_mode()))
            st.caption(T("표준화 효과 = Wald Z 값, 기준선 = 정규분포 z(1 − α/2).",
                         "Standardized effect = Wald Z; reference line = normal z(1 − α/2)."))
        except ValueError as err:
            st.info(str(err))
