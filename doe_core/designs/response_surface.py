"""반응표면 설계 — Minitab 'Create Response Surface Design'(중심합성설계 CCD, Box-Behnken).

문서 근거(docs/spec/C_rsm_mixture_optimal.md 1~2절)
CCD
- 구성: 큐브(2^k 또는 2^(k−p) 요인점) + 2k 축점(±α) + 중앙점. 블록이 있으면 큐브 블록(블록 수 − 1개)과 축 블록 1개.
- 카탈로그: 'Summary of central composite designs' 표(요인 2~10, Full/Half/Quarter/Eighth, 블록 1/2/3/5)를 그대로 쓴다.
  큐브의 부분요인·블록 생성자는 2수준 요인설계 카탈로그를 쓴다.
- 기본 α: 회전 가능(y)이면 F^¼(F = 요인점 수), 아니면 직교 블록 α = √(F(2k + n_a) / (2(F + n_c)))
  (n_c = 큐브 블록 중앙점 합, n_a = 축 블록 중앙점). 표의 1.414, 1.633, 2.366, 2.828 … 과 일치.
  Face Centered 는 α = 1, Custom 은 직접 지정.
- 문서 표의 '3요인 Full 14런 1블록' 행은 산식(8 + 6 + 6 = 20)과 맞지 않아 20런으로 보정한다(CCD_ERRATA).
Box-Behnken
- 3~7요인. 3·4·5요인은 요인 쌍마다 2² 요인점(나머지 0), 6요인은 3요인 묶음 6개, 7요인은 BIBD(7,3,1) 묶음 7개의 2³ 요인점.
- 블록: 4요인 3블록(쌍 묶음 AB·CD / AC·BD / AD·BC), 5요인 2블록(오각형·별 모양 쌍), 6·7요인 2블록(묶음마다 3요인 곱 부호로 반쪽 분할).
  모든 블록은 직교. 3요인은 블록 없음.
- 런 수는 문서 표(15, 27, 46, 54, 62)와 같다. 5요인 표의 '기본 중앙점 3' 은 46런과 맞지 않아(40 + 6) 블록당 3으로 해석.
- 9·10요인은 구성법이 문서에 없어 아직 지원하지 않는다.
공통
- 워크시트 C3 열 PtType: 1 큐브(요인)점, −1 축점, 0 중앙점, 2 Box-Behnken 모서리 중점(문서 'what points can I use').
- 반복: 기본 설계의 모든 런을 반복. Block on replicates 면 블록 체계를 반복마다 복제(블록 수 = 기본 블록 × 반복).
- 요인 수준 정의: 'Cube points'(저/고가 ±1) 또는 'Axial points'(저/고가 ±α).
- 범주형 요인은 아직 지원하지 않는다(문서: 범주형 수준마다 연속 설계를 복제).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product

import numpy as np
import pandas as pd

from .catalog import CATALOG
from .common import Factor, assign_orders, default_factors, factor_letters
from .factorial import _yates_matrix, block_numbers

FRACTION_DENOM = {"Full": 1, "Half": 2, "Quarter": 4, "Eighth": 8}

# (요인, 부분, 블록) -> (런, 큐브 블록 수, 큐브 런, 중앙점 합, 큐브 중앙점 합, 축 중앙점, 기본 α 표시값, 회전 가능)
_CCD_TEXT = """
2 Full 13 1 0 4 5 0 0 1.414 y
2 Full 14 2 1 4 6 3 3 1.414 y
3 Full 20 1 0 8 6 0 0 1.682 y
3 Full 20 2 1 8 6 4 2 1.633 n
3 Full 20 3 2 8 6 4 2 1.633 n
4 Full 31 1 0 16 7 0 0 2 y
4 Full 30 2 1 16 6 4 2 2 y
4 Full 30 3 2 16 6 4 2 2 y
5 Full 52 1 0 32 10 0 0 2.378 y
5 Full 54 2 1 32 12 8 4 2.366 n
5 Full 54 3 2 32 12 8 4 2.366 n
5 Half 32 1 0 16 6 0 0 2 y
5 Half 33 2 1 16 7 6 1 2 y
6 Full 90 1 0 64 14 0 0 2.828 y
6 Full 90 2 1 64 14 8 6 2.828 y
6 Full 90 3 2 64 14 8 6 2.828 y
6 Full 90 5 4 64 14 8 6 2.828 y
6 Half 53 1 0 32 9 0 0 2.378 y
6 Half 54 2 1 32 10 8 2 2.366 n
6 Half 54 3 2 32 10 8 2 2.366 n
7 Full 152 1 0 128 10 0 0 3.364 y
7 Full 160 2 1 128 18 8 10 3.364 y
7 Full 160 3 2 128 18 8 10 3.364 y
7 Full 160 5 4 128 18 8 10 3.364 y
7 Half 88 1 0 64 10 0 0 2.828 y
7 Half 90 2 1 64 12 8 4 2.828 y
7 Half 90 3 2 64 12 8 4 2.828 y
7 Half 90 5 4 64 12 8 4 2.828 y
8 Half 154 1 0 128 10 0 0 3.364 y
8 Half 160 2 1 128 16 8 8 3.364 y
8 Half 160 3 2 128 16 8 8 3.364 y
8 Half 160 5 4 128 16 8 8 3.364 y
8 Quarter 90 1 0 64 10 0 0 2.828 y
8 Quarter 90 2 1 64 10 8 2 2.828 y
8 Quarter 90 3 2 64 10 8 2 2.828 y
8 Quarter 90 5 4 64 10 8 2 2.828 y
9 Quarter 156 1 0 128 10 0 0 3.364 y
9 Quarter 160 2 1 128 14 8 6 3.364 y
9 Quarter 160 3 2 128 14 8 6 3.364 y
9 Quarter 160 5 4 128 14 8 6 3.364 y
10 Eighth 158 1 0 128 10 0 0 3.364 y
10 Eighth 160 2 1 128 12 8 4 3.364 y
10 Eighth 160 3 2 128 12 8 4 3.364 y
10 Eighth 160 5 4 128 12 8 4 3.364 y
"""

# 문서 표 오류 보정: (요인, 부분, 블록) -> (문서 값, 보정 값, 설명)
CCD_ERRATA = {(3, "Full", 1): ("Runs 14", "Runs 20", "8 큐브 + 6 축 + 6 중앙 = 20")}


@dataclass(frozen=True)
class CCDEntry:
    k: int
    fraction: str
    runs: int
    blocks: int
    cube_blocks: int
    cube_runs: int
    center: int
    cube_center: int
    axial_center: int
    alpha_text: str
    rotatable: bool

    @property
    def default_alpha(self) -> float:
        if self.rotatable:
            return self.cube_runs ** 0.25
        f = self.cube_runs
        return float(np.sqrt(f * (2 * self.k + self.axial_center) / (2 * (f + self.cube_center))))


CCD_CATALOG: dict[tuple[int, str, int], CCDEntry] = {}
for _line in _CCD_TEXT.strip().splitlines():
    p = _line.split()
    _e = CCDEntry(int(p[0]), p[1], int(p[2]), int(p[3]), int(p[4]), int(p[5]), int(p[6]), int(p[7]), int(p[8]),
                  p[9], p[10] == "y")
    CCD_CATALOG[(_e.k, _e.fraction, _e.blocks)] = _e


def available_ccd(k: int) -> list[CCDEntry]:
    return [e for (kk, _, _), e in CCD_CATALOG.items() if kk == k]


BBD_CATALOG = {  # 요인 -> (런, 가능한 블록 수, 기본 중앙점(블록 없을 때 총수))
    3: (15, (1,), 3), 4: (27, (1, 3), 3), 5: (46, (1, 2), 6), 6: (54, (1, 2), 6), 7: (62, (1, 2), 6),
}
_BBD_GROUPS = {
    6: ["ABD", "BCE", "CDF", "ADE", "BEF", "ACF"],
    7: ["DEF", "AFG", "BEG", "ABD", "CDG", "BCF", "ACE"],
}


@dataclass
class ResponseSurfaceDesign:
    kind: str                         # "ccd" | "bbd"
    factors: list[Factor]
    letters: list[str]
    runs: pd.DataFrame
    coded: pd.DataFrame               # StdOrder, RunOrder, <point_col>, Blocks, 요인(코드값, 축점은 ±α)
    alpha: float | None
    base_runs: int
    base_blocks: int
    replicates: int
    n_blocks: int
    fraction: str = "Full"            # CCD 큐브 부분
    generators: dict = field(default_factory=dict)
    seed: int | None = None
    point_col: str = "PtType"
    folded_on = None

    @property
    def n_factors(self) -> int:
        return len(self.factors)

    @property
    def n_runs(self) -> int:
        return len(self.runs)

    def rebuild_runs(self, coded: pd.DataFrame) -> pd.DataFrame:
        runs = coded[["StdOrder", "RunOrder", self.point_col, "Blocks"]].copy()
        for L, f in zip(self.letters, self.factors):
            lo, hi = float(f.low), float(f.high)
            runs[f.name] = (lo + hi) / 2 + coded[L].values.astype(float) * (hi - lo) / 2
        return runs

    def point_counts(self) -> dict:
        pt = self.coded[self.point_col]
        return {"cube": int((pt == 1).sum()), "axial": int((pt == -1).sum()), "edge": int((pt == 2).sum()),
                "center": int((pt == 0).sum())}

    def summary(self) -> dict:
        d = {"Factors": self.n_factors, "Replicates": self.replicates, "Base runs": self.base_runs,
             "Total runs": self.n_runs, "Base blocks": self.base_blocks, "Total blocks": self.n_blocks}
        if self.kind == "ccd":
            pc = self.point_counts()
            ax_blocks = set(self.coded.loc[self.coded[self.point_col] == -1, "Blocks"])
            cen = self.coded[self.coded[self.point_col] == 0]
            in_axial = int(cen["Blocks"].isin(ax_blocks).sum()) if self.base_blocks > 1 else 0
            d.update({"α": self.alpha, "Two-level factorial": "Full factorial" if self.fraction == "Full"
                      else f"{self.fraction} fraction",
                      "Cube points": pc["cube"], "Center points in cube": pc["center"] - in_axial,
                      "Axial points": pc["axial"], "Center points in axial": in_axial})
        else:
            d["Center points"] = self.point_counts()["center"]
        return d

    def summary_text(self) -> str:
        s = self.summary()
        lines = ["Design Summary",
                 f"Factors: {s['Factors']}  Replicates: {s['Replicates']}",
                 f"Base runs: {s['Base runs']}  Total runs: {s['Total runs']}",
                 f"Base blocks: {s['Base blocks']}  Total blocks: {s['Total blocks']}"]
        if self.kind == "ccd":
            lines += [f"α = {s['α']:.4g}" if abs(s['α'] - round(s['α'])) < 1e-12 else f"α = {s['α']:.3f}",
                      f"Two-level factorial: {s['Two-level factorial']}",
                      "Point Types",
                      f"Cube points: {s['Cube points']}", f"Center points in cube: {s['Center points in cube']}",
                      f"Axial points: {s['Axial points']}", f"Center points in axial: {s['Center points in axial']}"]
        else:
            lines.append(f"Center points: {s['Center points']}")
        return "\n".join(lines)

    def design_table(self) -> pd.DataFrame:
        tbl = self.coded[self.letters].copy()
        if self.kind == "ccd":
            tbl = tbl.apply(lambda c: c.map(lambda v: f"{v:.3f}"))
        else:
            tbl = tbl.astype(int)
        tbl.insert(0, "Blk", self.coded["Blocks"].values)
        tbl.insert(0, "Run", self.coded["RunOrder"].values)
        return tbl.reset_index(drop=True)


# ---------------------------------------------------------------- 공통 마무리


def _finish(kind, base: pd.DataFrame, letters, factors, *, alpha, base_blocks, replicates, block_on_replicates,
            randomize, seed, fraction="Full", generators=None, levels_define="cube") -> ResponseSurfaceDesign:
    parts = []
    for r in range(replicates):
        c = base.copy()
        if block_on_replicates:
            c["Blocks"] = c["Blocks"] + r * base_blocks
        c["_rep"] = r
        parts.append(c)
    coded = pd.concat(parts, ignore_index=True)
    coded = assign_orders(coded, ["Blocks", "_rep", "_order"], randomize=randomize, seed=seed)
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", *letters]]
    if levels_define == "axial" and alpha:
        # 입력한 저/고가 ±α 위치 → 큐브 점(±1)의 실제 값으로 환산
        factors = [Factor(f.name, (float(f.low) + float(f.high)) / 2 - (float(f.high) - float(f.low)) / 2 / alpha,
                          (float(f.low) + float(f.high)) / 2 + (float(f.high) - float(f.low)) / 2 / alpha)
                   for f in factors]
    d = ResponseSurfaceDesign(kind, factors, letters, pd.DataFrame(), coded, alpha, len(base), base_blocks,
                              replicates, base_blocks * replicates if block_on_replicates else base_blocks,
                              fraction, dict(generators or {}), seed)
    d.runs = d.rebuild_runs(coded)
    return d


def _check_factors(k, factors):
    if factors is None:
        factors = default_factors(k)
    if len(factors) != k:
        raise ValueError("factors 길이가 요인 수와 다릅니다.")
    if not all(f.is_numeric for f in factors):
        raise ValueError("반응표면 설계의 요인은 숫자(연속) 요인이어야 합니다. 범주형 요인은 아직 지원하지 않습니다.")
    return factors


# ---------------------------------------------------------------- CCD


def create_ccd(
    k: int,
    *,
    fraction: str = "Full",
    blocks: int = 1,
    factors: list[Factor] | None = None,
    alpha: str | float = "default",
    center_points: int | tuple[int, int] | None = None,
    replicates: int = 1,
    block_on_replicates: bool = False,
    levels_define: str = "cube",
    randomize: bool = True,
    seed: int | None = None,
) -> ResponseSurfaceDesign:
    """중심합성설계. alpha: "default" | "face" | 숫자. center_points: None(기본) | 정수(블록 없음) |
    (큐브 블록당, 축 블록) 튜플(블록 설계)."""
    key = (k, fraction, blocks)
    if key not in CCD_CATALOG:
        opts = sorted({(e.fraction, e.blocks) for e in available_ccd(k)})
        raise ValueError(f"{k}요인 {fraction} {blocks}블록 CCD 는 카탈로그에 없습니다. 가능한 (부분, 블록): {opts}")
    e = CCD_CATALOG[key]
    factors = _check_factors(k, factors)
    letters = factor_letters(k)

    # 중앙점 배분
    if center_points is None:
        cube_c_total, axial_c = (e.cube_center, e.axial_center) if blocks > 1 else (e.center, 0)
        per_cube_block = [cube_c_total // max(e.cube_blocks, 1)] * max(e.cube_blocks, 1)
        for i in range(cube_c_total % max(e.cube_blocks, 1)):
            per_cube_block[i] += 1
    elif blocks == 1:
        if not isinstance(center_points, int):
            raise ValueError("블록이 없는 설계의 중앙점 수는 정수입니다.")
        per_cube_block, axial_c = [center_points], 0
    else:
        cc, axial_c = center_points
        per_cube_block = [cc] * e.cube_blocks

    # α
    if alpha == "default":
        a_val = e.default_alpha
    elif alpha in ("face", "face_centered"):
        a_val = 1.0
    else:
        a_val = float(alpha)
        if a_val <= 0:
            raise ValueError("α 는 양수여야 합니다.")

    # 큐브(부분요인) + 블록 생성자
    n_cube = e.cube_runs
    entry = CATALOG.get((k, n_cube))
    gens = {} if n_cube == 2 ** k else entry.generators
    kk = int(np.log2(n_cube))
    base = _yates_matrix(kk)
    cols = {L: base[:, i] for i, L in enumerate(letters[:kk])}
    for L, w in gens.items():
        cols[L] = np.prod([cols[ch] for ch in w], axis=0)
    cube = pd.DataFrame({L: cols[L] for L in letters}).astype(float)
    if e.cube_blocks > 1:
        bg = entry.blocks[e.cube_blocks].generators if entry and e.cube_blocks in entry.blocks else None
        if bg is None:
            raise ValueError("큐브 블록 생성자를 찾을 수 없습니다.")
        cube["Blocks"] = block_numbers(cube, bg)
    else:
        cube["Blocks"] = 1
    cube["PtType"] = 1
    cube["_order"] = np.arange(len(cube))
    parts = [cube]
    order = len(cube)
    cube_block_ids = sorted(cube["Blocks"].unique())
    for b, nc in zip(cube_block_ids, per_cube_block):
        if nc:
            cp = pd.DataFrame({L: [0.0] * nc for L in letters})
            cp["Blocks"], cp["PtType"], cp["_order"] = b, 0, order + np.arange(nc)
            order += nc
            parts.append(cp)
    axial_block = (max(cube_block_ids) + 1) if blocks > 1 else 1
    ax_rows = []
    for i in range(k):
        for s in (-1, 1):
            row = [0.0] * k
            row[i] = s * a_val
            ax_rows.append(row)
    ax = pd.DataFrame(ax_rows, columns=letters)
    ax["Blocks"], ax["PtType"], ax["_order"] = axial_block, -1, order + np.arange(len(ax))
    order += len(ax)
    parts.append(ax)
    if axial_c:
        cp = pd.DataFrame({L: [0.0] * axial_c for L in letters})
        cp["Blocks"], cp["PtType"], cp["_order"] = axial_block, 0, order + np.arange(axial_c)
        parts.append(cp)
    if blocks == 1:
        # 블록이 없으면 표준 순서: 큐브 → 축점 → 중앙점
        allp = pd.concat(parts, ignore_index=True)
        rank = allp["PtType"].map({1: 0, -1: 1, 0: 2})
        allp["_order"] = np.lexsort((allp["_order"].values, rank.values))
        allp["_order"] = allp["_order"].argsort()
        base_df = allp
    else:
        base_df = pd.concat(parts, ignore_index=True)
    return _finish("ccd", base_df, letters, factors, alpha=a_val, base_blocks=blocks, replicates=replicates,
                   block_on_replicates=block_on_replicates, randomize=randomize, seed=seed, fraction=fraction,
                   generators=gens, levels_define=levels_define)


# ---------------------------------------------------------------- Box-Behnken


def _bbd_points(k: int) -> tuple[list[np.ndarray], list[list[int]]]:
    """(묶음별 요인점 행렬 목록, 묶음별 블록 분할 정보) — 블록 분할은 bbd_blocks 에서 처리."""
    letters = factor_letters(k)
    groups = [tuple(c) for c in combinations(letters, 2)] if k <= 5 else [tuple(g) for g in _BBD_GROUPS[k]]
    mats = []
    for g in groups:
        sub = np.array(list(product((-1, 1), repeat=len(g))))[:, ::-1]   # 첫 요인이 가장 빨리 바뀜
        m = np.zeros((len(sub), k))
        for j, L in enumerate(g):
            m[:, letters.index(L)] = sub[:, j]
        mats.append(m)
    return mats, groups


def create_box_behnken(
    k: int,
    *,
    blocks: int = 1,
    factors: list[Factor] | None = None,
    center_points: int | None = None,
    replicates: int = 1,
    block_on_replicates: bool = False,
    randomize: bool = True,
    seed: int | None = None,
) -> ResponseSurfaceDesign:
    """Box-Behnken 설계(3~7요인). center_points: 블록당 중앙점(None 이면 기본)."""
    if k not in BBD_CATALOG:
        raise ValueError("Box-Behnken 설계는 3~7요인을 지원합니다(9·10요인은 아직 지원하지 않음).")
    runs_doc, block_opts, default_cp = BBD_CATALOG[k]
    if blocks not in block_opts:
        raise ValueError(f"{k}요인 Box-Behnken 의 블록 수는 {block_opts} 중 하나입니다.")
    factors = _check_factors(k, factors)
    letters = factor_letters(k)
    mats, groups = _bbd_points(k)
    edge = pd.DataFrame(np.vstack(mats), columns=letters)
    grp = np.concatenate([[gi] * len(m) for gi, m in enumerate(mats)])
    if blocks == 1:
        blk = np.ones(len(edge), dtype=int)
    elif k == 4:
        pair_block = {("A", "B"): 1, ("C", "D"): 1, ("A", "C"): 2, ("B", "D"): 2, ("A", "D"): 3, ("B", "C"): 3}
        blk = np.array([pair_block[groups[g]] for g in grp])
    elif k == 5:
        ring = {("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("A", "E")}
        blk = np.array([1 if groups[g] in ring else 2 for g in grp])
    else:  # 6, 7요인: 묶음마다 3요인 곱 부호로 반쪽 분할
        prod3 = np.array([np.prod([edge.iloc[i][L] for L in groups[g]]) for i, g in enumerate(grp)])
        blk = np.where(prod3 > 0, 1, 2)
    edge["Blocks"] = blk
    edge["PtType"] = 2
    edge["_order"] = np.arange(len(edge))
    per_block = (default_cp // blocks) if center_points is None else center_points
    parts = [edge]
    order = len(edge)
    for b in range(1, blocks + 1):
        if per_block:
            cp = pd.DataFrame({L: [0.0] * per_block for L in letters})
            cp["Blocks"], cp["PtType"], cp["_order"] = b, 0, order + np.arange(per_block)
            order += per_block
            parts.append(cp)
    base = pd.concat(parts, ignore_index=True)
    base = base.sort_values(["Blocks", "_order"], kind="stable").reset_index(drop=True)
    base["_order"] = np.arange(len(base))
    if center_points is None and len(base) != runs_doc:
        raise AssertionError(f"Box-Behnken {k}요인 런 수 {len(base)} 가 문서 표({runs_doc})와 다릅니다.")
    return _finish("bbd", base, letters, factors, alpha=None, base_blocks=blocks, replicates=replicates,
                   block_on_replicates=block_on_replicates, randomize=randomize, seed=seed)


# ---------------------------------------------------------------- 축점 추가(Modify Design)


def axial_alpha(design, alpha: str | float = "default") -> float:
    """축점 추가에 쓸 α 값: 'default' 는 모서리점 수 F 의 F^¼(회전 가능), 'face' 는 1, 숫자는 그대로."""
    if alpha == "default":
        n_corner = int((design.coded[design.point_col] == 1).sum()) // max(design.replicates, 1)
        return n_corner ** 0.25
    if alpha in ("face", "face_centered"):
        return 1.0
    return float(alpha)


def axial_preview(design, alpha: str | float = "default") -> pd.DataFrame:
    """축점의 실제 값(요인별 −α·+α 수준). 실험할 수 있는 범위인지 추가 전에 확인하는 표."""
    a = axial_alpha(design, alpha)
    rows = []
    for L, f in zip(design.letters, design.factors):
        mid, half = (f.low + f.high) / 2, (f.high - f.low) / 2
        rows.append({"Factor": f.name, "−α": mid - a * half, "Low": f.low, "Center": mid, "High": f.high,
                     "+α": mid + a * half})
    return pd.DataFrame(rows)


def add_axial_points(design, *, alpha: str | float = "default", center_points: int = 0) -> ResponseSurfaceDesign:
    """2수준 요인설계·PB 에 축점(새 블록)을 붙여 중심합성설계로 바꾼다(Minitab Modify Design > Add axial points).

    기본 α 는 모서리점 수 F 의 F^¼(회전 가능). 축점의 점 유형은 −1, 블록은 기존 최대 블록 + 1.
    StdOrder·RunOrder 는 이어서 매긴다. 결과 설계의 점 유형 열 이름은 원래 이름(CenterPt/PtType)을 유지한다.
    """
    from .factorial import TwoLevelDesign
    from .plackett_burman import PlackettBurmanDesign

    if not isinstance(design, (TwoLevelDesign, PlackettBurmanDesign)):
        raise ValueError("축점은 2수준 요인설계와 Plackett-Burman 설계에만 추가할 수 있습니다.")
    if not all(f.is_numeric for f in design.factors):
        raise ValueError("모든 요인이 숫자 요인이어야 축점을 추가할 수 있습니다.")
    coded = design.coded
    pc = design.point_col
    letters = list(design.letters)
    k = len(letters)
    a_val = axial_alpha(design, alpha)
    rows = []
    for i in range(k):
        for s in (-1, 1):
            r = [0.0] * k
            r[i] = s * a_val
            rows.append(r)
    ax = pd.DataFrame(rows, columns=letters)
    ax[pc] = -1
    if center_points:
        cp = pd.DataFrame({L: [0.0] * center_points for L in letters})
        cp[pc] = 0
        ax = pd.concat([ax, cp], ignore_index=True)
    new_block = int(coded["Blocks"].max()) + 1
    ax["Blocks"] = new_block
    ax["StdOrder"] = int(coded["StdOrder"].max()) + np.arange(1, len(ax) + 1)
    ax["RunOrder"] = int(coded["RunOrder"].max()) + np.arange(1, len(ax) + 1)
    out = pd.concat([coded.astype({L: float for L in letters}), ax[coded.columns]], ignore_index=True)
    d = ResponseSurfaceDesign("ccd", list(design.factors), letters, pd.DataFrame(), out, a_val,
                              len(out), int(out["Blocks"].nunique()), 1, int(out["Blocks"].nunique()),
                              "Full" if not getattr(design, "generators", None) else f"1/{2 ** len(design.generators)}",
                              dict(getattr(design, "generators", {}) or {}), design.seed, pc)
    d.runs = d.rebuild_runs(out)
    return d
