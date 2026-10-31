"""픽스처가 제대로 추출되었는지 확인하는 기본 테스트."""
from conftest import FIXTURE_DIR, load_fixture, table


def test_fixture_dir_has_files():
    files = list(FIXTURE_DIR.glob("*.json"))
    assert len(files) >= 15, f"픽스처가 너무 적음: {len(files)}"


def test_analyze_factorial_example_anova_total():
    fx = load_fixture("analyze-factorial-design__example")
    anova = table(fx, "Analysis of Variance")
    assert anova["header"] == ["Source", "DF", "Adj SS", "Adj MS", "F-Value", "P-Value"]
    total = [r for r in anova["rows"] if r[0] == "Total"][0]
    assert total[1] == "15" and total[2] == "460.478"


def test_analyze_rs_example_model_summary():
    fx = load_fixture("analyze-response-surface-design__example")
    ms = table(fx, "Model Summary")
    assert ms["header"] == ["S", "R-sq", "R-sq(adj)", "R-sq(pred)"]
    assert ms["rows"][0] == ["4.40228", "78.58%", "59.84%", "0.00%"]
