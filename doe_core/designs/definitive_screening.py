"""확정적 선별설계(DSD) 생성 — Minitab 'Create Screening Design > Definitive Screening'.

구성(Jones & Nachtsheim): 차수 n 의 콘퍼런스 행렬 C(대각 0, 나머지 ±1, CᵀC = (n−1)I)로
[C 의 행 i, −C 의 행 i] 쌍을 차례로 두고 끝에 중앙점을 붙인다. 요인이 n 보다 적으면 뒤쪽 열을 버린다.

문서·예제로 확인한 것
- 런 수(문서 'Available definitive screening designs'): 2–6 요인 13, 7–8 17, 9–10 21, 11–12 25, 13–14 29, 15–16 33,
  17–18 37, 19–20 41, 21–24 49, 25–26 53, 27–30 61, 31–32 65, 33–38 77, 39–42 85, 43–44 89, 45–48 97
  → 쓰는 콘퍼런스 행렬 차수 n = (런 수 − 1)/2 ∈ {6, 8, 10, …, 48}.
- 차수 8 의 행렬은 문서 예제(8요인 2반복 설계표)에서 그대로 복원했고, 7요인 표본 데이터 ultrasonic_cleaner 의
  표준 순서가 이 행렬에서 마지막 열을 뺀 [C 행 i, −C 행 i, …, 중앙점] 순서와 정확히 같다.
- 점 유형: 0 이 있는 런 2(edge), 0 이 없는 런 1, 중앙점 0. 중앙점은 반복당 1개, 텍스트 요인이 있으면 2개(런 1개 추가).
- 텍스트 요인은 2수준만. 블록 수는 반복 수의 약수(블록마다 같은 수의 반복).

문서에 없어 정한 것
- 차수 8 이외의 콘퍼런스 행렬: Paley 구성(q = n − 1 이 소수 또는 9·25)으로 [[0, 1ᵀ], [1, Q]], Q_ij = χ(a_i − a_j).
  차수 16 은 차수 8 의 반대칭형을 두 배로 늘린 [[S, S+I], [S−I, −S]]. 모두 첫 행·첫 열이 + 가 되도록 부호를 맞춘다.
  Minitab 실물 행렬과는 행·열 순서나 부호가 다를 수 있다(설계의 성질은 같음).
- 텍스트 요인 열의 0 은 C 쪽 런에서 +1(높은 수준), −C 쪽 런에서 −1 로 바꾸고, 두 중앙점은 텍스트 요인을
  각각 높은 수준·낮은 수준으로 둔다(반복 안에서 열 합 0 유지).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .common import Factor, assign_orders, default_factors, factor_letters, sign_table, to_levels

DSD_ORDERS = (6, 8, 10, 12, 14, 16, 18, 20, 24, 26, 30, 32, 38, 42, 44, 48)
MAX_FACTORS = 48

# 문서 예제(8요인)에서 복원한 Minitab 의 차수 8 콘퍼런스 행렬(표준 순서의 C 쪽 행)
_C8 = """
0 + + + + + + +
+ 0 + - + - - +
+ - 0 - + + + -
+ + + 0 - + - -
+ - - + 0 + - +
+ + - - - 0 + +
+ + - + + - 0 -
+ - + + - - + 0
"""


def conference_order(n_factors: int) -> int:
    """요인 수에 맞는 콘퍼런스 행렬 차수(문서 런 수 표)."""
    if not 2 <= n_factors <= MAX_FACTORS:
        raise ValueError(f"확정적 선별설계의 요인 수는 2~{MAX_FACTORS} 입니다.")
    return next(n for n in DSD_ORDERS if n >= max(n_factors, 6))


def base_runs_for(n_factors: int, n_text: int = 0) -> int:
    return 2 * conference_order(n_factors) + (2 if n_text else 1)


def _field(q: int):
    """GF(q) 의 원소(0..q−1 정수 부호화)와 뺄셈·곱셈. q 는 소수 또는 p²(p = 3, 5)."""
    for p in (3, 5):
        if q == p * p:
            r = 2                           # x² = 2 가 기약: GF(3) 에서 2 = −1, GF(5) 에서 2 는 비잉여
            def sub(u, v, p=p):
                return (u % p - v % p) % p + p * ((u // p - v // p) % p)

            def mul(u, v, p=p, r=r):
                a, b, c, d = u % p, u // p, v % p, v // p
                return (a * c + b * d * r) % p + p * ((a * d + b * c) % p)
            return list(range(q)), sub, mul
    if q < 2 or any(q % k == 0 for k in range(2, int(q ** 0.5) + 1)):
        raise ValueError(f"Paley 구성을 쓸 수 없는 차수입니다: {q + 1}")
    return list(range(q)), (lambda u, v: (u - v) % q), (lambda u, v: (u * v) % q)


def _paley_core(q: int) -> np.ndarray:
    el, sub, mul = _field(q)
    squares = {mul(u, u) for u in el if u}
    chi = {u: (0 if u == 0 else (1 if u in squares else -1)) for u in el}
    return np.array([[chi[sub(a, b)] for b in el] for a in el], dtype=int)


def _normalize(C: np.ndarray) -> np.ndarray:
    C = C.copy()
    C[:, 1:] *= np.sign(C[0, 1:])
    C[1:, :] *= np.sign(C[1:, 0])[:, None]
    return C


def conference_matrix(n: int) -> np.ndarray:
    """차수 n 의 콘퍼런스 행렬(대각 0, 첫 행·첫 열 +)."""
    if n not in DSD_ORDERS:
        raise ValueError(f"콘퍼런스 행렬 차수는 {DSD_ORDERS} 중 하나입니다.")
    if n == 8:
        return np.array([[{"0": 0, "+": 1, "-": -1}[t] for t in r.split()] for r in _C8.strip().splitlines()])
    if n == 16:
        c8 = conference_matrix(8)
        S = c8.copy()
        S[1:, 0] = -1                                                   # 반대칭형 [[0, 1ᵀ], [−1, Q]]
        eye = np.eye(8, dtype=int)
        return _normalize(np.block([[S, S + eye], [S - eye, -S]]))
    Q = _paley_core(n - 1)
    C = np.zeros((n, n), dtype=int)
    C[0, 1:], C[1:, 0], C[1:, 1:] = 1, 1, Q
    return _normalize(C)


@dataclass
class DefinitiveScreeningDesign:
    factors: list[Factor]
    letters: list[str]
    runs: pd.DataFrame
    coded: pd.DataFrame               # StdOrder, RunOrder, PtType, Blocks, 요인(−1/0/+1)
    order: int                        # 콘퍼런스 행렬 차수
    replicates: int
    n_blocks: int
    seed: int | None = None

    point_col = "PtType"
    folded_on = None

    def rebuild_runs(self, coded: pd.DataFrame) -> pd.DataFrame:
        return to_levels(coded, self.letters, self.factors, self.point_col)

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
    def total_center_points(self) -> int:
        return int((self.coded[self.point_col] == 0).sum())

    @property
    def base_runs(self) -> int:
        return 2 * self.order + (2 if self.n_text_factors else 1)

    def summary(self) -> dict:
        return {"Factors": self.n_factors, "Replicates": self.replicates, "Base runs": self.base_runs,
                "Total runs": self.n_runs, "Base blocks": 1, "Total blocks": self.n_blocks,
                "Center points": self.total_center_points}

    def summary_table(self) -> pd.DataFrame:
        """문서 'Design Summary' 표(4열, 빈 행 다음 Center points)."""
        s = self.summary()
        rows = [["Factors:", str(s["Factors"]), "Replicates:", str(s["Replicates"])],
                ["Base runs:", str(s["Base runs"]), "Total runs:", str(s["Total runs"])],
                ["Base blocks:", str(s["Base blocks"]), "Total blocks:", str(s["Total blocks"])],
                ["", "", "", ""],
                ["Center points:", str(s["Center points"]), "", ""]]
        return pd.DataFrame(rows)

    def summary_text(self) -> str:
        s = self.summary()
        return "\n".join([
            "Design Summary",
            f"Factors: {s['Factors']}  Replicates: {s['Replicates']}",
            f"Base runs: {s['Base runs']}  Total runs: {s['Total runs']}",
            f"Base blocks: {s['Base blocks']}  Total blocks: {s['Total blocks']}",
            "",
            f"Center points: {s['Center points']}",
        ])

    def design_table(self) -> pd.DataFrame:
        """'Design Table (randomized)': Run, Blk, 요인 기호(+/−/0)."""
        tbl = pd.DataFrame(sign_table(self.coded, self.letters), columns=self.letters)
        tbl.insert(0, "Blk", self.coded["Blocks"].values)
        tbl.insert(0, "Run", self.coded["RunOrder"].values)
        return tbl


def base_matrix(n_factors: int, text: list[bool] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """반복 하나의 코드 행렬(표준 순서)과 점 유형. text[j] 가 참인 열은 텍스트 요인."""
    text = list(text) if text is not None else [False] * n_factors
    n = conference_order(n_factors)
    C = conference_matrix(n)[:, :n_factors]
    rows = []
    for i in range(n):
        up, down = C[i].copy(), -C[i]
        for j in range(n_factors):
            if text[j] and up[j] == 0:
                up[j], down[j] = 1, -1
        rows += [up, down]
    numeric = ~np.array(text, dtype=bool)
    M = np.array(rows, dtype=int)
    pt = np.where((M[:, numeric] == 0).any(axis=1), 2, 1)
    centers = [np.where(text, 1, 0)] + ([np.where(text, -1, 0)] if any(text) else [])
    M = np.vstack([M, np.array(centers, dtype=int)])
    pt = np.concatenate([pt, np.zeros(len(centers), dtype=int)])
    return M, pt


def create_definitive_screening(
    n_factors: int,
    *,
    factors: list[Factor] | None = None,
    replicates: int = 1,
    n_blocks: int = 1,
    randomize: bool = True,
    seed: int | None = None,
) -> DefinitiveScreeningDesign:
    """Minitab 'Create Screening Design(Definitive Screening)' 과 같은 설계를 만든다."""
    if factors is None:
        factors = default_factors(n_factors)
    if len(factors) != n_factors:
        raise ValueError("factors 길이가 n_factors 와 다릅니다.")
    if replicates < 1:
        raise ValueError("반복 수는 1 이상이어야 합니다.")
    if n_blocks < 1 or replicates % n_blocks:
        raise ValueError("블록 수는 반복 수의 약수여야 합니다(블록마다 같은 수의 반복).")
    letters = factor_letters(n_factors)
    M, pt = base_matrix(n_factors, [not f.is_numeric for f in factors])
    per_block = replicates // n_blocks
    parts = []
    for r in range(replicates):
        c = pd.DataFrame(M, columns=letters)
        c["PtType"], c["Blocks"], c["_rep"], c["_order"] = pt, r // per_block + 1, r, np.arange(len(M))
        parts.append(c)
    coded = assign_orders(pd.concat(parts, ignore_index=True), ["Blocks", "_rep", "_order"],
                          randomize=randomize, seed=seed)
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", *letters]]
    return DefinitiveScreeningDesign(factors, letters, to_levels(coded, letters, factors, "PtType"), coded,
                                     conference_order(n_factors), replicates, n_blocks, seed)
