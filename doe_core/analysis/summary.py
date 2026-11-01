"""분석 결과 요약(주요 결과) — 표를 읽기 전에 무엇을 봐야 하는지 문장으로 알려 준다.

Minitab 문서의 '결과 해석' 순서(1. 반응과 유의하게 관련된 항 2. 모형이 데이터를 얼마나 잘 설명하는지 3. 가정 확인)를 따라
숫자에서 바로 나오는 사실만 적는다. 문구는 직접 쓴 것이며 Minitab 도움말 문장을 옮기지 않는다.

대상: 요인·반응표면·선별 설계(최소제곱), 분할구, 혼합물, 산포(최소제곱·최대우도), 이항 반응. Taguchi 는 아직 아님.

정한 규칙(문서에 없는 기준)
- 유의: p < α(분석 화면의 유의 수준). 항 p 값은 분산분석 표의 개별 항 행(블록·곡면성은 그룹 행)을 쓴다.
- 과적합 경고: R²(pred) 가 R²(adj) 보다 15%p 이상 낮을 때.
- 큰 잔차: 진단 표의 R 표시(|표준화 잔차| > 2)를 센다.
- 모형 줄이기 제안: 유의하지 않은 요인 항이 있고 단계적 선택을 쓰지 않았을 때, 고차 항부터 빼라고만 한다
  (계층 구조 — 교호작용·제곱 항에 들어 있는 주효과는 남김).
- 분할구: 바꾸기 어려운 요인의 항(전구 항)은 전구 오차로 검정한다. 전구 오차 자유도가 0 이면 그 항의 p 값이 없다고,
  1~2 면 검정력이 낮다고 알린다.
- 혼합물: 성분 비율의 효과는 'Linear' 묶음 행으로 본다(성분 선형 항은 하나씩 검정하지 않는다). 비선형 혼합 항·공정 변수 항은
  개별 행. 성분 곱 항(AB, ABC …)은 계수 부호로 상승(+)·상쇄(−)를 붙인다. 모형을 줄일 때 성분 선형 항은 남긴다.
- 산포(최소제곱): 같은 규칙에 '반응' 대신 '표준편차'. 유의한 주효과는 2수준 설계면 Ratio Effect = exp(효과)
  (높은 수준 표준편차 / 낮은 수준 표준편차), 아니면 계수 부호로 방향만 적는다.
- 산포(최대우도): 분산분석표·모형 요약이 없어 계수의 Z 검정 p 로 유의를 보고, 설명력·잔차 문장은 없다.
- 이항: 이탈도 표의 카이제곱 p 로 유의를 본다. 이탈도 R² 는 낮게 나오기 쉬워 '참고' 로만 보이고, 적합도는
  Hosmer-Lemeshow 검정(사건/시행 형식이면 이탈도 검정도). 유의한 주효과(고차 항에 들지 않은 것)의 오즈비를 적는다
  (숫자 요인: 코드 1단위 = (높음 − 낮음)/2 만큼 늘 때, 텍스트 요인: 높음 대 낮음). 잔차 문장은 없다(잔차 그림 미지원).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

PRED_GAP = 0.15


@dataclass
class Finding:
    level: str            # "good" | "warn" | "info"
    ko: str
    en: str


@dataclass
class _Row:
    source: str
    p: float


def _p(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def _names(rows) -> str:
    return ", ".join(f"{r.source} (p {_p(r.p)})" for r in rows)


def supports(a) -> bool:
    """요약을 만들 수 있는 분석인지. 요인·반응표면·선별·분할구·산포·이항(FactorialAnalysis 계열)과 혼합물."""
    from .factorial import FactorialAnalysis
    from .mixture import MixtureAnalysis
    return isinstance(a, (FactorialAnalysis, MixtureAnalysis))


def key_findings(a, alpha: float = 0.05) -> list[Finding]:
    """분석 결과의 주요 결과(분석 종류에 맞는 규칙으로)."""
    if getattr(a, "is_binary", False):
        return _binary(a, alpha)
    if getattr(a, "is_ml", False):
        return _variability_ml(a, alpha)
    if getattr(a, "is_mixture", False):
        return _mixture(a, alpha)
    return _least_squares(a, alpha)


# ---------------------------------------------------------------- 공통 조각

T_REDUCE = (" 고차 항부터 하나씩 빼고 다시 분석하면 모형을 줄일 수 있습니다(교호작용·제곱 항에 들어 있는 주효과는 남김). "
            "단계적 선택을 써도 됩니다.",
            " You can reduce the model by removing higher-order terms one at a time (keep main effects contained in "
            "interactions or squares), or use stepwise selection.")
T_REDUCE_MIX = (" 고차 혼합 항부터 하나씩 빼고 다시 분석하면 모형을 줄일 수 있습니다(성분의 선형 항은 남김). "
                "단계적 선택을 써도 됩니다.",
                " You can reduce the model by removing higher-order blending terms one at a time (the linear component "
                "terms stay), or use stepwise selection.")
T_REDUCE_ML = (" 고차 항부터 하나씩 빼고 다시 분석하면 모형을 줄일 수 있습니다(교호작용·제곱 항에 들어 있는 주효과는 남김).",
               " You can reduce the model by removing higher-order terms one at a time (keep main effects contained in "
               "interactions or squares).")
REL_RESPONSE = ("반응과 유의하게 관련된 항", "Terms significantly related to the response")
REL_STD = ("표준편차와 유의하게 관련된 항", "Terms significantly related to the standard deviation")


def _split(terms, alpha):
    sig = sorted([r for r in terms if r.p < alpha], key=lambda r: r.p)
    non = sorted([r for r in terms if r.p >= alpha], key=lambda r: -r.p)
    return sig, non


def _significance(out, a, terms, alpha, rel, tail, *, sig_text=None, sig_extra=("", "")) -> tuple[list, list]:
    """유의한 항·유의하지 않은 항 문장. sig_text 는 (ko, en) 로 항 목록 표기를 바꿀 때."""
    sig, non = _split(terms, alpha)
    if not terms:
        return sig, non
    if sig:
        ko_list, en_list = sig_text(sig) if sig_text else (_names(sig), _names(sig))
        out.append(Finding("good", f"{rel[0]}(p < {alpha:g}): {ko_list}." + sig_extra[0],
                           f"{rel[1]} (p < {alpha:g}): {en_list}." + sig_extra[1]))
    else:
        out.append(Finding("warn", f"p < {alpha:g} 에서 유의한 항이 없습니다. 효과가 잡음보다 작거나, 요인 범위가 좁거나, "
                                   "런 수가 부족할 수 있습니다.",
                           f"No term is significant at p < {alpha:g}. The effects may be small relative to noise, "
                           "the factor ranges narrow, or the number of runs too small."))
    if non:
        stepwise = getattr(a, "selection", None) is not None
        t_ko, t_en = ("", "") if stepwise else tail
        out.append(Finding("info", f"유의하지 않은 항: {_names(non)}." + t_ko,
                           f"Terms that are not significant: {_names(non)}." + t_en))
    return sig, non


def _blocks(out, rows, alpha) -> None:
    blocks = next((r for r in rows if r.source == "Blocks" and r.p is not None), None)
    if blocks is not None and blocks.p < alpha:
        out.append(Finding("info", f"블록 차이가 유의합니다(p {_p(blocks.p)}). 실험 날짜·원료 로트 같은 블록 조건이 결과에 "
                                   "영향을 주었습니다.",
                           f"The blocks differ significantly (p {_p(blocks.p)}): block conditions such as day or raw "
                           "material lot affected the results."))


def _fit(out, s) -> None:
    r2, adj, pred = s["R-sq"], s["R-sq(adj)"], s["R-sq(pred)"]
    if adj is None:
        return
    txt_ko = f"모형 설명력: R² {r2:.2%}, 조정 R² {adj:.2%}" + (f", 예측 R² {pred:.2%}" if pred is not None else "") + "."
    txt_en = f"Model fit: R-sq {r2:.2%}, R-sq(adj) {adj:.2%}" + (f", R-sq(pred) {pred:.2%}" if pred is not None else "") + "."
    level = "good" if adj >= 0.8 else "info"
    if pred is not None and adj - pred >= PRED_GAP:
        level = "warn"
        txt_ko += " 예측 R² 가 조정 R² 보다 크게 낮아, 새 실험을 예측하는 힘이 약하거나 항이 너무 많을 수 있습니다."
        txt_en += " R-sq(pred) is much lower than R-sq(adj): the model may be overfit or predict new runs poorly."
    out.append(Finding(level, txt_ko, txt_en))


def _lack_of_fit(out, rows, alpha, missing=("빠진 항(교호작용·제곱 항)이 있거나", "Terms may be missing or")) -> None:
    lof = next((r for r in rows if r.source == "Lack-of-Fit" and r.p is not None), None)
    if lof is None:
        return
    if lof.p < alpha:
        out.append(Finding("warn", f"적합성 결여가 유의합니다(p {_p(lof.p)}): 반복 실험의 흩어짐보다 모형 오차가 큽니다. "
                                   f"{missing[0]} 반응 변환(Box-Cox)이 필요할 수 있습니다.",
                           f"Lack-of-fit is significant (p {_p(lof.p)}): the model error exceeds the scatter of "
                           f"the replicates. {missing[1]} the response may need a transformation."))
    else:
        out.append(Finding("good", f"적합성 결여가 없습니다(p {_p(lof.p)}): 모형이 반복 실험의 흩어짐 안에서 데이터를 "
                                   "설명합니다.",
                           f"No lack-of-fit (p {_p(lof.p)}): the model explains the data within the scatter of "
                           "the replicates."))


def _residuals(out, a) -> None:
    try:
        from .diagnostics import diagnostics
        dg = diagnostics(a)
        large = [str(int(o)) for o, f in zip(dg["Obs"], dg["Flag"]) if "R" in f]
    except Exception:  # noqa: BLE001 — 요약은 진단을 못 해도 나머지를 보인다
        large = []
    if large:
        out.append(Finding("warn", f"표준화 잔차가 큰 관측치 {len(large)}개(관측 번호 {', '.join(large)}): 실험 기록·측정값을 "
                                   "확인하고, 잔차 그림에서 패턴이 없는지 보세요.",
                           f"{len(large)} observation(s) with a large standardized residual (obs {', '.join(large)}): "
                           "check the records and measurements and look at the residual plots."))
    else:
        out.append(Finding("good", "표준화 잔차가 큰 관측치가 없습니다. 잔차 그림에서 정규성·등분산을 함께 확인하세요.",
                           "No observation has a large standardized residual. Check normality and constant variance "
                           "in the residual plots too."))


def _term_cols(a, ti: int) -> list[int]:
    return [j for j, k in enumerate(a.col_term) if k == ti]


def _term_index(a) -> dict[str, int]:
    return {t.name: i for i, t in enumerate(a.terms)}


# ---------------------------------------------------------------- 최소제곱(요인·반응표면·선별·분할구·산포)

def _least_squares(a, alpha: float) -> list[Finding]:
    out: list[Finding] = []
    variability = getattr(a, "is_variability", False)
    rows = a.anova_rows()
    term_names = {t.name for t in a.terms if t.kind in ("factor", "covariate")}
    terms = [r for r in rows if r.level == 2 and r.source in term_names and r.p is not None]
    err = next((r for r in rows if r.source == "Error"), None)
    if err is None or not err.df:
        out.append(Finding("info", "오차 자유도가 0 이라 p 값을 구할 수 없습니다. 효과도(Lenth PSE)로 큰 효과를 고르거나 "
                                   "반복·중앙점을 더해 오차를 추정하세요.",
                           "There are no error degrees of freedom, so p-values cannot be computed. Pick large effects "
                           "from the effects plots (Lenth's PSE) or add replicates or center points."))
    sig, _ = _significance(out, a, terms, alpha, REL_STD if variability else REL_RESPONSE, T_REDUCE)
    if getattr(a, "is_split_plot", False):
        _whole_plot(out, a)
    if variability:
        _std_direction(out, a, sig)
    _blocks(out, [r for r in rows if r.level == 1], alpha)
    _fit(out, a.summary())

    curv = next((r for r in rows if r.source == "Curvature" and r.p is not None), None)
    has_ct = any(t.kind == "center" for t in a.terms)
    subj_ko, subj_en = ("표준편차가", "standard deviation") if variability else ("반응이", "response")
    if curv is not None:
        if curv.p < alpha:
            out.append(Finding("warn", f"곡면성이 유의합니다(p {_p(curv.p)}): 중앙점의 {subj_ko} 모서리점으로 예상한 값과 다릅니다. "
                                       "요인 범위 안에 최적점(봉우리·골짜기)이 있을 수 있으니, 워크시트 화면의 '축점 추가'로 "
                                       "반응표면 설계로 넓혀 제곱 항을 추정하세요.",
                               f"Curvature is significant (p {_p(curv.p)}): the center points differ from what the "
                               "corner points predict. An optimum may lie inside the factor ranges; add axial points "
                               "on the Worksheet page to estimate square terms with a response surface design."
                               if not variability else
                               f"Curvature is significant (p {_p(curv.p)}): the {subj_en} at the center points differs "
                               "from what the corner points predict. Add axial points on the Worksheet page to estimate "
                               "square terms with a response surface design."))
        elif has_ct:
            out.append(Finding("info", f"곡면성이 유의하지 않습니다(p {_p(curv.p)}). '모형에 중앙점 포함' 을 끄고 다시 분석하면 "
                                       "등고선도·최적화를 쓸 수 있습니다.",
                               f"Curvature is not significant (p {_p(curv.p)}). Turn off 'Include center points' and "
                               "analyze again to use contour plots and the optimizer."))
    _lack_of_fit(out, rows, alpha)
    _residuals(out, a)
    return out


def _whole_plot(out, a) -> None:
    """분할구: 바꾸기 어려운 요인의 항은 전구 오차로 검정한다."""
    wp = [t.name for i, t in enumerate(a.terms) if t.kind == "factor" and a.is_wp_term(i)]
    if not wp:
        return
    names = ", ".join(wp)
    df = a.df_wp
    if df <= 0:
        out.append(Finding("warn", f"바꾸기 어려운 요인의 항({names})은 전구 오차의 자유도가 0 이라 p 값을 구할 수 없습니다. "
                                   "전구(바꾸기 어려운 요인의 설정 묶음)를 반복해야 검정할 수 있습니다.",
                           f"The hard-to-change terms ({names}) cannot be tested: the whole-plot error has 0 degrees "
                           "of freedom. Replicate the whole plots to test them."))
    elif df <= 2:
        out.append(Finding("info", f"바꾸기 어려운 요인의 항({names})은 자유도 {df} 인 전구 오차로 검정해 검정력이 낮습니다. "
                                   "p 값이 커도 효과가 없다고 단정하지 마세요.",
                           f"The hard-to-change terms ({names}) are tested against the whole-plot error with only "
                           f"{df} degree(s) of freedom, so the test has little power. A large p-value does not prove "
                           "there is no effect."))
    else:
        out.append(Finding("info", f"바꾸기 어려운 요인의 항({names})은 전구 오차(자유도 {df})로, 나머지 항은 하위구 오차로 "
                                   "검정했습니다.",
                           f"The hard-to-change terms ({names}) are tested against the whole-plot error ({df} DF); "
                           "the other terms against the subplot error."))


def _std_direction(out, a, sig) -> None:
    """산포 분석: 유의한 주효과가 표준편차를 어느 쪽으로 바꾸는지."""
    idx = _term_index(a)
    ko, en = [], []
    for r in sig:
        ti = idx.get(r.source)
        if ti is None:
            continue
        t = a.terms[ti]
        cols = _term_cols(a, ti)
        if t.kind != "factor" or t.order != 1 or len(cols) != 1:
            continue
        b = float(a.beta[cols[0]])
        if a.two_level:
            ratio = math.exp(2 * b)
            ko.append(f"{t.name} — 높은 수준의 표준편차가 낮은 수준의 {ratio:.2f}배")
            en.append(f"{t.name}: the standard deviation at the high level is {ratio:.2f} times that at the low level")
        else:
            ko.append(f"{t.name} — 값이 클수록 표준편차가 {'커짐' if b > 0 else '작아짐'}")
            en.append(f"{t.name}: the standard deviation {'increases' if b > 0 else 'decreases'} as it increases")
    if not ko:
        return
    txt_ko = "요인별 산포 방향: " + "; ".join(ko) + "."
    txt_en = "Direction of the spread: " + "; ".join(en) + "."
    if a.two_level:
        txt_ko += " 산포를 줄이려면 배수가 1 보다 큰 요인은 낮은 수준, 1 보다 작은 요인은 높은 수준 쪽이 유리합니다."
        txt_en += " To reduce the spread, use the low level of factors above 1 and the high level of factors below 1."
    if any(a.terms[idx[r.source]].kind == "factor" and a.terms[idx[r.source]].order > 1 for r in sig if r.source in idx):
        txt_ko += " 유의한 교호작용이 있어 실제 크기는 다른 요인의 수준에 따라 달라집니다."
        txt_en += " A significant interaction means the size also depends on the other factors' levels."
    out.append(Finding("info", txt_ko, txt_en))


# ---------------------------------------------------------------- 산포(최대우도)

def _variability_ml(a, alpha: float) -> list[Finding]:
    out: list[Finding] = []
    c = a.coefficients()
    terms = []
    for ti, t in enumerate(a.terms):
        cols = _term_cols(a, ti)
        if t.kind not in ("factor", "covariate") or len(cols) != 1:
            continue
        p = float(c["P-Value"].iloc[cols[0]])
        if not math.isnan(p):
            terms.append(_Row(t.name, p))
    sig, _ = _significance(out, a, terms, alpha, REL_STD, T_REDUCE_ML)
    _std_direction(out, a, sig)
    out.append(Finding("info", "최대우도 추정이라 모형 요약(R²)과 분산분석표는 없습니다. 유의성은 계수표의 Z 값과 p 값으로 봅니다.",
                       "With maximum likelihood there is no model summary (R-sq) or ANOVA table; judge significance "
                       "by the Z-values and p-values in the coefficients table."))
    return out


# ---------------------------------------------------------------- 혼합물

def _mixture(a, alpha: float) -> list[Finding]:
    from .mixture import GROUP_LABEL
    out: list[Finding] = []
    rows = a.anova_rows()
    if not a.df_error:
        out.append(Finding("info", "오차 자유도가 0 이라 p 값을 구할 수 없습니다. 반복 런(특히 중심점)을 더해 오차를 추정하세요.",
                           "There are no error degrees of freedom, so p-values cannot be computed. Add replicate runs "
                           "(especially the centroid) to estimate the error."))
    linear = next((r for r in rows if r.source == GROUP_LABEL["linear"]), None)    # 첫 'Linear' = 성분만의 선형 묶음
    if linear is not None and linear.p is not None:
        if linear.p < alpha:
            out.append(Finding("good", f"성분 비율에 따라 반응이 유의하게 달라집니다(선형 혼합 p {_p(linear.p)}).",
                               f"The response changes significantly with the component proportions (linear blending "
                               f"p {_p(linear.p)})."))
        else:
            out.append(Finding("warn", f"성분 비율에 따른 반응 차이(선형 혼합)가 유의하지 않습니다(p {_p(linear.p)}). "
                                       "성분 범위가 좁거나 잡음이 클 수 있습니다.",
                               f"The response does not differ significantly with the component proportions (linear "
                               f"blending p {_p(linear.p)}). The component ranges may be narrow or the noise large."))
    idx = {t.name: i for i, t in enumerate(a.terms) if t.kind != "blocks" and not t.is_component_linear}
    terms = [r for r in rows if r.level >= 2 and r.source in idx and r.p is not None]

    def tag(r) -> tuple[str, str]:
        """성분 곱 항(AB, ABC …)의 계수 부호: 상승(+)·상쇄(−)."""
        t = a.terms[idx[r.source]]
        cols = _term_cols(a, idx[r.source])
        if t.kind != "product" or t.proc or len(cols) != 1:
            return "", ""
        return (", 상승", ", synergistic") if float(a.beta[cols[0]]) > 0 else (", 상쇄", ", antagonistic")

    sig, _ = _split(terms, alpha)
    tags = {r.source: tag(r) for r in sig}
    listing = (", ".join(f"{r.source} (p {_p(r.p)}{tags[r.source][0]})" for r in sig),
               ", ".join(f"{r.source} (p {_p(r.p)}{tags[r.source][1]})" for r in sig))
    extra = ((" 상승은 섞었을 때 반응이 선형 혼합으로 예상한 값보다 커지는 것, 상쇄는 작아지는 것입니다.",
              " Synergistic means the blend gives a higher response than linear blending predicts; antagonistic, lower.")
             if any(k for k, _ in tags.values()) else ("", ""))
    _significance(out, a, terms, alpha, ("성분 혼합의 비선형 효과·공정 변수 항 중 유의한 항",
                                         "Significant nonlinear blending or process-variable terms"), T_REDUCE_MIX,
                  sig_text=lambda _: listing, sig_extra=extra)
    _blocks(out, rows, alpha)
    _fit(out, a.summary())
    _lack_of_fit(out, rows, alpha, missing=("빠진 혼합 항(2차·특수 3차 등)이 있거나", "Blending terms (quadratic, special "
                                                                                 "cubic …) may be missing or"))
    _residuals(out, a)
    return out


# ---------------------------------------------------------------- 이항 반응

def _binary(a, alpha: float) -> list[Finding]:
    from scipy import stats
    out: list[Finding] = []
    ev = str(a.event_value if a.binary_format else a.event_name or "")
    ev_ko = f"사건({ev})" if ev and ev != "Event" else "사건"
    ev_en = f"the event ({ev})" if ev and ev != "Event" else "the event"
    rows = [_Row(r["Source"], r["P-Value"]) for r in a.anova_rows()]
    term_names = {t.name for t in a.terms if t.kind in ("factor", "covariate")}
    terms = [r for r in rows if r.source in term_names and r.p is not None]
    sig, _ = _significance(out, a, terms, alpha, (f"{ev_ko} 확률과 유의하게 관련된 항",
                                                  f"Terms significantly related to the probability of {ev_en}"), T_REDUCE)
    _odds(out, a, sig, ev_ko, ev_en)
    _blocks(out, rows, alpha)

    s = a.summary()
    if s["Deviance R-Sq"] is not None:
        out.append(Finding("info", f"모형 설명력: 이탈도 R² {s['Deviance R-Sq']:.2%}, 조정 {s['Deviance R-Sq(adj)']:.2%}, "
                                   f"AIC {s['AIC']:.2f}. 이항 반응은 이탈도 R² 만으로 판단하기 어려우니 적합도 검정과 함께 "
                                   "보세요.",
                           f"Model fit: deviance R-sq {s['Deviance R-Sq']:.2%}, adjusted {s['Deviance R-Sq(adj)']:.2%}, "
                           f"AIC {s['AIC']:.2f}. For a binary response, read deviance R-sq together with the "
                           "goodness-of-fit tests."))
    hl, hl_df = a.hosmer_lemeshow()
    if hl_df > 0:
        p = float(stats.chi2.sf(hl, hl_df))
        if p < alpha:
            out.append(Finding("warn", f"Hosmer-Lemeshow 적합도 검정이 유의합니다(p {_p(p)}): 예측 확률이 관측 비율과 맞지 않는 "
                                       "구간이 있습니다. 빠진 항(교호작용·제곱 항)이 있을 수 있습니다.",
                               f"The Hosmer-Lemeshow test is significant (p {_p(p)}): the predicted probabilities "
                               "miss the observed proportions somewhere. Terms may be missing."))
        else:
            out.append(Finding("good", f"Hosmer-Lemeshow 적합도 검정에서 문제가 없습니다(p {_p(p)}): 예측 확률이 관측 비율과 "
                                       "잘 맞습니다.",
                               f"The Hosmer-Lemeshow test shows no problem (p {_p(p)}): the predicted probabilities "
                               "match the observed proportions."))
    if not a.binary_format and a.df_resid > 0:
        p = float(stats.chi2.sf(a.deviance(), a.df_resid))
        if p < alpha:
            out.append(Finding("warn", f"이탈도 적합도 검정이 유의합니다(p {_p(p)}): 같은 조건의 시행 사이 흩어짐이 이항 분포로 "
                                       "설명되는 것보다 클 수 있습니다(과대산포).",
                               f"The deviance goodness-of-fit test is significant (p {_p(p)}): the trials may vary "
                               "more than the binomial distribution allows (overdispersion)."))
    return out


def _odds(out, a, sig, ev_ko, ev_en) -> None:
    """유의한 주효과의 오즈비(고차 항에 들어 있지 않은 2수준·숫자 요인만)."""
    from ..designs.general_full import GeneralFullFactorialDesign
    d = a.design
    if isinstance(d, GeneralFullFactorialDesign):
        return
    idx = _term_index(a)
    ko, en = [], []
    for r in sig:
        ti = idx.get(r.source)
        if ti is None:
            continue
        t = a.terms[ti]
        cols = _term_cols(a, ti)
        if t.kind != "factor" or t.order != 1 or len(cols) != 1 or a._in_higher_terms(t.letters[0]):
            continue
        f = d.factors[list(d.letters).index(t.letters[0])]
        if not hasattr(f, "low"):
            continue
        b = float(a.beta[cols[0]])
        if getattr(f, "is_numeric", False):
            unit = (float(f.high) - float(f.low)) / 2
            ko.append(f"{f.name} {unit:g} 증가 → 오즈 {math.exp(b):.2f}배")
            en.append(f"{f.name} +{unit:g} → odds × {math.exp(b):.2f}")
        else:
            ko.append(f"{f.name} {f.high} 대 {f.low} → 오즈 {math.exp(2 * b):.2f}배")
            en.append(f"{f.name} {f.high} vs {f.low} → odds × {math.exp(2 * b):.2f}")
    if ko:
        out.append(Finding("info", "오즈비(유의한 주효과): " + "; ".join(ko) + f". 1 보다 크면 {ev_ko}이 일어날 가능성이 커지는 "
                                   "쪽입니다.",
                           "Odds ratios (significant main effects): " + "; ".join(en) + f". Above 1 makes {ev_en} "
                           "more likely."))


def worst_level(findings: list[Finding]) -> str:
    return "warn" if any(f.level == "warn" for f in findings) else "good"
