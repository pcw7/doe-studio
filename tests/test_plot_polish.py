"""그래프 다듬기 검증 — 실사용 점검 ⑥.

- Pareto: 기준선 값(그림 위 글자)과 범례가 겹치지 않게 범례를 올리고, 오른쪽에 요인 문자 → 이름 표.
- 주효과도: 범례(모서리점·중앙점)가 첫 소제목과 겹치지 않게 올림.
- 영어 전환: '온도(°C)' 처럼 단위를 붙여 쓴 요인 이름은 그대로(전에는 괄호 속 '°C' 만 남았다),
  '한글 (English)' 라벨은 그대로 영어로, 한글 반응 이름이 든 영어 제목은 통째로(전에는 'Fitted Means' 만 남았다).
"""
import numpy as np
import pytest

from doe_core.analysis.effects import effects
from doe_core.analysis.factorial import analyze_worksheet
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.io.worksheet import Worksheet
from doe_core.plots.effects_plots import pareto_chart
from doe_core.plots.factorial_plots import interaction_plot, main_effects_plot
from doe_core.plots.lang import english_of, to_english

NAMES = ["온도(°C)", "시간(h)", "촉매(wt%)"]


@pytest.fixture(scope="module")
def analysis():
    fac = [Factor(NAMES[0], 60, 80), Factor(NAMES[1], 1, 3), Factor(NAMES[2], 0.5, 1.5)]
    d = create_two_level_design(3, 8, factors=fac, center_points=3, seed=4)
    c = d.coded.sort_values("StdOrder")
    rng = np.random.default_rng(0)
    y = 70 + 6 * c["A"] + 3 * c["B"] + 4 * c["C"] - 2.5 * c["A"] * c["B"] + rng.normal(0, 0.4, len(c))
    ws = Worksheet(d)
    ws.add_column("수율", y.values, order="std")
    return analyze_worksheet(ws, "수율", order=2, include_center=True)   # Ct Pt → 주효과도에 중앙점·범례


def test_english_of_keeps_unit_names():
    assert english_of("온도(°C)") is None
    assert english_of("촉매(wt%)") is None
    assert english_of("표준화 효과 (Standardized Effect)") == "Standardized Effect"
    assert english_of("**요인 (Factors)**") == "**Factors**"


def test_pareto_legend_and_factor_names(analysis):
    fig = pareto_chart(effects(analysis))
    assert fig.layout.legend.y > 1.02                                  # 기준선 값 위로 올림
    keep = [a for a in fig.layout.annotations if a.name == "keep"]
    assert len(keep) == 1 and all(n in keep[0].text for n in NAMES) and keep[0].text.startswith("A")
    en = to_english(fig)
    keep_en = [a for a in en.layout.annotations if a.name == "keep"]
    assert all(n in keep_en[0].text for n in NAMES)                   # 이름은 영어 전환에도 그대로
    assert any(a.text == "Factor" for a in en.layout.annotations)
    # 이름이 문자와 같으면(이름을 정하지 않은 설계) 표를 넣지 않는다
    d = create_two_level_design(3, 8, seed=1)
    ws = Worksheet(d)
    ws.add_column("Y", np.arange(8.0) ** 1.5, order="std")
    plain = pareto_chart(effects(analyze_worksheet(ws, "Y", order=1)))
    assert not [a for a in plain.layout.annotations if a.name == "keep"]


def test_main_effects_legend_and_english_titles(analysis):
    fig = main_effects_plot(analysis)
    titles = [a.text for a in fig.layout.annotations]
    assert titles == NAMES
    assert fig.layout.showlegend and fig.layout.legend.y > 1.02
    en = to_english(fig)
    assert [a.text for a in en.layout.annotations] == NAMES             # 전에는 ['°C', 'h', 'wt%']
    assert en.layout.title.text == "Main Effects Plot for 수율 (Fitted Means)"   # 전에는 'Fitted Means'
    ix = to_english(interaction_plot(analysis, "A", "B"))
    assert ix.layout.xaxis.title.text == NAMES[0]
