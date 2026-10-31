"""2수준 (부분)요인설계 생성 — Minitab 'Create Factorial Design (2-level, default/specify generators)' 에 해당.

용어
- 단어(word): 요인들의 곱(예: ABCE). 내부적으로는 요인 인덱스 비트마스크 int 로 다룬다(words.py).
- 정의관계(defining relation): 생성자 단어들이 만드는 군. I = ABCE = ADEF = BCDF …
- 별칭(alias) 사슬: 효과 e 에 대한 잉여류 {e·w : w ∈ 정의관계}. 가장 낮은 차수(동률이면 알파벳순) 단어가 대표.
- 해상도: 정의관계의 최단 단어 길이. 블록 포함 해상도: 블록과 교락된 최단 단어 길이 + 1.

Minitab 규칙(문서 근거는 docs/spec/A_factorial_create.md)
- 요인 문자는 I 를 건너뛴다. 워크시트 열: StdOrder, RunOrder, CenterPt(1=모서리, 0=중앙점), Blocks, 요인열.
- 중앙점은 블록마다 지정 수를 더하고, 텍스트 요인이 Q 개면 텍스트 수준 조합마다 더해 2^Q 배가 된다.
- 블록 수가 반복 수의 배수이면 반복이 곧 블록이 되고(생성자 불필요), 그 외에는 블록 생성자로 나눈다.
- 랜덤화는 블록 안에서만 하고 블록은 순서대로 둔다. 표준 순서(StdOrder)는 블록별로 묶은 뒤 1부터 매긴다.
- 별칭표 기본 차수 상한: 요인 ≤7 전부, 8~10 은 3차까지, 11~15 는 2차까지.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd

from .catalog import CATALOG, CatalogEntry
from .words import (
    LETTERS, ROMAN, generator_words, resolution_of, resolution_with_blocks_of, span,
    word_from_str, word_key as _word_key, word_len, word_to_str,
)

__all__ = ["Factor", "TwoLevelDesign", "AliasStructure", "alias_structure", "create_two_level_design",
           "default_alias_order", "resolution_of", "resolution_with_blocks_of", "word_from_str", "word_to_str"]


def default_alias_order(n_factors: int) -> int | None:
    """Minitab 'Default interactions': ≤7요인 전부(None), 8~10요인 3차까지, 11~15요인 2차까지."""
    if n_factors <= 7:
        return None
    return 3 if n_factors <= 10 else 2


# ---------------------------------------------------------------- 별칭 구조


@dataclass
class AliasStructure:
    n_factors: int
    defining: list[int]                     # 정의관계 단어(I 제외), 정렬됨
    block_words: list[int]                  # 블록 생성자 군(I 제외)
    chains: list[list[int]]                 # 추정 가능한 효과의 별칭 사슬(대표 순 정렬)
    block_chains: list[list[int]]           # Blk1, Blk2 … 사슬

    @property
    def resolution(self) -> int | None:
        return min((word_len(w) for w in self.defining), default=None)

    @property
    def resolution_with_blocks(self) -> int | None:
        if not self.block_chains:
            return None
        return min(word_len(w) for ch in self.block_chains for w in ch) + 1

    @property
    def is_free(self) -> bool:
        return not self.defining and not self.block_chains

    def lines(self, max_order: int | None = None) -> list[str]:
        """Minitab 'Alias Structure' 와 같은 줄 목록.

        max_order: 표시할 항의 최대 차수. 사슬은 대표 차수가 그 이하인 것만 남기고, 사슬 안에서도 그 차수 이하
        단어만 남긴다(혼자 남으면 단독 표기). None 이면 전부.
        """
        def fmt(chain: list[int]) -> str:
            words = chain if max_order is None else [w for w in chain if word_len(w) <= max_order]
            return " + ".join(word_to_str(w) for w in (words or chain[:1]))

        out = ["I" + "".join(f" + {word_to_str(w)}" for w in self.defining)]
        for i, ch in enumerate(self.block_chains, 1):
            out.append(f"Blk{i} = " + fmt(ch))
        for ch in self.chains:
            if max_order is not None and word_len(ch[0]) > max_order:
                continue
            out.append(fmt(ch))
        return out

    def text(self, max_order: int | None = "default") -> str:
        if self.is_free:
            return "Alias Structure\nAll terms are free from aliasing."
        if max_order == "default":
            max_order = default_alias_order(self.n_factors)
        title = "Alias Structure" if max_order is None or max_order >= self.n_factors else f"Alias Structure (up to order {max_order})"
        return title + "\n" + "\n".join(self.lines(max_order))


def alias_structure(n_factors: int, generator_words_: list[int], block_generator_words: list[int] | None = None) -> AliasStructure:
    """정의관계와 모든 잉여류(별칭 사슬)를 계산한다."""
    defining = span(generator_words_)
    dset = set(defining) | {0}
    block_group = span(block_generator_words or [])
    block_chains: list[list[int]] = []
    block_cover: set[int] = set()
    for bw in block_group:
        chain = sorted({bw ^ w for w in dset}, key=_word_key)
        block_chains.append(chain)
        block_cover |= set(chain)
    seen: set[int] = set()
    chains: list[list[int]] = []
    for e in range(1, 1 << n_factors):
        if e in dset or e in block_cover or e in seen:
            continue
        chain = sorted({e ^ w for w in dset}, key=_word_key)
        seen |= set(chain)
        chains.append(chain)
    chains.sort(key=lambda ch: _word_key(ch[0]))
    return AliasStructure(n_factors, defining, block_group, chains, block_chains)


# ---------------------------------------------------------------- 설계 생성


@dataclass
class Factor:
    name: str
    low: float | str = -1
    high: float | str = 1
    numeric: bool = True

    @property
    def is_numeric(self) -> bool:
        return self.numeric and isinstance(self.low, (int, float)) and isinstance(self.high, (int, float))


@dataclass
class TwoLevelDesign:
    factors: list[Factor]
    runs: pd.DataFrame                       # StdOrder, RunOrder, CenterPt, Blocks, 요인열(실제 수준값), RunOrder 순
    coded: pd.DataFrame                      # 같은 행 순서, 요인열은 -1/0/+1 코드(열 이름은 A,B,…)
    entry: CatalogEntry | None
    base_runs: int
    generators: dict[str, str]
    block_generators: tuple[str, ...]
    alias: AliasStructure
    n_blocks: int
    center_points_per_block: int
    replicates: int
    seed: int | None = None

    @property
    def n_factors(self) -> int:
        return len(self.factors)

    @property
    def n_runs(self) -> int:
        return len(self.runs)

    @property
    def n_text_factors(self) -> int:
        return sum(not f.is_numeric for f in self.factors)

    @property
    def fraction(self) -> str:
        denom = 2 ** self.n_factors // self.base_runs
        return "full" if denom == 1 else f"1/{denom}"

    @property
    def resolution_text(self) -> str:
        r = self.alias.resolution
        return "Full" if r is None else ROMAN.get(r, str(r))

    def summary(self) -> dict:
        """Minitab 'Design Summary' 의 항목(순서 포함)."""
        d = {
            "Factors": self.n_factors,
            "Base Design": f"{self.n_factors}, {self.base_runs}",
            "Runs": self.n_runs,
            "Replicates": self.replicates,
            "Blocks": self.n_blocks,
            "Center pts (total)": int((self.runs["CenterPt"] == 0).sum()),
        }
        if self.alias.block_chains:
            d["Resolution with blocks"] = ROMAN.get(self.alias.resolution_with_blocks, str(self.alias.resolution_with_blocks))
        elif self.alias.resolution is not None:
            d["Resolution"] = self.resolution_text
        if self.generators:
            d["Fraction"] = self.fraction
            d["Design Generators"] = ", ".join(f"{k} = {v}" for k, v in self.generators.items())
        if self.block_generators:
            d["Block Generators"] = ", ".join(self.block_generators)
        return d

    def notes(self) -> list[str]:
        out = []
        if self.alias.resolution == 3:
            out.append("* NOTE * Some main effects are confounded with two-way interactions.")
        if self.alias.block_chains and self.alias.resolution_with_blocks == 3:
            out.append("* NOTE * Blocks are confounded with two-way interactions.")
        if self.center_points_per_block and self.n_text_factors:
            out.append("* NOTE * The number of centerpoints specified is doubled for each categorical factor. "
                       "For Q categorical factors, the result is 2^Q times as many centerpoints.")
        return out

    def summary_text(self) -> str:
        s = self.summary()
        lines = ["Design Summary"]
        lines += [f"{k}: {v}" for k, v in s.items() if k not in ("Design Generators", "Block Generators")]
        lines += self.notes()
        for k in ("Design Generators", "Block Generators"):
            if k in s:
                lines.append(f"{k}: {s[k]}")
        return "\n".join(lines)

    def alias_text(self, max_order: int | None = "default") -> str:
        return self.alias.text(max_order)


def _yates_matrix(k: int) -> np.ndarray:
    """k 개 기본 요인의 2^k 완전 요인설계, 표준(Yates) 순서. A 가 가장 빨리 바뀐다. 값은 -1/+1."""
    n = 1 << k
    return np.array([[1 if (i >> j) & 1 else -1 for j in range(k)] for i in range(n)], dtype=int)


def create_two_level_design(
    n_factors: int,
    n_runs: int | None = None,
    *,
    fraction: str | None = None,
    generators: dict[str, str] | None = None,
    factors: list[Factor] | None = None,
    n_blocks: int = 1,
    block_generators: list[str] | None = None,
    center_points: int = 0,
    replicates: int = 1,
    randomize: bool = True,
    seed: int | None = None,
) -> TwoLevelDesign:
    """Minitab 'Create 2-Level Factorial Design' 과 같은 설계를 만든다.

    n_runs 또는 fraction('1/2', '1/4', …, 'full') 로 기본 설계를 고른다. generators 를 주면(Specify Generators)
    카탈로그 대신 그 생성자를 쓴다. center_points 는 '블록당 중앙점 수'. n_blocks 가 replicates 의 배수이면
    반복이 블록이 되고, 그렇지 않으면 블록 생성자(카탈로그 또는 block_generators)로 나눈다.
    """
    if not 2 <= n_factors <= 15:
        raise ValueError("요인 수는 2~15 이어야 합니다.")
    if factors is None:
        factors = [Factor(LETTERS[i]) for i in range(n_factors)]
    if len(factors) != n_factors:
        raise ValueError("factors 길이가 n_factors 와 다릅니다.")
    if replicates < 1 or center_points < 0 or n_blocks < 1:
        raise ValueError("replicates ≥ 1, center_points ≥ 0, n_blocks ≥ 1 이어야 합니다.")

    # --- 기본 설계의 런 수
    if n_runs is None:
        denom = 1 if fraction in (None, "full") else int(fraction.split("/")[1])
        n_runs = 2 ** n_factors // denom
    k = int(np.log2(n_runs))
    if 1 << k != n_runs or k < 1:
        raise ValueError("런 수는 2의 거듭제곱이어야 합니다.")
    n_added = n_factors - k
    if n_added < 0:
        raise ValueError("런 수가 2^요인수 보다 큽니다.")
    entry = CATALOG.get((n_factors, n_runs))

    # --- 블록 구성: 블록 수가 반복 수의 배수이면 반복이 블록이 되고(남는 배수는 생성자로),
    #     아니면 모든 반복에 같은 블록 생성자를 적용한다(블록 1개면 전부 블록 1).
    block_on_reps = replicates > 1 and n_blocks > 1 and n_blocks % replicates == 0
    blocks_per_rep = n_blocks // replicates if block_on_reps else n_blocks
    if blocks_per_rep & (blocks_per_rep - 1):
        raise ValueError("블록 수(반복당)는 1, 2, 4, 8, … 이어야 합니다.")

    # --- 생성자
    if generators is None:
        if n_added == 0:
            generators = {}
        elif entry is None:
            raise ValueError(f"{n_factors}요인 {n_runs}런 기본 생성자가 카탈로그에 없습니다. generators 를 직접 지정하세요.")
        else:
            generators = entry.generators_for(blocks_per_rep)
    if len(generators) != n_added:
        raise ValueError(f"생성자 수({len(generators)})가 추가 요인 수({n_added})와 다릅니다.")

    # --- 블록 생성자
    if blocks_per_rep > 1 and block_generators is None:
        if entry is None or blocks_per_rep not in entry.blocks:
            raise ValueError(f"{n_factors}요인 {n_runs}런 설계에서 반복당 블록 {blocks_per_rep}개는 카탈로그에 없습니다. block_generators 를 지정하세요.")
        block_generators = list(entry.blocks[blocks_per_rep].generators)
    block_generators = tuple(block_generators or ()) if blocks_per_rep > 1 else ()
    if len(block_generators) != int(np.log2(blocks_per_rep)):
        raise ValueError("블록 생성자 수는 log2(반복당 블록 수) 이어야 합니다.")

    # --- 설계 행렬(코드값), 표준 순서
    base = _yates_matrix(k)
    cols = {LETTERS[i]: base[:, i] for i in range(k)}
    for added_letter, word in generators.items():
        cols[added_letter] = np.prod([cols[ch] for ch in word], axis=0)
    letters = LETTERS[:n_factors]
    corner = pd.DataFrame({L: cols[L] for L in letters})

    if block_generators:
        signs = np.stack([np.prod([corner[ch].values for ch in w], axis=0) for w in block_generators], axis=1)
        bits = (signs == -1).astype(int)
        block_in_rep = 1 + sum(bits[:, i] << (len(block_generators) - 1 - i) for i in range(len(block_generators)))
    else:
        block_in_rep = np.ones(len(corner), dtype=int)
    corner["Blocks"] = block_in_rep
    corner["CenterPt"] = 1
    corner["_yates"] = np.arange(len(corner))

    # --- 반복: 반복이 블록이면 블록 번호를 이어 붙인다
    reps = []
    for r in range(replicates):
        c = corner.copy()
        if block_on_reps:
            c["Blocks"] = c["Blocks"] + r * blocks_per_rep
        c["_rep"] = r
        reps.append(c)
    coded = pd.concat(reps, ignore_index=True)

    # --- 중앙점: 최종 블록마다 center_points 개, 텍스트 요인 수준 조합(2^Q)마다. 반복 수와 무관.
    numeric = [f.is_numeric for f in factors]
    if center_points and not any(numeric):
        raise ValueError("모든 요인이 텍스트이면 중앙점을 추가할 수 없습니다.")
    if center_points:
        text_letters = [L for L, isnum in zip(letters, numeric) if not isnum]
        cps = []
        for b in sorted(coded["Blocks"].unique()):
            for combo in product((-1, 1), repeat=len(text_letters)):
                cp = pd.DataFrame({L: [0] * center_points for L in letters})
                for L, v in zip(text_letters, combo):
                    cp[L] = v
                cp["Blocks"] = b
                cp["CenterPt"] = 0
                cp["_yates"] = np.arange(len(corner), len(corner) + center_points)
                cp["_rep"] = replicates  # 같은 블록의 모서리점 뒤에 오도록
                cps.append(cp)
        coded = pd.concat([coded, *cps], ignore_index=True)

    # --- 표준 순서: 블록 → 반복 → Yates 순(중앙점은 모서리점 뒤)
    coded = coded.sort_values(["Blocks", "_rep", "_yates"], kind="stable").reset_index(drop=True)
    coded.insert(0, "StdOrder", np.arange(1, len(coded) + 1))

    # --- 런 순서: 블록 안에서 랜덤화, 블록은 순서대로
    rng = np.random.default_rng(seed)
    run_order = np.empty(len(coded), dtype=int)
    pos = 0
    for b in sorted(coded["Blocks"].unique()):
        idx = np.where(coded["Blocks"].values == b)[0]
        perm = rng.permutation(idx) if randomize else idx
        run_order[perm] = np.arange(pos + 1, pos + len(idx) + 1)
        pos += len(idx)
    coded.insert(1, "RunOrder", run_order)
    coded = coded.sort_values("RunOrder").reset_index(drop=True)
    coded = coded[["StdOrder", "RunOrder", "CenterPt", "Blocks", *letters]]

    # --- 실제 수준값 워크시트
    runs = coded[["StdOrder", "RunOrder", "CenterPt", "Blocks"]].copy()
    for L, f in zip(letters, factors):
        c = coded[L].values
        if f.is_numeric:
            mid = (float(f.low) + float(f.high)) / 2
            runs[f.name] = np.where(c == -1, float(f.low), np.where(c == 1, float(f.high), mid))
        else:
            runs[f.name] = np.where(c == -1, f.low, f.high)

    alias = alias_structure(n_factors, generator_words(generators), [word_from_str(w) for w in block_generators])
    return TwoLevelDesign(
        factors=factors, runs=runs, coded=coded, entry=entry, base_runs=n_runs, generators=dict(generators),
        block_generators=block_generators, alias=alias, n_blocks=n_blocks, center_points_per_block=center_points,
        replicates=replicates, seed=seed,
    )
