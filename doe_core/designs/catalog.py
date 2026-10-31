"""2수준 요인설계 카탈로그: Minitab 의 기본 생성자(default generators)와 블록 생성자 표.

출처: Minitab 지원 문서 "Design generators for 2-level designs"(요인 2~15, 런 4~128).
표기: `E=ABCD (E=ABC for 8 blocks) 2(AB)3 4(AB,AC)3 8(AB,AC,AD)3`
  - `X=WORD`      : 추가 요인 X 를 기본 요인들의 곱 WORD 로 정의하는 설계 생성자
  - `n(W1,W2)r`   : 블록 n 개를 만들 때 쓰는 블록 생성자 W1,W2 와 블록 포함 해상도 r
  - `Full`        : 완전 요인설계(생성자 없음)
  - `No blocking` : 블록 설계 불가
요인 문자는 Minitab 관례대로 I 를 건너뛴다(A B C D E F G H J K L M N O P).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .words import LETTERS, ROMAN, ROMAN_INV, resolution_with_blocks_of

# (요인 수, 런 수, 해상도, 생성자 문자열) — 문서 표 그대로. 중복 행(5,16)은 하나만 둔다.
_TABLE_TEXT = """
2 | 4 | - | Full 2(AB)3
3 | 4 | III | C=AB No blocking
3 | 8 | - | Full 2(ABC)4 4(AB,AC)3
4 | 8 | IV | D=ABC 2(AB)3 4(AB,AC)3
4 | 16 | - | Full 2(ABCD)5 4(BC,ABD)3 8(AB,BC,CD)3
5 | 8 | III | D=AB, E=AC 2(BC)3
5 | 16 | V | E=ABCD (E=ABC for 8 blocks) 2(AB)3 4(AB,AC)3 8(AB,AC,AD)3
5 | 32 | - | Full 2(ABCDE)6 4(ABC,CDE)4 8(AC,BD,ADE)3 16(AB,AC,CD,DE)3
6 | 8 | III | D=AB, E=AC, F=BC 2(BE)3
6 | 16 | IV | E=ABC, F=BCD 2(ACD)4 4(AE,ACD)3 8(AB,BC,BF)3
6 | 32 | VI | F=ABCDE 2(ABF)4 4(BC,ABF)3 8(AD,BC,ABF)3 16(AB,BC,CD,DE)3
6 | 64 | - | Full 2(ABCDEF)7 4(ABCF,ABDE)5 8(ACE,ADF,BCF)4 16(AD,BE,CE,ABF)3 32(AB,BC,CD,DE,EF)3
7 | 8 | III | D=AB, E=AC, F=BC, G=ABC no blocking
7 | 16 | IV | E=ABC, F=BCD, G=ACD 2(ABD)4 4(AB,AC)3 8(AB,AC,AD)3
7 | 32 | IV | F=ABCD, G=ABDE 2(CDE)4 4(CF,CDE)3 8(AB,AD,CG)3
7 | 64 | VII | G=ABCDEF 2(CDE)4 4(ACF,CDE)4 8(ACF,ADG,CDE)4 16(AB,AC,EF,EG)3
7 | 128 | - | Full 2(ABCDEFG)8 4(ABDE,ABCFG)5 8(ABC,AFG,DEF)4 16(ABE,ADG,CDE,EFG)4 32(AC,BD,CE,DF,ABG)3 64(AB,BC,CD,DE,EF,FG)3
8 | 16 | IV | E=BCD, F=ACD, G=ABC, H=ABD 2(AB)3 4(AB,AC)3 8(AB,AC,AD)3
8 | 32 | IV | F=ABC, G=ABD, H=BCDE 2(ABE)4 4(EH,ABE)3 8(AB,AC,BD)3
8 | 64 | V | G=ABCD, H=ABEF 2(ACE)4 4(ACE,BDF)4 8(BC,FH,BDF)3 16(BC,DE,FH,BDF)3
8 | 128 | VIII | H=ABCDEFG 2(ABCD)5 4(ABCD,ABEF)5 8(ABCD,ABEF,BCEG)5 16(BF,DE,ABG,AEH)3 32(AC,BD,BF,DE,AEH)3
9 | 16 | III | E=ABC, F=BCD, G=ACD, H=ABD, J=ABCD 2(AB)3 4(AB,AC)3
9 | 32 | IV | F=BCDE, G=ACDE, H=ABDE, J=ABCE 2(AEF)4 4(AB,CD)3 8(AB,AC,CD)3
9 | 64 | IV | G=ABCD, H=ACEF, J=CDEF 2(BCE)4 4(ABF,ACJ)4 8(AD,AH,BDE)3 16(AC,AD,AJ,BF)3
9 | 128 | VI | H=ACDFG, J=BCEFG 2(CDEJ)5 4(ABFJ,CDEJ)5 8(ACF,AHJ,BCJ)4 16(AE,CG,BCJ,BDE)3
10 | 16 | III | E=ABC, F=BCD, G=ACD, H=ABD, J=ABCD, K=AB 2(AC)3 4(AD,AG)3
10 | 32 | IV | F=BCDE, G=ACDE, H=ABDE, J=ABCE 2(AB)3 4(AB,BC)3 8(AB,AC,AH)3
10 | 64 | IV | G=BCDF, H=ACDF, J=ABDE, K=ABCE 2(AGJ)4 4(CD,AGJ)3 8(AG,CJ,CK)3 16(AC,AG,CJ,CK)3
10 | 128 | V | H=ABCG, J=BCDE, K=ACDF 2(ADG)4 4(ADG,BDF)4 8(AEH,AGK,CDH)4 16(BH,EG,JK,ADG)3
11 | 16 | III | E=ABC, F=BCD, G=ACD, H=ABD, J=ABCD, K=AB, L=AC 2(AD)3 4(AE,AH)3
11 | 32 | IV | F=ABC, G=BCD, H=CDE, J=ACD, K=ADE, L=BDE 2(ABD)4 4(AK,ABD)3 8(AB,AC,AD)3
11 | 64 | IV | G=CDE, H=ABCD, J=ABF, K=BDEF, L=ADEF 2(AHJ)4 4(FL,AHJ)3 8(CD,CE,DL)3 16(AB,AC,AE,AF)3
11 | 128 | V | H=ABCG, J=BCDE, K=ACDF 2(ADJ)4 4(ADJ,BFH)4 8(ADJ,AHL,BFH)4 16(BC,DF,GL,BFH)3
12 | 16 | III | E=ABC, F=ABD, G=ACD, H=BCD, J=ABCD, K=AB, L=AC, M=AD 2(AG)3 4(AF,AG)3
12 | 32 | IV | F=ACE, G=ACD, H=ABD, J=ABE, K=CDE, L=ABCDE, M=ADE 2(ABC)4 4(DG,DH)3 8(AB,AC,AD)3
12 | 64 | IV | G=DEF, H=ABC, J=BCDE, K=BCDF, L=ABEF, M=ACEF 2(ABM)4 4(AB,AC)3 8(AB,AC,BM)3 16(AB,AD,BE,BM)3
12 | 128 | IV | H=ACDG, J=ABCD, K=BCFG, L=ABDEFG, M=CDEF 2(ACF)4 4(BG,BJ)3 8(BG,BJ,AGM)3 16(BG,BJ,FM,AGM)3
13 | 16 | III | E=ABC, F=ABD, G=ACD, H=BCD, J=ABCD, K=AB, L=AC, M=AD, N=BC 2(AG)3
13 | 32 | IV | F=ACE, G=BCE, H=ABC, J=CDE, K=ABCDE, L=ABE, M=ACD, N=ADE 2(ABD)4 4(CG,GH)3 8(AB,AC,AD)3
13 | 64 | IV | G=ABC, H=DEF, J=BCDF, K=BCDE, L=ABEF, M=ACEF, N=BCEF 2(AB)3 4(AB,AC)3 8(AB,AC,AN)3 16(AB,AD,BE,BM)3
13 | 128 | IV | H=DEFG, J=BCEG, K=BCDFG, L=ABDEF, M=ACEF, N=ABC 2(ACF)4 4(BG,BJ)3 8(BG,BJ,AGM)3 16(BG,BJ,FM,AGM)3
14 | 16 | III | E=ABC, F=ABD, G=ACD, H=BCD, J=ABCD, K=AB, L=AC, M=AD, N=BC, O=BD 2(AG)3
14 | 32 | IV | F=ABC, G=ABD, H=ABE, J=ACD, K=ACE, L=ADE, M=BCD, N=BCE, O=BDE 2(ACL)4 4(AB,ACL)3 8(AC,AL,AO)3
14 | 64 | IV | G=BEF, H=BCF, J=DEF, K=CEF, L=BCE, M=CDF, N=ACDE, O=BCDEF 2(ABC)4 4(BC,BE)3 8(BC,BE,BG)3 16(AB,BC,BE,BG)3
14 | 128 | IV | H=EFG, J=BCFG, K=BCEG, L=ABEF, M=ACEF, N=BCDEF, O=ABC 2(ADE)4 4(AB,AC)3 8(AB,AC,BM)3 16(AB,AC,BM,DG)3
15 | 16 | III | E=ABC, F=ABD, G=ACD, H=BCD, J=ABCD, K=AB, L=AC, M=AD, N=BC, O=BD, P=CD No blocking
15 | 32 | IV | F=ABC, G=ABD, H=ABE, J=ACD, K=ACE, L=ADE, M=BCD, N=BCE, O=BDE, P=CDE 2(ABP)4 4(AB,BP)3 8(AB,AD,AK)3
15 | 64 | IV | G=ABC, H=ABD, J=ABE, K=ABF, L=ACD, M=ACE, N=ACF, O=ADE, P=ADF 2(ABL)4 4(AM,ABL)3 8(AB,AC,AD)3 16(AB,AC,AD,AE)3
15 | 128 | IV | H=ABFG, J=ACDEF, K=BEF, L=ABCEG, M=CDFG, N=ACDEG, O=EFG, P=ABDEFG 2(ADE)4 4(EG,GP)3 8(EG,GP,OP)3 16(BO,EG,GP,OP)3
"""


@dataclass(frozen=True)
class BlockSpec:
    n_blocks: int
    generators: tuple[str, ...]       # 예: ("AB", "AC")
    resolution_with_blocks: int       # 예: 3


@dataclass(frozen=True)
class CatalogEntry:
    n_factors: int
    n_runs: int
    resolution: int | None            # 완전 요인설계면 None
    generators: dict[str, str]        # 예: {"E": "ABC", "F": "BCD"}; 완전 요인설계면 {}
    alt_generators: dict[int, dict[str, str]] = field(default_factory=dict)  # 블록 수별 대체 생성자(5요인 16런 8블록)
    blocks: dict[int, BlockSpec] = field(default_factory=dict)
    no_blocking: bool = False

    @property
    def is_full(self) -> bool:
        return not self.generators

    @property
    def fraction(self) -> str:
        """'1/4' 같은 분수 표기. 완전 요인설계는 'full'."""
        denom = 2 ** self.n_factors // self.n_runs
        return "full" if denom == 1 else f"1/{denom}"

    def generators_for(self, n_blocks: int) -> dict[str, str]:
        return self.alt_generators.get(n_blocks, self.generators)


_GEN_RE = re.compile(r"([A-HJ-P])\s*=\s*([A-HJ-P]+)")
_BLK_RE = re.compile(r"(\d+)\(([A-HJ-P,]+)\)(\d)")
_ALT_RE = re.compile(r"\(([A-HJ-P])\s*=\s*([A-HJ-P]+)\s+for\s+(\d+)\s+blocks\)")


def _parse_row(line: str) -> CatalogEntry:
    f, r, res, spec = [c.strip() for c in line.split("|")]
    alt: dict[int, dict[str, str]] = {}
    for m in _ALT_RE.finditer(spec):
        alt[int(m.group(3))] = {m.group(1): m.group(2)}
    spec_wo_alt = _ALT_RE.sub(" ", spec)
    head = _BLK_RE.split(spec_wo_alt)[0]  # 블록 지정 앞부분만 생성자 탐색
    gens = {} if head.strip().lower().startswith("full") else dict(_GEN_RE.findall(head))
    blocks = {
        int(n): BlockSpec(int(n), tuple(w.split(",")), int(rr))
        for n, w, rr in _BLK_RE.findall(spec_wo_alt)
    }
    return CatalogEntry(
        n_factors=int(f),
        n_runs=int(r),
        resolution=None if res == "-" else ROMAN_INV[res],
        generators=gens,
        alt_generators=alt,
        blocks=blocks,
        no_blocking="no blocking" in spec.lower(),
    )


def _validate(entry: CatalogEntry, errata: dict) -> CatalogEntry:
    """블록 지정을 생성자와 대조한다. 문서 표의 오류(12요인 행을 복사한 13요인 128런 행 등)를 바로잡는다.

    - 블록 포함 해상도 표기가 계산값과 다르면 계산값으로 고친다.
    - 블록이 주효과와 교락되면(해상도 < III) 그 블록 지정은 제외한다.
    """
    fixed: dict[int, BlockSpec] = {}
    for nb, spec in entry.blocks.items():
        if entry.is_full and not entry.generators_for(nb):
            gens: dict[str, str] = {}
        else:
            gens = entry.generators_for(nb)
        got = resolution_with_blocks_of(gens, list(spec.generators))
        if got < 3:
            errata[(entry.n_factors, entry.n_runs, nb)] = (spec.resolution_with_blocks, got, "dropped")
            continue
        if got != spec.resolution_with_blocks:
            errata[(entry.n_factors, entry.n_runs, nb)] = (spec.resolution_with_blocks, got, "corrected")
            spec = BlockSpec(nb, spec.generators, got)
        fixed[nb] = spec
    return CatalogEntry(entry.n_factors, entry.n_runs, entry.resolution, entry.generators,
                        entry.alt_generators, fixed, entry.no_blocking)


CATALOG: dict[tuple[int, int], CatalogEntry] = {}
CATALOG_ERRATA: dict[tuple[int, int, int], tuple[int, int, str]] = {}  # (요인, 런, 블록) -> (문서값, 계산값, 처리)
for _line in _TABLE_TEXT.strip().splitlines():
    _e = _validate(_parse_row(_line), CATALOG_ERRATA)
    CATALOG[(_e.n_factors, _e.n_runs)] = _e


def available_designs(n_factors: int) -> list[CatalogEntry]:
    """Minitab 'Display Available Designs' 와 같은 내용: 요인 수에 대해 가능한 런 수와 해상도."""
    return sorted((e for (k, _), e in CATALOG.items() if k == n_factors), key=lambda e: e.n_runs)


def lookup(n_factors: int, n_runs: int) -> CatalogEntry:
    try:
        return CATALOG[(n_factors, n_runs)]
    except KeyError:
        runs = [e.n_runs for e in available_designs(n_factors)]
        raise ValueError(f"{n_factors}요인 {n_runs}런 설계는 카탈로그에 없습니다. 가능한 런 수: {runs}") from None
