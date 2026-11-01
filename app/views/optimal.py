"""최적 설계 화면 — Minitab 'Select Optimal Design'(선택 · 증강/개선 · 평가)."""
import pandas as pd
import streamlit as st

from app.i18n import O, T, lang
from app.state import report_downloads, require_ws, set_ws, show_table, worksheet_json, ws_caption
from doe_core.analysis.mixture import MIX_MODELS
from doe_core.analysis.model import RS_MODELS
from doe_core.designs.definitive_screening import DefinitiveScreeningDesign
from doe_core.designs.general_full import GeneralFullFactorialDesign
from doe_core.designs.mixture import MixtureDesign
from doe_core.designs.optimal import augment_optimal_design, evaluate_design, optimal_subset, select_optimal_design
from doe_core.designs.response_surface import ResponseSurfaceDesign
from doe_core.io.worksheet import Worksheet

RS_KO = {"linear": "선형", "linear+squares": "선형 + 제곱", "linear+interactions": "선형 + 교호작용",
         "full quadratic": "완전 2차"}
MIX_KO = {"linear": "선형", "quadratic": "2차", "special cubic": "특수 3차", "full cubic": "완전 3차",
          "special quartic": "특수 4차", "full quartic": "완전 4차"}

st.title(T("최적 설계", "Optimal design"))
st.caption(T("Select Optimal Design — 워크시트의 설계 행(후보점)에서 D-최적 또는 거리 기반으로 점을 고릅니다.",
             "Select Optimal Design — picks points from the worksheet design rows (candidates) by D-optimality or "
             "distance."))
ws = require_ws()
d = ws.design
st.caption(ws_caption(ws))
n_cand = len(d.coded)

with st.container(border=True):
    task = st.segmented_control(T("작업 (Task)"), ["설계 선택 (Select)", "설계 증강·개선 (Augment/improve)",
                                                  "설계 평가 (Evaluate)"], default="설계 선택 (Select)", required=True,
                                format_func=O)
    c1, c2, c3 = st.columns(3)
    model, order = None, None
    if isinstance(d, MixtureDesign):
        model = c1.selectbox(T("모형 (Include the following terms)"), list(MIX_MODELS), index=1,
                             format_func=lambda m: T(MIX_KO[m]))
    elif isinstance(d, (ResponseSurfaceDesign, DefinitiveScreeningDesign)):
        model = c1.selectbox(T("모형 (Include the following terms)"), list(RS_MODELS),
                             index=0 if isinstance(d, DefinitiveScreeningDesign) else 3,
                             format_func=lambda m: T(RS_KO[m]))
    else:
        order = c1.slider(T("모형 항의 최대 차수", "Include terms up through order"), 1, len(d.letters),
                          min(2, len(d.letters)))
    has_blocks = d.coded["Blocks"].nunique() > 1
    inc_blocks = c2.checkbox(T("블록 항 포함 (Block)"), value=has_blocks, disabled=not has_blocks)
    num_cols = [c for c in ws.columns.columns if pd.api.types.is_numeric_dtype(ws.columns[c])]
    indicator_col = None
    if not task.startswith("설계 선택"):
        if not num_cols:
            st.info(T("지시자 열이 없습니다. 워크시트에 지시자 열(뽑을 점 1, 보호할 점 −1, 후보 0)을 만들거나 "
                      "먼저 '설계 선택' 결과를 워크시트에 추가하세요.",
                      "There is no indicator column. Add one to the worksheet (1 = selected, -1 = protected, "
                      "0 = candidate) or first add the result of Select design."))
            st.stop()
        indicator_col = c3.selectbox(T("지시자 열 (Indicator column)"), num_cols,
                                     help=T("음수 = 보호(빼지 않음), 양수 = 초기 설계(교환 가능), 절댓값 = 반복 수, 0 = 후보",
                                            "negative = protected, positive = initial design (exchangeable), "
                                            "absolute value = replicates, 0 = candidate"))
    criterion, improve, n_exch, n_points = "D", None, 1, None
    if not task.startswith("설계 평가"):
        c4, c5, c6 = st.columns(3)
        criterion = "distance" if c4.radio(T("최적성 기준", "Optimality criterion"),
                                          ["D-최적성 (D-optimality)", "거리 기반 (Distance-based)"], format_func=O,
                                          disabled=isinstance(d, GeneralFullFactorialDesign)).startswith("거리") else "D"
        n_points = int(c5.number_input(T("최적 설계의 점 수 (Number of points in optimal design)"), 1, 10 * n_cand,
                                       min(n_cand, 20)))
        if criterion == "D":
            imp = c6.radio(T("개선 방법 (Method)"), ["교환 (Exchange)", "Fedorov", "개선 안 함"], format_func=O)
            improve = {"교": "exchange", "F": "fedorov"}.get(imp[0])
            if improve == "exchange":
                n_exch = int(c6.number_input(T("교환할 점 수", "Points to exchange"), 1, max(1, n_points - 1), 1))
    run = st.button(T("실행", "Run"), type="primary")

if run:
    try:
        kw = dict(model=model, order=order, include_blocks=inc_blocks)
        if task.startswith("설계 선택"):
            res = select_optimal_design(d, n_points, criterion=criterion, improve=improve, n_exchange=n_exch, **kw)
        elif task.startswith("설계 증강"):
            ind = ws.column(indicator_col).fillna(0).values
            res = augment_optimal_design(d, ind, n_points, criterion=criterion, improve=improve, n_exchange=n_exch, **kw)
        else:
            res = evaluate_design(d, ws.column(indicator_col).fillna(0).values, **kw)
        st.session_state["optimal"] = res
    except Exception as e:  # noqa: BLE001
        st.session_state.pop("optimal", None)
        st.error(T("실행하지 못했습니다: ", "Could not run: ") + str(e))

res = st.session_state.get("optimal")
if res is None or res.n_candidates != n_cand:
    st.stop()

st.subheader(T("결과", "Results"))
st.code("\n".join([*res.header_lines(), "Specified Design" if res.task == "evaluate" else "Optimal Design",
                   res.rows_text()]), language=None, wrap_lines=True)
if res.statistics:
    show_table(res.statistics_table().rename(columns={0: T("통계량", "Statistic"), 1: T("값", "Value")}))
    st.caption(T("D-optimality 는 클수록, A-optimality 는 작을수록 좋습니다. 최적성은 설계 크기와 모형이 같을 때만 비교합니다.",
                 "Larger D-optimality and smaller A-optimality are better. Compare optimality only for the same "
                 "design size and model."))
from doe_core.report.builders import optimal_design_report  # noqa: E402
report_downloads(lambda figs: optimal_design_report(res, ws, lang=lang()), f"rep_optd_{id(res)}_{lang()}",
                 T("최적설계보고서", "optimal_design_report"))

if res.task != "evaluate":
    c1, c2, c3 = st.columns(3)
    name = c1.text_input(T("지시자 열 이름", "Indicator column name"), "OptPoint")
    if c1.button(T("지시자 열을 워크시트에 추가", "Add the indicator column to the worksheet")):
        ws.add_column(name.strip() or "OptPoint", res.indicator().tolist(), order="worksheet")
        st.toast(T(f"'{name}' 열을 추가했습니다(뽑힌 횟수).", f"Added column '{name}' (times selected)."))
    sub = Worksheet(optimal_subset(d, res.rows))
    c2.download_button(T("고른 점의 새 워크시트 (.json)", "New worksheet with the selected points (.json)"),
                       worksheet_json(sub), "optimal_design.json", "application/json")
    if c3.button(T("고른 점으로 현재 워크시트 바꾸기", "Replace the current worksheet with the selected points")):
        set_ws(sub)
        st.session_state.pop("optimal", None)
        st.rerun()
