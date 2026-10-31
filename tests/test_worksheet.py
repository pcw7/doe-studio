"""워크시트 저장·불러오기, 비설계 열 정렬, 사용자 2수준 설계 정의 검증."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from doe_core.designs.common import Factor
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.general_full import GeneralFactor, create_general_full_factorial
from doe_core.designs.modify import fold_design, randomize_design, replicate_design
from doe_core.designs.plackett_burman import create_plackett_burman_design
from doe_core.io.worksheet import (
    Worksheet, define_custom_two_level, export_csv, load_mwx_worksheet, load_worksheet, save_worksheet,
)

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "minitab_samples"


def designs():
    f = [Factor("Temp", 150, 200), Factor("Mat", "X", "Y", numeric=False), Factor("Time", 10, 20)]
    yield "two_level", create_two_level_design(3, factors=f, center_points=2, seed=1)
    yield "two_level_blocked_folded", fold_design(create_two_level_design(5, 16, n_blocks=4, seed=2), "all")
    yield "pb_replicated", replicate_design(create_plackett_burman_design(7, 12, center_points=1, seed=3))
    yield "gff", create_general_full_factorial(
        [GeneralFactor("Solvent", ["MeOH", "EtOH", "IPA"]), GeneralFactor("Temp", [40, 60])], replicates=2,
        block_on_replicates=True, seed=4)


@pytest.mark.parametrize("name,d", list(designs()))
def test_save_load_round_trip(tmp_path, name, d):
    ws = Worksheet(d)
    ws.add_column("Yield", np.arange(d.n_runs, dtype=float) + 0.5)
    ws.add_column("Note", [f"r{i}" for i in range(d.n_runs)])
    p = save_worksheet(ws, tmp_path / f"{name}.json")
    back = load_worksheet(p)
    assert type(back.design) is type(d)
    pd.testing.assert_frame_equal(back.table(), ws.table(), check_dtype=False)
    assert back.design.summary() == d.summary()
    if hasattr(d, "alias"):
        assert back.design.alias.lines() == d.alias.lines()


def test_columns_follow_runs_after_modify():
    d = create_two_level_design(3, center_points=1, seed=5)
    ws = Worksheet(d)
    ws.add_column("Y", list(range(100, 100 + d.n_runs)))           # RunOrder 순 값
    y_by_std = ws.table("std").set_index("StdOrder")["Y"]
    ws2 = ws.with_design(randomize_design(d, seed=99))
    assert ws2.table("std").set_index("StdOrder")["Y"].equals(y_by_std)
    ws3 = ws.with_design(replicate_design(d))
    t = ws3.table("std")
    assert t["Y"].iloc[: d.n_runs].tolist() == y_by_std.tolist() and t["Y"].iloc[d.n_runs:].isna().all()
    # 분석용: design.coded 행 순서로 정렬된 반응
    assert ws.column("Y").tolist() == ws.table("worksheet")["Y"].tolist()
    with pytest.raises(ValueError):
        ws.add_column("A", [1, 2])                                    # 개수 불일치


def test_define_custom_recovers_fractional_design():
    f = [Factor(n) for n in ["P", "Q", "R", "S", "T", "U"]]
    d = create_two_level_design(6, 16, factors=f, center_points=3, seed=6)    # E=ABC, F=BCD
    df = d.runs.drop(columns=["StdOrder", "RunOrder"]).copy()               # 순서 열 없이
    df["Y"] = np.linspace(1, 2, len(df))
    ws = define_custom_two_level(df, ["P", "Q", "R", "S", "T", "U"], levels={n: (-1, 1) for n in "PQRSTU"})
    assert not ws.nonregular
    assert ws.design.alias.lines() == d.alias.lines()
    assert ws.design.base_runs == 16 and ws.design.replicates == 1
    assert (ws.design.runs["CenterPt"] == 0).sum() == 3
    assert ws.design.coded["StdOrder"].tolist() == list(range(1, 20))
    assert list(ws.columns.columns) == ["Y"]


def test_define_custom_text_factor_and_nonregular_pb():
    df = pd.DataFrame({"Cat": ["b", "a", "a", "b"], "T": [10, 10, 20, 20], "Y": [1, 2, 3, 4]})
    ws = define_custom_two_level(df, ["Cat", "T"])
    assert ws.design.factors[0].low == "a" and ws.design.coded["A"].tolist() == [1, -1, -1, 1]
    assert ws.design.alias.is_free and not ws.nonregular
    pb = create_plackett_burman_design(5, 12, seed=0)
    ws_pb = define_custom_two_level(pb.runs, pb.letters[:5], center_point=None)
    assert ws_pb.nonregular and ws_pb.design.alias.is_free
    with pytest.raises(ValueError):
        define_custom_two_level(pd.DataFrame({"A": ["x", "y", "z"], "B": [1, 2, 3]}), ["A", "B"])


def test_export_csv(tmp_path):
    ws = Worksheet(create_two_level_design(2, seed=0))
    ws.add_column("Y", [1, 2, 3, 4])
    p = export_csv(ws, tmp_path / "w.csv")
    back = pd.read_csv(p, encoding="utf-8-sig")
    assert list(back.columns) == ["StdOrder", "RunOrder", "CenterPt", "Blocks", "A", "B", "Y"]
    assert back["RunOrder"].tolist() == [1, 2, 3, 4] and back["Y"].tolist() == [1, 2, 3, 4]


def test_insulation_properties_mwx_as_custom_design():
    p = SAMPLES / "InsulationProperties.MWX"
    if not p.exists():
        pytest.skip("InsulationProperties.MWX 없음")
    ws = load_mwx_worksheet(p, ["Material", "InjPress", "InjTemp", "CoolTemp"])
    d = ws.design
    assert d.n_runs == 16 and d.base_runs == 16 and d.replicates == 1 and not ws.nonregular
    assert d.alias.is_free
    assert d.factors[0].low == "Formula1" and d.factors[1].low == 75.0 and d.factors[1].high == 150.0
    assert set(ws.columns.columns) == {"MeasTemp", "Insulation", "Density", "Strength", "Machine"}
    assert ws.column("Strength").notna().all()
