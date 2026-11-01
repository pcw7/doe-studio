"""내장 예제(가상 데이터)와 화면 안내 문구 — 실사용 점검 ⑦.

- Minitab 예제 파일(.MWX)은 저장소에 없어서 새로 받은 사람은 시작 화면에 예제가 하나도 없었다.
  코드로 만드는 가상 화학 예제 3개: 선별(곡면성 유의·적합성 결여 없음) → 최적화(17런, 수율·순도) → 용매 배합(혼합물).
- 다중 선택의 기본 영어 안내('Choose options')를 화면 언어로.
"""
import numpy as np
import pytest

from doe_core.analysis.factorial import analyze_worksheet
from doe_core.examples import EXAMPLES, reaction_optimization, reaction_screening, solvent_blend
from tests.test_app import run


def test_screening_example_teaches_curvature():
    ws = reaction_screening()
    assert type(ws.design).__name__ == "TwoLevelDesign" and ws.design.n_runs == 11
    rows = {r.source: r for r in analyze_worksheet(ws, "수율(%)", order=2).anova_rows()}
    assert rows["Curvature"].p < 0.001 and rows["Lack-of-Fit"].p > 0.3
    assert reaction_screening().table("run").equals(ws.table("run"))              # 고정 난수: 언제나 같은 값


def test_optimization_and_blend_examples():
    ws = reaction_optimization()
    assert type(ws.design).__name__ == "ResponseSurfaceDesign" and ws.design.n_runs == 17
    assert list(ws.columns.columns) == ["수율(%)", "순도(%)"]
    for c in ws.columns.columns:
        rows = {r.source: r for r in analyze_worksheet(ws, c).anova_rows()}
        assert rows["Lack-of-Fit"].p > 0.3 and rows["Model"].p < 0.001
    mix = solvent_blend()
    assert type(mix.design).__name__ == "MixtureDesign" and mix.design.n_runs == 10
    a = analyze_worksheet(mix, "용해도(g/L)")
    assert a.summary()["R-sq"] > 0.99
    assert {e.key for e in EXAMPLES} == {"screening", "optimization", "blend"}
    assert all(e.desc_ko and e.desc_en and e.title_en for e in EXAMPLES)


def test_home_loads_builtin_example():
    at = run("home.py")
    assert not at.exception
    btns = [b for b in at.button if b.label.endswith("예제 불러오기") and b.key and b.key.startswith("builtin_")]
    assert len(btns) == 3
    [b] = [b for b in btns if b.key == "builtin_optimization"]
    b.click().run()
    assert not at.exception
    ws = at.session_state["worksheet"]
    assert ws.design.n_runs == 17 and np.isfinite(ws.column("순도(%)")).all()


@pytest.mark.parametrize("lang, choose", [("ko", "선택하세요"), ("en", "Choose options")])
def test_multiselect_placeholder_follows_language(lang, choose):
    from tests.test_app_english import run_en
    at = (run_en if lang == "en" else run)("optimize.py", reaction_screening())
    assert not at.exception
    ph = {m.label: m.proto.placeholder for m in at.multiselect}
    assert choose in ph.values()                                            # 반응 목록
    assert any(v in ("고를 항목이 없습니다", "No options to select") for v in ph.values())   # 공변량(고를 것 없음)
