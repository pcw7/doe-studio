"""일반 완전요인설계 생성 검증.

정답 출처: Minitab 문서 예제 "Create General Full Factorial Design"(3요인 × 3수준 텍스트 요인, 27런).
설계표는 Minitab 난수로 랜덤화되었으므로 행 집합과 요약표를 비교한다.
"""
from collections import Counter

import pytest

from tests.helpers import load_fixture, table
from doe_core.designs.general_full import GeneralFactor, create_general_full_factorial

EXAMPLE_FACTORS = [
    GeneralFactor("Website", ["News", "Social Media", "Sports"]),
    GeneralFactor("Product", ["Car", "Video Game", "Medicine"]),
    GeneralFactor("Message style", ["You know you should.", "Just the facts.", "That is awesome!"]),
]


def test_example_3_text_factors_3_levels():
    fx = load_fixture("create-general-full-factorial__example")
    d = create_general_full_factorial(EXAMPLE_FACTORS, seed=11)

    summ = table(fx, "Design Summary")
    cells = [summ["header"], *summ["rows"]]
    expected = {}
    for r in cells:
        for k, v in zip(r[0::2], r[1::2]):
            if k:
                expected[k] = v
    got = {f"{k}:": str(v) for k, v in d.summary().items()}
    for k, v in expected.items():
        assert got[k] == v, (k, got[k], v)
    assert d.summary()["Number of levels"] == "3, 3, 3"
    assert "Number of levels: 3, 3, 3" in d.summary_text()

    dt = table(fx, "Design Table")
    assert dt["header"] == ["Run", "Blk", "A", "B", "C"]
    want = Counter(tuple(int(x) for x in r[2:]) for r in dt["rows"])
    mine = d.design_table()
    assert list(mine.columns) == dt["header"]
    have = Counter(tuple(r) for r in mine[["A", "B", "C"]].values.tolist())
    assert have == want and len(have) == 27
    assert mine["Run"].tolist() == list(range(1, 28))


def test_worksheet_uses_level_labels_and_ptype():
    d = create_general_full_factorial(EXAMPLE_FACTORS, randomize=False)
    assert list(d.runs.columns) == ["StdOrder", "RunOrder", "PtType", "Blocks", "Website", "Product", "Message style"]
    assert (d.runs["PtType"] == 1).all() and (d.runs["Blocks"] == 1).all()
    # 표준 순서: 첫 요인이 가장 빨리 바뀐다
    assert d.runs["Website"].tolist()[:4] == ["News", "Social Media", "Sports", "News"]
    assert d.runs["Product"].tolist()[:4] == ["Car", "Car", "Car", "Video Game"]
    assert d.runs["Message style"].iloc[-1] == "That is awesome!"


def test_mixed_levels_numeric_replicates_and_blocks():
    f = [GeneralFactor("Temp", [150, 175, 200]), GeneralFactor("Cat", ["X", "Y"]), GeneralFactor("Speed", n_levels=4)]
    d = create_general_full_factorial(f, replicates=2, block_on_replicates=True, seed=3)
    s = d.summary()
    assert s["Base runs"] == 24 and s["Total runs"] == 48 and s["Total blocks"] == 2
    assert s["Number of levels"] == "3, 2, 4"
    assert d.runs["Temp"].dtype == float and set(d.runs["Temp"]) == {150.0, 175.0, 200.0}
    assert set(d.runs["Speed"]) == {1.0, 2.0, 3.0, 4.0}
    assert d.coded.groupby("Blocks").size().tolist() == [24, 24]
    assert d.coded["Blocks"].is_monotonic_increasing  # 블록 안에서만 랜덤


def test_levels_shortcut_and_validation():
    d = create_general_full_factorial([2, 3], randomize=False)
    assert d.n_runs == 6 and [f.name for f in d.factors] == ["A", "B"]
    with pytest.raises(ValueError):
        create_general_full_factorial([3])                     # 요인 1개
    with pytest.raises(ValueError):
        GeneralFactor("A", ["x", "x"])                          # 중복 수준
    with pytest.raises(ValueError):
        GeneralFactor("A", n_levels=1)                          # 수준 1개
    with pytest.raises(ValueError):
        GeneralFactor("A", ["a", 2], numeric=True)              # 숫자 요인에 텍스트 수준
