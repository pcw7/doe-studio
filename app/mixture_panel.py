"""혼합물 설계 분석 화면 — Minitab 'Analyze Mixture Design'(분석 화면에서 혼합물 설계일 때 그린다)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.state import plot_mode, report_downloads, show_plot, show_table, ws_caption
from doe_core.analysis.diagnostics import unusual_legend, unusual_table
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.mixture import (
    MIX_MODELS, UNITS, component_terms, mixture_terms, predict_mixture, process_words, reference_blend,
)
from doe_core.optimize.mixture_optimizer import optimize_mixture, search_bounds
from doe_core.optimize.predict import prediction_table
from doe_core.plots.mixture_plots import (
    mixture_contour_plot, mixture_overlaid_contour_plot, mixture_surface_plot, response_trace_plot,
)
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


def process_inputs(d, key: str) -> dict:
    """공정 변수 고정값 입력(기본: 낮은 수준)."""
    out = {}
    if not d.process:
        return out
    cols = st.columns(min(4, len(d.process)))
    for i, f in enumerate(d.process):
        with cols[i % len(cols)]:
            if f.is_numeric:
                out[f.name] = st.number_input(f.name, value=float(f.low), key=f"{key}_{f.name}")
            else:
                out[f.name] = st.selectbox(f.name, [f.low, f.high], key=f"{key}_{f.name}")
    return out


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
    from doe_core.report import analysis_report
    report_downloads(lambda figs: analysis_report(ws, a, figures=figs), f"rep_mix_{id(a)}", f"{a.response}_분석보고서")
    tab_tbl, tab_res, tab_trace, tab_con, tab_pred = st.tabs(["결과표", "잔차 그림", "반응 추적 그림",
                                                              "삼각 등고선·표면도", "예측"])
    mode_plot = plot_mode()
    names = [c.name for c in d.components]
    ref = reference_blend(d)
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
            show_plot(four_in_one(a, kind, mode_plot))
    with tab_trace:
        direction = st.radio("추적 방향 (Trace Direction)", ["cox", "piepel"], horizontal=True,
                             format_func={"cox": "Cox (비율)", "piepel": "Piepel (유사성분)"}.get)
        st.caption("기준 혼합물 = 꼭지점 혼합물의 평균(Centroid of vertices): "
                   + ", ".join(f"{n} {v:.4g}" for n, v in zip(names, ref)))
        proc = process_inputs(d, "trace")
        try:
            show_plot(response_trace_plot(a, direction=direction, process=proc, mode=mode_plot))
        except ValueError as err:
            st.info(str(err))
    with tab_con:
        if d.q < 3:
            st.info("삼각 등고선도는 성분이 3개 이상일 때 그립니다.")
        else:
            trip = st.multiselect("축 성분 3개 (X·Y·Z)", names, default=names[:3], max_selections=3)
            hold = {}
            others = [n for n in names if n not in trip]
            if others:
                st.markdown("**나머지 성분 고정값 (비율)**")
                cols = st.columns(min(4, len(others)))
                for i, n in enumerate(others):
                    hold[n] = cols[i % len(cols)].number_input(n, 0.0, 1.0, float(ref[names.index(n)]),
                                                               step=0.01, format="%.4f", key=f"hold_{n}")
            proc = process_inputs(d, "contour")
            n_lv = st.slider("등고선 수", 2, 11, 7, key="mix_levels")
            if len(trip) == 3:
                try:
                    show_plot(mixture_contour_plot(a, trip, hold=hold, process=proc, levels=n_lv, mode=mode_plot))
                    show_plot(mixture_surface_plot(a, trip, hold=hold, process=proc, mode=mode_plot))
                except ValueError as err:
                    st.info(str(err))
    with tab_pred:
        st.write("성분 비율(합 1)과 공정 변수 값을 넣으면 적합치와 신뢰구간·예측구간을 계산합니다(Predict).")
        cols = st.columns(min(4, d.q))
        blend = {n: cols[i % len(cols)].number_input(n, 0.0, 1.0, float(ref[i]), step=0.01, format="%.4f",
                                                     key=f"pred_{n}") for i, n in enumerate(names)}
        proc = process_inputs(d, "pred")
        conf = st.number_input("신뢰 수준 (%)", 50.0, 99.9, 95.0, key="mix_conf")
        try:
            show_table(prediction_table(predict_mixture(a, blend, proc, confidence=conf / 100)))
        except ValueError as err:
            st.info(str(err))


def render_optimizer(ws) -> None:
    """혼합물 반응 최적화(Response Optimizer) 화면."""
    from app.goals import goals_editor, nonzero_bounds, show_results

    d = ws.design
    st.title("혼합물 반응 최적화")
    st.caption("Mixture Response Optimizer — 성분 비율 합 1, 성분 범위·선형 제약 안에서 종합 만족도를 최대화합니다.")
    st.caption(ws_caption(ws))
    numeric_cols = [c for c in ws.columns.columns
                    if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 1]
    if not numeric_cols:
        st.info("반응 열이 없습니다. **워크시트** 화면에서 결과를 입력하세요.")
        st.stop()
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        responses = c1.multiselect("반응 (Responses)", numeric_cols, default=numeric_cols[:1])
        model = c2.selectbox("모든 반응에 쓸 성분 모형", list(MIX_MODELS), index=1, format_func=MIX_KO.get)
        order = c3.slider("공정 변수 항의 차수", 0, len(d.process), min(1, len(d.process))) if d.process else 0
        lo, hi = search_bounds(d)
        st.caption("탐색 범위(비율): " + ", ".join(f"{c.name} {a:.4g}~{b:.4g}" for c, a, b in zip(d.components, lo, hi))
                   + (" · 사용자 정의 설계라 설계점 비율의 범위를 씁니다." if d.kind == "custom" else ""))
    if not responses:
        st.stop()
    models = {}
    for r in responses:
        try:
            models[r] = analyze_worksheet(ws, r, model=model, process_order=order)
        except Exception as e:  # noqa: BLE001
            st.error(f"{r} 모형을 적합하지 못했습니다: {e}")
            st.stop()
    goals = goals_editor(models, key=f"mixgoals_{'_'.join(responses)}_{model}_{order}")
    hold = {}
    with st.expander("고정 (Constraints: Hold at value)"):
        for f in [*d.components, *d.process]:
            if st.checkbox(f"{f.name} 고정", key=f"mhold_on_{f.name}"):
                if hasattr(f, "lower"):
                    hold[f.name] = st.number_input(f"{f.name} 비율", 0.0, 1.0, float(reference_blend(d)[
                        [c.name for c in d.components].index(f.name)]), format="%.4f", key=f"mhold_v_{f.name}")
                elif f.is_numeric:
                    hold[f.name] = st.number_input(f"{f.name} 값", float(f.low), float(f.high), float(f.low),
                                                   key=f"mhold_v_{f.name}")
                else:
                    hold[f.name] = st.selectbox(f"{f.name} 값", [f.low, f.high], key=f"mhold_v_{f.name}")
    if st.button("최적화", type="primary"):
        try:
            st.session_state["mix_opt"] = (responses, model, order, optimize_mixture(list(models.values()), goals,
                                                                                     hold=hold))
        except Exception as e:  # noqa: BLE001
            st.error(f"최적화하지 못했습니다: {e}")
    opt = st.session_state.get("mix_opt")
    if not opt or opt[:3] != (responses, model, order):
        st.stop()
    res = opt[3]
    show_results(res, models, goals)
    from doe_core.report import optimization_report
    report_downloads(lambda figs: optimization_report(models, goals, res, title="혼합물 반응 최적화 보고서"),
                     f"rep_mopt_{id(res)}", "혼합물_최적화보고서")
    if d.q >= 3 and len(responses) >= 2:
        st.subheader("혼합물 중첩 등고선도 (Overlaid Contour Plot)")
        names = [c.name for c in d.components]
        trip = names[:3]
        hold_c = {n: res.settings[n] for n in names if n not in trip}
        proc = {f.name: res.settings[f.name] for f in d.process}
        try:
            show_plot(mixture_overlaid_contour_plot(list(models.values()), nonzero_bounds(goals), trip, hold=hold_c,
                                                    process=proc, mode=plot_mode()))
            st.caption("회색이 아닌 영역: 모든 반응이 만족도 0 이 아닌 범위. 공정 변수와 나머지 성분은 최적 해에 고정.")
        except ValueError as err:
            st.info(str(err))

