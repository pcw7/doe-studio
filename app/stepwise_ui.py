"""단계적 선택 입력(Analyze … > Stepwise) — 분석 화면과 산포 분석 화면이 함께 쓴다."""
from __future__ import annotations

from typing import Callable

import streamlit as st

from app.i18n import T
from doe_core.analysis.stepwise import CRITERIA, DEFAULT_ALPHA, StepwiseOptions

METHOD_KO = {"none": "없음 (None)", "forward_ic": "정보 기준 전진 선택 (Forward information criteria)",
             "stepwise": "단계적 (Stepwise)", "forward": "전진 선택 (Forward selection)",
             "backward": "후진 제거 (Backward elimination)"}
HIER_KO = {"each_step": "매 단계 계층 모형 (Require a hierarchical model at each step)",
           "at_end": "마지막에 항을 더해 계층 모형으로 (Add terms at the end to make the model hierarchical)",
           "none": "계층 모형 요구 안 함 (Do not require a hierarchical model)"}


def stepwise_input(candidate_names: Callable[[], list[str]], prefix: str = "sw") -> StepwiseOptions | None:
    """단계적 선택 설정. candidate_names: E·I 항 선택지(후보 항 이름)를 돌려주는 함수. 방법이 '없음' 이면 None."""
    s1, s2 = st.columns(2)
    method = s1.selectbox(T("방법 (Method)"), list(METHOD_KO), format_func=lambda m: T(METHOD_KO[m]),
                          key=f"{prefix}_method")
    if method == "none":
        return None
    de, dr = DEFAULT_ALPHA[method]
    a_enter = a_remove = None
    crit = "aicc"
    if de is not None:
        a_enter = s2.number_input(T("진입 α (Alpha to enter)"), 0.001, 0.999, de, step=0.01, format="%.3f",
                                  key=f"{prefix}_ae_{method}")
    if dr is not None:
        a_remove = s2.number_input(T("제거 α (Alpha to remove)"), 0.001, 0.999, dr, step=0.01, format="%.3f",
                                   key=f"{prefix}_ar_{method}")
    if method == "forward_ic":
        crit = s2.selectbox(T("기준 (Criterion)"), list(CRITERIA), format_func=CRITERIA.get, key=f"{prefix}_crit")
    hier_opts = [h for h in HIER_KO if not (method == "forward_ic" and h == "at_end")]
    hier = s1.selectbox(T("계층 (Hierarchy)"), hier_opts, format_func=lambda h: T(HIER_KO[h]), key=f"{prefix}_hier")
    scope, extra = "all", False
    if hier != "none":
        scope = s1.radio(T("계층을 요구할 항 (Require hierarchy for)"), ["all", "categorical"], horizontal=True,
                         format_func=lambda v: T({"all": "모든 항 (All terms)",
                                                  "categorical": "범주형 요인 항 (Terms with categorical predictors)"}[v]),
                         key=f"{prefix}_scope")
    if hier == "each_step":
        extra = s1.checkbox(T("계층 유지를 위해 하위 항도 함께 진입 (Extra terms can enter to maintain hierarchy)"),
                            key=f"{prefix}_extra")
    try:
        names = candidate_names()
    except ValueError:
        names = []
    force = st.multiselect(T("E = 모든 모형에 포함 (Include term in every model)"), names, key=f"{prefix}_force")
    initial = []
    if method == "stepwise":
        initial = st.multiselect(T("I = 시작 모형에 포함 (Include term in the initial model)"),
                                 [n for n in names if n not in force], key=f"{prefix}_initial")
    return StepwiseOptions(method=method, alpha_enter=a_enter, alpha_remove=a_remove, criterion=crit, hierarchy=hier,
                           scope=scope, extra_terms=extra, force=tuple(force), initial=tuple(initial))


def selection_details(a, en: bool) -> None:
    """분석 결과의 단계적 선택 정보(방법·세부 표·단계 설명)."""
    from app.state import show_table
    from doe_core.analysis.stepwise import METHOD_TITLE_KO
    sel = getattr(a, "selection", None)
    if sel is None:
        return
    st.markdown(T(f"**{METHOD_TITLE_KO[sel.method]} ({sel.title()})**", f"**{sel.title()}**"))
    st.code("\n".join(sel.method_lines()), language=None)
    if not a.terms:
        st.warning(T("어떤 항도 기준을 넘지 못해 상수만 남았습니다.", "No term met the criterion; only the constant remains."))
    with st.expander(T("모형 선택 세부 (Model selection details)", "Model selection details")):
        st.caption(sel.candidate_line())
        show_table(sel.details_table())
        st.caption("  ".join(sel.footer_lines()))
        st.code("\n".join(sel.step_notes(en=en)), language=None)
