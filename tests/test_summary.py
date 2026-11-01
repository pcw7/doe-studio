"""분석 결과 요약(주요 결과) 검증 — 실사용 점검 ⑤.

시나리오(온도·시간·촉매 2³ + 중앙점 3, 참 모형에 제곱 항이 있어 곡면성이 유의):
- 유의한 항·유의하지 않은 항(모형 줄이기 제안), 곡면성 경고(축점 추가 안내), 적합성 결여 없음, 큰 잔차 없음.
- 곡면성이 없는 데이터에서 Ct Pt 를 넣으면 '중앙점 포함을 끄라' 는 안내.
- 포화 모형(오차 자유도 0), 과적합(R²(pred) ≪ R²(adj)), 큰 잔차(이상값), 단계적 선택이면 모형 줄이기 제안 없음.
- 분석 화면·분석 보고서에 '주요 결과 요약' 이 나오고, 분할구·혼합물 등은 대상이 아니다.
"""
import numpy as np
import pytest

from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.stepwise import StepwiseOptions
from doe_core.analysis.summary import PRED_GAP, key_findings, supports
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet
from tests.test_app import run


def _ws(curv=True, outlier=False, seed=5, cp=3):
    fac = [Factor("온도", 60, 80), Factor("시간", 1, 3), Factor("촉매", 0.5, 1.5)]
    d = create_two_level_design(3, 8, factors=fac, center_points=cp, seed=1)
    rng = np.random.default_rng(seed)
    c = d.coded.sort_values("StdOrder")
    a, b, k = c["A"].values, c["B"].values, c["C"].values
    y = 70 + 6 * a + 3 * b + 4 * k - 2.5 * a * b + rng.normal(0, 0.4, len(c))
    if curv:
        y += -3 * a * a - 2 * b * b - 1.5 * k * k + 6.5
    if outlier:
        y[2] += 8
    ws = Worksheet(d)
    ws.add_column("수율", y, order="std")
    return ws


def _by_level(fs, level):
    return [f.ko for f in fs if f.level == level]


def test_curvature_scenario():
    a = analyze_worksheet(_ws(), "수율", order=2)
    fs = key_findings(a)
    good = " ".join(_by_level(fs, "good"))
    assert "반응과 유의하게 관련된 항" in good and "온도" in good and "온도*시간" in good
    assert "적합성 결여가 없습니다" in good and "큰 관측치가 없습니다" in good
    warn = " ".join(_by_level(fs, "warn"))
    assert "곡면성이 유의합니다" in warn and "축점 추가" in warn
    info = " ".join(_by_level(fs, "info"))
    assert "유의하지 않은 항" in info and "시간*촉매" in info and "고차 항부터" in info
    assert all(f.en for f in fs)
    assert supports(a)


def test_no_curvature_with_ct_pt_in_model():
    a = analyze_worksheet(_ws(curv=False), "수율", order=2, include_center=True)
    info = " ".join(_by_level(key_findings(a), "info"))
    assert "곡면성이 유의하지 않습니다" in info and "중앙점 포함" in info


def test_saturated_overfit_outlier_and_stepwise():
    a = analyze_worksheet(_ws(cp=0), "수율", order=3)
    assert a.df_error == 0
    fs = key_findings(a)
    assert any("오차 자유도가 0" in f.ko for f in fs)

    a = analyze_worksheet(_ws(), "수율", order=2)
    s = a.summary()
    a.summary = lambda: {**s, "R-sq(adj)": 0.90, "R-sq(pred)": 0.90 - PRED_GAP - 0.01}
    assert any("예측 R²" in f.ko and f.level == "warn" for f in key_findings(a))

    # 잔차 자유도 3 이면 내부 표준화 잔차는 √3 을 넘지 못한다 → 주효과 모형(자유도 7)에 이상값 +8
    a = analyze_worksheet(_ws(curv=False, outlier=True), "수율", order=1, include_center=False)
    assert any("표준화 잔차가 큰 관측치 1개" in f.ko and f.level == "warn" for f in key_findings(a))

    a = analyze_worksheet(_ws(), "수율", order=2, stepwise=StepwiseOptions(method="backward"))
    assert not any("고차 항부터" in f.ko for f in key_findings(a))


def test_summary_on_page_and_report():
    from doe_core.report.builders import analysis_report
    ws = _ws()
    at = run("analyze.py", ws)
    [b] = [b for b in at.button if b.label == "분석"]
    b.click().run()
    assert not at.exception
    assert any(e.label == "주요 결과 요약" for e in at.expander)
    assert any("곡면성이 유의합니다" in m.value for m in at.markdown)
    rep = analysis_report(ws, at.session_state["analysis"], figures=False)
    heads = [b.content for b in rep.blocks if b.kind == "heading"]
    assert "주요 결과 요약" in heads
    rep_en = analysis_report(ws, at.session_state["analysis"], figures=False, lang="en")
    assert "Key results" in [b.content for b in rep_en.blocks if b.kind == "heading"]
    assert any("Curvature is significant" in str(b.content) for b in rep_en.blocks)


def test_report_marks_render_in_korean_pdf_fonts():
    """보고서의 요약 기호는 한글 PDF 글꼴에 있는 글자여야 한다(✓ 는 맑은 고딕에 없어 네모로 깨졌다)."""
    from pathlib import Path
    from doe_core.report.builders import KEY_MARKS
    for ch in KEY_MARKS.values():
        ch.encode("cp949")                                       # KS X 1001 에 있는 기호(한글 글꼴 공통)
    font = Path("C:/Windows/Fonts/malgun.ttf")
    if font.exists():
        from reportlab.pdfbase.ttfonts import TTFont
        cmap = TTFont("MalgunCheck", str(font)).face.charToGlyph
        assert all(ord(ch) in cmap for ch in KEY_MARKS.values())
