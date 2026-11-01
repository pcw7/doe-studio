"""분석 화면 — Minitab 'Analyze Factorial Design' · 'Analyze Response Surface Design' + 효과도·잔차·요인 그림·등고선."""
from itertools import combinations

import pandas as pd
import streamlit as st

from app.i18n import O, T, lang
from app.state import boxcox_input, plot_mode, report_downloads, require_ws, show_plot, show_table, ws_caption
from doe_core.analysis.alias import alias_lines, alias_title, factor_name_table, has_aliasing
from doe_core.analysis.diagnostics import unusual_legend, unusual_table
from doe_core.analysis.storage import fits_table, store_statistics
from doe_core.analysis.effects import effects
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.means import means_table
from doe_core.analysis.model import RS_MODELS, factor_term, factorial_terms, rs_terms
from doe_core.analysis.stepwise import CRITERIA, DEFAULT_ALPHA, METHOD_TITLE_KO, StepwiseOptions
from doe_core.designs.definitive_screening import DefinitiveScreeningDesign
from doe_core.designs.general_full import GeneralFullFactorialDesign
from doe_core.designs.mixture import MixtureDesign
from doe_core.designs.response_surface import ResponseSurfaceDesign
from doe_core.designs.split_plot import SplitPlotDesign
from doe_core.plots.contour_plots import contour_plot, default_hold, surface_plot
from doe_core.plots.effects_plots import half_normal_effects_chart, normal_effects_chart, pareto_chart
from doe_core.plots.factorial_plots import cube_plot, interaction_pairs, interaction_plot, main_effects_plot
from doe_core.plots.residual_plots import four_in_one

ws = require_ws()
d = ws.design
if isinstance(d, MixtureDesign):
    from app.mixture_panel import render
    render(ws)
    st.stop()
from doe_core.designs.taguchi import TaguchiDesign  # noqa: E402
if isinstance(d, TaguchiDesign):
    from app.taguchi_panel import render as render_taguchi
    render_taguchi(ws)
    st.stop()
is_dsd = isinstance(d, DefinitiveScreeningDesign)
is_sp = isinstance(d, SplitPlotDesign)
is_rs = isinstance(d, ResponseSurfaceDesign) or is_dsd          # 제곱 항을 쓸 수 있는 설계
if is_dsd:
    st.title(T("선별 설계 분석", "Analyze screening design"))
    st.caption("Analyze Screening Design (Definitive Screening)")
elif is_rs:
    st.title(T("반응표면 설계 분석", "Analyze response surface design"))
    st.caption("Analyze Response Surface Design")
else:
    st.title(T("분할구 설계 분석", "Analyze split-plot design") if is_sp else T("요인설계 분석", "Analyze factorial design"))
    st.caption("Analyze Factorial Design" + (" (split-plot)" if is_sp else ""))
st.caption(ws_caption(ws))
if is_sp:
    htc = ", ".join(d.htc_letters)
    st.caption(T(f"바꾸기 어려운 요인({htc})만으로 된 항은 전구 오차(WP Error)로, 나머지 항은 하위구 오차로 검정합니다.",
                 f"Terms with only hard-to-change factors ({htc}) are tested against the whole-plot error (WP Error); "
                 "the other terms against the subplot error."))
names = dict(zip(d.letters, [f.name for f in d.factors]))

numeric_cols = [c for c in ws.columns.columns if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 1]
if not numeric_cols:
    st.info(T("분석할 반응 열이 없습니다. **워크시트** 화면에서 반응 열을 추가하고 결과를 입력하세요.",
              "There is no response to analyze. Add a response column on the **Worksheet** page and enter results."))
    st.page_link("views/worksheet.py", label=T("워크시트로 가기"), icon=":material/table:")
    st.stop()

with st.container(border=True):
    c1, c2 = st.columns(2)
    response = c1.selectbox(T("반응 (Responses)"), numeric_cols)
    covariates = c2.multiselect(T("공변량 (Covariates)"), [c for c in numeric_cols if c != response])
    k = len(d.letters)
    rs_model = "full quadratic"
    first = "모형 종류로 지정" if is_rs else "차수로 지정"
    mode_terms = st.segmented_control(T("모형 항 (Terms)"), [first, "항 직접 선택"], default=first, required=True,
                                      format_func=O)
    if mode_terms == first:
        terms = None
        if is_rs:
            ko = {"linear": "선형 (Linear)", "linear+squares": "선형 + 제곱 (Linear + squares)",
                  "linear+interactions": "선형 + 교호작용 (Linear + interactions)",
                  "full quadratic": "완전 2차 (Full quadratic)"}
            rs_model = st.selectbox(T("포함할 항 (Include the following terms)"), list(RS_MODELS),
                                    index=0 if is_dsd else 3, format_func=lambda m: T(ko[m]))
            order = None
        else:
            order = st.slider(T("모형에 포함되는 항의 최대 차수 (Include terms up through order)"), 1, k, min(2, k))
    else:
        all_terms = [factor_term(d, c) for r in range(1, k + 1) for c in combinations(d.letters, r)]
        if is_rs:
            all_terms = [t for t in all_terms if t.order <= 2] + [factor_term(d, (L, L)) for L in d.letters]
            all_terms.sort(key=lambda t: (t.group_rank, [d.letters.index(L) for L in t.letters]))
        labels = {t.word: f"{t.word}  ({t.name})" for t in all_terms}
        default = [t.word for t in all_terms if t.order <= 2]
        terms = st.multiselect(T("선택 항 (Selected Terms)"), list(labels), default=default, format_func=labels.get)
        order = None
    c3, c4, c5 = st.columns(3)
    has_blocks = d.coded["Blocks"].nunique() > 1
    has_center = (not isinstance(d, (GeneralFullFactorialDesign, ResponseSurfaceDesign, DefinitiveScreeningDesign,
                                     SplitPlotDesign))) and bool((d.coded[d.point_col] == 0).any())
    inc_blocks = c3.checkbox(T("모형에 블록 포함 (Include blocks)"), value=has_blocks, disabled=not has_blocks)
    inc_center = c4.checkbox(T("모형에 중앙점 포함 (Include center points)"), value=has_center, disabled=not has_center)
    alpha = c5.number_input(T("유의 수준 α"), 0.001, 0.5, 0.05, step=0.01, format="%.3f")
    sw_opts = None
    with st.expander(T("단계적 선택 (Stepwise)", "Stepwise"), expanded=False):
        if is_sp:
            st.caption(T("분할구 설계에서는 단계적 선택을 쓸 수 없습니다.",
                         "Stepwise methods are not available for split-plot designs."))
        else:
            METHOD_KO = {"none": "없음 (None)", "forward_ic": "정보 기준 전진 선택 (Forward information criteria)",
                         "stepwise": "단계적 (Stepwise)", "forward": "전진 선택 (Forward selection)",
                         "backward": "후진 제거 (Backward elimination)"}
            HIER_KO = {"each_step": "매 단계 계층 모형 (Require a hierarchical model at each step)",
                       "at_end": "마지막에 항을 더해 계층 모형으로 (Add terms at the end to make the model hierarchical)",
                       "none": "계층 모형 요구 안 함 (Do not require a hierarchical model)"}
            s1, s2 = st.columns(2)
            method = s1.selectbox(T("방법 (Method)"), list(METHOD_KO), format_func=lambda m: T(METHOD_KO[m]),
                                  key="sw_method")
            if method != "none":
                de, dr = DEFAULT_ALPHA[method]
                a_enter = a_remove = None
                crit = "aicc"
                if de is not None:
                    a_enter = s2.number_input(T("진입 α (Alpha to enter)"), 0.001, 0.999, de, step=0.01, format="%.3f",
                                              key=f"sw_ae_{method}")
                if dr is not None:
                    a_remove = s2.number_input(T("제거 α (Alpha to remove)"), 0.001, 0.999, dr, step=0.01,
                                               format="%.3f", key=f"sw_ar_{method}")
                if method == "forward_ic":
                    crit = s2.selectbox(T("기준 (Criterion)"), list(CRITERIA), format_func=CRITERIA.get, key="sw_crit")
                hier_opts = [h for h in HIER_KO if not (method == "forward_ic" and h == "at_end")]
                hier = s1.selectbox(T("계층 (Hierarchy)"), hier_opts, format_func=lambda h: T(HIER_KO[h]), key="sw_hier")
                scope, extra = "all", False
                if hier != "none":
                    scope = s1.radio(T("계층을 요구할 항 (Require hierarchy for)"), ["all", "categorical"], horizontal=True,
                                     format_func=lambda v: T({"all": "모든 항 (All terms)",
                                                              "categorical": "범주형 요인 항 (Terms with categorical predictors)"}[v]),
                                     key="sw_scope")
                if hier == "each_step":
                    extra = s1.checkbox(T("계층 유지를 위해 하위 항도 함께 진입 (Extra terms can enter to maintain hierarchy)"),
                                        key="sw_extra")
                try:
                    if is_rs:
                        cand = rs_terms(d, model=rs_model, terms=terms, covariates=covariates, include_blocks=inc_blocks,
                                        blocks_present=has_blocks)
                    else:
                        cand = factorial_terms(d, order=order, terms=terms, covariates=covariates,
                                               include_blocks=inc_blocks, include_center=inc_center,
                                               blocks_present=has_blocks, center_present=has_center)
                    cand_names = [t.name for t in cand]
                except ValueError:
                    cand_names = []
                force = st.multiselect(T("E = 모든 모형에 포함 (Include term in every model)"), cand_names, key="sw_force")
                initial = []
                if method == "stepwise":
                    initial = st.multiselect(T("I = 시작 모형에 포함 (Include term in the initial model)"),
                                             [n for n in cand_names if n not in force], key="sw_initial")
                sw_opts = StepwiseOptions(method=method, alpha_enter=a_enter, alpha_remove=a_remove, criterion=crit,
                                          hierarchy=hier, scope=scope, extra_terms=extra, force=tuple(force),
                                          initial=tuple(initial))
    bc_spec, bc_rounded, w_col = None, True, None
    with st.expander(T("옵션 (Options)", "Options"), expanded=False):
        if is_sp:
            st.caption(T("분할구 설계에서는 Box-Cox 변환을 지원하지 않습니다.",
                         "Box-Cox transformation is not supported for split-plot designs."))
        else:
            bc_spec, bc_rounded = boxcox_input("bc_analyze")
            st.caption(T("Box-Cox 변환은 반응이 모두 양수일 때 쓸 수 있습니다. 분석 표는 변환한 단위, "
                         "예측·최적화·등고선은 원래 단위로 보입니다.",
                         "Box-Cox requires all responses to be positive. Tables use transformed units; "
                         "predictions, the optimizer and contour plots use original units."))
            w_pick = st.selectbox(T("가중치 열 (Weights)"), ["-"] + [c for c in numeric_cols if c != response],
                                  key="weights_col")
            w_col = None if w_pick == "-" else w_pick
            st.caption(T("가중 회귀: 가중치는 0 이상이고 0 인 런은 분석에서 빠집니다.",
                         "Weighted regression: weights must be ≥ 0; runs with weight 0 are left out."))
        conf_pct = st.number_input(T("모든 구간의 신뢰수준(%) (Confidence level for all intervals)"), 80.0, 99.9, 95.0,
                                   step=1.0, format="%.1f", key="conf_level")
    run = st.button(T("분석", "Analyze"), type="primary")

if run:
    try:
        st.session_state["analysis"] = analyze_worksheet(
            ws, response, covariates=covariates, order=order, terms=terms,
            include_blocks=inc_blocks, include_center=inc_center, model=rs_model, stepwise=sw_opts,
            boxcox=bc_spec, boxcox_rounded=bc_rounded, weights=w_col)
        sel = st.session_state["analysis"].selection
        st.session_state["alpha"] = sel.effects_alpha(alpha) if sel is not None else alpha
        st.session_state["confidence"] = conf_pct / 100
    except Exception as e:  # noqa: BLE001
        st.session_state.pop("analysis", None)
        st.error(T("분석하지 못했습니다: ", "Could not analyze: ") + str(e))

a = st.session_state.get("analysis")
if a is None:
    st.stop()
alpha = st.session_state.get("alpha", 0.05)
mode = plot_mode()

st.subheader(T(f"{a.response} 분석 결과", f"Results for {a.response}"))
if a.removed_terms:
    st.warning(T("다음 항은 앞의 항과 완전히 별칭이라 모형에서 뺐습니다: ",
                 "These terms are completely aliased with earlier terms and were removed: ")
               + ", ".join(t.name for t in a.removed_terms))
if a.n < len(d.coded):
    st.info(T(f"반응 또는 공변량이 비어 있는 런 {len(d.coded) - a.n}개를 제외했습니다.",
              f"{len(d.coded) - a.n} runs with a missing response or covariate were left out."))
if a.df_error == 0:
    st.info(T("오차 자유도가 0 인 포화 모형입니다. 효과도는 Lenth 의 의사 표준오차(PSE)로 판단합니다.",
              "Saturated model (0 error DF). Effects plots use Lenth's pseudo standard error (PSE)."))

numeric_letters = [L for L, f in zip(d.letters, d.factors) if getattr(f, "is_numeric", False) and hasattr(f, "low")]
can_contour = len(numeric_letters) >= 2 and not any(t.kind == "center" for t in a.terms)
from doe_core.report import analysis_report  # noqa: E402
report_downloads(lambda figs: analysis_report(ws, a, alpha=alpha, figures=figs, lang=lang()), f"rep_an_{id(a)}_{lang()}",
                 T(f"{a.response}_분석보고서", f"{a.response}_analysis_report"))
tab_tbl, tab_eff, tab_res, tab_fac, tab_con = st.tabs([T("결과표", "Tables"), T("효과도", "Effects"),
                                                      T("잔차 그림", "Residuals"), T("요인 그림", "Factorial plots"),
                                                      T("등고선·표면도", "Contour & surface")])

with tab_tbl:
    if getattr(a, "boxcox", None) is not None:
        st.markdown(T("**방법 (Method)**"))
        show_table(a.boxcox.method_table())
        st.caption(T(f"분석 표는 변환한 반응 {a.response_label} 기준입니다.",
                     f"Tables are for the transformed response {a.response_label}."))
    sel = a.selection
    if sel is not None:
        st.markdown(T(f"**{METHOD_TITLE_KO[sel.method]} ({sel.title()})**", f"**{sel.title()}**"))
        st.code("\n".join(sel.method_lines()), language=None)
        if not a.terms:
            st.warning(T("어떤 항도 기준을 넘지 못해 상수만 남았습니다.", "No term met the criterion; only the constant remains."))
        with st.expander(T("모형 선택 세부 (Model selection details)", "Model selection details")):
            st.caption(sel.candidate_line())
            show_table(sel.details_table())
            st.caption("  ".join(sel.footer_lines()))
            st.code("\n".join(sel.step_notes(en=lang() == "en")), language=None)
    st.markdown(T("**코드화된 계수 (Coded Coefficients)**"))
    conf = st.session_state.get("confidence", 0.95)
    coef_expanded = st.toggle(T(f"확장 계수표 ({conf:.0%} 신뢰구간)", f"Expanded table ({conf:.0%} CI)"),
                              key="coef_expanded")
    show_table(a.coefficients_table(expanded=coef_expanded, confidence=conf))
    st.markdown(T("**모형 요약 (Model Summary)**"))
    if is_sp:                                   # 분할구 설계는 AICc·BIC 를 보이지 않는다(문서)
        show_table(a.summary_table())
    else:
        expanded = st.toggle(T("확장 표 (PRESS·AICc·BIC)", "Expanded table (PRESS, AICc, BIC)"), key="summary_expanded")
        show_table(a.summary_table(expanded=expanded))
    st.markdown(T("**분산 분석 (Analysis of Variance)**"))
    tbl = a.anova_table()
    levels = [r.level for r in a.anova_rows()]
    tbl["Source"] = [(" " * lv) + s for lv, s in zip(levels, tbl["Source"])]
    show_table(tbl)
    eq = a.equation()
    if eq:
        ko_eq = "코드화되지 않은 단위의 회귀 방정식" if "Uncoded" in eq[0] else "코드화된 단위의 회귀 방정식"
        st.markdown(T(f"**{ko_eq} ({eq[0]})**", f"**{eq[0]}**"))
        st.code(eq[1], language=None, wrap_lines=True)
    if (a.two_level or getattr(a, "is_dsd", False)) and has_aliasing(a):
        st.markdown(T(f"**별칭 구조 ({alias_title(a)})**", f"**{alias_title(a)}**"))
        c1, c2 = st.columns([1, 3])
        with c1:
            show_table(factor_name_table(a))
        with c2:
            st.code("\n".join(alias_lines(a)), language=None)
    un = unusual_table(a)
    if not un.empty:
        st.markdown(T("**비정상적인 관측치에 대한 적합치 및 진단 (Fits and Diagnostics for Unusual Observations)**"))
        show_table(un)
        st.caption(" · ".join(unusual_legend(a)))
    with st.expander(T("평균 표 (Means)")):
        try:
            show_table(means_table(a))
        except Exception as err:  # noqa: BLE001
            st.info(T("평균 표를 만들 수 없습니다: ", "Means are not available: ") + str(err))
    with st.expander(T("모든 관측치의 적합치 및 진단 (Fits and Diagnostics for All Observations)",
                       "Fits and Diagnostics for All Observations")):
        show_table(fits_table(a, conf), max_rows=60)
    with st.expander(T("워크시트에 저장 (Storage)", "Storage")):
        STORE_KO = {"fits": "적합치 (Fits)", "resid": "잔차 (Residuals)", "sres": "표준화 잔차 (Standardized residuals)",
                    "tres": "삭제 잔차 (Deleted residuals)", "hi": "레버리지 (Leverages)", "cook": "Cook 거리 (Cook's distance)",
                    "dfit": "DFITS (DFITS)", "bcre": "Box-Cox 변환 반응 (Box-Cox transformation of response)",
                    "bfit": "원래 반응 단위 적합치 (Fits for original response)"}
        keys = [k for k in STORE_KO if k not in ("bcre", "bfit") or getattr(a, "boxcox", None) is not None]
        pick = st.multiselect(T("저장할 통계", "Statistics to store"), keys, default=["fits", "resid"],
                              format_func=lambda k: T(STORE_KO[k]), key="store_pick")
        if st.button(T("저장", "Store"), key="store_btn"):
            try:
                new = store_statistics(ws, a, pick)
                st.success(T("저장한 열: ", "Stored columns: ") + ", ".join(new))
            except Exception as err:  # noqa: BLE001
                st.error(T("저장하지 못했습니다: ", "Could not store: ") + str(err))

with tab_eff:
    if not a.terms:
        st.info(T("모형에 항이 없어 효과도를 그리지 않습니다.", "The model has no terms, so there are no effects plots."))
    elif not (a.two_level or a.is_rs):
        st.info(T("효과도는 2수준 설계와 반응표면 설계에서 그립니다.",
                  "Effects plots are available for 2-level and response surface designs."))
    else:
        try:
            e = effects(a, alpha)
            show_plot(pareto_chart(e, mode))
            c1, c2 = st.columns(2)
            with c1:
                show_plot(normal_effects_chart(e, mode))
            with c2:
                show_plot(half_normal_effects_chart(e, mode))
            if e.pse is not None:
                st.caption(f"Lenth PSE = {e.pse:.4g}, ME = {e.reference:.4g}")
        except ValueError as err:
            st.info(str(err))

with tab_res:
    kind = st.segmented_control(T("잔차 종류"), ["regular", "standardized", "deleted"], default="regular", required=True,
                                format_func=lambda v: T({"regular": "일반", "standardized": "표준화", "deleted": "삭제"}[v],
                                                        O(v)))
    if a.df_error == 0 and kind != "regular":
        st.info(T("오차 자유도가 0 이라 표준화·삭제 잔차를 계산할 수 없습니다.",
                  "With 0 error DF, standardized and deleted residuals cannot be calculated."))
    else:
        show_plot(four_in_one(a, kind, mode))

with tab_fac:
    if a.is_rs:
        st.info(T("반응표면 설계는 **등고선·표면도** 탭에서 요인 효과를 봅니다.",
                  "For response surface designs, see the factor effects on the **Contour & surface** tab."))
    else:
        show_plot(main_effects_plot(a, mode=mode))
        pairs = interaction_pairs(a)
        if pairs:
            st.markdown(T("**교호작용도 (Interaction Plot)**"))
            cols = st.columns(2)
            for i, (x, tr) in enumerate(pairs[:6]):
                with cols[i % 2]:
                    show_plot(interaction_plot(a, x, tr, mode))
    if a.two_level and len(d.letters) >= 2:
        st.markdown(T("**입방체도 (Cube Plot)**"))
        default = list(d.letters[: min(3, len(d.letters))])
        pick = st.multiselect(T("입방체도 요인(2~4개)", "Cube plot factors (2 to 4)"), list(d.letters), default=default,
                              max_selections=4, format_func=lambda L: f"{L} ({names[L]})")
        if 2 <= len(pick) <= 4:
            show_plot(cube_plot(a, pick, mode))

with tab_con:
    if not can_contour:
        st.info(T("연속 요인이 2개 이상이고 모형에 중앙점 항이 없어야 등고선도를 그립니다. "
                  "중앙점 항이 있으면 '모형에 중앙점 포함' 을 끄고 다시 분석하세요.",
                  "Contour plots need at least 2 continuous factors and no center point term. "
                  "If the model has a center point term, clear 'Include center points' and analyze again."))
    else:
        c1, c2, c3 = st.columns(3)
        xL = c1.selectbox(T("X 축"), numeric_letters, format_func=lambda L: f"{L} ({names[L]})")
        yL = c2.selectbox(T("Y 축"), [L for L in numeric_letters if L != xL], format_func=lambda L: f"{L} ({names[L]})")
        n_lv = c3.slider(T("등고선 수"), 2, 11, 7)
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
                        hold[f.name] = st.number_input(f.name, value=float(defaults[f.name]), key=f"hold_{L}")
                    else:
                        opts = list(getattr(f, "levels", [f.low, f.high]))
                        hold[f.name] = st.selectbox(f.name, opts, key=f"hold_{L}")
        try:
            show_plot(contour_plot(a, xL, yL, hold=hold, levels=n_lv, mode=mode))
            show_plot(surface_plot(a, xL, yL, hold=hold, mode=mode))
        except ValueError as err:
            st.info(str(err))
