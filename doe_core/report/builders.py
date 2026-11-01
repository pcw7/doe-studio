"""보고서 생성기 — 화면에 보이는 결과표·그래프를 같은 순서로 보고서에 담는다.

- 설계 보고서: 설계 요약, 별칭 구조, (혼합물) 경계·점 유형·성분 범위·선형 제약 표와 단순체 설계도, 설계표, 실험 순서표.
- 분석 보고서: 계수표, 모형 요약, 분산분석표(행 들여쓰기), 회귀식, 별칭 구조, 이상 관측치, 평균 표,
  그래프(잔차 4종, 효과 파레토, 주효과도, 반응표면 등고선, 혼합물 반응 추적 그림).
- 최적화 보고서: Parameters, Solution, Setting, Multiple Response Prediction, 개별 만족도.
- 최적 설계 보고서: 선택 정보·행 번호·최적성 통계량.
원자료(실험 순서표, 적합치·진단)는 Excel 의 별도 시트로만 넣는다. lang="en" 이면 제목·소제목·그래프 글자가 영어.
"""
from __future__ import annotations

import pandas as pd

from ..plots.lang import english_of
from .model import Report

KIND_KO = {
    "TwoLevelDesign": "2수준 요인설계", "PlackettBurmanDesign": "Plackett-Burman 설계",
    "GeneralFullFactorialDesign": "일반 완전요인설계", "ResponseSurfaceDesign": "반응표면 설계",
    "MixtureDesign": "혼합물 설계", "DefinitiveScreeningDesign": "확정적 선별설계", "SplitPlotDesign": "2수준 분할구 설계",
    "TaguchiDesign": "Taguchi 설계",
}
KIND_EN = {
    "TwoLevelDesign": "2-level factorial design", "PlackettBurmanDesign": "Plackett-Burman design",
    "GeneralFullFactorialDesign": "General full factorial design", "ResponseSurfaceDesign": "Response surface design",
    "MixtureDesign": "Mixture design", "DefinitiveScreeningDesign": "Definitive screening design",
    "SplitPlotDesign": "2-level split-plot design", "TaguchiDesign": "Taguchi design",
}


def kind_ko(design, lang: str = "ko") -> str:
    name = type(design).__name__
    return (KIND_EN if lang == "en" else KIND_KO).get(name, name)


def _tr(lang: str):
    def t(ko: str, en: str | None = None) -> str:
        if lang != "en":
            return ko
        return en if en is not None else (english_of(ko) or ko)
    return t


def _try(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except Exception:  # noqa: BLE001  보고서는 가능한 것만 담는다
        return None


def design_report(ws, *, figures: bool = True, mode: str = "light", lang: str = "ko") -> Report:
    from ..designs.mixture import MixtureDesign
    t = _tr(lang)
    d = ws.design
    if isinstance(d, MixtureDesign):
        sub = t(f"성분 {d.q}개" + (f" · 공정 변수 {len(d.process)}개" if d.process else "") + f" · 런 {d.n_runs}개",
                f"{d.q} components" + (f" · {len(d.process)} process variables" if d.process else "")
                + f" · {d.n_runs} runs")
    else:
        sub = t(f"요인 {len(d.factors)}개 · 런 {d.n_runs}개", f"{len(d.factors)} factors · {d.n_runs} runs")
    r = Report(t(f"설계 보고서 — {kind_ko(d)}", f"Design report — {kind_ko(d, 'en')}"), sub, lang=lang)
    r.heading(t("설계 요약 (Design Summary)"))
    r.mono(d.summary_text())
    if hasattr(d, "alias_text"):
        r.heading(t("별칭 구조 (Alias Structure)"))
        r.mono(d.alias_text())
    if isinstance(d, MixtureDesign):
        if d.boundaries:
            r.table(d.boundaries_table(), t("경계 수 (Number of Boundaries for Each Dimension)"))
        r.table(d.points_table(), t("점 유형별 설계점 수 (Number of Design Points for Each Type)"))
        r.table(d.bounds_table(), t("성분 범위 (Bounds of Mixture Components)"))
        if d.constraints:
            r.table(d.constraints_table(), t("선형 제약 (Linear Constraints of Mixture Components)"))
        if figures and d.q >= 3:
            from ..plots.mixture_plots import simplex_design_plot
            fig = _try(simplex_design_plot, d, mode=mode)
            if fig is not None:
                r.figure(fig, t("단순체 설계도 (Simplex Design Plot)"))
    if hasattr(d, "design_table"):
        r.heading(t("설계표 (Design Table)"))
        r.table(d.design_table())
    table = ws.table("run")
    r.heading(t("실험 순서표 (Worksheet, 런 순서)", "Worksheet (run order)"))
    r.table(table)
    r.data_sheets[t("워크시트", "Worksheet")] = table
    return r


def _anova_with_indent(a) -> pd.DataFrame:
    tbl = a.anova_table()
    tbl["Source"] = [("  " * row.level) + s for row, s in zip(a.anova_rows(), tbl["Source"])]
    return tbl


def analysis_report(ws, a, *, alpha: float = 0.05, figures: bool = True, mode: str = "light",
                    lang: str = "ko") -> Report:
    """분석 결과 보고서. a 는 analyze_worksheet 의 결과(요인·반응표면·DSD·분할구·혼합물)."""
    from ..analysis.diagnostics import diagnostics, unusual_legend, unusual_table
    t = _tr(lang)
    d = a.design
    mixture = getattr(a, "is_mixture", False)
    r = Report(t(f"{a.response} 분석 보고서", f"Analysis report — {a.response}"),
               t(f"{kind_ko(d)} · 분석에 쓴 런 {a.n}개 / 전체 {len(d.coded)}개",
                 f"{kind_ko(d, 'en')} · {a.n} of {len(d.coded)} runs used"), lang=lang)
    terms = ", ".join(getattr(t_, "short", None) or t_.name for t_ in a.terms)
    r.text(t("모형 항: ", "Model terms: ") + terms)
    if a.removed_terms:
        r.text(t("완전 별칭(선형 종속)이라 뺀 항: ", "Removed (completely aliased) terms: ")
               + ", ".join(x.name for x in a.removed_terms))
    sel = getattr(a, "selection", None)
    if sel is not None:
        from ..analysis.stepwise import METHOD_TITLE_KO
        r.heading(t(f"{METHOD_TITLE_KO[sel.method]} ({sel.title()})", sel.title()))
        r.mono("\n".join(sel.method_lines()))
        r.text(sel.candidate_line())
        per = 5                                     # 쪽 너비에 맞게 5단계씩 나눈다
        for k in range(0, len(sel.steps), per):
            last = k + per >= len(sel.steps)
            r.table(sel.details_table(k, per), note="  ".join(sel.footer_lines()) if last else None)
        r.mono("\n".join(sel.step_notes(en=lang == "en")))

    if mixture:
        r.heading(a.coefficients_title())
        r.table(a.coefficients_table(), note=a.coefficients_note())
    else:
        r.heading(t("코드화된 계수 (Coded Coefficients)"))
        r.table(a.coefficients_table())
    r.heading(t("모형 요약 (Model Summary)"))
    r.table(a.summary_table())
    r.heading(a.anova_title() if mixture else t("분산 분석 (Analysis of Variance)"))
    r.table(_anova_with_indent(a))
    eq = a.equation() if hasattr(a, "equation") else None
    if eq:
        r.heading(t("회귀 방정식 (" + eq[0] + ")"))
        r.mono(eq[1])
    if not mixture and (a.two_level or getattr(a, "is_dsd", False)):
        from ..analysis.alias import alias_lines, alias_title, factor_name_table, has_aliasing
        if _try(has_aliasing, a):
            r.heading(t("별칭 구조 (" + alias_title(a) + ")"))
            r.table(factor_name_table(a))
            r.mono("\n".join(alias_lines(a)))
    un = unusual_table(a)
    if not un.empty:
        r.heading(t("비정상적인 관측치에 대한 적합치 및 진단 (Fits and Diagnostics for Unusual Observations)"))
        r.table(un, note="  ".join(unusual_legend(a)))
    if not mixture:
        from ..analysis.means import means_table
        m = _try(means_table, a)
        if m is not None and not m.empty:
            r.heading(t("평균 표 (Means)"))
            r.table(m)

    if figures:
        from ..plots.residual_plots import four_in_one
        r.heading(t("그래프", "Graphs"))
        fig = _try(four_in_one, a, "regular", mode)
        if fig is not None:
            r.figure(fig, t("잔차 그림 (Residual Plots)"))
        if mixture:
            from ..plots.mixture_plots import response_trace_plot
            fig = _try(response_trace_plot, a, mode=mode)
            if fig is not None:
                r.figure(fig, t("반응 추적 그림 (Response Trace Plot)"))
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
                    r.figure(fig, t("주효과도 (Main Effects Plot)"))
            if a.is_rs:
                from ..plots.contour_plots import contour_plot
                num = [L for L, f in zip(d.letters, d.factors) if getattr(f, "is_numeric", False)]
                if len(num) >= 2:
                    fig = _try(contour_plot, a, num[0], num[1], levels=7, mode=mode)
                    if fig is not None:
                        r.figure(fig, t("등고선도 (Contour Plot)"))
    r.data_sheets[t("워크시트", "Worksheet")] = ws.table("run")
    r.data_sheets[t("적합치·진단", "Fits and diagnostics")] = diagnostics(a)
    return r


def optimization_report(models: dict, goals: list, res, *, title: str | None = None, lang: str = "ko") -> Report:
    from ..optimize.optimizer import multiple_response_prediction, parameters_table, setting_table, solution_table
    t = _tr(lang)
    r = Report(title or t("반응 최적화 보고서", "Response optimization report"),
               t(f"반응 {', '.join(models)} · 종합 만족도 {res.D:.4f}",
                 f"Responses {', '.join(models)} · composite desirability {res.D:.4f}"), lang=lang)
    r.heading(t("파라미터 (Parameters)"))
    r.table(parameters_table(list(models.values()), goals))
    r.heading(t("해 (Solution)"))
    r.table(solution_table(res, goals))
    r.heading(t("설정 (Setting)"))
    r.table(setting_table(res))
    r.heading(t("다중 반응 예측 (Multiple Response Prediction)"))
    r.table(multiple_response_prediction(res))
    r.table(pd.DataFrame([{t("반응", "Response"): k, t("개별 만족도 d", "Individual desirability d"): f"{v:.5f}"}
                          for k, v in res.d.items()]))
    return r


def optimal_design_report(res, ws=None, *, lang: str = "ko") -> Report:
    t = _tr(lang)
    r = Report(t("최적 설계 보고서", "Optimal design report"), "Select Optimal Design", lang=lang)
    title = "Specified Design" if res.task == "evaluate" else "Optimal Design"
    r.mono("\n".join([*res.header_lines(), title, res.rows_text()]))
    if res.statistics:
        r.table(res.statistics_table().rename(columns={0: t("통계량", "Statistic"), 1: t("값", "Value")}),
                t("최적성 통계량", "Optimality statistics"))
    if ws is not None:
        tbl = ws.table("worksheet").copy()
        tbl.insert(0, "Row", range(1, len(tbl) + 1))
        tbl["OptPoint"] = res.indicator()
        r.data_sheets[t("후보점·지시자", "Candidates and indicator")] = tbl
    return r


def taguchi_report(ws, analyses: dict, *, figures: bool = True, mode: str = "light", lang: str = "ko") -> Report:
    """Taguchi 분석 보고서: 특성(S/N 비·평균 …)마다 계수표·모형 요약·분산분석표·반응표·주효과도."""
    from ..analysis.taguchi import SN_TYPES
    t = _tr(lang)
    d = ws.design
    r = Report(t("Taguchi 분석 보고서", "Taguchi analysis report"),
               f"{d.used_name} · " + t(f"요인 {len(d.factors)}개 · 런 {d.n_runs}개",
                                      f"{len(d.factors)} factors · {d.n_runs} runs"), lang=lang)
    r.mono(d.columns_text())
    for c, a in analyses.items():
        r.heading(a.coefficients_title())
        r.table(a.coefficients_table())
        r.table(a.summary_table(), t("모형 요약 (Model Summary)"))
        r.table(a.anova_table(), a.anova_title())
        r.table(a.response_table(), a.response_title() + (f" — {SN_TYPES[a.sn_type]}" if c == "sn" else ""))
        if figures:
            from ..plots.taguchi_plots import taguchi_main_effects_plot
            fig = _try(taguchi_main_effects_plot, a, mode)
            if fig is not None:
                r.figure(fig)
    r.data_sheets[t("워크시트", "Worksheet")] = ws.table("run")
    return r
