"""최적 설계 — Minitab 'Select Optimal Design'(선택·증강/개선·평가, D-최적과 거리 기반).

워크시트의 설계 행들이 후보점 집합이다. 모형 항으로 후보점의 설계행렬 F(상수 + 블록 효과 코딩 + 항, 코드화 단위)를
만들고 그 행을 골라 X'X 의 행렬식을 키운다. 출력 통계량 정의는 문서 예제 3개(CrystalGrowth)로 확인했다.
- D-optimality = det(X'X), A-optimality = trace((X'X)⁻¹), 레버리지 h = diag(X(X'X)⁻¹X'),
  G-optimality = 평균 h / 최대 h, V-optimality = 평균 h, Maximum leverage = 최대 h.
- Condition number = 상수항을 뺀 모형 열들의 상관행렬의 최대 고유값 / 최소 고유값(세 예제 모두 일치).

알고리즘(문서 'Methods' + 예제 1·2 의 선택 순서를 그대로 재현하도록 정한 세부 규칙)
- 순차(sequential) 초기 설계: X'X 가 특이한 동안은 이미 고른 점들이 펼치는 공간에서 가장 먼 후보
  (잔차 제곱 노름 최대), 그 뒤로는 분산 함수 d(x) = x'(X'X)⁻¹x 최대 후보를 하나씩 더한다(복원 추출, 동점은 앞 행).
- 교환(exchange, k점): d 최대 후보 k 개를 차례로 더한 뒤 제거 가능한 점 중 d 최소 점 k 개를 차례로 뺀다
  (동점은 목록 앞쪽). 빠진 점은 목록에서 지우고 더한 점은 끝에 붙인다. 행렬식이 커지면 계속하고, 같으면 그 교환을
  둔 채 멈추고, 작아지면 되돌리고 멈춘다(예제 1: 26↔1 개선 후 1↔5 동점 교환에서 정지).
- Fedorov: 설계점 하나와 후보 하나의 맞바꿈 중 행렬식 증가가 가장 큰 쌍을 적용, 개선이 없으면 멈춘다.
- 증강: 지시자 열의 음수 = 보호(빼지 않음), 양수 = 초기 설계(교환 가능), 절댓값 = 반복 수, 0 = 후보만.
- 거리 기반: 원점에서 가장 먼 후보(혼합물은 순수 성분에 가장 가까운 후보)에서 시작해 이미 고른 점들과의
  최소 거리가 가장 큰 후보를 차례로 더한다(반복 없음, 교환 없음). 일반 완전요인설계에는 쓸 수 없다.

문서에 없어 정한 것: 표시 형식(유효숫자 6자리, 정수부가 더 길면 정수부 전체, 10⁹ 이상은 1.23456E+18 꼴),
거리 기반의 거리 척도(코드화 요인 공간의 유클리드 거리), 요인설계·혼합물 제목 문구.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

_TOL = 1e-9


# ---------------------------------------------------------------- 후보 설계행렬


def _kind_label(design) -> str:
    from .mixture import MixtureDesign
    from .response_surface import ResponseSurfaceDesign
    if isinstance(design, ResponseSurfaceDesign):
        return "Response surface"
    if isinstance(design, MixtureDesign):
        return "Mixture"
    return "Factorial"


def candidate_matrix(design, *, model: str | None = None, order: int | None = None, terms: list[str] | None = None,
                     include_blocks: bool | None = None) -> tuple[np.ndarray, list[str]]:
    """후보점(design.coded 행 순서)의 설계행렬과 'Model terms' 표기(Block, A, AA, AB …)."""
    from ..analysis.model import Term, factorial_terms, rs_terms, term_matrix
    from .definitive_screening import DefinitiveScreeningDesign
    from .mixture import MixtureDesign
    from .response_surface import ResponseSurfaceDesign

    coded = design.coded.reset_index(drop=True)
    blocks_present = coded["Blocks"].nunique() > 1
    if isinstance(design, MixtureDesign):
        from ..analysis.mixture import component_values, mixture_terms
        from ..analysis.mixture import term_matrix as mix_matrix
        tl = mixture_terms(design, model=model or "quadratic", terms=terms, include_blocks=include_blocks,
                           blocks_present=blocks_present)
        P = component_values(design, coded, "proportions")
        cols, labels = [], []
        for t in tl:
            M, _ = mix_matrix(t, design, coded, P)
            cols.append(M)
            labels.append("Block" if t.kind == "blocks" else t.short)
        return np.hstack(cols), labels
    if isinstance(design, (ResponseSurfaceDesign, DefinitiveScreeningDesign)):
        default = "linear" if isinstance(design, DefinitiveScreeningDesign) else "full quadratic"
        tl = rs_terms(design, model=model or default, terms=terms, include_blocks=include_blocks,
                      blocks_present=blocks_present)
    else:
        tl = factorial_terms(design, order=2 if order is None else order, terms=terms, include_blocks=include_blocks,
                             blocks_present=blocks_present)
    cols, labels = [np.ones((len(coded), 1))], []
    for t in tl:
        M, _ = term_matrix(t, design, coded, {})
        cols.append(M)
        labels.append("Block" if t.kind == "blocks" else ("Ct Pt" if t.kind == "center" else t.word))
    return np.hstack(cols), labels


# ---------------------------------------------------------------- 통계량·표시


def _gfmt(x: float) -> str:
    if x == 0:
        return "0"
    if abs(x) >= 1e9:
        return f"{x:.5E}"
    digits = max(1, int(np.floor(np.log10(abs(x)))) + 1)
    return f"{x:.{max(6, digits)}g}"


def design_statistics(X: np.ndarray, has_constant: bool = True) -> dict:
    XtX = X.T @ X
    inv = np.linalg.inv(XtX)
    h = np.einsum("ij,jk,ik->i", X, inv, X)
    P = X[:, 1:] if has_constant else X
    P = P[:, np.std(P, axis=0) > 0]
    if P.shape[1] >= 2:
        ev = np.linalg.eigvalsh(np.corrcoef(P, rowvar=False))
        cond = float(ev[-1] / ev[0]) if ev[0] > 0 else float("inf")
    else:
        cond = 1.0
    return {"Condition number": cond, "D-optimality": float(np.linalg.det(XtX)), "A-optimality": float(np.trace(inv)),
            "G-optimality": float(h.mean() / h.max()), "V-optimality": float(h.mean()), "Maximum leverage": float(h.max())}


STAT_LABELS = {
    "Condition number": "Condition number:",
    "D-optimality": "D-optimality (determinant of XTX):",
    "A-optimality": "A-optimality (trace of inv(XTX)):",
    "G-optimality": "G-optimality (avg leverage/max leverage):",
    "V-optimality": "V-optimality (average leverage):",
    "Maximum leverage": "Maximum leverage:",
}


@dataclass
class OptimalDesignResult:
    task: str                         # "select" | "augment" | "evaluate"
    criterion: str                    # "D" | "distance"
    kind_label: str                   # "Response surface" | "Factorial" | "Mixture"
    n_candidates: int
    rows: list[int]                   # 고른 후보 행(0부터, 고른 순서, 중복 가능)
    terms: list[str]
    n_initial: int | None = None      # 증강할 초기 설계 점 수
    initial_method: str = "Sequential"
    improve_method: str | None = "Exchange"
    n_exchange: int = 1
    statistics: dict = field(default_factory=dict)

    @property
    def n_points(self) -> int:
        return len(self.rows)

    def indicator(self) -> np.ndarray:
        """원래 워크시트에 붙일 지시자 열(OptPoint): 각 후보가 뽑힌 횟수."""
        return np.bincount(np.asarray(self.rows, dtype=int), minlength=self.n_candidates)

    def header_lines(self) -> list[str]:
        crit = "D-optimality" if self.criterion == "D" else "distance-based optimality"
        if self.task == "evaluate":
            return [f"Evaluation of Specified {self.kind_label.title()} Design",
                    f"Number of design points in optimal design: {self.n_points}",
                    "Model terms: " + ", ".join(self.terms)]
        verb = "augmented" if self.task == "augment" else "selected"
        out = [f"{self.kind_label} design {verb} according to {crit}",
               f"Number of candidate design points: {self.n_candidates}"]
        if self.task == "augment":
            out.append(f"Number of design points to augment/improve: {self.n_initial}")
        out.append(f"Number of design points in optimal design: {self.n_points}")
        if self.criterion == "D":
            out.append("Model terms: " + ", ".join(self.terms))
            out.append(f"Initial design {'augmented' if self.task == 'augment' else 'generated'} by "
                       f"{self.initial_method} method")
            if self.improve_method:
                out.append(f"Initial design improved by {self.improve_method} method")
                if self.improve_method == "Exchange":
                    out.append(f"Number of design points exchanged is {self.n_exchange}")
        return out

    def rows_text(self, per_line: int = 15) -> str:
        nums = [str(r + 1) for r in self.rows]
        lines = [", ".join(nums[i:i + per_line]) for i in range(0, len(nums), per_line)]
        return "Row number of selected design points: " + ",\n     ".join(lines)

    def statistics_table(self) -> pd.DataFrame:
        return pd.DataFrame([[STAT_LABELS[k], _gfmt(v)] for k, v in self.statistics.items()])

    def text(self) -> str:
        title = "Specified Design" if self.task == "evaluate" else "Optimal Design"
        body = [*self.header_lines(), title, self.rows_text()]
        body += [f"{a} {b}" for a, b in self.statistics_table().values.tolist()]
        return "\n".join(body)


# ---------------------------------------------------------------- 알고리즘


def _first_max(v: np.ndarray) -> int:
    m = np.max(v)
    return int(np.flatnonzero(v >= m - _TOL * max(1.0, abs(m)))[0])


def _first_min(v: np.ndarray) -> int:
    m = np.min(v)
    return int(np.flatnonzero(v <= m + _TOL * max(1.0, abs(m)))[0])


def _variance(F: np.ndarray, X: np.ndarray) -> np.ndarray:
    return np.einsum("ij,jk,ik->i", F, np.linalg.inv(X.T @ X), F)


def _rank(X: np.ndarray) -> int:
    if len(X) == 0:
        return 0
    s = np.linalg.svd(X, compute_uv=False)
    return int((s > 1e-9 * s[0]).sum()) if s[0] > 0 else 0


def _sequential(F: np.ndarray, n: int, start: list[int]) -> list[int]:
    sel = list(start)
    p = F.shape[1]
    while len(sel) < n:
        X = F[sel]
        if _rank(X) < p:
            if sel:
                _, s, vt = np.linalg.svd(X, full_matrices=False)
                U = vt[s > 1e-9 * s[0]].T
                R = F - (F @ U) @ U.T
            else:
                R = F
            d = (R ** 2).sum(axis=1)
        else:
            d = _variance(F, X)
        sel.append(_first_max(d))
    if _rank(F[sel]) < p:
        raise ValueError("후보점으로는 이 모형의 모든 항을 추정할 수 없습니다(점 수를 늘리거나 항을 줄이세요).")
    return sel


def _logdet(X: np.ndarray) -> float:
    s, v = np.linalg.slogdet(X.T @ X)
    return v if s > 0 else -np.inf


def _exchange(F: np.ndarray, sel: list[int], n_protected: int, k: int = 1, maxit: int = 1000) -> list[int]:
    """sel 의 앞 n_protected 점은 빼지 않는다."""
    sel = list(sel)
    cur = _logdet(F[sel])
    for _ in range(maxit):
        new = list(sel)
        for _ in range(k):
            new.append(_first_max(_variance(F, F[new])))
        prot = n_protected
        for _ in range(k):
            d = _variance(F[new], F[new])
            d[:prot] = np.inf
            pos = _first_min(d)
            del new[pos]
        val = _logdet(F[new])
        if val < cur - 1e-12:
            return sel
        sel = new
        if val <= cur + 1e-12:
            return sel
        cur = val
    return sel


def _fedorov(F: np.ndarray, sel: list[int], n_protected: int, maxit: int = 1000) -> list[int]:
    sel = list(sel)
    for _ in range(maxit):
        X = F[sel]
        Mi = np.linalg.inv(X.T @ X)
        dF = np.einsum("ij,jk,ik->i", F, Mi, F)
        best, arg = 1e-10, None
        for pos in range(n_protected, len(sel)):
            xi = F[sel[pos]]
            di = xi @ Mi @ xi
            dij = F @ (Mi @ xi)
            delta = dF - di - dF * di + dij ** 2      # Fedorov Δ(x_i, x_j)
            j = _first_max(delta)
            if delta[j] > best:
                best, arg = delta[j], (pos, j)
        if arg is None:
            return sel
        pos, j = arg
        del sel[pos]
        sel.append(j)
    return sel


def _improve(F, sel, n_protected, method, k):
    if method is None:
        return sel
    if method == "exchange":
        return _exchange(F, sel, n_protected, k)
    if method == "fedorov":
        return _fedorov(F, sel, n_protected)
    raise ValueError("개선 방법은 'exchange', 'fedorov', None 중 하나입니다.")


def _distance_points(design) -> np.ndarray:
    from .mixture import MixtureDesign
    coded = design.coded.reset_index(drop=True)
    if isinstance(design, MixtureDesign):
        return coded[list(design.letters) + design.process_letters].values.astype(float)
    return coded[list(design.letters)].values.astype(float)


def _distance_select(design, n: int, start: list[int]) -> list[int]:
    from .general_full import GeneralFullFactorialDesign
    from .mixture import MixtureDesign
    if isinstance(design, GeneralFullFactorialDesign):
        raise ValueError("거리 기반 최적성은 일반 완전요인설계에서 쓸 수 없습니다.")
    Z = _distance_points(design)
    sel = list(dict.fromkeys(start))
    if n > len(np.unique(Z.round(9), axis=0)):
        raise ValueError("거리 기반 선택은 점을 반복하지 않으므로 서로 다른 후보 수보다 많이 고를 수 없습니다.")
    if not sel:
        if isinstance(design, MixtureDesign):
            q = len(design.letters)
            sel = [_first_max(Z[:, :q].max(axis=1))]       # 순수 성분(꼭지점)에 가장 가까운 점
        else:
            sel = [_first_max((Z ** 2).sum(axis=1))]
    while len(sel) < n:
        D = np.sqrt(((Z[:, None, :] - Z[None, sel, :]) ** 2).sum(axis=2)).min(axis=1)
        D[sel] = -np.inf
        sel.append(_first_max(D))
    return sel


def _result(task, criterion, design, F, terms, rows, *, n_initial=None, improve=None, k=1,
            has_constant=True) -> OptimalDesignResult:
    return OptimalDesignResult(task, criterion, _kind_label(design), len(F), list(map(int, rows)), terms, n_initial,
                               "Sequential", {"exchange": "Exchange", "fedorov": "Fedorov"}.get(improve), k,
                               design_statistics(F[rows], has_constant))


def _has_constant(design) -> bool:
    from .mixture import MixtureDesign
    return not isinstance(design, MixtureDesign)


# ---------------------------------------------------------------- 진입점


def select_optimal_design(
    design,
    n_points: int,
    *,
    criterion: str = "D",
    model: str | None = None,
    order: int | None = None,
    terms: list[str] | None = None,
    include_blocks: bool | None = None,
    improve: str | None = "exchange",
    n_exchange: int = 1,
) -> OptimalDesignResult:
    """후보점(워크시트의 설계 행)에서 n_points 점을 고른다."""
    F, labels = candidate_matrix(design, model=model, order=order, terms=terms, include_blocks=include_blocks)
    if criterion == "distance":
        rows = _distance_select(design, n_points, [])
        return _result("select", "distance", design, F, labels, rows, improve=None,
                       has_constant=_has_constant(design)) if _rank(F[rows]) == F.shape[1] else \
            OptimalDesignResult("select", "distance", _kind_label(design), len(F), rows, labels, improve_method=None)
    if criterion != "D":
        raise ValueError("최적성 기준은 'D' 또는 'distance' 입니다.")
    if n_points < F.shape[1]:
        raise ValueError(f"점 수({n_points})가 모형 항 수(상수 포함 {F.shape[1]})보다 적습니다.")
    if not 1 <= n_exchange < n_points:
        raise ValueError("교환할 점 수는 1 이상, 점 수 미만이어야 합니다.")
    rows = _sequential(F, n_points, [])
    rows = _improve(F, rows, 0, improve, n_exchange)
    return _result("select", "D", design, F, labels, rows, improve=improve, k=n_exchange,
                   has_constant=_has_constant(design))


def _from_indicator(indicator) -> tuple[list[int], list[int]]:
    ind = np.asarray(indicator, dtype=float)
    if np.isnan(ind).any() or np.any(ind != np.round(ind)):
        raise ValueError("지시자 열은 정수여야 합니다.")
    prot = [i for i, v in enumerate(ind) if v < 0 for _ in range(int(-v))]
    free = [i for i, v in enumerate(ind) if v > 0 for _ in range(int(v))]
    return prot, free


def augment_optimal_design(
    design,
    indicator,
    n_points: int,
    *,
    criterion: str = "D",
    model: str | None = None,
    order: int | None = None,
    terms: list[str] | None = None,
    include_blocks: bool | None = None,
    improve: str | None = "exchange",
    n_exchange: int = 1,
) -> OptimalDesignResult:
    """지시자 열로 준 설계를 n_points 점으로 늘리거나 개선한다(음수 = 보호, 양수 = 교환 가능, 0 = 후보)."""
    F, labels = candidate_matrix(design, model=model, order=order, terms=terms, include_blocks=include_blocks)
    prot, free = _from_indicator(indicator)
    start = prot + free
    if len(start) > n_points:
        raise ValueError("최적 설계 점 수가 초기 설계 점 수보다 적습니다.")
    if criterion == "distance":
        rows = _distance_select(design, n_points, start)
        return OptimalDesignResult("augment", "distance", _kind_label(design), len(F), rows, labels, len(start),
                                   improve_method=None,
                                   statistics=design_statistics(F[rows], _has_constant(design))
                                   if _rank(F[rows]) == F.shape[1] else {})
    if n_points < F.shape[1]:
        raise ValueError(f"점 수({n_points})가 모형 항 수(상수 포함 {F.shape[1]})보다 적습니다.")
    rows = _sequential(F, n_points, start)
    rows = _improve(F, rows, len(prot), improve, n_exchange)
    return _result("augment", "D", design, F, labels, rows, n_initial=len(start), improve=improve, k=n_exchange,
                   has_constant=_has_constant(design))


def evaluate_design(
    design,
    indicator,
    *,
    model: str | None = None,
    order: int | None = None,
    terms: list[str] | None = None,
    include_blocks: bool | None = None,
) -> OptimalDesignResult:
    """지시자 열(뽑힌 횟수)로 준 설계의 최적성 통계량을 계산한다."""
    F, labels = candidate_matrix(design, model=model, order=order, terms=terms, include_blocks=include_blocks)
    prot, free = _from_indicator(indicator)
    rows = sorted(prot + free)
    if _rank(F[rows]) < F.shape[1]:
        raise ValueError("지정한 설계로는 이 모형의 모든 항을 추정할 수 없습니다.")
    return OptimalDesignResult("evaluate", "D", _kind_label(design), len(F), rows, labels, improve_method=None,
                               statistics=design_statistics(F[rows], _has_constant(design)))


def optimal_subset(design, rows: list[int]):
    """고른 행으로 만든 새 설계(새 워크시트용). StdOrder·RunOrder 는 고른 순서로 1부터 다시 매긴다."""
    from .modify import _finish
    coded = design.coded.reset_index(drop=True).iloc[list(rows)].reset_index(drop=True).copy()
    coded["StdOrder"] = np.arange(1, len(coded) + 1)
    coded["RunOrder"] = np.arange(1, len(coded) + 1)
    changes = {}
    if hasattr(design, "replicates"):
        changes["replicates"] = 1
    if hasattr(design, "n_blocks"):
        changes["n_blocks"] = int(coded["Blocks"].nunique())
    return _finish(design, coded, **changes)
