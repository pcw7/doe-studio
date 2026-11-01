"""분석 결과 요약(주요 결과) — 표를 읽기 전에 무엇을 봐야 하는지 문장으로 알려 준다.

Minitab 문서의 '결과 해석' 순서(1. 반응과 유의하게 관련된 항 2. 모형이 데이터를 얼마나 잘 설명하는지 3. 가정 확인)를 따라
숫자에서 바로 나오는 사실만 적는다. 문구는 직접 쓴 것이며 Minitab 도움말 문장을 옮기지 않는다.

정한 규칙(문서에 없는 기준)
- 유의: p < α(분석 화면의 유의 수준). 항 p 값은 분산분석 표의 개별 항 행(블록·곡면성은 그룹 행)을 쓴다.
- 과적합 경고: R²(pred) 가 R²(adj) 보다 15%p 이상 낮을 때.
- 큰 잔차: 진단 표의 R 표시(|표준화 잔차| > 2)를 센다.
- 모형 줄이기 제안: 유의하지 않은 요인 항이 있고 단계적 선택을 쓰지 않았을 때, 고차 항부터 빼라고만 한다
  (계층 구조 — 교호작용·제곱 항에 들어 있는 주효과는 남김).
"""
from __future__ import annotations

from dataclasses import dataclass

PRED_GAP = 0.15


@dataclass
class Finding:
    level: str            # "good" | "warn" | "info"
    ko: str
    en: str


def _p(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def _names(rows) -> str:
    return ", ".join(f"{r.source} (p {_p(r.p)})" for r in rows)


def supports(a) -> bool:
    """요약을 만들 수 있는 분석인지(요인·반응표면·선별 설계의 최소제곱 분석). 분할구·혼합물·산포·이항·Taguchi 는 아직 아님."""
    from .factorial import FactorialAnalysis
    return type(a) is FactorialAnalysis


def key_findings(a, alpha: float = 0.05) -> list[Finding]:
    """요인·반응표면·선별 설계 분석(FactorialAnalysis)의 주요 결과."""
    out: list[Finding] = []
    rows = a.anova_rows()
    term_names = {t.name for t in a.terms if t.kind in ("factor", "covariate")}
    terms = [r for r in rows if r.level == 2 and r.source in term_names and r.p is not None]
    err = next((r for r in rows if r.source == "Error"), None)
    if err is None or not err.df:
        out.append(Finding("info", "오차 자유도가 0 이라 p 값을 구할 수 없습니다. 효과도(Lenth PSE)로 큰 효과를 고르거나 "
                                   "반복·중앙점을 더해 오차를 추정하세요.",
                           "There are no error degrees of freedom, so p-values cannot be computed. Pick large effects "
                           "from the effects plots (Lenth's PSE) or add replicates or center points."))
    sig = sorted([r for r in terms if r.p < alpha], key=lambda r: r.p)
    non = sorted([r for r in terms if r.p >= alpha], key=lambda r: -r.p)
    if terms:
        if sig:
            out.append(Finding("good", f"반응과 유의하게 관련된 항(p < {alpha:g}): {_names(sig)}.",
                               f"Terms significantly related to the response (p < {alpha:g}): {_names(sig)}."))
        else:
            out.append(Finding("warn", f"p < {alpha:g} 에서 유의한 항이 없습니다. 효과가 잡음보다 작거나, 요인 범위가 좁거나, "
                                       "런 수가 부족할 수 있습니다.",
                               f"No term is significant at p < {alpha:g}. The effects may be small relative to noise, "
                               "the factor ranges narrow, or the number of runs too small."))
        if non:
            stepwise = getattr(a, "selection", None) is not None
            tail = "" if stepwise else T_REDUCE
            out.append(Finding("info", f"유의하지 않은 항: {_names(non)}." + (tail[0] if tail else ""),
                               f"Terms that are not significant: {_names(non)}." + (tail[1] if tail else "")))
    blocks = next((r for r in rows if r.source == "Blocks" and r.level == 1 and r.p is not None), None)
    if blocks is not None and blocks.p < alpha:
        out.append(Finding("info", f"블록 차이가 유의합니다(p {_p(blocks.p)}). 실험 날짜·원료 로트 같은 블록 조건이 결과에 "
                                   "영향을 주었습니다.",
                           f"The blocks differ significantly (p {_p(blocks.p)}): block conditions such as day or raw "
                           "material lot affected the results."))

    s = a.summary()
    r2, adj, pred = s["R-sq"], s["R-sq(adj)"], s["R-sq(pred)"]
    if adj is not None:
        txt_ko = f"모형 설명력: R² {r2:.2%}, 조정 R² {adj:.2%}" + (f", 예측 R² {pred:.2%}" if pred is not None else "") + "."
        txt_en = f"Model fit: R-sq {r2:.2%}, R-sq(adj) {adj:.2%}" + (f", R-sq(pred) {pred:.2%}" if pred is not None else "") + "."
        level = "good" if adj >= 0.8 else "info"
        if pred is not None and adj - pred >= PRED_GAP:
            level = "warn"
            txt_ko += " 예측 R² 가 조정 R² 보다 크게 낮아, 새 실험을 예측하는 힘이 약하거나 항이 너무 많을 수 있습니다."
            txt_en += " R-sq(pred) is much lower than R-sq(adj): the model may be overfit or predict new runs poorly."
        out.append(Finding(level, txt_ko, txt_en))

    curv = next((r for r in rows if r.source == "Curvature" and r.p is not None), None)
    has_ct = any(t.kind == "center" for t in a.terms)
    if curv is not None:
        if curv.p < alpha:
            out.append(Finding("warn", f"곡면성이 유의합니다(p {_p(curv.p)}): 중앙점의 반응이 모서리점으로 예상한 값과 다릅니다. "
                                       "요인 범위 안에 최적점(봉우리·골짜기)이 있을 수 있으니, 워크시트 화면의 '축점 추가'로 "
                                       "반응표면 설계로 넓혀 제곱 항을 추정하세요.",
                               f"Curvature is significant (p {_p(curv.p)}): the center points differ from what the "
                               "corner points predict. An optimum may lie inside the factor ranges; add axial points "
                               "on the Worksheet page to estimate square terms with a response surface design."))
        elif has_ct:
            out.append(Finding("info", f"곡면성이 유의하지 않습니다(p {_p(curv.p)}). '모형에 중앙점 포함' 을 끄고 다시 분석하면 "
                                       "등고선도·최적화를 쓸 수 있습니다.",
                               f"Curvature is not significant (p {_p(curv.p)}). Turn off 'Include center points' and "
                               "analyze again to use contour plots and the optimizer."))
    lof = next((r for r in rows if r.source == "Lack-of-Fit" and r.p is not None), None)
    if lof is not None:
        if lof.p < alpha:
            out.append(Finding("warn", f"적합성 결여가 유의합니다(p {_p(lof.p)}): 반복 실험의 흩어짐보다 모형 오차가 큽니다. "
                                       "빠진 항(교호작용·제곱 항)이 있거나 반응 변환(Box-Cox)이 필요할 수 있습니다.",
                               f"Lack-of-fit is significant (p {_p(lof.p)}): the model error exceeds the scatter of "
                               "the replicates. Terms may be missing or the response may need a transformation."))
        else:
            out.append(Finding("good", f"적합성 결여가 없습니다(p {_p(lof.p)}): 모형이 반복 실험의 흩어짐 안에서 데이터를 "
                                       "설명합니다.",
                               f"No lack-of-fit (p {_p(lof.p)}): the model explains the data within the scatter of "
                               "the replicates."))

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
    return out


T_REDUCE = (" 고차 항부터 하나씩 빼고 다시 분석하면 모형을 줄일 수 있습니다(교호작용·제곱 항에 들어 있는 주효과는 남김). "
            "단계적 선택을 써도 됩니다.",
            " You can reduce the model by removing higher-order terms one at a time (keep main effects contained in "
            "interactions or squares), or use stepwise selection.")


def worst_level(findings: list[Finding]) -> str:
    return "warn" if any(f.level == "warn" for f in findings) else "good"

