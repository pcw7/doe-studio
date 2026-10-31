"""반응 최적화 목표 입력과 결과 표 — 요인·반응표면 최적화 화면과 혼합물 최적화 화면이 함께 쓴다."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from app.state import show_table
from doe_core.optimize.optimizer import (
    default_goal, multiple_response_prediction, parameters_table, setting_table, solution_table,
)

GOAL_KO = {"maximize": "최대화", "minimize": "최소화", "target": "목표값"}
GOAL_EN = {v: k for k, v in GOAL_KO.items()}


def goals_editor(models: dict, key: str) -> list:
    """목표 표(반응·목표·하한·목표값·상한·가중치·중요도)를 그리고 ResponseGoal 목록을 돌려준다. 잘못되면 멈춘다."""
    st.subheader("목표 (Desirability)")
    st.write("목표·하한·목표값·상한을 정합니다. 빈 값은 데이터 최솟값·최댓값으로 채웁니다. 가중치·중요도는 0.1~10.")
    rows = [{"반응": r, "목표": "최대화", "하한": float(np.min(a.y)), "목표값": float(np.max(a.y)),
             "상한": float(np.max(a.y)), "가중치": 1.0, "중요도": 1.0} for r, a in models.items()]
    gdf = st.data_editor(pd.DataFrame(rows), key=key, hide_index=True, width="stretch", disabled=["반응"],
                         column_config={"목표": st.column_config.SelectboxColumn("목표", options=list(GOAL_EN),
                                                                                 required=True)})
    goals = []
    try:
        for row in gdf.itertuples(index=False):
            a = models[row[0]]
            g = GOAL_EN[row[1]]
            lo, tg, hi = float(row[2]), float(row[3]), float(row[4])
            ymin, ymax = float(np.min(a.y)), float(np.max(a.y))
            kw = {}
            if g in ("maximize", "target") and not np.isclose(lo, ymin):
                kw["lower"] = lo
            if g in ("minimize", "target") and not np.isclose(hi, ymax):
                kw["upper"] = hi
            if g == "target" or not np.isclose(tg, ymax if g == "maximize" else ymin):
                kw["target"] = tg
            goals.append(default_goal(a, g, weight=float(row[5]), importance=float(row[6]), **kw))
    except Exception as e:  # noqa: BLE001
        st.error(f"목표 설정이 올바르지 않습니다: {e}")
        st.stop()
    return goals


def show_results(res, models: dict, goals: list) -> None:
    st.subheader("결과")
    st.metric("종합 만족도 (Composite Desirability)", f"{res.D:.4f}")
    st.markdown("**파라미터 (Parameters)**")
    show_table(parameters_table(list(models.values()), goals))
    st.markdown("**해 (Solution)**")
    show_table(solution_table(res, goals))
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("**설정 (Setting)**")
        show_table(setting_table(res))
    with c2:
        st.markdown("**다중 반응 예측 (Multiple Response Prediction)**")
        show_table(multiple_response_prediction(res))
        show_table(pd.DataFrame([{"반응": r, "개별 만족도 d": f"{v:.5f}"} for r, v in res.d.items()]))


def nonzero_bounds(goals: list) -> dict:
    """만족도가 0 이 아닌 범위: 최대화 (하한, ∞), 최소화 (−∞, 상한), 목표값 (하한, 상한)."""
    return {g.response: (g.lower if g.lower is not None else -np.inf, g.upper if g.upper is not None else np.inf)
            for g in goals}
