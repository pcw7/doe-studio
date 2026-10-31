"""워크시트: 설계 객체 + 비설계 열(반응·공변량 등). 저장·불러오기와 사용자 설계 정의.

Minitab 은 설계 정보를 워크시트와 함께 저장해 'Analyze' 가 설계를 인식한다. 여기서도 같은 구조를 쓴다.
- 설계 열(StdOrder, RunOrder, CenterPt/PtType, Blocks, 요인열)은 설계 객체가 갖는다.
- 비설계 열은 StdOrder 를 키로 보관해 재랜덤화·반복 추가·접기 뒤에도 런을 따라간다(새 런은 빈 값).

저장 형식(JSON, `format: doe-studio-worksheet`, `version: 1`)
  design : 설계 종류와 재구성에 필요한 정보(요인, 생성자, 정의관계, 블록 생성자, 반복, 중앙점, 접기, 시드)
  coded  : 설계 코드값 워크시트({열: 값 목록})
  columns: 비설계 열({열: 값 목록}, StdOrder 순)

사용자 설계 정의(Minitab 'Define Custom 2-Level Factorial Design')
- 필수: 요인 열. 저/고 수준은 숫자면 최솟값/최댓값, 텍스트면 정렬 순서 첫/둘째 값(직접 지정 가능).
- 선택: StdOrder, RunOrder, CenterPt, Blocks 열. 없으면 만든다(StdOrder·RunOrder 는 행 순서, 중앙점은 숫자 요인이
  모두 중간값인 런, 블록은 전부 1).
- 정의관계는 모서리점에서 곱이 상수인 단어로 복원한다. 정규 부분요인(고유 런 수 × 정의관계 크기 = 2^k)일 때만
  쓰고, 아니면 비정규 설계로 표시하고 별칭 구조는 분석 단계에서 회귀로 계산한다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from ..designs.catalog import CATALOG
from ..designs.common import Factor
from ..designs.factorial import TwoLevelDesign, alias_structure
from ..designs.general_full import GeneralFactor, GeneralFullFactorialDesign
from ..designs.plackett_burman import PlackettBurmanDesign
from ..designs.words import LETTERS, word_from_str, word_to_str

FORMAT = "doe-studio-worksheet"
VERSION = 1
DESIGN_COLS = ("StdOrder", "RunOrder", "CenterPt", "PtType", "Blocks")


# ---------------------------------------------------------------- 워크시트


@dataclass
class Worksheet:
    design: TwoLevelDesign | PlackettBurmanDesign | GeneralFullFactorialDesign
    columns: pd.DataFrame = field(default_factory=pd.DataFrame)   # index = StdOrder
    nonregular: bool = False                                       # 사용자 정의 설계가 정규 부분요인이 아님

    def __post_init__(self):
        if self.columns.empty and not len(self.columns.columns):
            self.columns = pd.DataFrame(index=pd.Index(self.design.coded["StdOrder"].values, name="StdOrder"))
        self.columns.index.name = "StdOrder"

    def table(self, order: str = "run") -> pd.DataFrame:
        """설계 열 + 비설계 열. order="run" 은 RunOrder 순, "std" 는 StdOrder 순, "worksheet" 는 현재 행 순서."""
        runs = self.design.runs.reset_index(drop=True)
        extra = self.columns.reindex(runs["StdOrder"].values).reset_index(drop=True)
        out = pd.concat([runs, extra], axis=1)
        if order == "run":
            out = out.sort_values("RunOrder")
        elif order == "std":
            out = out.sort_values("StdOrder")
        return out.reset_index(drop=True)

    def add_column(self, name: str, values, order: str = "run") -> None:
        """비설계 열을 추가하거나 바꾼다. values 는 order 순서(기본 RunOrder 순)로 준다."""
        if name in self.design.runs.columns:
            raise ValueError(f"{name!r} 은 설계 열입니다.")
        keys = self.table(order)["StdOrder"].values
        values = list(values)
        if len(values) != len(keys):
            raise ValueError(f"값 개수({len(values)})가 런 수({len(keys)})와 다릅니다.")
        self.columns = self.columns.reindex(self.design.coded["StdOrder"].values)
        self.columns.index.name = "StdOrder"
        self.columns.loc[keys, name] = values

    def column(self, name: str) -> pd.Series:
        """비설계 열을 설계 코드값 워크시트(design.coded)의 행 순서로 돌려준다(분석용)."""
        return self.columns[name].reindex(self.design.coded["StdOrder"].values).reset_index(drop=True)

    def with_design(self, design) -> "Worksheet":
        """설계를 바꾼(재랜덤화·반복·접기 등) 새 워크시트. 비설계 열은 StdOrder 로 이어 붙이고 새 런은 빈 값."""
        cols = self.columns.reindex(design.coded["StdOrder"].values)
        cols.index.name = "StdOrder"
        return Worksheet(design, cols, self.nonregular)


# ---------------------------------------------------------------- 직렬화


def _plain(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, float) and np.isnan(v):
        return None
    return v


def _frame_to_dict(df: pd.DataFrame) -> dict:
    return {c: [_plain(v) for v in df[c].tolist()] for c in df.columns}


def _factor_to_dict(f) -> dict:
    if isinstance(f, GeneralFactor):
        return {"name": f.name, "levels": [_plain(v) for v in f.levels], "numeric": f.numeric}
    return {"name": f.name, "low": _plain(f.low), "high": _plain(f.high), "numeric": f.numeric}


def design_to_dict(d) -> dict:
    base = {"factors": [_factor_to_dict(f) for f in d.factors], "replicates": d.replicates,
            "n_blocks": d.n_blocks, "seed": d.seed}
    if isinstance(d, TwoLevelDesign):
        return {"type": "two_level", **base, "base_runs": d.base_runs, "generators": d.generators,
                "block_generators": list(d.block_generators),
                "defining": [word_to_str(w) for w in d.alias.defining],
                "center_points_per_block": d.center_points_per_block, "folded_on": d.folded_on}
    if isinstance(d, PlackettBurmanDesign):
        return {"type": "plackett_burman", **base, "letters": d.letters, "corner_runs": d.corner_runs,
                "center_points_per_replicate": d.center_points_per_replicate, "folded_on": d.folded_on}
    if isinstance(d, GeneralFullFactorialDesign):
        return {"type": "general_full", **base, "letters": d.letters}
    raise TypeError(f"저장할 수 없는 설계 종류: {type(d).__name__}")


def design_from_dict(meta: dict, coded: pd.DataFrame):
    kind = meta["type"]
    if kind == "general_full":
        factors = [GeneralFactor(f["name"], f["levels"], numeric=f["numeric"]) for f in meta["factors"]]
        d = GeneralFullFactorialDesign(factors, meta["letters"], pd.DataFrame(), coded, meta["replicates"],
                                       meta["n_blocks"], meta["seed"])
    else:
        factors = [Factor(f["name"], f["low"], f["high"], f["numeric"]) for f in meta["factors"]]
        if kind == "two_level":
            n = len(factors)
            alias = alias_structure(n, [word_from_str(w) for w in meta["defining"]],
                                    [word_from_str(w) for w in meta["block_generators"]])
            d = TwoLevelDesign(factors, pd.DataFrame(), coded, CATALOG.get((n, meta["base_runs"])), meta["base_runs"],
                               dict(meta["generators"]), tuple(meta["block_generators"]), alias, meta["n_blocks"],
                               meta["center_points_per_block"], meta["replicates"], meta["seed"], meta["folded_on"])
        elif kind == "plackett_burman":
            d = PlackettBurmanDesign(factors, meta["letters"], pd.DataFrame(), coded, meta["corner_runs"],
                                     meta["center_points_per_replicate"], meta["replicates"], meta["n_blocks"],
                                     meta["seed"], meta["folded_on"])
        else:
            raise ValueError(f"알 수 없는 설계 종류: {kind!r}")
    d.runs = d.rebuild_runs(coded)
    return d


def save_worksheet(ws: Worksheet, path: str | Path) -> Path:
    path = Path(path)
    doc = {
        "format": FORMAT, "version": VERSION,
        "design": design_to_dict(ws.design),
        "nonregular": ws.nonregular,
        "coded": _frame_to_dict(ws.design.coded),
        "columns": {"StdOrder": [int(v) for v in ws.columns.index], **_frame_to_dict(ws.columns)},
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def load_worksheet(path: str | Path) -> Worksheet:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("format") != FORMAT:
        raise ValueError("DOE Studio 워크시트 파일이 아닙니다.")
    if doc.get("version", 0) > VERSION:
        raise ValueError(f"더 새 버전({doc['version']})의 파일입니다. 프로그램을 업데이트하세요.")
    coded = pd.DataFrame(doc["coded"])
    design = design_from_dict(doc["design"], coded)
    cols = pd.DataFrame(doc["columns"]).set_index("StdOrder")
    return Worksheet(design, cols, doc.get("nonregular", False))


def export_csv(ws: Worksheet, path: str | Path, order: str = "run") -> Path:
    """설계 열 + 비설계 열을 CSV(UTF-8 BOM, 엑셀 호환)로 내보낸다. 설계 정보는 들어가지 않는다."""
    path = Path(path)
    ws.table(order).to_csv(path, index=False, encoding="utf-8-sig")
    return path


# ---------------------------------------------------------------- 사용자 설계 정의


def _detect_defining(coded_corners: np.ndarray) -> list[int]:
    """모서리점에서 요인 곱이 상수(+1 또는 −1)인 단어들."""
    k = coded_corners.shape[1]
    words = []
    for w in range(1, 1 << k):
        cols = [i for i in range(k) if w >> i & 1]
        prod = np.prod(coded_corners[:, cols], axis=1)
        if np.all(prod == prod[0]):
            words.append(w)
    return words


def define_custom_two_level(
    df: pd.DataFrame,
    factors: list[str],
    *,
    levels: dict[str, tuple] | None = None,
    std_order: str | None = "StdOrder",
    run_order: str | None = "RunOrder",
    center_point: str | None = "CenterPt",
    blocks: str | None = "Blocks",
) -> Worksheet:
    """기존 데이터에서 2수준 요인설계를 정의한다(Minitab 'Define Custom 2-Level Factorial Design').

    factors: 요인 열 이름(순서대로 A, B, C … 가 된다). levels: {열: (low, high)} 로 저/고 수준 지정.
    선택 열 이름이 df 에 없으면 그 정보는 새로 만든다. 나머지 열은 비설계 열이 된다.
    """
    if not 2 <= len(factors) <= 15:
        raise ValueError("2수준 요인설계의 요인 수는 2~15 이어야 합니다.")
    missing = [c for c in factors if c not in df.columns]
    if missing:
        raise ValueError(f"요인 열이 없습니다: {missing}")
    levels = levels or {}
    df = df.reset_index(drop=True)
    n = len(df)
    letters = list(LETTERS[: len(factors)])

    facs: list[Factor] = []
    coded = pd.DataFrame(index=range(n))
    for L, col in zip(letters, factors):
        x = df[col]
        numeric = pd.api.types.is_numeric_dtype(x)
        if col in levels:
            low, high = levels[col]
        elif numeric:
            low, high = float(x.min()), float(x.max())
        else:
            vals = sorted(x.dropna().astype(str).unique())
            if len(vals) != 2:
                raise ValueError(f"텍스트 요인 {col!r} 은 수준이 정확히 2개여야 합니다: {vals}")
            low, high = vals
        if numeric:
            low, high = float(low), float(high)
            if low == high:
                raise ValueError(f"요인 {col!r} 의 저/고 수준이 같습니다.")
            c = (x.astype(float) - (low + high) / 2) / ((high - low) / 2)
            c = c.round(10)
            coded[L] = c.astype(int) if np.all(np.isin(c, (-1, 0, 1))) else c
        else:
            xs = x.astype(str)
            bad = sorted(set(xs) - {str(low), str(high)})
            if bad:
                raise ValueError(f"텍스트 요인 {col!r} 에 저/고 수준이 아닌 값이 있습니다: {bad}")
            coded[L] = np.where(xs == str(low), -1, 1)
        facs.append(Factor(col, low, high, numeric))

    numeric_letters = [L for L, f in zip(letters, facs) if f.is_numeric]
    if center_point and center_point in df.columns:
        cpt = df[center_point].astype(int).values
    else:
        cpt = np.where((coded[numeric_letters] == 0).all(axis=1), 0, 1) if numeric_letters else np.ones(n, int)
    coded.insert(0, "CenterPt", cpt)
    coded.insert(1, "Blocks", df[blocks].astype(int).values if blocks and blocks in df.columns else 1)
    coded.insert(0, "RunOrder", df[run_order].astype(int).values if run_order and run_order in df.columns else np.arange(1, n + 1))
    coded.insert(0, "StdOrder", df[std_order].astype(int).values if std_order and std_order in df.columns else np.arange(1, n + 1))
    if coded["StdOrder"].duplicated().any():
        raise ValueError("StdOrder 값이 중복됩니다.")
    coded = coded[["StdOrder", "RunOrder", "CenterPt", "Blocks", *letters]]

    corners = coded[coded["CenterPt"] == 1][letters].values
    if not np.all(np.isin(corners, (-1, 1))):
        raise ValueError("모서리점의 요인 값이 저/고 수준이 아닙니다.")
    unique_corners = {tuple(r) for r in corners.tolist()}
    defining = _detect_defining(corners)
    k = len(factors)
    regular = len(unique_corners) * (len(defining) + 1) == 2 ** k
    base_runs = len(unique_corners)
    replicates = max(1, round(len(corners) / base_runs))
    n_blocks = int(coded["Blocks"].nunique())
    n_cp = int((coded["CenterPt"] == 0).sum())
    alias = alias_structure(k, defining if regular else [], [])
    design = TwoLevelDesign(
        factors=facs, runs=pd.DataFrame(), coded=coded, entry=CATALOG.get((k, base_runs)), base_runs=base_runs,
        generators={}, block_generators=(), alias=alias, n_blocks=n_blocks,
        center_points_per_block=n_cp // n_blocks, replicates=replicates, seed=None,
    )
    design.runs = design.rebuild_runs(coded)

    used = set(factors) | {c for c in (std_order, run_order, center_point, blocks) if c}
    extra = df[[c for c in df.columns if c not in used]].copy()
    extra.index = pd.Index(coded["StdOrder"].values, name="StdOrder")
    return Worksheet(design, extra, nonregular=not regular)


def load_mwx_worksheet(path: str | Path, factors: list[str], **kwargs) -> Worksheet:
    """Minitab .MWX 를 읽어 2수준 사용자 설계로 정의한 워크시트를 만든다."""
    from .mwx import read_mwx
    return define_custom_two_level(read_mwx(path), factors, **kwargs)
