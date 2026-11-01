"""Taguchi 설계 생성·분석 검증.

정답 출처(Minitab 문서)
- 'Catalogue of Taguchi designs': 직교배열 21종(문서 표의 옮겨 적기 오류 4건을 직교성으로 고침).
- 'Example of creating a static design': L8, 4요인 → 'L8(2^4)', 'Columns of L8(2^7) array: 1 2 4 7', 설계표.
- 'Example of analyzing a static design'(GolfBall, Larger is better, 항 A B C D AB): 원자료(GolfBall.MWX)가 없어
  문서 분산분석표의 SS·MS 와 S 로부터 같은 표가 나오는 런별 S/N·평균 값을 거꾸로 만든 뒤,
  계수표·모형 요약·분산분석표·반응표를 글자 단위로 비교한다(표 계산과 표시 형식 검증).
"""
from collections import Counter
from itertools import combinations

import numpy as np
import pytest

from doe_core.analysis.taguchi import analyze_characteristic, analyze_taguchi, response_table, sn_ratio
from doe_core.designs.general_full import GeneralFactor
from doe_core.designs.taguchi import ARRAYS, available_taguchi, create_taguchi_design, default_columns
from doe_core.io.worksheet import Worksheet, load_worksheet, save_worksheet
from tests.helpers import load_fixture


def fx(name):
    return load_fixture(f"taguchi__{name}")


def full(t):
    return [t["header"], *t["rows"]]


def test_catalog_arrays_orthogonal_and_match_document():
    doc = load_fixture("topic__taguchi-designs__catalogue-of-taguchi-designs")
    assert len(ARRAYS) == 21
    diffs = 0
    tabs, i = doc["tables"], 0
    for arr in ARRAYS:
        M = arr.matrix
        assert M.shape == (arr.runs, len(arr.levels))
        for a, b in combinations(range(M.shape[1]), 2):
            c = Counter(zip(M[:, a], M[:, b]))
            assert len(c) == arr.levels[a] * arr.levels[b] and len(set(c.values())) == 1, (arr.name, a, b)
        rows = [r[1:] for r in tabs[i]["rows"]]
        i += 1
        while i < len(tabs) and len(tabs[i]["rows"]) == arr.runs and tabs[i]["header"][1] != "1":
            rows = [x + r[1:] for x, r in zip(rows, tabs[i]["rows"])]
            i += 1
        diffs += int((np.array(rows, dtype=int) != M).sum())
    assert diffs == 13                                                        # 오기 수정 칸 수(4개 배열)


def test_example_create_static_l8():
    f = fx("create-taguchi-design__example-of-creating-a-static-design")
    d = create_taguchi_design("L8(2^7)", n_factors=4)
    assert d.summary_table().values.tolist() == full(f["tables"][0])
    assert d.columns_text() == f["notes"][-1]
    t = f["tables"][1]
    assert [str(f.name) for f in d.factors] == t["rows"][0]
    assert d.design_table().astype(str).values.tolist() == t["rows"][1:]


def test_available_designs_and_default_columns():
    assert [a.name for a in available_taguchi("2-level", {2: 4})] == ["L8(2^7)", "L12(2^11)", "L16(2^15)", "L32(2^31)"]
    assert [a.name for a in available_taguchi("3-level", {3: 5})] == ["L27(3^13)"]
    assert [a.name for a in available_taguchi("mixed 2-3", {2: 1, 3: 7})][0] == "L18(2^1 3^7)"
    l16 = next(a for a in ARRAYS if a.name == "L16(2^15)")
    assert default_columns(l16, {2: 5}) == [1, 2, 4, 8, 15]                  # E = ABCD → 15열(해상도 V)
    l27 = next(a for a in ARRAYS if a.name == "L27(3^13)")
    assert default_columns(l27, {3: 4}) == [1, 2, 5, 9]
    mixed = create_taguchi_design("L18(2^1 3^7)", [GeneralFactor("Temp", [100, 120, 140]),
                                                   GeneralFactor("Cat", ["x", "y"]), GeneralFactor("P", [1, 2, 3])])
    assert mixed.used_name == "L18(2^1 3^2)" and [f.name for f in mixed.factors] == ["Cat", "Temp", "P"]
    assert set(mixed.runs["Cat"]) == {"x", "y"}
    with pytest.raises(ValueError):
        create_taguchi_design("L8(2^7)", [GeneralFactor("A", [1, 2, 3])], columns=[1])
    with pytest.raises(ValueError):
        available_taguchi("4-level", {2: 2})


# ---------------------------------------------------------------- 분석: 문서 표 재현용 런별 특성값


def golf_design():
    facs = [GeneralFactor("Material", ["Liquid", "Solid"]), GeneralFactor("Diameter", [118, 106]),
            GeneralFactor("Dimples", [392, 422]), GeneralFactor("Thickness", [0.03, 0.06])]
    return create_taguchi_design("L8(2^7)", facs)


def reconstruct(d, c0, coefs, sse):
    """효과 코딩 x(수준 1 = +1, 2 = −1)로 c0 + Σ계수·x + 잔차(AC 방향)."""
    x = {L: np.where(d.coded[L].values == 1, 1.0, -1.0) for L in d.letters}
    y = c0 + coefs["A"] * x["A"] + coefs["B"] * x["B"] + coefs["C"] * x["C"] + coefs["D"] * x["D"] \
        + coefs["AB"] * x["A"] * x["B"] + np.sqrt(sse / 8) * x["A"] * x["C"]
    return y


def test_example_analyze_static_golfball():
    f = fx("analyze-taguchi-design__example-of-analyzing-a-static-design")
    d = golf_design()
    t = f["tables"]
    # S/N: SS(소수 3자리 + 0.00016)와 잔차 MS 1.6365016 → 문서 표가 그대로 나오는 값
    ss = {"A": 94.42716, "B": 125.91716, "C": 71.13316, "D": 96.82816, "AB": 21.50416}
    sign = {"A": 1, "B": 1, "C": 1, "D": -1, "AB": 1}
    sn = reconstruct(d, 38.1812, {k: sign[k] * np.sqrt(v / 8) for k, v in ss.items()}, 2 * 1.6365016)
    a = analyze_characteristic(d, sn, "sn", terms=["A", "B", "C", "D", "AB"], sn_type="larger")
    assert a.coefficients_title() == "Estimated Model Coefficients for SN ratios"
    assert a.coefficients_table().values.tolist() == t[0]["rows"] and list(a.coefficients_table().columns) == t[0]["header"]
    assert a.summary_table().values.tolist() == t[1]["rows"]
    assert a.anova_table().values.tolist() == t[2]["rows"] and list(a.anova_table().columns) == t[2]["header"]
    assert a.response_table().values.tolist() == t[6]["rows"] and a.response_title() == \
        "Response Table for Signal to Noise Ratios"
    # 평균: MS(소수 1~2자리)와 S = 22.9035
    ms = {"A": 10870.8, "B": 21053.52, "C": 4324.52, "D": 4172.44, "AB": 7994.8}
    mean = reconstruct(d, 110.40, {k: sign[k] * np.sqrt(v / 8) for k, v in ms.items()}, 2 * 22.9035 ** 2)
    m = analyze_characteristic(d, mean, "mean", terms=["A", "B", "C", "D", "AB"])
    assert m.coefficients_table().values.tolist() == t[3]["rows"]
    assert m.summary_table().values.tolist() == t[4]["rows"]
    assert m.anova_table().values.tolist() == t[5]["rows"]
    assert m.response_table().values.tolist() == t[7]["rows"]


def test_sn_formulas_and_raw_analysis():
    Y = np.array([[10.0, 12.0], [8.0, 9.0], [20.0, 18.0], [5.0, 7.0]])
    np.testing.assert_allclose(sn_ratio(Y, "larger"), -10 * np.log10(np.mean(1 / Y ** 2, axis=1)))
    np.testing.assert_allclose(sn_ratio(Y, "smaller"), -10 * np.log10(np.mean(Y ** 2, axis=1)))
    s2 = Y.var(axis=1, ddof=1)
    np.testing.assert_allclose(sn_ratio(Y, "nominal"), 10 * np.log10(Y.mean(axis=1) ** 2 / s2))
    np.testing.assert_allclose(sn_ratio(Y, "nominal_s"), -10 * np.log10(s2))
    assert np.isnan(sn_ratio([[1.0, 1.0]], "nominal")[0])                  # s = 0
    with pytest.raises(ValueError):
        sn_ratio(Y, "other")
    d = create_taguchi_design("L9(3^4)", n_factors=3)
    rng = np.random.default_rng(0)
    Yd = 50 + 3 * d.coded[["A"]].values + rng.normal(size=(9, 3))
    res = analyze_taguchi(d, Yd, characteristics=("sn", "mean", "std", "lnstd"), sn_type="nominal")
    assert set(res) == {"sn", "mean", "std", "lnstd"}
    m = res["mean"]
    # 효과 코딩: 계수 = 수준 평균 − 전체 평균
    lv1 = Yd.mean(axis=1)[d.coded["A"].values == 1].mean()
    np.testing.assert_allclose(m.beta[1], lv1 - Yd.mean())
    assert m.coefficients_table()["Term"].tolist()[:3] == ["Constant", "A 1", "A 2"]
    rt = response_table(d, Yd.mean(axis=1))
    assert rt["Level"].tolist() == ["1", "2", "3", "Delta", "Rank"] and rt.loc[4, "A"] == "1"


def test_taguchi_interaction_and_save(tmp_path):
    d = golf_design()
    rng = np.random.default_rng(1)
    y = rng.normal(size=8)
    with pytest.raises(ValueError):                                         # L8 의 3열은 AB 와 같은 열
        analyze_characteristic(d, y, "mean", terms=["A", "B", "C", "D", "AB", "AC", "BC", "AD"])
    a = analyze_characteristic(d, y, "mean", terms=["Material", "Diameter", "Material*Diameter"])
    assert a.coefficients_table()["Term"].tolist()[-1] == "Material*Diameter Liquid 118"
    ws = Worksheet(d)
    ws.add_column("Driver", rng.normal(200, 5, 8), order="worksheet")
    back = load_worksheet(save_worksheet(ws, tmp_path / "tg.json"))
    assert back.design.columns == [1, 2, 4, 7] and back.design.design_table().equals(d.design_table())
