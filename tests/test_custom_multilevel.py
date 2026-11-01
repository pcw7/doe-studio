"""다수준 사용자 설계 정의(일반 완전요인·Taguchi) 검증.

- 만든 일반 완전요인설계의 워크시트를 다시 정의하면 같은 분석 결과, 반복 수·블록 인식.
- Taguchi 카탈로그 배열(L9)로 만든 설계를 정의하면 같은 배열·열 번호, 행을 섞으면 사용자 배열(직교), 분석 결과 같음.
- 자동 판정: 중앙점이 있는 2수준은 그대로 2수준, 3수준 완전 배치는 일반 완전요인, 직교 부분 배치는 Taguchi.
- 저장·불러오기(사용자 배열 포함).
"""
import numpy as np
import pandas as pd
import pytest

from doe_core.analysis.factorial import analyze_worksheet
from doe_core.analysis.taguchi import analyze_taguchi_worksheet
from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.general_full import GeneralFactor, create_general_full_factorial
from doe_core.designs.taguchi import create_taguchi_design
from doe_core.io.custom_designs import define_custom_general_full, define_custom_taguchi, is_orthogonal
from doe_core.io.worksheet import Worksheet, define_custom_design, design_kind_of, load_worksheet, save_worksheet


def _gff_ws():
    d = create_general_full_factorial([GeneralFactor("Temp", [60, 80, 100]), GeneralFactor("Cat", ["X", "Y"])],
                                      replicates=2, seed=3)
    ws = Worksheet(d)
    rng = np.random.default_rng(1)
    t = d.runs["Temp"].astype(float).values
    y = 50 + 0.2 * t + (d.runs["Cat"].values == "Y") * 3 + rng.normal(0, 1, len(t))
    ws.add_column("Yield", list(y))
    return ws


def test_general_full_roundtrip():
    ws = _gff_ws()
    df = ws.table("run")
    assert design_kind_of(df, ["Temp", "Cat"]) == "general_full"
    w2 = define_custom_design(df, ["Temp", "Cat"])
    d2 = w2.design
    assert type(d2).__name__ == "GeneralFullFactorialDesign" and d2.replicates == 2
    assert [f.levels for f in d2.factors] == [[60, 80, 100], ["X", "Y"]]
    a, b = analyze_worksheet(ws, "Yield", order=2), analyze_worksheet(w2, "Yield", order=2)
    assert a.anova_table().values.tolist() == b.anova_table().values.tolist()
    with pytest.raises(ValueError):
        define_custom_general_full(df.iloc[:-1], ["Temp", "Cat"])          # 조합 횟수가 다르면 거부


def _taguchi_ws(shuffle=False):
    d = create_taguchi_design("L9(3^4)", [GeneralFactor("A1", [1, 2, 3]), GeneralFactor("B1", [10, 20, 30]),
                                          GeneralFactor("C1", ["p", "q", "r"])])
    ws = Worksheet(d)
    rng = np.random.default_rng(2)
    for k in range(2):
        ws.add_column(f"R{k}", list(30 + d.coded["A"].values * 2 - d.coded["C"].values + rng.normal(0, 0.5, 9)))
    df = ws.table("run")
    if shuffle:
        df = df.sample(frac=1, random_state=4).drop(columns=["StdOrder", "RunOrder"]).reset_index(drop=True)
    return ws, df


def test_taguchi_catalog_match_and_custom_array():
    ws, df = _taguchi_ws()
    assert design_kind_of(df, ["A1", "B1", "C1"]) == "taguchi"
    w2, orth = define_custom_taguchi(df, ["A1", "B1", "C1"])
    assert orth and w2.design.array.name == "L9(3^4)" and w2.design.columns == ws.design.columns
    assert w2.design.columns_text() == ws.design.columns_text()
    a = analyze_taguchi_worksheet(ws, ["R0", "R1"], characteristics=("sn", "mean"), sn_type="larger")
    b = analyze_taguchi_worksheet(w2, ["R0", "R1"], characteristics=("sn", "mean"), sn_type="larger")
    assert a["sn"].response_table().values.tolist() == b["sn"].response_table().values.tolist()
    # 행을 섞으면 카탈로그와 같은 행 순서가 아니므로 사용자 배열(여전히 직교)
    _, df3 = _taguchi_ws(shuffle=True)
    w3, orth3 = define_custom_taguchi(df3, ["A1", "B1", "C1"])
    assert orth3 and w3.design.array.name == "L9(3^3)" and w3.design.used_name == "L9(3^3)"
    c = analyze_taguchi_worksheet(w3, ["R0", "R1"], characteristics=("sn",), sn_type="larger")
    assert c["sn"].response_table().values.tolist() == a["sn"].response_table().values.tolist()


def test_save_load_custom_taguchi(tmp_path):
    _, df3 = _taguchi_ws(shuffle=True)
    w3, _ = define_custom_taguchi(df3, ["A1", "B1", "C1"])
    p = save_worksheet(w3, tmp_path / "t.json")
    back = load_worksheet(p)
    assert back.design.array.rows == w3.design.array.rows and back.design.array.name == "L9(3^3)"
    assert back.design.coded[["A", "B", "C"]].values.tolist() == w3.design.coded[["A", "B", "C"]].values.tolist()


def test_kind_detection_keeps_two_level_with_center_points():
    d = create_two_level_design(3, factors=[Factor("T", 10, 20), Factor("P", 1, 3), Factor("S", 5, 9)],
                                center_points=3, seed=1)
    df = Worksheet(d).table("run")
    assert design_kind_of(df, ["T", "P", "S"]) == "two_level"
    assert is_orthogonal(np.array([[1, 1], [1, 2], [2, 1], [2, 2]]))
    assert not is_orthogonal(np.array([[1, 1], [1, 1], [2, 1], [2, 2]]))
    # 비직교 부분 배치는 일반 완전요인으로 시도 → 거부
    bad = pd.DataFrame({"A": [1, 2, 3, 1, 2], "B": [1, 1, 2, 2, 3]})
    assert design_kind_of(bad, ["A", "B"]) == "general_full"
    with pytest.raises(ValueError):
        define_custom_design(bad, ["A", "B"])
    # 2수준 데이터라도 Taguchi 로 정의할 수 있다(kind 지정)
    l4 = Worksheet(create_taguchi_design("L4(2^3)", n_factors=3)).table("run")
    assert design_kind_of(l4, ["A", "B", "C"]) == "two_level"
    w = define_custom_design(l4, ["A", "B", "C"], kind="taguchi")
    assert w.design.array.name == "L4(2^3)"
