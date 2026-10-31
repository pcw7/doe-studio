"""2수준 분할구 설계 — Minitab 'Create Factorial Design > 2-level split-plot (hard-to-change factors)'.

문서 근거(docs/spec/A_factorial_create.md 1.4·3.9절, 예제 4요인·HTC 1·전구 반복 2)
- 바꾸기 어려운 요인(HTC) 수준을 여러 런 동안 고정한 묶음 = 전구(whole plot), 그 안의 쉬운 요인(ETC) 조합 = 하위구.
- 총 요인 수 최대 7. 전구 반복(whole-plot replicates): 기본 설계를 통째로 반복. 1 이면 HTC 효과를 검정할 수 없는
  설계가 있어 기본값 2. 하위구 반복(subplot replicates): 전구 안에서 ETC 조합을 반복. Block on replicates.
- 중앙점 없음. 워크시트에 WP(전구 번호) 열, 점 유형 열 이름은 PtType.
- 랜덤화: 전구 순서(블록 안)와 전구 안의 런 순서를 모두 섞는다(설계표에서 같은 WP 의 런이 연속).
- 출력: Design Summary 4행 × 4칸(Factors, Whole plots / Hard-to-change, Runs per whole plot / Runs,
  Whole-plot replicates / Blocks, Subplot replicates), 'Hard-to-change factors: A', 'Whole Plot Generators: A',
  별칭 구조, Design Table(Run | Blk | WP | 요인 기호).

문서에 없어 정한 것(가용 설계 표의 숫자가 문서에 없음)
- HTC 요인은 앞쪽 문자(A, B, …). 기본 설계는 2수준 카탈로그의 기본 생성자 설계 가운데 기본 요인 수가 HTC 수보다
  많은 것(HTC 요인이 모두 기본 요인 → 전구 = HTC 조합 2^h 개, 전구당 하위구 = 런 / 2^h). ETC 교호작용으로 전구를 늘리는
  설계(전구 생성자에 ETC 단어가 들어가는 경우)는 아직 제공하지 않는다.
- 설계 이름: 'Full factorial with 2 whole plots and 8 subplots'(문서 예제), 부분 요인은 '1/2 fraction with …'.
- 표준 순서: 반복 → HTC 조합(첫 요인이 가장 빨리 바뀜) → 하위구 반복 → 기본 설계의 표준 순서. WP 는 이 순서로 1부터.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .catalog import available_designs
from .common import Factor, sign_table, to_levels
from .factorial import AliasStructure, create_two_level_design, default_alias_order
from .words import LETTERS, ROMAN, word_to_str

MAX_FACTORS = 7


@dataclass(frozen=True)
class SplitPlotOption:
    n_factors: int
    n_htc: int
    n_runs: int                       # 기본 설계(전구 반복 1, 하위구 반복 1) 런 수
    resolution: int | None

    @property
    def whole_plots(self) -> int:
        return 2 ** self.n_htc

    @property
    def subplots(self) -> int:
        return self.n_runs // self.whole_plots

    @property
    def label(self) -> str:
        denom = 2 ** self.n_factors // self.n_runs
        head = "Full factorial" if denom == 1 else f"1/{denom} fraction"
        return f"{head} with {self.whole_plots} whole plots and {self.subplots} subplots"


def available_split_plot(n_factors: int, n_htc: int) -> list[SplitPlotOption]:
    """선택할 수 있는 분할구 기본 설계(전구 수 오름차순 → 런 수 오름차순)."""
    if not 2 <= n_factors <= MAX_FACTORS:
        raise ValueError(f"분할구 설계의 총 요인 수는 2~{MAX_FACTORS} 입니다.")
    if not 1 <= n_htc < n_factors:
        raise ValueError("바꾸기 어려운 요인 수는 1 이상, 총 요인 수 미만이어야 합니다.")
    out = []
    for e in available_designs(n_factors):
        base_k = int(np.log2(e.n_runs))
        if base_k > n_htc:
            out.append(SplitPlotOption(n_factors, n_htc, e.n_runs, e.resolution))
    return sorted(out, key=lambda o: (o.whole_plots, o.n_runs))


@dataclass
class SplitPlotDesign:
    factors: list[Factor]
    runs: pd.DataFrame
    coded: pd.DataFrame               # StdOrder, RunOrder, PtType, Blocks, WP, 요인(−1/+1)
    n_htc: int
    base_runs: int
    generators: dict[str, str]
    alias: AliasStructure
    n_blocks: int
    wp_replicates: int
    subplot_replicates: int
    seed: int | None = None

    point_col = "PtType"
    folded_on = None
    center_points_per_block = 0

    @property
    def letters(self) -> list[str]:
        return list(LETTERS[: len(self.factors)])

    @property
    def htc_letters(self) -> list[str]:
        return self.letters[: self.n_htc]

    @property
    def n_factors(self) -> int:
        return len(self.factors)

    @property
    def n_runs(self) -> int:
        return len(self.runs)

    @property
    def replicates(self) -> int:
        return self.wp_replicates

    @property
    def n_whole_plots(self) -> int:
        return int(self.coded["WP"].nunique())

    @property
    def runs_per_whole_plot(self) -> int:
        return self.n_runs // self.n_whole_plots

    def rebuild_runs(self, coded: pd.DataFrame) -> pd.DataFrame:
        runs = to_levels(coded, self.letters, self.factors, self.point_col)
        runs.insert(4, "WP", coded["WP"].values)
        return runs

    def summary(self) -> dict:
        return {"Factors": self.n_factors, "Whole plots": self.n_whole_plots, "Hard-to-change": self.n_htc,
                "Runs per whole plot": self.runs_per_whole_plot, "Runs": self.n_runs,
                "Whole-plot replicates": self.wp_replicates, "Blocks": self.n_blocks,
                "Subplot replicates": self.subplot_replicates}

    def summary_table(self) -> pd.DataFrame:
        s = self.summary()
        keys = list(s)
        return pd.DataFrame([[f"{keys[i]}:", str(s[keys[i]]), f"{keys[i + 1]}:", str(s[keys[i + 1]])]
                             for i in range(0, len(keys), 2)])

    @property
    def resolution_text(self) -> str:
        r = self.alias.resolution
        return "Full" if r is None else ROMAN.get(r, str(r))

    def summary_text(self) -> str:
        rows = self.summary_table().values.tolist()
        lines = ["Design Summary", *[f"{a} {b}  {c} {d}" for a, b, c, d in rows]]
        if self.generators:
            lines.append("Design Generators: " + ", ".join(f"{k} = {v}" for k, v in self.generators.items()))
        lines.append("Hard-to-change factors: " + ", ".join(self.htc_letters))
        lines.append("Whole Plot Generators: " + ", ".join(self.htc_letters))
        return "\n".join(lines)

    def defining_relation_text(self) -> str:
        if not self.alias.defining:
            return "Defining Relation: (full factorial)"
        return "Defining Relation: I = " + " = ".join(word_to_str(w) for w in self.alias.defining)

    def alias_text(self, max_order: int | None = "default") -> str:
        if self.alias.is_free:
            return "All terms are free from aliasing."
        return self.alias.text(max_order if max_order != "default" else default_alias_order(self.n_factors))

    def design_table(self) -> pd.DataFrame:
        tbl = pd.DataFrame(sign_table(self.coded, self.letters), columns=self.letters)
        tbl.insert(0, "WP", self.coded["WP"].values)
        tbl.insert(0, "Blk", self.coded["Blocks"].values)
        tbl.insert(0, "Run", self.coded["RunOrder"].values)
        return tbl


def _randomize(coded: pd.DataFrame, rng) -> np.ndarray:
    """블록 순서대로, 블록 안에서 전구 순서를 섞고 전구 안의 런을 섞은 RunOrder."""
    run_order = np.empty(len(coded), dtype=int)
    pos = 0
    for b in sorted(coded["Blocks"].unique()):
        wps = sorted(coded.loc[coded["Blocks"] == b, "WP"].unique())
        for wp in rng.permutation(wps):
            idx = np.where(coded["WP"].values == wp)[0]
            run_order[rng.permutation(idx)] = np.arange(pos + 1, pos + len(idx) + 1)
            pos += len(idx)
    return run_order


def randomize_split_plot(d: SplitPlotDesign, seed: int | None = None) -> SplitPlotDesign:
    from .modify import _finish
    coded = d.coded.copy()
    coded["RunOrder"] = _randomize(coded, np.random.default_rng(seed))
    return _finish(d, coded.sort_values("RunOrder"), seed=seed)


def create_split_plot_design(
    n_factors: int,
    n_htc: int,
    n_runs: int | None = None,
    *,
    factors: list[Factor] | None = None,
    wp_replicates: int = 2,
    subplot_replicates: int = 1,
    block_on_replicates: bool = False,
    randomize: bool = True,
    seed: int | None = None,
) -> SplitPlotDesign:
    """Minitab 'Create 2-Level Split-Plot Design' 과 같은 설계를 만든다. n_runs 는 기본 설계 런 수(기본: 완전 요인)."""
    opts = available_split_plot(n_factors, n_htc)
    if n_runs is None:
        n_runs = 2 ** n_factors
    opt = next((o for o in opts if o.n_runs == n_runs), None)
    if opt is None:
        raise ValueError(f"{n_factors}요인·HTC {n_htc}개에서 가능한 기본 런 수는 {[o.n_runs for o in opts]} 입니다.")
    if wp_replicates < 1 or subplot_replicates < 1:
        raise ValueError("전구 반복·하위구 반복은 1 이상이어야 합니다.")
    base = create_two_level_design(n_factors, n_runs, factors=factors, randomize=False)
    letters = base.letters
    htc = letters[:n_htc]
    b = base.coded.sort_values("StdOrder").reset_index(drop=True)
    combo = sum(((b[L].values > 0).astype(int) << i) for i, L in enumerate(htc))   # 첫 HTC 요인이 가장 빨리 바뀜
    b["_combo"], b["_base"] = combo, b["StdOrder"].values
    parts = []
    for r in range(wp_replicates):
        for s in range(subplot_replicates):
            c = b[[*letters, "_combo", "_base"]].copy()
            c["_rep"], c["_sub"] = r, s
            parts.append(c)
    coded = pd.concat(parts, ignore_index=True).sort_values(["_rep", "_combo", "_sub", "_base"], kind="stable")
    coded = coded.reset_index(drop=True)
    coded["WP"] = coded["_rep"] * (2 ** n_htc) + coded["_combo"] + 1
    coded["Blocks"] = coded["_rep"] + 1 if block_on_replicates else 1
    coded["PtType"] = 1
    coded["StdOrder"] = np.arange(1, len(coded) + 1)
    rng = np.random.default_rng(seed)
    coded["RunOrder"] = _randomize(coded, rng) if randomize else coded["StdOrder"].values
    coded = coded.sort_values("RunOrder").reset_index(drop=True)
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", "WP", *letters]]
    d = SplitPlotDesign(list(base.factors), pd.DataFrame(), coded, n_htc, n_runs, dict(base.generators), base.alias,
                        wp_replicates if block_on_replicates else 1, wp_replicates, subplot_replicates, seed)
    d.runs = d.rebuild_runs(coded)
    return d
