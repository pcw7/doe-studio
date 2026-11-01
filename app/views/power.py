"""검정력·표본 크기 화면 — Minitab 'Power and Sample Size'(2-Level Factorial · Plackett-Burman · General Full Factorial)."""
import streamlit as st

from app.i18n import T
from app.state import plot_mode, show_plot, show_table
from doe_core.plots.power_plots import power_curve
from doe_core.power import power_gff, power_pb, power_two_level

st.title(T("검정력·표본 크기", "Power and sample size"))
st.caption("Power and Sample Size for 2-Level Factorial / Plackett-Burman / General Full Factorial Design")
st.write(T("실험 전에 **몇 번 반복해야 원하는 크기의 효과를 찾을 수 있는지** 계산합니다. 반복 수·효과·검정력 중 두 가지를 "
           "적으면 나머지 하나를 구합니다. 여러 값은 쉼표로 구분합니다.",
           "Before running the experiment, find **how many replicates are needed to detect an effect of a given size**. "
           "Enter two of replicates, effects and power values to solve for the third. Separate multiple values with commas."))

KIND = {"two_level": ("2수준 요인설계", "2-level factorial"), "pb": ("Plackett-Burman", "Plackett-Burman"),
        "gff": ("일반 완전요인설계", "General full factorial")}
kind = st.segmented_control(T("설계 종류", "Design type"), list(KIND), default="two_level", required=True,
                            format_func=lambda k: T(*KIND[k]), key="pw_kind")


def _nums(text: str, cast=float) -> list:
    vals = [v.strip() for v in str(text).replace(";", ",").split(",") if v.strip()]
    return [cast(v) for v in vals]


with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    if kind == "two_level":
        factors = c1.number_input(T("요인 수 (Number of factors)"), 2, 15, 5, key="pw_k")
        opts = [2 ** j for j in range(2, factors + 1) if 2 ** j <= 128]
        corner = c2.selectbox(T("꼭짓점 수 (Number of corner points)"), opts, index=min(1, len(opts) - 1), key="pw_r")
    elif kind == "pb":
        factors = c1.number_input(T("요인 수 (Number of factors)"), 2, 47, 10, key="pw_k_pb")
        opts = [r for r in range(8, 52, 4) if r > factors]
        corner = c2.selectbox(T("런 수 (Number of corner points)", "Number of corner points"), opts, key="pw_r_pb")
    else:
        levels_txt = c1.text_input(T("요인별 수준 수 (Number of levels)", "Number of levels"), "3, 3", key="pw_levels")
        order = c2.number_input(T("모형의 최고 차수 (Include terms up through order)"), 1, 5, 2, key="pw_order")
    sigma = c3.number_input(T("표준편차 (Standard deviation)"), 0.0, 1e9, 4.5 if kind != "gff" else 0.15,
                            format="%.6g", key=f"pw_sigma_{kind}")
    st.markdown(T("**두 가지를 적으세요 (Specify values for any two)**", "**Specify values for any two**"))
    d1, d2, d3 = st.columns(3)
    reps_txt = d1.text_input(T("반복 수 (Replicates)"), "1, 2, 3, 4", key=f"pw_reps_{kind}")
    eff_label = T("최대 차이 (Maximum difference)") if kind == "gff" else T("효과 (Effects)")
    eff_txt = d2.text_input(eff_label, "0.4" if kind == "gff" else "5", key=f"pw_eff_{kind}")
    pow_txt = d3.text_input(T("검정력 (Power values)"), "", key=f"pw_pow_{kind}")
    e1, e2, e3, e4 = st.columns(4)
    alpha = e1.number_input(T("유의수준 (Significance level)"), 0.001, 0.5, 0.05, step=0.01, format="%.3f",
                            key="pw_alpha")
    if kind == "gff":
        blocks_on = e2.checkbox(T("모형에 블록 포함 — 반복마다 블록 (Include blocks in model)"), key="pw_gff_blocks")
    else:
        cp_txt = e2.text_input(T("중앙점 수 (Number of center points)" if kind == "pb" else
                                 "블록당 중앙점 수 (Center points per block)"), "3", key=f"pw_cp_{kind}")
        omit = e3.number_input(T("모형에서 뺀 항 수 (Number of terms omitted from model)"), 0, 100, 0, key=f"pw_omit_{kind}")
        ct = e4.checkbox(T("중앙점 항 포함 (Include term for center points)"), value=True, key=f"pw_ct_{kind}")
        blocks = 1
        if kind == "two_level":
            blocks = st.selectbox(T("블록 수 (Number of blocks)"), [1, 2, 4, 8, 16], key="pw_blocks")
    run = st.button(T("계산", "Calculate"), type="primary", key="pw_run")

if run:
    try:
        reps = _nums(reps_txt, int) or None
        effs = _nums(eff_txt) or None
        pows = _nums(pow_txt) or None
        if kind == "two_level":
            res = power_two_level(factors=int(factors), corner_points=int(corner), sigma=float(sigma), reps=reps,
                                  effects=effs, powers=pows, center_points=_nums(cp_txt, int) or [0], blocks=int(blocks),
                                  omit=int(omit), center_term=ct, alpha=float(alpha))
        elif kind == "pb":
            res = power_pb(factors=int(factors), runs=int(corner), sigma=float(sigma), reps=reps, effects=effs,
                           powers=pows, center_points=_nums(cp_txt, int) or [0], omit=int(omit), center_term=ct,
                           alpha=float(alpha))
        else:
            res = power_gff(levels=_nums(levels_txt, int), sigma=float(sigma), reps=reps, deltas=effs, powers=pows,
                            order=int(order), blocks=blocks_on, alpha=float(alpha))
        st.session_state["power"] = res
    except Exception as e:  # noqa: BLE001
        st.session_state.pop("power", None)
        st.error(T("계산하지 못했습니다: ", "Could not calculate: ") + str(e))

res = st.session_state.get("power")
if res is None:
    st.stop()
st.code("\n".join(res.header), language=None)
show_table(res.table)
st.caption(T("검정력 = 그 크기의 효과를 유의하게 찾아낼 확률. 보통 0.8~0.9 이상이면 충분합니다.",
             "Power = probability of detecting an effect of that size as significant. 0.8–0.9 or more is usually adequate."))
try:
    show_plot(power_curve(res, plot_mode()))
except Exception as err:  # noqa: BLE001
    st.info(str(err))
