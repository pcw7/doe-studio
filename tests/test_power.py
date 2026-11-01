"""검정력·표본 크기 검증 — Minitab 문서 예제 숫자(데이터 파일 없이 입력값만으로 재현).

- 2수준 예제: 5요인 8꼭짓점, 블록당 중앙점 3, σ 4.5, 효과 5, 생략 항 2, 반복 1~4 → 0.229 0.533 0.735 0.858(6자리 0.229128…)
- 해석 페이지 표(입력값은 표 숫자로 역추정): 4요인 16꼭짓점 σ 1.8 생략 4(중앙점 0·6, 블록 4), 5요인 32꼭짓점 σ 1.7 생략 16,
  15요인 32꼭짓점 중앙점 4 σ 0.01017(효과 풀기)
- PB 예제: 10요인 12런, 중앙점 3, σ 4.5, 효과 5 → 0.272032 0.720550 0.894838 0.963485
- 일반 완전요인 예제: 3×3, 최대 차이 0.4, σ 0.15, 2차, 블록 포함, 목표 0.9 → 반복 2, 18런, 0.930521
"""
import pytest

from doe_core.power import gff_term_df, power_curve_data, power_gff, power_pb, power_two_level


def rows(df):
    return df.astype(str).values.tolist()


def test_two_level_example():
    r = power_two_level(factors=5, corner_points=8, sigma=4.5, reps=[1, 2, 3, 4], effects=[5], center_points=[3],
                        omit=2)
    assert list(r.table.columns) == ["Center Points", "Effect", "Reps", "Total Runs", "Power"]
    got = [(row[2], row[3], round(float(row[4]), 3)) for row in rows(r.table)]
    assert got == [("1", "11", 0.229), ("2", "19", 0.533), ("3", "27", 0.735), ("4", "35", 0.858)]
    assert r.header[:3] == ["2-Level Factorial Design", "α = 0.05  Assumed standard deviation = 4.5",
                            "Factors: 5  Base Design: 5, 8"]


def test_two_level_interpret_page_tables():
    r = power_two_level(factors=4, corner_points=16, sigma=1.8, reps=[1, 2], effects=[2.5], center_points=[0, 6],
                        omit=4)
    assert rows(r.table) == [["0", "2.5", "1", "16", "0.557255"], ["0", "2.5", "2", "32", "0.961939"],
                             ["6", "2.5", "1", "22", "0.696490"], ["6", "2.5", "2", "38", "0.965121"]]
    b = power_two_level(factors=4, corner_points=16, sigma=1.8, reps=[1, 2], effects=[2.5], center_points=[4],
                        blocks=4, omit=4)
    assert list(b.table.columns)[0] == "Center Points Per Block"
    assert rows(b.table) == [["4", "2.5", "1", "32", "0.741569"], ["4", "2.5", "2", "48", "0.967699"]]
    s = power_two_level(factors=5, corner_points=32, sigma=1.7, effects=[2.0, 0.9], powers=[0.8, 0.9], omit=16)
    assert list(s.table.columns) == ["Center Points", "Effect", "Reps", "Total Runs", "Target Power", "Actual Power"]
    assert rows(s.table) == [["0", "2", "1", "32", "0.8", "0.877445"], ["0", "2", "2", "64", "0.9", "0.995974"],
                             ["0", "0.9", "4", "128", "0.8", "0.843529"], ["0", "0.9", "5", "160", "0.9", "0.914018"]]
    p = power_two_level(factors=5, corner_points=32, sigma=1.7, reps=[5, 2], effects=[1.5, 0.9], omit=16)
    assert [row[4] for row in rows(p.table)] == ["0.999830", "0.932932", "0.914018", "0.545887"]
    e = power_two_level(factors=15, corner_points=32, sigma=0.01017, reps=[1, 2], powers=[0.8, 0.9], center_points=[4])
    assert list(e.table.columns) == ["Center Points", "Reps", "Total Runs", "Power", "Effect"]
    assert rows(e.table) == [["4", "1", "36", "0.8", "0.0153027"], ["4", "1", "36", "0.9", "0.0180278"],
                             ["4", "2", "68", "0.8", "0.0073261"], ["4", "2", "68", "0.9", "0.0084775"]]


def test_plackett_burman_example():
    r = power_pb(factors=10, runs=12, sigma=4.5, reps=[1, 2, 3, 4], effects=[5], center_points=[3])
    assert rows(r.table) == [["3", "5", "1", "15", "0.272032"], ["3", "5", "2", "27", "0.720550"],
                             ["3", "5", "3", "39", "0.894838"], ["3", "5", "4", "51", "0.963485"]]
    assert r.header == ["Plackett-Burman Design", "α = 0.05  Assumed standard deviation = 4.5", "Factors: 10  Design: 12",
                        "Center pts (total): 3", "Including a term for center points in model."]


def test_general_full_factorial_example():
    assert gff_term_df([3, 3], 2) == 8 and gff_term_df([2, 3, 4], 1) == 6 and gff_term_df([2, 3, 4], 3) == 23
    r = power_gff(levels=[3, 3], sigma=0.15, deltas=[0.4], powers=[0.9], order=2, blocks=True)
    assert list(r.table.columns) == ["Maximum Difference", "Reps", "Total Runs", "Target Power", "Actual Power"]
    assert rows(r.table) == [["0.4", "2", "18", "0.9", "0.930521"]]
    assert r.header == ["General Full Factorial Design", "α = 0.05  Assumed standard deviation = 0.15",
                        "Factors: 2  Number of levels: 3, 3", "Include terms in the model up through order: 2",
                        "Include blocks in model."]


def test_solving_consistency_and_curves():
    e = power_two_level(factors=4, corner_points=16, sigma=1.8, reps=[2], powers=[0.8], omit=4)
    eff = float(e.table["Effect"].iloc[0])
    p = power_two_level(factors=4, corner_points=16, sigma=1.8, reps=[2], effects=[eff], omit=4)
    assert float(p.table["Power"].iloc[0]) == pytest.approx(0.8, abs=2e-6)
    curves = power_curve_data(p)
    name, xs, ys = curves[0]
    assert ys[0] == pytest.approx(0.05) and all(b >= a - 1e-12 for a, b in zip(ys, ys[1:]))
    with pytest.raises(ValueError):
        power_two_level(factors=4, corner_points=16, sigma=1.8, reps=[1], effects=[2], powers=[0.8])
    with pytest.raises(ValueError):
        power_two_level(factors=4, corner_points=12, sigma=1.8, reps=[1], effects=[2])
    # 오차 DF 가 없으면 '*'
    z = power_two_level(factors=4, corner_points=16, sigma=1.8, reps=[1], effects=[2])
    assert z.table["Power"].iloc[0] == "*"
