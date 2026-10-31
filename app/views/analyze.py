"""분석 화면 — Minitab 'Analyze Factorial Design' · 'Analyze Response Surface Design' + 효과도·잔차·요인 그림·등고선."""
from itertools import combinations

import pandas as pd
import streamlit as st

from app.state import plot_mode, require_ws, show_plot, show_table, ws_caption
from doe_core.analysis.alias import alias_lines, alias_title, factor_name_table, has_aliasing
from doe_core.analysis.diagnostics import unusual_legend, unusual_table
from doe_core.analysis.effects import effects
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.means import means_table
from doe_core.analysis.model import RS_MODELS, factor_term
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
is_dsd = isinstance(d, DefinitiveScreeningDesign)
is_sp = isinstance(d, SplitPlotDesign)
is_rs = isinstance(d, ResponseSurfaceDesign) or is_dsd          # 제곱 항을 쓸 수 있는 설계
if is_dsd:
    st.title("선별 설계 분석")
    st.caption("Analyze Screening Design (Definitive Screening)")
elif is_rs:
    st.title("반응표면 설계 분석")
    st.caption("Analyze Response Surface Design")
else:
    st.title("분할구 설계 분석" if is_sp else "요인설계 분석")
    st.caption("Analyze Factorial Design" + (" (split-plot)" if is_sp else ""))
st.caption(ws_caption(ws))
if is_sp:
    st.caption("바꾸기 어려운 요인(" + ", ".join(d.htc_letters) + ")만으로 된 항은 전구 오차(WP Error)로, "
               "나머지 항은 하위구 오차로 검정합니다.")
names = dict(zip(d.letters, [f.name for f in d.factors]))

numeric_cols = [c for c in ws.columns.columns if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 1]
if not numeric_cols:
    st.info("분석할 반응 열이 없습니다. **워크시트** 화면에서 반응 열을 추가하고 결과를 입력하세요.")
    st.page_link("views/worksheet.py", label="워크시트로 가기", icon=":material/table:")
    st.stop()

with st.container(border=True):
    c1, c2 = st.columns(2)
    response = c1.selectbox("반응 (Responses)", numeric_cols)
    covariates = c2.multiselect("공변량 (Covariates)", [c for c in numeric_cols if c != response])
    k = len(d.letters)
    rs_model = "full quadratic"
    first = "모형 종류로 지정" if is_rs else "차수로 지정"
    mode_terms = st.segmented_control("모형 항 (Terms)", [first, "항 직접 선택"], default=first, required=True)
    if mode_terms == first:
        terms = None
        if is_rs:
            ko = {"linear": "선형 (Linear)", "linear+squares": "선형 + 제곱 (Linear + squares)",
                  "linear+interactions": "선형 + 교호작용", "full quadratic": "완전 2차 (Full quadratic)"}
            rs_model = st.selectbox("포함할 항 (Include the following terms)", list(RS_MODELS), index=0 if is_dsd else 3,
                                    format_func=ko.get)
            order = None
        else:
            order = st.slider("모형에 포함되는 항의 최대 차수 (Include terms up through order)", 1, k, min(2, k))
    else:
        all_terms = [factor_term(d, c) for r in range(1, k + 1) for c in combinations(d.letters, r)]
        if is_rs:
            all_terms = [t for t in all_terms if t.order <= 2] + [factor_term(d, (L, L)) for L in d.letters]
            all_terms.sort(key=lambda t: (t.group_rank, [d.letters.index(L) for L in t.letters]))
        labels = {t.word: f"{t.word}  ({t.name})" for t in all_terms}
        default = [t.word for t in all_terms if t.order <= 2]
        terms = st.multiselect("선택 항 (Selected Terms)", list(labels), default=default, format_func=labels.get)
        order = None
    c3, c4, c5 = st.columns(3)
    has_blocks = d.coded["Blocks"].nunique() > 1
    has_center = (not isinstance(d, (GeneralFullFactorialDesign, ResponseSurfaceDesign, DefinitiveScreeningDesign,
                                     SplitPlotDesign))) and bool((d.coded[d.point_col] == 0).any())
    inc_blocks = c3.checkbox("모형에 블록 포함 (Include blocks)", value=has_blocks, disabled=not has_blocks)
    inc_center = c4.checkbox("모형에 중앙점 포함 (Include center points)", value=has_center, disabled=not has_center)
    alpha = c5.number_input("유의 수준 α", 0.001, 0.5, 0.05, step=0.01, format="%.3f")
    run = st.button("분석", type="primary")

if run:
    try:
        st.session_state["analysis"] = analyze_worksheet(
            ws, response, covariates=covariates, order=order, terms=terms,
            include_blocks=inc_blocks, include_center=inc_center, model=rs_model)
        st.session_state["alpha"] = alpha
    except Exception as e:  # noqa: BLE001
        st.session_state.pop("analysis", None)
        st.error(f"분석하지 못했습니다: {e}")

a = st.session_state.get("analysis")
if a is None:
    st.stop()
alpha = st.session_state.get("alpha", 0.05)
mode = plot_mode()

st.subheader(f"{a.response} 분석 결과")
if a.removed_terms:
    st.warning("다음 항은 앞의 항과 완전히 별칭이라 모형에서 뺐습니다: " + ", ".join(t.name for t in a.removed_terms))
if a.n < len(d.coded):
    st.info(f"반응 또는 공변량이 비어 있는 런 {len(d.coded) - a.n}개를 제외했습니다.")
if a.df_error == 0:
    st.info("오차 자유도가 0 인 포화 모형입니다. 효과도는 Lenth 의 의사 표준오차(PSE)로 판단합니다.")

numeric_letters = [L for L, f in zip(d.letters, d.factors) if getattr(f, "is_numeric", False) and hasattr(f, "low")]
can_contour = len(numeric_letters) >= 2 and not any(t.kind == "center" for t in a.terms)
tab_tbl, tab_eff, tab_res, tab_fac, tab_con = st.tabs(["결과표", "효과도", "잔차 그림", "요인 그림", "등고선·표면도"])

with tab_tbl:
    st.markdown("**코드화된 계수 (Coded Coefficients)**")
    show_table(a.coefficients_table())
    st.markdown("**모형 요약 (Model Summary)**")
    show_table(a.summary_table())
    st.markdown("**분산 분석 (Analysis of Variance)**")
    tbl = a.anova_table()
    levels = [r.level for r in a.anova_rows()]
    tbl["Source"] = [(" " * lv) + s for lv, s in zip(levels, tbl["Source"])]
    show_table(tbl)
    eq = a.equation()
    if eq:
        st.markdown(f"**{'코드화되지 않은 단위의 회귀 방정식' if 'Uncoded' in eq[0] else '코드화된 단위의 회귀 방정식'} ({eq[0]})**")
        st.code(eq[1], language=None, wrap_lines=True)
    if (a.two_level or getattr(a, "is_dsd", False)) and has_aliasing(a):
        st.markdown(f"**별칭 구조 ({alias_title(a)})**")
        c1, c2 = st.columns([1, 3])
        with c1:
            show_table(factor_name_table(a))
        with c2:
            st.code("\n".join(alias_lines(a)), language=None)
    un = unusual_table(a)
    if not un.empty:
        st.markdown("**비정상적인 관측치에 대한 적합치 및 진단 (Fits and Diagnostics for Unusual Observations)**")
        show_table(un)
        st.caption(" · ".join(unusual_legend(a)))
    with st.expander("평균 표 (Means)"):
        try:
            show_table(means_table(a))
        except Exception as err:  # noqa: BLE001
            st.info(f"평균 표를 만들 수 없습니다: {err}")

with tab_eff:
    if not (a.two_level or a.is_rs):
        st.info("효과도는 2수준 설계와 반응표면 설계에서 그립니다.")
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
    kind = st.segmented_control("잔차 종류", ["regular", "standardized", "deleted"], default="regular", required=True,
                                format_func={"regular": "일반", "standardized": "표준화", "deleted": "삭제"}.get)
    if a.df_error == 0 and kind != "regular":
        st.info("오차 자유도가 0 이라 표준화·삭제 잔차를 계산할 수 없습니다.")
    else:
        show_plot(four_in_one(a, kind, mode))

with tab_fac:
    if a.is_rs:
        st.info("반응표면 설계는 **등고선·표면도** 탭에서 요인 효과를 봅니다.")
    else:
        show_plot(main_effects_plot(a, mode=mode))
        pairs = interaction_pairs(a)
        if pairs:
            st.markdown("**교호작용도 (Interaction Plot)**")
            cols = st.columns(2)
            for i, (x, tr) in enumerate(pairs[:6]):
                with cols[i % 2]:
                    show_plot(interaction_plot(a, x, tr, mode))
    if a.two_level and len(d.letters) >= 2:
        st.markdown("**입방체도 (Cube Plot)**")
        default = list(d.letters[: min(3, len(d.letters))])
        pick = st.multiselect("입방체도 요인(2~4개)", list(d.letters), default=default, max_selections=4,
                              format_func=lambda L: f"{L} ({names[L]})")
        if 2 <= len(pick) <= 4:
            show_plot(cube_plot(a, pick, mode))

with tab_con:
    if not can_contour:
        st.info("연속 요인이 2개 이상이고 모형에 중앙점 항이 없어야 등고선도를 그립니다. "
                "중앙점 항이 있으면 '모형에 중앙점 포함' 을 끄고 다시 분석하세요.")
    else:
        c1, c2, c3 = st.columns(3)
        xL = c1.selectbox("X 축", numeric_letters, format_func=lambda L: f"{L} ({names[L]})")
        yL = c2.selectbox("Y 축", [L for L in numeric_letters if L != xL], format_func=lambda L: f"{L} ({names[L]})")
        n_lv = c3.slider("등고선 수", 2, 11, 7)
        hold = {}
        others = [L for L in d.letters if L not in (xL, yL)]
        if others:
            st.markdown("**고정값 (Hold values)**")
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
