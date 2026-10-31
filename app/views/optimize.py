"""반응 최적화·예측 화면 — Minitab 'Response Optimizer' · 'Predict' · 'Overlaid Contour Plot'."""
import numpy as np
import pandas as pd
import streamlit as st

from app.state import plot_mode, require_ws, show_plot, show_table, ws_caption
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.model import RS_MODELS
from doe_core.designs.general_full import GeneralFullFactorialDesign
from doe_core.designs.response_surface import ResponseSurfaceDesign
from doe_core.optimize.optimizer import (
    default_goal, multiple_response_prediction, optimize, parameters_table, setting_table, solution_table,
)
from doe_core.optimize.predict import predict, prediction_table, settings_table
from doe_core.plots.contour_plots import factor_range, overlaid_contour_plot

GOAL_KO = {"maximize": "최대화", "minimize": "최소화", "target": "목표값"}
GOAL_EN = {v: k for k, v in GOAL_KO.items()}

st.title("반응 최적화·예측")
st.caption("Response Optimizer · Predict · Overlaid Contour Plot")
ws = require_ws()
st.caption(ws_caption(ws))
d = ws.design
is_rs = isinstance(d, ResponseSurfaceDesign)
numeric_cols = [c for c in ws.columns.columns if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 1]
if not numeric_cols:
    st.info("반응 열이 없습니다. **워크시트** 화면에서 결과를 입력하세요.")
    st.stop()

with st.container(border=True):
    c1, c2 = st.columns(2)
    responses = c1.multiselect("반응 (Responses)", numeric_cols, default=numeric_cols[:1])
    covariates = c2.multiselect("공변량 (Covariates)", [c for c in numeric_cols if c not in responses])
    if is_rs:
        ko = {"linear": "선형", "linear+squares": "선형 + 제곱", "linear+interactions": "선형 + 교호작용",
              "full quadratic": "완전 2차"}
        model = st.selectbox("모든 반응에 쓸 모형", list(RS_MODELS), index=3, format_func=ko.get)
        order = None
    else:
        model = "full quadratic"
        order = st.slider("모든 반응에 쓸 모형 차수", 1, len(d.letters), min(2, len(d.letters)))
    st.caption("최적화는 요인 수준 사이를 보간하므로 중앙점 항(Ct Pt)은 넣지 않습니다.")

if not responses:
    st.stop()

models = {}
for r in responses:
    try:
        models[r] = analyze_worksheet(ws, r, covariates=covariates, order=order, model=model, include_center=False)
    except Exception as e:  # noqa: BLE001
        st.error(f"{r} 모형을 적합하지 못했습니다: {e}")
        st.stop()

st.subheader("목표 (Desirability)")
st.write("목표·하한·목표값·상한을 정합니다. 빈 값은 데이터 최솟값·최댓값으로 채웁니다. 가중치·중요도는 0.1~10.")
rows = []
for r, a in models.items():
    rows.append({"반응": r, "목표": "최대화", "하한": float(np.min(a.y)), "목표값": float(np.max(a.y)),
                 "상한": float(np.max(a.y)), "가중치": 1.0, "중요도": 1.0})
gdf = st.data_editor(pd.DataFrame(rows), key=f"goals_{'_'.join(responses)}", hide_index=True, width="stretch",
                     disabled=["반응"],
                     column_config={"목표": st.column_config.SelectboxColumn("목표", options=list(GOAL_EN), required=True)})

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

hold = {}
with st.expander("요인 고정 (Constraints: Hold at value)"):
    for L, f in zip(d.letters, d.factors):
        if st.checkbox(f"{f.name} 고정", key=f"hold_on_{L}"):
            if isinstance(d, GeneralFullFactorialDesign):
                hold[f.name] = st.selectbox(f"{f.name} 값", list(f.levels), key=f"hold_v_{L}")
            elif f.is_numeric:
                lo, hi = factor_range(next(iter(models.values())), L)
                hold[f.name] = st.number_input(f"{f.name} 값", float(lo), float(hi), float((lo + hi) / 2), key=f"hold_v_{L}")
            else:
                hold[f.name] = st.selectbox(f"{f.name} 값", [f.low, f.high], key=f"hold_v_{L}")

if st.button("최적화", type="primary"):
    try:
        st.session_state["opt"] = (responses, optimize(list(models.values()), goals, hold=hold))
    except Exception as e:  # noqa: BLE001
        st.error(f"최적화하지 못했습니다: {e}")

opt = st.session_state.get("opt")
if opt and opt[0] == responses:
    res = opt[1]
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

    cont = [L for L, f in zip(d.letters, d.factors) if getattr(f, "is_numeric", False) and hasattr(f, "low")]
    if len(responses) >= 2 and len(cont) >= 2:
        st.subheader("중첩 등고선도 (Overlaid Contour Plot)")
        names = dict(zip(d.letters, [f.name for f in d.factors]))
        c1, c2 = st.columns(2)
        xL = c1.selectbox("X 축", cont, format_func=lambda L: names[L])
        yL = c2.selectbox("Y 축", [L for L in cont if L != xL], format_func=lambda L: names[L])
        # 만족도가 0 이 아닌 범위: 최대화 (하한, ∞), 최소화 (−∞, 상한), 목표값 (하한, 상한)
        bounds = {g.response: (g.lower if g.lower is not None else -np.inf,
                               g.upper if g.upper is not None else np.inf) for g in goals}
        hold_other = {k: v for k, v in res.settings.items() if k not in (names[xL], names[yL])}
        try:
            show_plot(overlaid_contour_plot(list(models.values()), bounds, xL, yL, hold=hold_other, mode=plot_mode()))
            st.caption("흰 영역: 모든 반응이 만족도 0 이 아닌 범위(최대화는 하한 이상, 최소화는 상한 이하, 목표값은 하한~상한). "
                       "나머지 요인은 최적 해에 고정.")
        except ValueError as err:
            st.info(str(err))

st.divider()
st.subheader("예측 (Predict)")
base = opt[1].settings if opt and opt[0] == responses else {}
if base and st.button("최적 해로 채우기"):
    for L, f in zip(d.letters, d.factors):
        st.session_state[f"pred_{L}"] = base[f.name]
    st.rerun()
inputs = {}
cols = st.columns(min(4, len(d.letters)))
for i, (L, f) in enumerate(zip(d.letters, d.factors)):
    with cols[i % len(cols)]:
        if isinstance(d, GeneralFullFactorialDesign):
            inputs[f.name] = st.selectbox(f.name, list(f.levels), key=f"pred_{L}")
        elif f.is_numeric:
            lo, hi = float(f.low), float(f.high)
            inputs[f.name] = st.number_input(f.name, value=float(base.get(f.name, (lo + hi) / 2)), key=f"pred_{L}",
                                             format="%.6g")
        else:
            opts = [f.low, f.high]
            inputs[f.name] = st.selectbox(f.name, opts, index=opts.index(base[f.name]) if base.get(f.name) in opts else 0,
                                          key=f"pred_{L}")
for r, a in models.items():
    st.markdown(f"**{r}**")
    if a.equation():
        st.code(a.equation()[1], language=None, wrap_lines=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        show_table(settings_table(a, inputs))
    with c2:
        show_table(prediction_table(predict(a, inputs)))
