"""혼합물 설계 — Minitab 'Create Mixture Design'(단순 중심, 단순 격자, 극꼭지점 + 공정 변수).

문서 근거(docs/spec/C_rsm_mixture_optimal.md 4절)
- 단순 중심(simplex centroid): q 성분의 2^q − 1 점(부분집합 S 의 성분을 1/|S| 씩). 기본으로 축점 증강.
- 단순 격자(simplex lattice, 차수 m): 비율 {0, 1/m, …, 1} 로 합이 1 인 점. 기본으로 중앙점·축점 증강.
  차수별 성분 수 한계: m=1·2 → 2~20, 3 → 2~17, 4 → 2~11, 5 → 2~8, 6 → 2~7, 7 → 2~6, 8~10 → 2~5.
- 극꼭지점(extreme vertices, 차수 d): 성분 하한·상한과 선형 제약(최대 10개)으로 정의된 영역의 꼭지점,
  d ≥ 2 이면 모서리 중심, d ≥ 3 이면 2차원 면 중심까지. 기본으로 중앙점(꼭지점 평균)·축점 증강.
- 축점 = 꼭지점과 설계 중심의 중간. 중앙점은 기본 설계에 없을 때만 추가.
- 단순 설계에 성분 하한이 있으면 유사성분(pseudocomponent) 공간에서 만든 뒤 비율로 바꾼다.
  pseudo = (비율 − 하한) / (1 − 하한 합), 비율 = pseudo·(1 − 하한 합) + 하한.
- 점 유형(PtType): 비제약 설계는 0 아닌 성분 수(중심 0, 축점 −1), 제약 설계는 꼭지점 1, 모서리 중심 2,
  면 중심 3, 중심 0, 축점 −1.
- 공정 변수: 최대 7개의 2수준 변수(X1 …). 공정 변수 조합마다 혼합물 점 전체를 둔다(코드 −1/+1).
- 성분 문자는 알파벳 순서로 I·T 를 건너뛴다(문서: T 를 건너뜀, 다른 설계와 같이 I 도 건너뜀).
- 표준 순서: 공정 변수 조합(첫 변수가 가장 빨리 바뀜) 안에서 꼭지점 → 모서리 중심 → … → 중심 → 축점,
  같은 유형 안에서는 성분 순서(문서 예제 1 워크시트로 확인).

문서에 없거나 문서와 다를 수 있는 것
- 극꼭지점의 'Number of Boundaries' 표: 문서 예제(꼭지점 5·모서리 5)는 퇴화 꼭지점을 중복으로 센 값으로 보인다.
  여기서는 기하학적으로 서로 다른 꼭지점·면만 센다(같은 예제에서 4·4). 설계점·중심·축점은 문서와 같다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
from math import comb

import numpy as np
import pandas as pd

from .common import Factor, assign_orders

MIX_ALPHABET = "ABCDEFGHJKLMNOPQRSUVWXYZ"   # I, T 제외
LATTICE_MAX_Q = {1: 20, 2: 20, 3: 17, 4: 11, 5: 8, 6: 7, 7: 6, 8: 5, 9: 5, 10: 5}
_TOL = 1e-9


def mix_letters(q: int) -> list[str]:
    if q > len(MIX_ALPHABET):
        raise ValueError(f"성분은 최대 {len(MIX_ALPHABET)}개입니다.")
    return list(MIX_ALPHABET[:q])


@dataclass
class Component:
    name: str
    lower: float = 0.0
    upper: float = 1.0


@dataclass
class LinearConstraint:
    coefs: dict                     # 성분 이름 또는 문자 → 계수
    lower: float | None = None
    upper: float | None = None


@dataclass
class MixtureDesign:
    kind: str                        # "simplex_centroid" | "simplex_lattice" | "extreme_vertices" | "custom"
    components: list[Component]
    letters: list[str]
    process: list[Factor]
    runs: pd.DataFrame
    coded: pd.DataFrame              # StdOrder, RunOrder, PtType, Blocks, 성분 비율, X1… (−1/+1)
    degree: int | None               # 사용자 정의 설계는 None
    total: float
    constraints: list[LinearConstraint]
    constrained: bool
    replicates: int
    boundaries: list[int]            # 차원 0, 1, …, q−1 경계 수
    n_blocks: int = 1
    seed: int | None = None
    point_col: str = "PtType"
    folded_on = None

    # 설계 공통 인터페이스(분석·저장)
    @property
    def factors(self) -> list:
        return list(self.components) + list(self.process)

    @property
    def process_letters(self) -> list[str]:
        return [f"X{i + 1}" for i in range(len(self.process))]

    @property
    def n_runs(self) -> int:
        return len(self.runs)

    @property
    def q(self) -> int:
        return len(self.components)

    @property
    def lower_sum(self) -> float:
        return float(sum(c.lower for c in self.components))

    def rebuild_runs(self, coded: pd.DataFrame) -> pd.DataFrame:
        runs = coded[["StdOrder", "RunOrder", self.point_col, "Blocks"]].copy()
        for L, c in zip(self.letters, self.components):
            runs[c.name] = coded[L].astype(float) * self.total
        for X, f in zip(self.process_letters, self.process):
            v = coded[X].values
            if f.is_numeric:
                runs[f.name] = np.where(v < 0, float(f.low), float(f.high))
            else:
                runs[f.name] = np.where(v < 0, f.low, f.high)
        return runs

    # ------------------------------------------------------------ 출력
    def point_type_columns(self) -> list[int]:
        return [*range(1, self.q + 1), 0, -1]

    def summary(self) -> dict:
        d = {"Components": self.q, "Design points": self.n_runs, "Process variables": len(self.process)}
        if self.degree is not None:
            d["Lattice degree" if self.kind == "simplex_lattice" else "Design degree"] = self.degree
        d["Mixture total"] = self.total
        return d

    def summary_text(self) -> str:
        s = self.summary()
        deg_key = "Lattice degree" if self.kind == "simplex_lattice" else "Design degree"
        deg = f"  {deg_key}: {s[deg_key]}" if deg_key in s else ""
        return "\n".join([
            "Design Summary",
            f"Components: {s['Components']}  Design points: {s['Design points']}",
            f"Process variables: {s['Process variables']}{deg}",
            f"Mixture total: {self.total:.5f}",
        ])

    def boundaries_table(self) -> pd.DataFrame:
        q = self.q
        if not self.boundaries:
            return pd.DataFrame(columns=["Point Type"])
        types = [str(d + 1) if d < q - 1 else "0" for d in range(q)]
        return pd.DataFrame([["Dimension", *[str(d) for d in range(q)]], ["Number", *[str(n) for n in self.boundaries]]],
                            columns=["Point Type", *types])

    def points_table(self) -> pd.DataFrame:
        cols = self.point_type_columns()
        pt = self.coded[self.point_col]
        mix_cols = list(self.letters) + self.process_letters
        distinct, reps, total = [], [], []
        for t in cols:
            g = self.coded[pt == t][mix_cols].round(9)
            n_total = len(g)
            n_distinct = len(g.drop_duplicates())
            distinct.append(n_distinct)
            total.append(n_total)
            reps.append(n_total // n_distinct if n_distinct else 0)
        return pd.DataFrame([["Distinct", *map(str, distinct)], ["Replicates", *map(str, reps)],
                             ["Total number", *map(str, total)]], columns=["Point Type", *map(str, cols)])

    def bounds_table(self, decimals: int = 5) -> pd.DataFrame:
        f = lambda v: f"{v:.{decimals}f}"  # noqa: E731
        rows = []
        ls = self.lower_sum
        for L, c in zip(self.letters, self.components):
            pu = (c.upper - c.lower) / (1 - ls) if ls < 1 else float("nan")
            rows.append([L, f(c.lower * self.total), f(c.upper * self.total), f(c.lower), f(c.upper), f(0.0), f(pu)])
        return pd.DataFrame(rows, columns=["Comp", "Amount Lower", "Amount Upper", "Proportion Lower",
                                           "Proportion Upper", "Pseudocomponent Lower", "Pseudocomponent Upper"])

    def constraints_table(self, decimals: int = 5) -> pd.DataFrame:
        f = lambda v: "" if v is None else f"{v:.{decimals}f}"  # noqa: E731
        rows = []
        for i, lc in enumerate(self.constraints, 1):
            coefs = _resolve_coefs(lc.coefs, self.components, self.letters)
            rows.append([str(i), f(lc.lower), *[f(coefs[j]) for j in range(self.q)], f(lc.upper)])
        return pd.DataFrame(rows, columns=["Constraint", "Lower", *self.letters, "Upper"])

    def design_table(self, decimals: int = 5) -> pd.DataFrame:
        tbl = pd.DataFrame({"Run": self.coded["RunOrder"].values, "Type": self.coded[self.point_col].values})
        for L in self.letters:
            tbl[L] = [f"{v * self.total:.{decimals}f}" for v in self.coded[L].values]
        for X in self.process_letters:
            tbl[X] = self.coded[X].astype(int).values
        return tbl


# ---------------------------------------------------------------- 기하: 꼭지점·면 열거


def _resolve_coefs(coefs: dict, comps: list[Component], letters: list[str]) -> np.ndarray:
    a = np.zeros(len(comps))
    names = [c.name for c in comps]
    for k, v in coefs.items():
        if k in letters:
            a[letters.index(k)] = float(v)
        elif k in names:
            a[names.index(k)] = float(v)
        else:
            raise ValueError(f"선형 제약의 성분 {k!r} 이 없습니다.")
    return a


def _inequalities(comps, letters, constraints) -> tuple[np.ndarray, np.ndarray]:
    """G p ≤ h 형태의 부등식 목록."""
    q = len(comps)
    G, h = [], []
    for i, c in enumerate(comps):
        e = np.zeros(q)
        e[i] = 1
        G.append(-e)
        h.append(-c.lower)
        G.append(e)
        h.append(c.upper)
    for lc in constraints:
        a = _resolve_coefs(lc.coefs, comps, letters)
        if lc.lower is not None:
            G.append(-a)
            h.append(-lc.lower)
        if lc.upper is not None:
            G.append(a)
            h.append(lc.upper)
    return np.array(G), np.array(h)


def _vertices(G: np.ndarray, h: np.ndarray, q: int):
    """합 = 1 과 활성 부등식 q−1 개를 풀어 꼭지점을 찾는다. (꼭지점 배열, 꼭지점별 활성 부등식 집합)"""
    if comb(len(G), q - 1) > 3_000_000:
        raise ValueError("제약이 너무 많아 꼭지점을 열거할 수 없습니다.")
    found: list[np.ndarray] = []
    for idx in combinations(range(len(G)), q - 1):
        A = np.vstack([np.ones(q), G[list(idx)]])
        b = np.concatenate([[1.0], h[list(idx)]])
        if abs(np.linalg.det(A)) < 1e-12:
            continue
        p = np.linalg.solve(A, b)
        if np.all(G @ p <= h + 1e-9):
            p = np.where(np.abs(p) < 1e-12, 0.0, p)
            if not any(np.allclose(p, v, atol=1e-9) for v in found):
                found.append(p)
    if not found:
        raise ValueError("제약을 모두 만족하는 혼합물 영역이 없습니다.")
    V = np.array(found)
    active = [frozenset(np.where(np.abs(G @ v - h) < 1e-9)[0]) for v in V]
    return V, active


def _affine_dim(P: np.ndarray) -> int:
    if len(P) <= 1:
        return 0
    return int(np.linalg.matrix_rank(P[1:] - P[0], tol=1e-9))


def _faces(V: np.ndarray, active: list[frozenset], q: int) -> dict[int, list[frozenset]]:
    """차원별 면(꼭지점 인덱스 집합). 활성 부등식 부분집합의 공통 꼭지점으로 면을 찾는다."""
    cons = sorted(set().union(*active))
    faces: dict[int, set] = {d: set() for d in range(q)}
    faces[q - 1].add(frozenset(range(len(V))))
    for s in range(1, q):
        for S in combinations(cons, s):
            vs = frozenset(i for i, a in enumerate(active) if set(S) <= a)
            if vs:
                faces[_affine_dim(V[sorted(vs)])].add(vs)
    return {d: sorted(f, key=sorted) for d, f in faces.items()}


# ---------------------------------------------------------------- 점 생성


def _simplex_centroid_points(q: int):
    pts, types = [], []
    for r in range(1, q + 1):
        for S in combinations(range(q), r):
            p = np.zeros(q)
            p[list(S)] = 1.0 / r
            pts.append(p)
            types.append(0 if r == q else r)
    return pts, types


def _lattice_points(q: int, m: int):
    pts, types = [], []
    for counts in product(range(m + 1), repeat=q):
        if sum(counts) != m:
            continue
        p = np.array(counts, dtype=float) / m
        nz = int((p > 0).sum())
        pts.append(p)
        types.append(0 if nz == q and np.allclose(p, 1 / q) else nz)
    order = sorted(range(len(pts)), key=lambda i: (types[i] if types[i] > 0 else 99, [-x for x in pts[i]]))
    return [pts[i] for i in order], [types[i] for i in order]


def _type_rank(t: int) -> int:
    return {0: 900, -1: 1000}.get(t, t)


def _build(kind, comps, letters, process, base_pts, base_types, *, degree, total, constraints, constrained,
           boundaries, replicates, type_replicates, randomize, seed) -> MixtureDesign:
    # 공정 변수 조합(첫 변수가 가장 빨리 바뀜)
    k = len(process)
    combos = [tuple(reversed(c)) for c in product((-1, 1), repeat=k)] if k else [()]
    xs = [f"X{i + 1}" for i in range(k)]
    order = sorted(range(len(base_pts)), key=lambda i: (_type_rank(base_types[i]), i))
    rows = []
    n = 0
    for rep in range(replicates):
        for ci, combo in enumerate(combos):
            for i in order:
                t = base_types[i]
                times = 1 + (type_replicates.get(t, 1) - 1 if type_replicates else 0)
                for _ in range(times):
                    row = {"PtType": t, "Blocks": 1, "_order": n}
                    row.update(dict(zip(letters, base_pts[i])))
                    row.update(dict(zip(xs, combo)))
                    rows.append(row)
                    n += 1
    coded = pd.DataFrame(rows)
    coded["_rep"] = 0
    coded = assign_orders(coded, ["Blocks", "_order"], randomize=randomize, seed=seed)
    coded = coded[["StdOrder", "RunOrder", "PtType", "Blocks", *letters, *xs]]
    d = MixtureDesign(kind, comps, letters, list(process), pd.DataFrame(), coded, degree, total, list(constraints),
                      constrained, replicates, boundaries, 1, seed)
    d.runs = d.rebuild_runs(coded)
    return d


def _prepare_components(q, components):
    if components is None:
        components = [Component(L) for L in mix_letters(q)]
    if len(components) != q:
        raise ValueError("components 길이가 성분 수와 다릅니다.")
    if not 2 <= q <= 20:
        raise ValueError("성분 수는 2~20 입니다.")
    for c in components:
        if not 0 <= c.lower < c.upper <= 1 + _TOL:
            raise ValueError(f"성분 {c.name}: 0 ≤ 하한 < 상한 ≤ 1 이어야 합니다(비율 기준).")
    if sum(c.lower for c in components) >= 1:
        raise ValueError("성분 하한의 합은 1 보다 작아야 합니다.")
    return components


def _check_process(process):
    process = list(process or [])
    if len(process) > 7:
        raise ValueError("공정 변수는 최대 7개입니다.")
    return process


def _to_proportions(p_pseudo: np.ndarray, comps: list[Component]) -> np.ndarray:
    L = np.array([c.lower for c in comps])
    return p_pseudo * (1 - L.sum()) + L


def _augment(pts, types, *, center: bool, axial: bool, constrained: bool, vertices: np.ndarray):
    pts, types = list(pts), list(types)
    centroid = vertices.mean(axis=0)
    has_center = any(np.allclose(p, centroid, atol=1e-9) for p in pts)
    if center and not has_center:
        pts.append(centroid)
        types.append(0)
    if axial:
        for v in vertices:
            pts.append((v + centroid) / 2)
            types.append(-1)
    return pts, types


def create_simplex_centroid(q: int, *, components: list[Component] | None = None, process: list[Factor] | None = None,
                            axial: bool = True, total: float = 1.0, replicates: int = 1,
                            type_replicates: dict | None = None, randomize: bool = True,
                            seed: int | None = None) -> MixtureDesign:
    comps = _prepare_components(q, components)
    letters = mix_letters(q)
    pts, types = _simplex_centroid_points(q)
    pts, types = _augment(pts, types, center=False, axial=axial, constrained=False, vertices=np.eye(q))
    pts = [_to_proportions(p, comps) for p in pts]
    bnd = [comb(q, d + 1) for d in range(q)]
    return _build("simplex_centroid", comps, letters, _check_process(process), pts, types, degree=q, total=total,
                  constraints=[], constrained=False, boundaries=bnd, replicates=replicates,
                  type_replicates=type_replicates, randomize=randomize, seed=seed)


def create_simplex_lattice(q: int, degree: int = 1, *, components: list[Component] | None = None,
                           process: list[Factor] | None = None, center: bool = True, axial: bool = True,
                           total: float = 1.0, replicates: int = 1, type_replicates: dict | None = None,
                           randomize: bool = True, seed: int | None = None) -> MixtureDesign:
    if degree not in LATTICE_MAX_Q:
        raise ValueError("격자 차수는 1~10 입니다.")
    if not 2 <= q <= LATTICE_MAX_Q[degree]:
        raise ValueError(f"차수 {degree} 격자는 성분 2~{LATTICE_MAX_Q[degree]}개까지 가능합니다.")
    comps = _prepare_components(q, components)
    letters = mix_letters(q)
    pts, types = _lattice_points(q, degree)
    pts, types = _augment(pts, types, center=center, axial=axial, constrained=False, vertices=np.eye(q))
    pts = [_to_proportions(p, comps) for p in pts]
    bnd = [comb(q, d + 1) for d in range(q)]
    return _build("simplex_lattice", comps, letters, _check_process(process), pts, types, degree=degree,
                  total=total, constraints=[], constrained=False, boundaries=bnd, replicates=replicates,
                  type_replicates=type_replicates, randomize=randomize, seed=seed)


def create_extreme_vertices(q: int, *, components: list[Component] | None = None,
                            constraints: list[LinearConstraint] | None = None, degree: int = 1,
                            process: list[Factor] | None = None, center: bool = True, axial: bool = True,
                            total: float = 1.0, replicates: int = 1, type_replicates: dict | None = None,
                            randomize: bool = True, seed: int | None = None) -> MixtureDesign:
    comps = _prepare_components(q, components)
    constraints = list(constraints or [])
    if len(constraints) > 10:
        raise ValueError("선형 제약은 최대 10개입니다.")
    if not 1 <= degree <= q:
        raise ValueError(f"설계 차수는 1~{q} 입니다.")
    letters = mix_letters(q)
    G, h = _inequalities(comps, letters, constraints)
    V, active = _vertices(G, h, q)
    faces = _faces(V, active, q)
    # 꼭지점은 성분 순서로 정렬(첫 성분 작은 순)
    pts = [V[i] for i in range(len(V))]
    types = [1] * len(V)
    for dim in range(1, min(degree, q - 1)):
        for fset in faces[dim]:
            pts.append(V[sorted(fset)].mean(axis=0))
            types.append(dim + 1)
    pts, types = _augment(pts, types, center=center, axial=axial, constrained=True, vertices=V)
    bnd = [len(faces[d]) for d in range(q)]
    return _build("extreme_vertices", comps, letters, _check_process(process), pts, types, degree=degree,
                  total=total, constraints=constraints, constrained=True, boundaries=bnd, replicates=replicates,
                  type_replicates=type_replicates, randomize=randomize, seed=seed)
