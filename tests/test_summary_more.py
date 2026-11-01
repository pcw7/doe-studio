"""주요 결과 요약 — 혼합물·분할구·산포(최소제곱·최대우도)·이항 반응.

요약 문장은 이미 문서 예제와 대조해 검증한 표(분산분석·계수·이탈도·적합도 검정)의 숫자에서만 나온다.
여기서는 분석 종류마다 정한 규칙(summary.py 머리말)대로 문장이 나오는지 본다.
- 혼합물: 성분 비율 효과는 'Linear' 묶음 p, 비선형 혼합 항은 개별 p 와 상승·상쇄(계수 부호), 줄이기 안내는 '성분의 선형 항은 남김'.
- 분할구: 바꾸기 어려운 요인의 항은 전구 오차 — 자유도 0(검정 불가)·2(검정력 낮음)·4(안내만).
- 산포: '표준편차와 유의하게 관련된 항', 2수준 주효과의 표준편차 배수(exp(2·계수)), 최대우도는 Z 검정 p·모형 요약 없음.
- 이항: 이탈도 표 p, 유의한 주효과의 오즈비(숫자: 코드 1단위, 텍스트: 높음 대 낮음), Hosmer-Lemeshow 적합도.
"""
import math
import re

import numpy as np
import pytest

from doe_core.analysis.binary import analyze_binary
from doe_core.analysis.factorial import analyze_factorial, analyze_worksheet
from doe_core.analysis.summary import key_findings, supports
from doe_core.analysis.variability import analyze_variability
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.split_plot import create_split_plot_design
from doe_core.examples import EXAMPLES
from doe_core.io.worksheet import Worksheet
from doe_core.report.builders import analysis_report, binary_report
from tests.test_app import run

HANGUL = re.compile(r"[가-힣]")


def _text(fs, level=None) -> str:
    return " ".join(f.ko for f in fs if level is None or f.level == level)


def _blend():
    return {e.key: e for e in EXAMPLES}["blend"].build()


def _variability_ws(names=("온도", "시간", "교반", "촉매")):
    """2⁴, ln(표준편차) = 0.3 + 0.35·A − 0.25·C + 잡음, 각 런 6회 측정."""
    F = [Factor(names[0], 60, 80), Factor(names[1], 1, 3), Factor(names[2], 100, 300), Factor(names[3], 0.5, 1.5)]
    d = create_two_level_design(4, factors=F, randomize=False)
    c = d.coded.reset_index(drop=True)
    ln_s = 0.3 + 0.35 * c["A"] - 0.25 * c["C"] + np.random.default_rng(2).normal(0, 0.05, len(c))
    ws = Worksheet(d)
    order = np.argsort(c["StdOrder"].values)
    ws.add_column("Std", list(np.exp(ln_s.values)[order]), order="std")
    ws.add_column("N", [6] * len(c), order="std")
    return ws


def _binary_ws(names=("온도", "습도", "포장", "보관일"), events="부패", trials="용기"):
    """2⁴ 사건/시행, 로짓 = −2.74 + 0.30·A + 0.13·B − 0.25·C(텍스트 요인) − 0.02·D."""
    F = [Factor(names[0], 20, 40), Factor(names[1], 30, 70), Factor(names[2], "A", "B"), Factor(names[3], 5, 15)]
    d = create_two_level_design(4, factors=F, randomize=False)
    c = d.coded.reset_index(drop=True)
    rng = np.random.default_rng(1)
    eta = -2.74 + 0.30 * c["A"] + 0.13 * c["B"] - 0.25 * c["C"] - 0.02 * c["D"]
    m = rng.integers(450, 550, len(c)).astype(float)
    y = rng.binomial(m.astype(int), 1 / (1 + np.exp(-eta))).astype(float)
    ws = Worksheet(d)
    order = np.argsort(c["StdOrder"].values)
    ws.add_column(events, list(y[order]), order="std")
    ws.add_column(trials, list(m[order]), order="std")
    return ws


def test_mixture_summary():
    a = analyze_worksheet(_blend(), "용해도(g/L)")
    assert supports(a)
    fs = key_findings(a)
    good = _text(fs, "good")
    assert "성분 비율에 따라 반응이 유의하게 달라집니다(선형 혼합 p < 0.001)" in good
    # 비선형 혼합 항: 계수 부호로 상승·상쇄
    beta = dict(zip(a.col_labels, a.beta))
    for name in ("물*에탄올", "에탄올*아세톤", "물*아세톤"):
        tag = "상승" if beta[name] > 0 else "상쇄"
        assert re.search(re.escape(name) + r" \(p [^)]*, " + tag + r"\)", good), (name, tag)
    assert "상승은 섞었을 때" in good and "모형 설명력" in good
    # 특수 3차: 유의하지 않은 3성분 항과 '성분의 선형 항은 남김'
    a3 = analyze_worksheet(_blend(), "용해도(g/L)", model="special cubic")
    info = _text(key_findings(a3), "info")
    assert "물*에탄올*아세톤" in info and "성분의 선형 항은 남김" in info
    assert all(f.en and not HANGUL.search(f.en.replace("물", "").replace("에탄올", "").replace("아세톤", ""))
               for f in key_findings(a3))
    rep = analysis_report(_blend(), a, figures=False)
    assert "주요 결과 요약" in [b.content for b in rep.blocks if b.kind == "heading"]


@pytest.mark.parametrize("n, htc, wp_reps, df_wp, want", [
    (3, 1, 1, 0, "자유도가 0 이라 p 값을 구할 수 없습니다"),
    (4, 1, 2, 2, "자유도 2 인 전구 오차로 검정해 검정력이 낮습니다"),
    (4, 2, 2, 4, "전구 오차(자유도 4)로, 나머지 항은 하위구 오차로"),
])
def test_split_plot_summary(n, htc, wp_reps, df_wp, want):
    d = create_split_plot_design(n, htc, seed=3, wp_replicates=wp_reps)
    rng = np.random.default_rng(5)
    c = d.coded
    wp = rng.normal(scale=2.0, size=int(c["WP"].max()) + 1)
    y = (10 + 3 * c["A"] + 2 * c["B"] - 1.5 * c["C"] + wp[c["WP"]] + rng.normal(scale=0.5, size=len(c))).values
    a = analyze_factorial(d, y.astype(float), order=2)
    assert a.df_wp == df_wp and supports(a)
    fs = key_findings(a)
    assert want in _text(fs)
    htc_names = [t.name for i, t in enumerate(a.terms) if t.kind == "factor" and a.is_wp_term(i)]
    assert f"바꾸기 어려운 요인의 항({', '.join(htc_names)})" in _text(fs)
    assert "반응과 유의하게 관련된 항" in _text(fs, "good") and "B (p" in _text(fs, "good")
    if df_wp == 0:                                             # 검정할 수 없는 전구 항은 유의·비유의 목록에 없다
        assert not re.search(r"(관련된 항|유의하지 않은 항)[^.]*\bA \(p", _text(fs))


def test_variability_summary_ls_and_ml():
    ws = _variability_ws()
    a = analyze_variability(ws, "Std", "N", order=1)
    assert supports(a)
    fs = key_findings(a)
    good, info = _text(fs, "good"), _text(fs, "info")
    assert "표준편차와 유의하게 관련된 항(p < 0.05): 온도 (p < 0.001), 교반 (p < 0.001)" in good
    beta = dict(zip(a.col_labels, a.beta))
    for name in ("온도", "교반"):                                # Ratio Effect = exp(효과) = exp(2·계수)
        assert f"{name} — 높은 수준의 표준편차가 낮은 수준의 {math.exp(2 * beta[name]):.2f}배" in info
    assert math.exp(2 * beta["온도"]) > 1 > math.exp(2 * beta["교반"])
    assert "산포를 줄이려면" in info and "모형 설명력" in good

    ml = analyze_variability(ws, "Std", "N", order=1, method="ml")
    fs_ml = key_findings(ml)
    assert supports(ml)
    assert "표준편차와 유의하게 관련된 항" in _text(fs_ml, "good")
    assert "최대우도 추정이라 모형 요약(R²)과 분산분석표는 없습니다" in _text(fs_ml, "info")
    assert not any("모형 설명력" in f.ko or "표준화 잔차" in f.ko for f in fs_ml)
    assert "단계적 선택" not in _text(fs_ml)                    # 최대우도에는 단계적 선택이 없다
    rep = analysis_report(ws, ml, figures=False)
    assert "주요 결과 요약" in [b.content for b in rep.blocks if b.kind == "heading"]


def test_binary_summary():
    ws = _binary_ws()
    a = analyze_binary(ws, events="부패", trials="용기", event_name="부패", order=1)
    assert supports(a)
    fs = key_findings(a)
    good, info = _text(fs, "good"), _text(fs, "info")
    assert "사건(부패) 확률과 유의하게 관련된 항" in good
    for name in ("온도", "포장"):
        assert f"{name} (p" in good
    beta = dict(zip(a.col_labels, a.beta))
    assert f"온도 10 증가 → 오즈 {math.exp(beta['온도']):.2f}배" in info              # 코드 1단위 = (40−20)/2
    assert f"포장 B 대 A → 오즈 {math.exp(2 * beta['포장']):.2f}배" in info           # 텍스트 요인: 높음 대 낮음
    assert "이탈도 R²" in info and "Hosmer-Lemeshow" in _text(fs)
    rep = binary_report(ws, a, figures=False)
    assert "주요 결과 요약" in [b.content for b in rep.blocks if b.kind == "heading"]

    # 교호작용에 들어 있는 주효과는 오즈비를 적지 않는다(문서 표에서도 '*')
    a2 = analyze_binary(ws, events="부패", trials="용기", event_name="부패", order=2)
    assert "오즈비" not in _text(key_findings(a2))

    # 영어 이름이면 영어 문장에 한글이 없다
    ws_en = _binary_ws(("Temp", "Humidity", "Pack", "Days"), "Spoiled", "Cans")
    a_en = analyze_binary(ws_en, events="Spoiled", trials="Cans", event_name="Spoiled", order=1)
    assert all(f.en and not HANGUL.search(f.en) for f in key_findings(a_en))
    assert "Temp +10 → odds ×" in " ".join(f.en for f in key_findings(a_en))


def test_summary_on_mixture_variability_binary_pages():
    at = run("analyze.py", _blend())                         # 혼합물 설계는 분석 화면에서 혼합물 분석으로
    at.button[0].click().run()
    assert not at.exception
    assert any(e.label == "주요 결과 요약" for e in at.expander)
    assert any("선형 혼합 p" in m.value for m in at.markdown)
    assert any("물\\*에탄올" in m.value for m in at.markdown)              # '*' 가 기울임이 되지 않게

    at = run("variability.py", _variability_ws())
    at.selectbox(key="var_resp").set_value("Std").run()
    at.selectbox(key="var_count").set_value("N").run()
    at.button(key="var_run").click().run()
    assert not at.exception
    assert any(e.label == "주요 결과 요약" for e in at.expander)
    assert any("표준편차와 유의하게 관련된 항" in m.value for m in at.markdown)

    at = run("binary.py", _binary_ws())
    at.selectbox(key="bin_events").set_value("부패").run()
    at.selectbox(key="bin_trials").set_value("용기").run()
    at.button(key="bin_run").click().run()
    assert not at.exception
    assert any(e.label == "주요 결과 요약" for e in at.expander)
    assert any("확률과 유의하게 관련된 항" in m.value for m in at.markdown)
