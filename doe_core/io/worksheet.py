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
from ..designs.common import Factor, factor_letters
from ..designs.factorial import TwoLevelDesign, alias_structure
from ..designs.general_full import GeneralFactor, GeneralFullFactorialDesign
from ..designs.plackett_burman import PlackettBurmanDesign
from ..designs.response_surface import ResponseSurfaceDesign
from ..designs.mixture import Component, LinearConstraint, MixtureDesign
from ..designs.definitive_screening import DefinitiveScreeningDesign
from ..designs.split_plot import SplitPlotDesign
from ..designs.taguchi import TaguchiDesign, array_by_name
from ..designs.words import LETTERS, word_from_str, word_to_str

FORMAT = "doe-studio-worksheet"
VERSION = 1
DESIGN_COLS = ("StdOrder", "RunOrder", "CenterPt", "PtType", "Blocks")


# ---------------------------------------------------------------- 워크시트


@dataclass
class Worksheet:
    design: (TwoLevelDesign | PlackettBurmanDesign | GeneralFullFactorialDesign | ResponseSurfaceDesign | MixtureDesign
             | DefinitiveScreeningDesign | SplitPlotDesign | TaguchiDesign)
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
    if isinstance(d, MixtureDesign):
        return {"type": "mixture", "kind": d.kind, "letters": d.letters, "replicates": d.replicates,
                "n_blocks": d.n_blocks, "seed": d.seed, "degree": d.degree, "total": d.total,
                "constrained": d.constrained, "boundaries": d.boundaries,
                "components": [{"name": c.name, "lower": c.lower, "upper": c.upper} for c in d.components],
                "process": [_factor_to_dict(f) for f in d.process],
                "constraints": [{"coefs": lc.coefs, "lower": lc.lower, "upper": lc.upper} for lc in d.constraints]}
    if isinstance(d, TaguchiDesign):
        out = {"type": "taguchi", "array": d.array.name, "columns": list(d.columns),
               "factors": [_factor_to_dict(f) for f in d.factors]}
        try:
            same = array_by_name(d.array.name).rows == d.array.rows
        except (KeyError, ValueError):
            same = False
        if not same:                                 # 사용자 배열(데이터로 만든 배열)
            out["custom_array"] = {"runs": d.array.runs, "levels": list(d.array.levels), "rows": d.array.rows}
        return out
    if isinstance(d, SplitPlotDesign):
        return {"type": "split_plot", "factors": [_factor_to_dict(f) for f in d.factors], "n_htc": d.n_htc,
                "base_runs": d.base_runs, "generators": d.generators,
                "defining": [word_to_str(w) for w in d.alias.defining], "n_blocks": d.n_blocks,
                "wp_replicates": d.wp_replicates, "subplot_replicates": d.subplot_replicates, "seed": d.seed}
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
    if isinstance(d, DefinitiveScreeningDesign):
        return {"type": "definitive_screening", **base, "letters": d.letters, "order": d.order}
    if isinstance(d, ResponseSurfaceDesign):
        return {"type": "response_surface", **base, "kind": d.kind, "letters": d.letters, "alpha": d.alpha,
                "base_runs": d.base_runs, "base_blocks": d.base_blocks, "fraction": d.fraction,
                "generators": d.generators, "point_col": d.point_col}
    raise TypeError(f"저장할 수 없는 설계 종류: {type(d).__name__}")


def design_from_dict(meta: dict, coded: pd.DataFrame):
    kind = meta["type"]
    if kind == "mixture":
        d = MixtureDesign(meta["kind"], [Component(**c) for c in meta["components"]], meta["letters"],
                          [Factor(f["name"], f["low"], f["high"], f["numeric"]) for f in meta["process"]],
                          pd.DataFrame(), coded, meta["degree"], meta["total"],
                          [LinearConstraint(**lc) for lc in meta["constraints"]], meta["constrained"],
                          meta["replicates"], meta["boundaries"], meta["n_blocks"], meta["seed"])
        d.runs = d.rebuild_runs(coded)
        return d
    if kind == "taguchi":
        factors = [GeneralFactor(f["name"], f["levels"], numeric=f["numeric"]) for f in meta["factors"]]
        if "custom_array" in meta:
            from ..designs.taguchi import TaguchiArray
            ca = meta["custom_array"]
            arr = TaguchiArray(int(ca["runs"]), tuple(ca["levels"]), ca["rows"], meta["array"])
        else:
            arr = array_by_name(meta["array"])
        d = TaguchiDesign(arr, list(meta["columns"]), factors, pd.DataFrame(), coded)
        d.runs = d.rebuild_runs(coded)
        return d
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
        elif kind == "response_surface":
            d = ResponseSurfaceDesign(meta["kind"], factors, meta["letters"], pd.DataFrame(), coded, meta["alpha"],
                                      meta["base_runs"], meta["base_blocks"], meta["replicates"], meta["n_blocks"],
                                      meta["fraction"], dict(meta["generators"]), meta["seed"], meta["point_col"])
        elif kind == "split_plot":
            alias = alias_structure(len(factors), [word_from_str(w) for w in meta["defining"]], [])
            d = SplitPlotDesign(factors, pd.DataFrame(), coded, meta["n_htc"], meta["base_runs"],
                                dict(meta["generators"]), alias, meta["n_blocks"], meta["wp_replicates"],
                                meta["subplot_replicates"], meta["seed"])
        elif kind == "definitive_screening":
            d = DefinitiveScreeningDesign(factors, meta["letters"], pd.DataFrame(), coded, meta["order"],
                                          meta["replicates"], meta["n_blocks"], meta["seed"])
        elif kind == "plackett_burman":
            d = PlackettBurmanDesign(factors, meta["letters"], pd.DataFrame(), coded, meta["corner_runs"],
                                     meta["center_points_per_replicate"], meta["replicates"], meta["n_blocks"],
                                     meta["seed"], meta["folded_on"])
        else:
            raise ValueError(f"알 수 없는 설계 종류: {kind!r}")
    d.runs = d.rebuild_runs(coded)
    return d


def worksheet_to_dict(ws: Worksheet) -> dict:
    """저장 형식(JSON 으로 바꿀 수 있는 사전)."""
    return {
        "format": FORMAT, "version": VERSION,
        "design": design_to_dict(ws.design),
        "nonregular": ws.nonregular,
        "coded": _frame_to_dict(ws.design.coded),
        "columns": {"StdOrder": [int(v) for v in ws.columns.index], **_frame_to_dict(ws.columns)},
    }


def save_worksheet(ws: Worksheet, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(json.dumps(worksheet_to_dict(ws), ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def load_worksheet(path: str | Path) -> Worksheet:
    return worksheet_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def worksheet_from_dict(doc: dict) -> Worksheet:
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


def define_custom_response_surface(
    df: pd.DataFrame,
    factors: list[str],
    *,
    levels: dict[str, tuple] | None = None,
    point_type: str | None = "PtType",
    std_order: str | None = "StdOrder",
    run_order: str | None = "RunOrder",
    blocks: str | None = "Blocks",
) -> Worksheet:
    """기존 데이터에서 반응표면 설계를 정의한다(Minitab 'Define Custom Response Surface Design').

    저/고 수준(코드 ±1): levels 로 주거나, 점 유형 열이 있으면 큐브점(1)의 최소·최대, 없으면 각 요인의
    서로 다른 값 가운데 둘째로 작은 값과 둘째로 큰 값(5수준 CCD) 또는 최소·최대(3수준)를 쓴다.
    점 유형 열이 없으면 코드값으로 만든다(모서리 1, 축 −1, 중앙 0, 그 밖의 3수준 점 2).
    """
    from ..designs.response_surface import ResponseSurfaceDesign

    missing = [c for c in factors if c not in df.columns]
    if missing:
        raise ValueError(f"요인 열이 없습니다: {missing}")
    levels = levels or {}
    df = df.reset_index(drop=True)
    n = len(df)
    letters = factor_letters(len(factors))
    has_pt = bool(point_type and point_type in df.columns)
    facs, coded = [], pd.DataFrame(index=range(n))
    for L, col in zip(letters, factors):
        x = df[col].astype(float)
        if col in levels:
            lo, hi = map(float, levels[col])
        elif has_pt and (df[point_type] == 1).any():
            cube = x[df[point_type] == 1]
            lo, hi = float(cube.min()), float(cube.max())
        else:
            u = np.sort(x.unique())
            lo, hi = (float(u[1]), float(u[-2])) if len(u) >= 5 else (float(u[0]), float(u[-1]))
        if lo == hi:
            raise ValueError(f"요인 {col!r} 의 저/고 수준이 같습니다.")
        coded[L] = ((x - (lo + hi) / 2) / ((hi - lo) / 2)).round(10)
        facs.append(Factor(col, lo, hi))
    if has_pt:
        pt = df[point_type].astype(int).values
    else:
        a = np.abs(coded[letters].values)
        pt = np.where((a == 0).all(axis=1), 0, np.where(((a == 1) | (a == 0)).all(axis=1) & (a == 1).all(axis=1), 1,
                                                         np.where((a > 1).any(axis=1), -1, 2)))
    coded.insert(0, "PtType", pt)
    coded.insert(1, "Blocks", df[blocks].astype(int).values if blocks and blocks in df.columns else 1)
    coded.insert(0, "RunOrder", df[run_order].astype(int).values if run_order and run_order in df.columns else np.arange(1, n + 1))
    coded.insert(0, "StdOrder", df[std_order].astype(int).values if std_order and std_order in df.columns else np.arange(1, n + 1))
    if coded["StdOrder"].duplicated().any():
        raise ValueError("StdOrder 값이 중복됩니다.")
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", *letters]]
    axial = np.abs(coded.loc[coded["PtType"] == -1, letters].values)
    alpha = float(axial.max()) if axial.size else None
    kind = "bbd" if (coded["PtType"] == 2).any() else "ccd"
    nb = int(coded["Blocks"].nunique())
    design = ResponseSurfaceDesign(kind, facs, letters, pd.DataFrame(), coded, alpha, n, nb, 1, nb)
    design.runs = design.rebuild_runs(coded)
    used = set(factors) | {c for c in (point_type, std_order, run_order, blocks) if c}
    extra = df[[c for c in df.columns if c not in used]].copy()
    extra.index = pd.Index(coded["StdOrder"].values, name="StdOrder")
    return Worksheet(design, extra)


def _constant_sum(df: pd.DataFrame, cols: list[str]) -> float | None:
    """열들의 행 합이 모든 런에서 같으면(음수 없음) 그 합, 아니면 None."""
    if len(cols) < 2:
        return None
    try:
        v = df[cols].astype(float).values
    except (TypeError, ValueError, KeyError):
        return None
    if np.isnan(v).any() or (v < -1e-12).any():
        return None
    s = v.sum(axis=1)
    tot = float(np.median(s))
    if tot <= 0 or np.abs(s - tot).max() > 1e-6 * max(1.0, tot):
        return None
    return tot


def define_custom_mixture(
    df: pd.DataFrame,
    components: list[str],
    *,
    process: list[str] | tuple[str, ...] = (),
    lower: dict[str, float] | None = None,
    upper: dict[str, float] | None = None,
    total: float | None = None,
    process_levels: dict[str, tuple] | None = None,
    point_type: str | None = "PtType",
    std_order: str | None = "StdOrder",
    run_order: str | None = "RunOrder",
    blocks: str | None = "Blocks",
) -> Worksheet:
    """기존 데이터에서 혼합물 설계를 정의한다(Minitab 'Define Custom Mixture Design').

    - 성분 열의 행 합이 모든 런에서 같아야 한다(그 값이 혼합 총량, total 로 직접 줄 수도 있음).
    - 성분 하한·상한(lower/upper)은 데이터와 같은 양 단위로 준다. 기본 하한 0, 상한 = 총량.
    - 공정 변수는 2수준 열(숫자면 최솟값·최댓값, 텍스트면 정렬 순서 첫/둘째 값, process_levels 로 지정 가능).
    - 점 유형 열이 없으면 하한 위에 있는 성분 수 k 로 만든다(k = 1 꼭지점, …, 모든 성분이면 0).
    """
    from ..designs.mixture import mix_letters

    missing = [c for c in [*components, *process] if c not in df.columns]
    if missing:
        raise ValueError(f"열이 없습니다: {missing}")
    df = df.reset_index(drop=True)
    n = len(df)
    tot = _constant_sum(df, list(components))
    if tot is None:
        raise ValueError("성분 열의 합이 런마다 같아야 합니다(혼합물 설계).")
    if total is not None:
        if abs(float(total) - tot) > 1e-6 * max(1.0, tot):
            raise ValueError(f"성분 합({tot:g})이 지정한 총량({total:g})과 다릅니다.")
        tot = float(total)
    lower, upper = lower or {}, upper or {}
    letters = mix_letters(len(components))
    comps, coded = [], pd.DataFrame(index=range(n))
    for L, col in zip(letters, components):
        x = df[col].astype(float).values / tot
        lo, hi = float(lower.get(col, 0.0)) / tot, float(upper.get(col, tot)) / tot
        if x.min() < lo - 1e-9 or x.max() > hi + 1e-9:
            raise ValueError(f"성분 {col!r} 의 값이 하한·상한 밖에 있습니다.")
        comps.append(Component(col, lo, hi))
        coded[L] = x.round(12)
    if sum(c.lower for c in comps) >= 1:
        raise ValueError("성분 하한의 합이 총량 이상입니다.")
    if len(process) > 7:
        raise ValueError("공정 변수는 최대 7개입니다.")
    procs = []
    for i, col in enumerate(process, 1):
        v = df[col]
        if process_levels and col in process_levels:
            lo, hi = process_levels[col]
        else:
            u = sorted(v.dropna().unique().tolist())
            if len(u) != 2:
                raise ValueError(f"공정 변수 {col!r} 는 서로 다른 값이 2개여야 합니다.")
            lo, hi = u
        numeric = pd.api.types.is_numeric_dtype(v)
        if not set(v.unique()) <= {lo, hi}:
            raise ValueError(f"공정 변수 {col!r} 에 저/고 수준이 아닌 값이 있습니다.")
        procs.append(Factor(col, float(lo) if numeric else lo, float(hi) if numeric else hi, numeric))
        coded[f"X{i}"] = np.where(v.values == lo, -1, 1)
    if point_type and point_type in df.columns:
        pt = df[point_type].astype(int).values
    else:
        lo = np.array([c.lower for c in comps])
        k = (coded[letters].values > lo + 1e-9).sum(axis=1)
        pt = np.where(k >= len(comps), 0, k)
    coded.insert(0, "Blocks", df[blocks].astype(int).values if blocks and blocks in df.columns else 1)
    coded.insert(0, "PtType", pt)
    coded.insert(0, "RunOrder", df[run_order].astype(int).values if run_order and run_order in df.columns else np.arange(1, n + 1))
    coded.insert(0, "StdOrder", df[std_order].astype(int).values if std_order and std_order in df.columns else np.arange(1, n + 1))
    if coded["StdOrder"].duplicated().any():
        raise ValueError("StdOrder 값이 중복됩니다.")
    xs = [f"X{i}" for i in range(1, len(procs) + 1)]
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", *letters, *xs]]
    constrained = any(c.lower > 0 or c.upper < 1 for c in comps)
    design = MixtureDesign("custom", comps, letters, procs, pd.DataFrame(), coded, None, tot, [], constrained, 1, [],
                           int(coded["Blocks"].nunique()))
    design.runs = design.rebuild_runs(coded)
    used = {*components, *process, *(c for c in (point_type, std_order, run_order, blocks) if c)}
    extra = df[[c for c in df.columns if c not in used]].copy()
    extra.index = pd.Index(coded["StdOrder"].values, name="StdOrder")
    return Worksheet(design, extra)


def _dsd_order(coded: np.ndarray, pt_center: np.ndarray, numeric: list[bool]) -> int | None:
    """코드 행렬이 확정적 선별설계 구조면 콘퍼런스 행렬 차수, 아니면 None.

    중앙점이 아닌 서로 다른 런: 숫자 요인의 0 이 런마다 최대 1개, 0 이 하나인 런이 (숫자 요인 수 × 2)개,
    모든 런의 부호 반전이 함께 있고, 전체가 2 × (요인 수에 맞는 차수)개.
    """
    from ..designs.definitive_screening import conference_order
    k = coded.shape[1]
    if k < 2 or k > 48:
        return None
    rows = {tuple(r) for r in coded[~pt_center].astype(int).tolist()}
    num = np.array(numeric, dtype=bool)
    zeros = [sum(1 for j, v in enumerate(r) if v == 0 and num[j]) for r in rows]
    n = conference_order(k)
    if max(zeros, default=2) > 1 or sum(zeros) != 2 * int(num.sum()) or len(rows) != 2 * n:
        return None
    if any(tuple(-v for v in r) not in rows for r in rows):
        return None
    return n


def define_custom_dsd(
    df: pd.DataFrame,
    factors: list[str],
    *,
    levels: dict[str, tuple] | None = None,
    point_type: str | None = "PtType",
    std_order: str | None = "StdOrder",
    run_order: str | None = "RunOrder",
    blocks: str | None = "Blocks",
) -> Worksheet:
    """기존 데이터에서 확정적 선별설계를 정의한다(숫자 요인은 최솟값·최댓값, 텍스트 요인은 정렬 순서 두 값)."""
    missing = [c for c in factors if c not in df.columns]
    if missing:
        raise ValueError(f"요인 열이 없습니다: {missing}")
    df = df.reset_index(drop=True)
    n = len(df)
    levels = levels or {}
    letters = factor_letters(len(factors))
    facs, coded = [], pd.DataFrame(index=range(n))
    for L, col in zip(letters, factors):
        v = df[col]
        numeric = pd.api.types.is_numeric_dtype(v)
        if col in levels:
            lo, hi = levels[col]
        elif numeric:
            lo, hi = float(v.min()), float(v.max())
        else:
            u = sorted(v.dropna().unique().tolist())
            if len(u) != 2:
                raise ValueError(f"텍스트 요인 {col!r} 는 수준이 2개여야 합니다.")
            lo, hi = u
        if lo == hi:
            raise ValueError(f"요인 {col!r} 의 저/고 수준이 같습니다.")
        if numeric:
            lo, hi = float(lo), float(hi)
            c = ((v.astype(float) - (lo + hi) / 2) / ((hi - lo) / 2)).round(10)
            if not c.isin([-1.0, 0.0, 1.0]).all():
                raise ValueError(f"요인 {col!r} 의 값이 저·중·고 세 수준이 아닙니다.")
        else:
            c = pd.Series(np.where(v.values == lo, -1, 1))
        facs.append(Factor(col, lo, hi, numeric))
        coded[L] = c.astype(int).values
    M = coded[letters].values
    num = [f.is_numeric for f in facs]
    center = (M[:, np.array(num)] == 0).all(axis=1) if any(num) else np.zeros(n, dtype=bool)
    order = _dsd_order(M, center, num)
    if order is None:
        raise ValueError("확정적 선별설계 구조(접힘 쌍 + 중앙점)가 아닙니다.")
    if point_type and point_type in df.columns:
        pt = df[point_type].astype(int).values
    else:
        pt = np.where(center, 0, np.where((M[:, np.array(num)] == 0).any(axis=1), 2, 1))
    coded.insert(0, "Blocks", df[blocks].astype(int).values if blocks and blocks in df.columns else 1)
    coded.insert(0, "PtType", pt)
    coded.insert(0, "RunOrder", df[run_order].astype(int).values if run_order and run_order in df.columns else np.arange(1, n + 1))
    coded.insert(0, "StdOrder", df[std_order].astype(int).values if std_order and std_order in df.columns else np.arange(1, n + 1))
    if coded["StdOrder"].duplicated().any():
        raise ValueError("StdOrder 값이 중복됩니다.")
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", *letters]]
    base = 2 * order + (2 if not all(num) else 1)
    reps = max(1, n // base)
    design = DefinitiveScreeningDesign(facs, letters, pd.DataFrame(), coded, order, reps,
                                       int(coded["Blocks"].nunique()))
    design.runs = design.rebuild_runs(coded)
    used = set(factors) | {c for c in (point_type, std_order, run_order, blocks) if c}
    extra = df[[c for c in df.columns if c not in used]].copy()
    extra.index = pd.Index(coded["StdOrder"].values, name="StdOrder")
    return Worksheet(design, extra)


def _looks_dsd(df: pd.DataFrame, factors: list[str]) -> bool:
    try:
        define_custom_dsd(df, factors)
        return True
    except (ValueError, KeyError, TypeError):
        return False


def design_kind_of(df: pd.DataFrame, factors: list[str], process=None) -> str:
    """데이터로 사용자 정의 설계 종류를 고른다: mixture / dsd / response_surface / general_full / taguchi / two_level."""
    from .custom_designs import multilevel_kind
    if process or _constant_sum(df, list(factors)) is not None:
        return "mixture"
    if _looks_dsd(df, list(factors)):
        return "dsd"
    if "PtType" in df.columns and df["PtType"].isin([-1, 2]).any():
        return "response_surface"
    return multilevel_kind(df, list(factors)) or "two_level"


def define_custom_design(df: pd.DataFrame, factors: list[str], **kwargs) -> Worksheet:
    """요인 열(혼합물이면 성분 열)로 설계 종류를 알아보고 사용자 설계로 정의한다.

    요인 열의 행 합이 일정하거나 process 를 주면 혼합물 설계, 확정적 선별설계 구조(접힘 쌍마다 0 이 하나,
    중앙점)면 확정적 선별설계, 점 유형 열(PtType)에 축점(−1)이나 모서리 중점(2)이 있으면 반응표면 설계,
    아니면 2수준 요인설계로 정의한다.
    """
    kind = kwargs.pop("kind", None) or design_kind_of(df, factors, kwargs.get("process"))
    if kind == "mixture":
        return define_custom_mixture(df, factors, **kwargs)
    kwargs.pop("process", None)
    if kind == "dsd":
        return define_custom_dsd(df, factors, **kwargs)
    if kind == "response_surface":
        return define_custom_response_surface(df, factors, **kwargs)
    if kind in ("general_full", "taguchi"):
        from .custom_designs import define_custom_general_full, define_custom_taguchi
        return define_custom_general_full(df, factors) if kind == "general_full" else define_custom_taguchi(df, factors)[0]
    return define_custom_two_level(df, factors, **kwargs)


def load_mwx_worksheet(path: str | Path, factors: list[str], **kwargs) -> Worksheet:
    """Minitab .MWX 를 읽어 사용자 설계로 정의한 워크시트를 만든다(종류는 define_custom_design 규칙)."""
    from .mwx import read_mwx
    return define_custom_design(read_mwx(path), factors, **kwargs)
