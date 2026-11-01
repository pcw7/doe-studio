"""반응 최적화·예측 화면 — Minitab 'Response Optimizer' · 'Predict' · 'Overlaid Contour Plot'."""
import pandas as pd
import streamlit as st

from app.state import boxcox_input, plot_mode, report_downloads, require_ws, show_plot, show_table
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.model import RS_MODELS
from doe_core.designs.definitive_screening import DefinitiveScreeningDesign
from doe_core.designs.general_full import GeneralFullFactorialDesign
from doe_core.designs.mixture import MixtureDesign
from doe_core.designs.response_surface import ResponseSurfaceDesign
from app import fitted_models
from app.goals import goals_editor, model_sources_table, nonzero_bounds, show_results
from app.i18n import T, lang
from doe_core.optimize.optimizer import optimize
from doe_core.optimize.predict import predict, prediction_table, settings_table
from doe_core.plots.contour_plots import factor_range, overlaid_contour_plot

st.title(T("반응 최적화·예측", "Response optimizer & predict"))
st.caption("Response Optimizer · Predict · Overlaid Contour Plot")
ws = require_ws()
d = ws.design
if isinstance(d, MixtureDesign):
    from app.mixture_panel import render_optimizer
    render_optimizer(ws)
    st.stop()
from doe_core.designs.taguchi import TaguchiDesign  # noqa: E402
if isinstance(d, TaguchiDesign):
    st.info(T("Taguchi 설계는 **분석** 화면의 '예측' 탭에서 수준 조합별 예측값(S/N 비·평균)을 확인합니다.",
              "For Taguchi designs, use the 'Predict' tab on the **Analyze** page to predict S/N ratios and means."))
    st.stop()
is_dsd = isinstance(d, DefinitiveScreeningDesign)
is_rs = isinstance(d, ResponseSurfaceDesign) or is_dsd
numeric_cols = [c for c in ws.columns.columns if pd.api.types.is_numeric_dtype(ws.columns[c]) and ws.columns[c].notna().sum() > 1]
if not numeric_cols:
    st.info(T("반응 열이 없습니다. **워크시트** 화면에서 결과를 입력하세요.",
              "There is no response. Enter results on the **Worksheet** page."))
    st.stop()

with st.container(border=True):
    c1, c2 = st.columns(2)
    responses = c1.multiselect(T("반응 (Responses)"), numeric_cols, default=numeric_cols[:1])
    covariates = c2.multiselect(T("공변량 (Covariates)"), [c for c in numeric_cols if c not in responses])
    if is_rs:
        ko = {"linear": "선형", "linear+squares": "선형 + 제곱", "linear+interactions": "선형 + 교호작용",
              "full quadratic": "완전 2차"}
        model = st.selectbox(T("공통 모형 — 분석 화면에서 분석하지 않은 반응", "Common model — responses not analyzed on the "
                                                                          "Analyze page"),
                             list(RS_MODELS), index=0 if is_dsd else 3, format_func=lambda m: T(ko[m]))
        order = None
    else:
        model = "full quadratic"
        order = st.slider(T("공통 모형 차수 — 분석 화면에서 분석하지 않은 반응",
                            "Common model order — responses not analyzed on the Analyze page"), 1, len(d.letters),
                          min(2, len(d.letters)))
    bc_spec, bc_rounded = boxcox_input("bc_optimize", allow_custom=False)
    use_stored = st.checkbox(T("분석 화면에서 적합한 모형 쓰기(반응별)", "Use the models fitted on the Analyze page"),
                             value=True, key="opt_use_stored",
                             help=T("반응마다 분석 화면에서 마지막으로 분석한 모형(항 선택·단계적 선택·Box-Cox·가중치 포함)을 "
                                    "씁니다. 끄면 모든 반응을 위의 공통 모형으로 다시 적합합니다.",
                                    "Each response uses its last model from the Analyze page (term selection, stepwise, "
                                    "Box-Cox and weights included). Turn off to refit every response with the common "
                                    "model above."))
    st.caption(T("최적화는 요인 수준 사이를 보간하므로 중앙점 항(Ct Pt)은 넣지 않습니다.",
                 "The optimizer interpolates between factor levels, so the center point term (Ct Pt) is left out."))
    # 다른 화면에서 만든 모형(같은 설계): 산포 분석(표준편차) · 이항 반응(확률)
    extra = {}
    for skey, lab_ko, lab_en in [("variability", "산포 분석 모형 포함 — 표준편차", "Include variability model — standard deviation"),
                                 ("binary", "이항 반응 모형 포함 — 사건 확률", "Include binary response model — event probability")]:
        ea = st.session_state.get(skey)
        if ea is not None and ea.design is d and ea.response not in responses:
            if st.checkbox(T(f"{lab_ko}: {ea.response}", f"{lab_en}: {ea.response}"), key=f"opt_extra_{skey}"):
                extra[ea.response] = ea
    if st.session_state.get("variability") is not None or st.session_state.get("binary") is not None:
        st.caption(T("산포·이항 모형은 각 분석 화면에서 만든 모형을 그대로 씁니다(표준편차·확률의 원래 단위로 최적화).",
                     "Variability and binary models are taken as fitted on their own pages (optimized in standard "
                     "deviation and probability units)."))

if not responses and not extra:
    st.stop()

models, sources = {}, []
for r in responses:
    try:
        a, notes = fitted_models.stored(ws, r) if use_stored else (None, [])
        if a is None:
            a, notes = analyze_worksheet(ws, r, covariates=covariates, order=order, model=model, include_center=False,
                                         boxcox=bc_spec, boxcox_rounded=bc_rounded), ["common"]
        models[r] = a
        sources.append((r, notes, a))
    except Exception as e:  # noqa: BLE001
        st.error(T(f"{r} 모형을 적합하지 못했습니다: ", f"Could not fit the model for {r}: ") + str(e))
        st.stop()
models.update(extra)
model_sources_table(sources)
names_key = list(models)

goals = goals_editor(models, key=f"goals_{'_'.join(names_key)}")

hold = {}
with st.expander(T("요인 고정 (Constraints: Hold at value)", "Constraints: hold factors at a value")):
    for L, f in zip(d.letters, d.factors):
        if st.checkbox(T(f"{f.name} 고정", f"Hold {f.name}"), key=f"hold_on_{L}"):
            val_label = T(f"{f.name} 값", f"{f.name} value")
            if isinstance(d, GeneralFullFactorialDesign):
                hold[f.name] = st.selectbox(val_label, list(f.levels), key=f"hold_v_{L}")
            elif f.is_numeric:
                lo, hi = factor_range(next(iter(models.values())), L)
                hold[f.name] = st.number_input(val_label, float(lo), float(hi), float((lo + hi) / 2), key=f"hold_v_{L}")
            else:
                hold[f.name] = st.selectbox(val_label, [f.low, f.high], key=f"hold_v_{L}")

if st.button(T("최적화", "Optimize"), type="primary"):
    try:
        st.session_state["opt"] = (names_key, optimize(list(models.values()), goals, hold=hold))
    except Exception as e:  # noqa: BLE001
        st.error(T("최적화하지 못했습니다: ", "Could not optimize: ") + str(e))

opt = st.session_state.get("opt")
if opt and opt[0] == names_key:
    res = opt[1]
    show_results(res, models, goals)
    from doe_core.report import optimization_report
    report_downloads(lambda figs: optimization_report(models, goals, res, lang=lang()), f"rep_opt_{id(res)}_{lang()}",
                     T("최적화보고서", "optimization_report"))

    cont = [L for L, f in zip(d.letters, d.factors) if getattr(f, "is_numeric", False) and hasattr(f, "low")]
    if len(models) >= 2 and len(cont) >= 2:
        st.subheader(T("중첩 등고선도 (Overlaid Contour Plot)"))
        names = dict(zip(d.letters, [f.name for f in d.factors]))
        c1, c2 = st.columns(2)
        xL = c1.selectbox(T("X 축"), cont, format_func=lambda L: names[L])
        yL = c2.selectbox(T("Y 축"), [L for L in cont if L != xL], format_func=lambda L: names[L])
        bounds = nonzero_bounds(goals)
        hold_other = {k: v for k, v in res.settings.items() if k not in (names[xL], names[yL])}
        try:
            show_plot(overlaid_contour_plot(list(models.values()), bounds, xL, yL, hold=hold_other, mode=plot_mode()))
            st.caption(T("회색이 아닌 영역: 모든 반응이 만족도 0 이 아닌 범위(최대화는 하한 이상, 최소화는 상한 이하, "
                         "목표값은 하한~상한). 나머지 요인은 최적 해에 고정.",
                         "Non-grey region: every response has nonzero desirability (maximize: above lower, minimize: "
                         "below upper, target: between lower and upper). Other factors are held at the solution."))
        except ValueError as err:
            st.info(str(err))

st.divider()
st.subheader(T("예측 (Predict)"))
base = opt[1].settings if opt and opt[0] == names_key else {}
if base and st.button(T("최적 해로 채우기", "Fill in the optimal solution")):
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
    if getattr(a, "is_binary", False):
        st.caption(T("Fit = 사건 확률(로지스틱), SE Fit 은 델타 방법.", "Fit = event probability (logistic); SE Fit by the delta method."))
    elif getattr(a, "is_variability", False):
        st.caption(T("Fit = 표준편차(exp(Ln 모형)).", "Fit = standard deviation (exp of the Ln model)."))
    if a.equation():
        st.code(a.equation()[1], language=None, wrap_lines=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        show_table(settings_table(a, inputs))
    with c2:
        show_table(prediction_table(predict(a, inputs)))
