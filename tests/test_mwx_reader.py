"""MWX 읽기 검증. 샘플 파일은 저장소에 없으므로(research/fetch_samples.py 로 내려받음) 없으면 건너뛴다.

교차 검증: 각 데이터셋의 행 수는 문서 예제 ANOVA 의 Total DF + 1 이어야 한다.
"""
from pathlib import Path

import numpy as np
import pytest

from tests.helpers import load_fixture, table
from doe_core.io.mwx import mwx_doe_flags, read_mwx, read_mwx_sheets

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "minitab_samples"


def sample(name: str) -> Path:
    p = SAMPLES / name
    if not p.exists():
        pytest.skip(f"{name} 없음 — python research/fetch_samples.py 로 내려받으세요")
    return p


def test_insulation_properties_columns_and_types():
    df = read_mwx(sample("InsulationProperties.MWX"))
    assert list(df.columns) == ["StdOrder", "RunOrder", "CenterPt", "Blocks", "Material", "InjPress", "InjTemp",
                                "CoolTemp", "MeasTemp", "Insulation", "Density", "Strength", "Machine"]
    assert len(df) == 16
    assert set(df["Material"]) == {"Formula1", "Formula2"}
    assert set(df["InjPress"]) == {75.0, 150.0} and set(df["InjTemp"]) == {85.0, 100.0} and set(df["CoolTemp"]) == {25.0, 45.0}
    assert df["Strength"].dtype == float and not df["Strength"].isna().any()
    # 2수준 완전요인설계: 요인 열은 직교(코드화 후 합 0)
    coded = np.where(df["InjPress"] == 150, 1, -1)
    assert coded.sum() == 0
    flags = mwx_doe_flags(sample("InsulationProperties.MWX"))
    assert "HasDesign" in flags


@pytest.mark.parametrize("file,fixture_fragment,anova_heading", [
    ("InsulationProperties.MWX", "analyze-factorial-design__example", "Analysis of Variance"),
    ("SealStrength.MWX", "analyze-response-surface-design__example", "Analysis of Variance"),
    ("FondueRecipe.MWX", "analyze-mixture-design__example", "Analysis of Variance"),
    ("ultrasonic_cleaner.MWX", "analyze-screening-design__example", "Analysis of Variance"),
])
def test_row_count_matches_anova_total_df(file, fixture_fragment, anova_heading):
    df = read_mwx(sample(file))
    anova = table(load_fixture(fixture_fragment), anova_heading)
    total = [r for r in anova["rows"] if r[0] == "Total"][0]
    assert len(df) == int(total[1]) + 1, (file, len(df), total)


def test_read_all_sheets_returns_named_frames():
    sheets = read_mwx_sheets(sample("ThermalEnergyTest.MWX"))
    assert len(sheets) >= 1
    df = next(iter(sheets.values()))
    assert {"East", "South", "North", "Insolation"} <= set(df.columns)
