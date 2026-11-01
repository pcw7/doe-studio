"""보고서 생성기 — 화면에 보이는 결과표·그래프를 같은 순서로 보고서에 담는다.

- 설계 보고서: 설계 요약, 별칭 구조, (혼합물) 경계·점 유형·성분 범위·선형 제약 표와 단순체 설계도, 설계표, 실험 순서표.
- 분석 보고서: 계수표, 모형 요약, 분산분석표(행 들여쓰기), 회귀식, 별칭 구조, 이상 관측치, 평균 표,
  그래프(잔차 4종, 효과 파레토, 주효과도, 반응표면 등고선, 혼합물 반응 추적 그림).
- 최적화 보고서: Parameters, Solution, Setting, Multiple Response Prediction, 개별 만족도.
- 최적 설계 보고서: 선택 정보·행 번호·최적성 통계량.
원자료(실험 순서표, 적합치·진단)는 Excel 의 별도 시트로만 넣는다.
"""
from __future__ import annotations

import pandas as pd

from .model import Report

KIND_KO = {
    "TwoLevelDesign": "2수준 요인설계", "PlackettBurmanDesign": "Plackett-Burman 설계",
    "GeneralFullFactorialDesign": "일반 완전요인설계", "ResponseSurfaceDesign": "반응표면 설계",
    "MixtureDesign": "혼합물 설계", "DefinitiveScreeningDesign": "확정적 선별설계", "SplitPlotDesign": "2수준 분할구 설계",
}


def kind_ko(design) -> str:
    return KIND_KO.get(type(design).__name__, type(design).__name__)


def _try(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except Exception:  # noqa: BLE001  보고서는 가능한 것만 담는다
        return None


def design_report(ws, *, figures: bool = True, mode: str = "light") -> Report:
    from ..designs.mixture import MixtureDesign
    d = ws.design
    if isinstance(d, MixtureDesign):
        sub = f"성분 {d.q}개" + (f" · 공정 변수 {len(d.process)}개" if d.process else "") + f" · 런 {d.n_runs}개"
    else:
        sub = f"요인 {len(d.factors)}개 · 런 {d.n_runs}개"
    r = Report(f"설계 보고서 — {kind_ko(d)}", sub)
    r.heading("설계 요약 (Design Summary)")
    r.mono(d.summary_text())
    if hasattr(d, "alias_text"):
        r.heading("별칭 구조 (Alias Structure)")
        r.mono(d.alias_text())
    if isinstance(d, MixtureDesign):
        if d.boundaries:
            r.table(d.boundaries_table(), "경계 수 (Number of Boundaries for Each Dimension)")
        r.table(d.points_table(), "점 유형별 설계점 수 (Number of Design Points for Each Type)")
        r.table(d.bounds_table(), "성분 범위 (Bounds of Mixture Components)")
        if d.constraints:
            r.table(d.constraints_table(), "선형 제약 (Linear Constraints of Mixture Components)")
        if figures and d.q >= 3:
            from ..plots.mixture_plots import simplex_design_plot
            fig = _try(simplex_design_plot, d, mode=mode)
            if fig is not None:
                r.figure(fig, "단순체 설계도 (Simplex Design Plot)")
    if hasattr(d, "design_table"):
        r.heading("설계표 (Design Table)")
        r.table(d.design_table())
    table = ws.table("run")
    r.heading("실험 순서표 (Worksheet, 런 순서)")
    r.table(table)
    r.data_sheets["워크시트"] = table
    return r


def _anova_with_indent(a) -> pd.DataFrame:
    tbl = a.anova_table()
    tbl["Source"] = [("  " * row.level) + s for row, s in zip(a.anova_rows(), tbl["Source"])]
    return tbl


def analysis_report(ws, a, *, alpha: float = 0.05, figures: bool = True, mode: str = "light") -> Report:
    """분석 결과 보고서. a 는 analyze_worksheet 의 결과(요인·반응표면·DSD·분할구·혼합물)."""
    from ..analysis.diagnostics import diagnostics, unusual_legend, unusual_table
    d = a.design
    mixture = getattr(a, "is_mixture", False)
    r = Report(f"{a.response} 분석 보고서", f"{kind_ko(d)} · 분석에 쓴 런 {a.n}개 / 전체 {len(d.coded)}개")
    terms = ", ".join(getattr(t, "short", None) or t.name for t in a.terms)
    r.text("모형 항: " + terms)
    if a.removed_terms:
        r.text("완전 별칭(선형 종속)이라 뺀 항: " + ", ".join(t.name for t in a.removed_terms))

    if mixture:
        r.heading(a.coefficients_title())
        r.table(a.coefficients_table(), note=a.coefficients_note())
    else:
        r.heading("코드화된 계수 (Coded Coefficients)")
        r.table(a.coefficients_table())
    r.heading("모형 요약 (Model Summary)")
    r.table(a.summary_table())
    r.heading(a.anova_title() if mixture else "분산 분석 (Analysis of Variance)")
    r.table(_anova_with_indent(a))
    eq = a.equation() if hasattr(a, "equation") else None
    if eq:
        r.heading("회귀 방정식 (" + eq[0] + ")")
        r.mono(eq[1])
    if not mixture and (a.two_level or getattr(a, "is_dsd", False)):
        from ..analysis.alias import alias_lines, alias_title, factor_name_table, has_aliasing
        if _try(has_aliasing, a):
            r.heading("별칭 구조 (" + alias_title(a) + ")")
            r.table(factor_name_table(a))
            r.mono("\n".join(alias_lines(a)))
    un = unusual_table(a)
    if not un.empty:
        r.heading("비정상적인 관측치에 대한 적합치 및 진단 (Fits and Diagnostics for Unusual Observations)")
        r.table(un, note="  ".join(unusual_legend(a)))
    if not mixture:
        from ..analysis.means import means_table
        m = _try(means_table, a)
        if m is not None and not m.empty:
            r.heading("평균 표 (Means)")
            r.table(m)

    if figures:
        from ..plots.residual_plots import four_in_one
        r.heading("그래프")
        fig = _try(four_in_one, a, "regular", mode)
        if fig is not None:
            r.figure(fig, "잔차 그림 (Residual Plots)")
        if mixture:
            from ..plots.mixture_plots import response_trace_plot
            fig = _try(response_trace_plot, a, mode=mode)
            if fig is not None:
                r.figure(fig, "반응 추적 그림 (Response Trace Plot)")
        else:
            if a.two_level or a.is_rs:
                from ..analysis.effects import effects
                from ..plots.effects_plots import pareto_chart
                e = _try(effects, a, alpha)
                if e is not None:
                    r.figure(pareto_chart(e, mode), e.pareto_title)
            if a.two_level:
                from ..plots.factorial_plots import main_effects_plot
                fig = _try(main_effects_plot, a, mode=mode)
                if fig is not None:
                    r.figure(fig, "주효과도 (Main Effects Plot)")
            if a.is_rs:
                from ..plots.contour_plots import contour_plot
                num = [L for L, f in zip(d.letters, d.factors) if getattr(f, "is_numeric", False)]
                if len(num) >= 2:
                    fig = _try(contour_plot, a, num[0], num[1], levels=7, mode=mode)
                    if fig is not None:
                        r.figure(fig, "등고선도 (Contour Plot)")
    r.data_sheets["워크시트"] = ws.table("run")
    r.data_sheets["적합치·진단"] = diagnostics(a)
    return r


def optimization_report(models: dict, goals: list, res, *, title: str = "반응 최적화 보고서") -> Report:
    from ..optimize.optimizer import multiple_response_prediction, parameters_table, setting_table, solution_table
    r = Report(title, f"반응 {', '.join(models)} · 종합 만족도 {res.D:.4f}")
    r.heading("파라미터 (Parameters)")
    r.table(parameters_table(list(models.values()), goals))
    r.heading("해 (Solution)")
    r.table(solution_table(res, goals))
    r.heading("설정 (Setting)")
    r.table(setting_table(res))
    r.heading("다중 반응 예측 (Multiple Response Prediction)")
    r.table(multiple_response_prediction(res))
    r.table(pd.DataFrame([{"반응": k, "개별 만족도 d": f"{v:.5f}"} for k, v in res.d.items()]))
    return r


def optimal_design_report(res, ws=None) -> Report:
    r = Report("최적 설계 보고서", "Select Optimal Design")
    title = "Specified Design" if res.task == "evaluate" else "Optimal Design"
    r.mono("\n".join([*res.header_lines(), title, res.rows_text()]))
    if res.statistics:
        r.table(res.statistics_table().rename(columns={0: "통계량", 1: "값"}), "최적성 통계량")
    if ws is not None:
        tbl = ws.table("worksheet").copy()
        tbl.insert(0, "Row", range(1, len(tbl) + 1))
        tbl["OptPoint"] = res.indicator()
        r.data_sheets["후보점·지시자"] = tbl
    return r
