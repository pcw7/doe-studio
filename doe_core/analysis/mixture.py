"""혼합물 분석 — Minitab 'Analyze Mixture Design'(Scheffé 모형 + 공정 변수, 혼합물 회귀).

계산 규칙(docs/spec/C_rsm_mixture_optimal.md 5절, FondueRecipe 예제로 검증)
- 상수항 없음. 성분 선형항 합이 절편 역할을 한다. 최소제곱 b = (X'X)⁻¹X'y.
- 성분 모형: Linear(A B C) / Quadratic(+AB AC BC) / Special cubic(+ABC) / Full cubic(+AB(A−B) …) /
  Special quartic(Quadratic + AABC ABBC ABCC, 성분 4개 이상이면 ABCD 도) / Full quartic(Special quartic + AB(A−B) + AB(A−B)²).
  역항 1/A 는 비율 단위이고 모든 성분 하한이 0 이 아닐 때만.
- 공정 변수: 코드값(−1/+1). 공정 변수 항은 성분 항과의 곱(A*X1, AB*X1, A*X1*X2 …)으로만 들어간다.
  'up through order k' 는 공정 변수 단어(X1, X2, X1X2 …, 길이 ≤ k)마다 성분 모형의 모든 항을 곱한 것.
- 분석 단위: 비율(proportions) / 유사성분(pseudocomponents, (비율 − 하한)/(1 − 하한 합)) / 양(amounts).
- 계수표: 성분 선형항(공정 변수 없는 것)은 T·P 를 '*' 로 표시. VIF 는 상수항 없는 모형이라
  중심화하지 않은 형태 VIF_j = [(X'X)⁻¹]_jj · Σx_j² (예제 15.94, 203.46 … 와 일치).
- 분산분석: Regression DF = p − 1, SS = SST − SSE(평균 중심 총제곱합 기준).
  성분 선형 그룹: DF = 선형항 수 − 1, Adj SS = '선형 계수가 모두 같다'(선형항을 상수 하나로 바꾼) 모형과의 SSE 차이,
  개별 선형항 행은 없음. 그 밖의 그룹·항: 그 열을 뺀 모형과의 SSE 차이. 공정 변수 곱 그룹의 선형 DF 는 성분 수 그대로.
  Seq SS: 표에 나오는 순서대로 항을 더할 때의 증가분(출발은 평균만 있는 모형).
  반복(같은 성분·공정 변수·블록 값)이 있으면 Residual Error 를 Lack-of-Fit / Pure Error 로 나눈다.

문서에 없어 정한 것
- 고차 항 표시 이름: AB(A−B) → 'A*B*(-)', AB(A−B)² → 'A*B*(-)^2', AABC → 'A*A*B*C', 역항 → '1/A'.
  그룹 이름: Special Cubic, Full Cubic, Special Quartic, Full Quartic, Inverse.
- 블록 항은 표의 맨 앞(효과 코딩). 'Component Only' 제목 행은 공정 변수 항이 있을 때만.
- 유사성분 단위 제목은 '(pseudo components)', 양 단위는 '(component amounts)'.
- 성분 선형항은 항상 모형에 넣는다(Minitab Terms 대화상자도 선형항을 빼지 못하게 한다고 가정).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from ..designs.mixture import MixtureDesign
from . import fmt
from .factorial import AnovaRow, _rank, _sse
from .model import _effect_coding

MIX_MODELS = ("linear", "quadratic", "special cubic", "full cubic", "special quartic", "full quartic")
UNITS = ("proportions", "pseudocomponents", "amounts")
UNIT_LABEL = {"proportions": "component proportions", "pseudocomponents": "pseudo components",
              "amounts": "component amounts"}
BLENDS = ("linear", "quadratic", "special cubic", "full cubic", "special quartic", "full quartic", "inverse")
_ZERO = 1e-14
GROUP_LABEL = {"linear": "Linear", "quadratic": "Quadratic", "special cubic": "Special Cubic",
               "full cubic": "Full Cubic", "special quartic": "Special Quartic", "full quartic": "Full Quartic",
               "inverse": "Inverse"}


@dataclass(frozen=True)
class MixTerm:
    kind: str                         # "blocks" | "linear" | "product" | "cubic" | "quartic" | "inverse"
    comps: tuple[str, ...] = ()       # 성분 문자(product 는 중복 허용: AABC = ('A','A','B','C'))
    proc: tuple[str, ...] = ()        # 공정 변수 문자(X1, X2 …)
    name: str = ""

    @property
    def blend(self) -> str:
        if self.kind == "product":
            n = len(self.comps)
            return {2: "quadratic", 3: "special cubic", 4: "special quartic"}[n]
        return {"linear": "linear", "cubic": "full cubic", "quartic": "full quartic", "inverse": "inverse",
                "blocks": "blocks"}[self.kind]

    @property
    def short(self) -> str:
        """Terms 대화상자 표기(AB, AABC, AB(A-B), AB(A-B)2, 1/A, A*X1 …)."""
        if self.kind == "blocks":
            return "Blocks"
        c = self.comps
        if self.kind == "inverse":
            base = f"1/{c[0]}"
        elif self.kind == "cubic":
            base = f"{c[0]}{c[1]}({c[0]}-{c[1]})"
        elif self.kind == "quartic":
            base = f"{c[0]}{c[1]}({c[0]}-{c[1]})2"
        else:
            base = "".join(c)
        return "*".join([base, *self.proc])

    @property
    def is_component_linear(self) -> bool:
        return self.kind == "linear" and not self.proc


# ---------------------------------------------------------------- 항 만들기·해석


def _names(design: MixtureDesign) -> dict[str, str]:
    d = dict(zip(design.letters, [c.name for c in design.components]))
    d.update(zip(design.process_letters, [f.name for f in design.process]))
    return d


def _make(design, kind, comps=(), proc=()) -> MixTerm:
    pos = {L: i for i, L in enumerate([*design.letters, *design.process_letters])}
    nm = _names(design)
    if kind == "blocks":
        return MixTerm("blocks", name="Blocks")
    if kind in ("product",):
        comps = tuple(sorted(comps, key=pos.__getitem__))
    proc = tuple(sorted(proc, key=pos.__getitem__))
    if kind == "linear":
        base = nm[comps[0]]
    elif kind == "product":
        base = "*".join(nm[c] for c in comps)
    elif kind == "cubic":
        base = f"{nm[comps[0]]}*{nm[comps[1]]}*(-)"
    elif kind == "quartic":
        base = f"{nm[comps[0]]}*{nm[comps[1]]}*(-)^2"
    elif kind == "inverse":
        base = f"1/{nm[comps[0]]}"
    else:
        raise ValueError(kind)
    return MixTerm(kind, tuple(comps), proc, "*".join([base, *(nm[x] for x in proc)]))


def component_terms(design: MixtureDesign, model: str = "quadratic", inverse: bool = False) -> list[MixTerm]:
    """성분만의 항(공정 변수 없음), 그룹 순서대로."""
    if model not in MIX_MODELS:
        raise ValueError(f"모형은 {MIX_MODELS} 중 하나입니다: {model!r}")
    L = list(design.letters)
    out = [_make(design, "linear", (a,)) for a in L]
    lvl = MIX_MODELS.index(model)
    if lvl >= 1:
        out += [_make(design, "product", p) for p in combinations(L, 2)]
    if model in ("special cubic", "full cubic"):
        out += [_make(design, "product", t) for t in combinations(L, 3)]
    if model in ("full cubic", "full quartic"):
        out += [_make(design, "cubic", p) for p in combinations(L, 2)]
    if model in ("special quartic", "full quartic"):
        for a, b, c in combinations(L, 3):
            out += [_make(design, "product", (a, a, b, c)), _make(design, "product", (a, b, b, c)),
                    _make(design, "product", (a, b, c, c))]
        out += [_make(design, "product", s) for s in combinations(L, 4)]
    if model == "full quartic":
        out += [_make(design, "quartic", p) for p in combinations(L, 2)]
    if inverse:
        out += [_make(design, "inverse", (a,)) for a in L]
    return sort_terms(out, design)


def process_words(design: MixtureDesign, order: int) -> list[tuple[str, ...]]:
    xs = design.process_letters
    return [w for r in range(1, min(order, len(xs)) + 1) for w in combinations(xs, r)]


def sort_terms(terms: list[MixTerm], design: MixtureDesign) -> list[MixTerm]:
    """표 순서: 블록 → 성분만(Linear, Quadratic, …, Inverse) → 공정 변수 단어별(같은 그룹 순서)."""
    pos = {L: i for i, L in enumerate([*design.letters, *design.process_letters])}
    words = {w: i for i, w in enumerate(process_words(design, len(design.process)))}
    kind_rank = {"product": 0, "cubic": 1, "quartic": 2, "linear": 0, "inverse": 0}

    def key(t: MixTerm):
        if t.kind == "blocks":
            return (-1,)
        return (0 if not t.proc else 1 + words[t.proc], BLENDS.index(t.blend), kind_rank[t.kind],
                len(set(t.comps)), [pos[c] for c in dict.fromkeys(t.comps)], [pos[c] for c in t.comps])
    return sorted(dict.fromkeys(terms), key=key)


_CUBIC_RE = re.compile(r"^([A-Z])([A-Z])\(([A-Z])-([A-Z])\)(\^?2)?$")


def parse_term(spec: str, design: MixtureDesign) -> MixTerm:
    """'AB', 'A*B', 'AABC', 'AB(A-B)', 'AB(A-B)2', '1/A', 'A*X1', 'Emmenthaler*Temperature', 'Blocks' 등."""
    nm = _names(design)
    by_name = {v: k for k, v in nm.items()}
    comps_set, proc_set = set(design.letters), set(design.process_letters)
    s = spec.strip()
    if s == "Blocks":
        return _make(design, "blocks")
    tokens = [t.strip() for t in s.replace("**", "^").split("*") if t.strip()]
    tokens = [by_name.get(t, t) for t in tokens]
    proc = [t for t in tokens if t in proc_set]
    rest = [t for t in tokens if t not in proc_set]
    if len(set(proc)) != len(proc) or not rest:
        raise ValueError(f"항을 해석할 수 없습니다: {spec!r}")

    def bad():
        return ValueError(f"항을 해석할 수 없습니다: {spec!r}")

    # 성분 부분
    if len(rest) >= 2 and rest[-1] in ("(-)", "(-)^2", "(-)2"):
        a, b = rest[0], rest[1]
        if len(rest) != 3 or a not in comps_set or b not in comps_set or a == b:
            raise bad()
        kind = "cubic" if rest[-1] == "(-)" else "quartic"
        return _make(design, kind, tuple(sorted((a, b), key=design.letters.index)), tuple(proc))
    if len(rest) == 1:
        t = rest[0]
        if t.startswith("1/"):
            c = by_name.get(t[2:], t[2:])
            if c not in comps_set:
                raise bad()
            return _make(design, "inverse", (c,), tuple(proc))
        m = _CUBIC_RE.match(t)
        if m:
            a, b, a2, b2, sq = m.groups()
            if {a, b} != {a2, b2} or a == b or a not in comps_set or b not in comps_set:
                raise bad()
            order = sorted((a, b), key=design.letters.index)
            return _make(design, "quartic" if sq else "cubic", tuple(order), tuple(proc))
        if t in comps_set:
            return _make(design, "linear", (t,), tuple(proc))
        letters = list(t)
    else:
        letters = []
        for t in rest:
            if t.endswith("^2") and by_name.get(t[:-2], t[:-2]) in comps_set:
                letters += [by_name.get(t[:-2], t[:-2])] * 2
            elif t in comps_set:
                letters.append(t)
            else:
                raise bad()
    if any(c not in comps_set for c in letters):
        raise bad()
    counts = sorted((letters.count(c) for c in set(letters)), reverse=True)
    if len(letters) == 1:
        return _make(design, "linear", tuple(letters), tuple(proc))
    ok = (len(letters) in (2, 3) and counts == [1] * len(letters)) or \
         (len(letters) == 4 and counts in ([2, 1, 1], [1, 1, 1, 1]))
    if not ok:
        raise bad()
    return _make(design, "product", tuple(letters), tuple(proc))


def mixture_terms(
    design: MixtureDesign,
    *,
    model: str = "quadratic",
    process_order: int | None = None,
    inverse: bool = False,
    terms: list[str] | None = None,
    include_blocks: bool | None = None,
    blocks_present: bool = False,
) -> list[MixTerm]:
    """분석에 쓸 항 목록. terms 를 주면 그것을 쓰고(성분 선형항은 항상 포함), 아니면 모형·공정 변수 차수로 만든다."""
    if terms is not None:
        tl = [parse_term(s, design) for s in terms]
    else:
        comp = component_terms(design, model, inverse)
        order = len(design.process) and (1 if process_order is None else process_order)
        tl = list(comp)
        for w in process_words(design, order):
            tl += [_make(design, t.kind, t.comps, w) for t in comp]
    tl = [t for t in tl if t.kind != "blocks"]
    tl = [_make(design, "linear", (a,)) for a in design.letters] + tl
    if include_blocks is None:
        include_blocks = blocks_present
    if include_blocks and blocks_present:
        tl.append(_make(design, "blocks"))
    return sort_terms(tl, design)


# ---------------------------------------------------------------- 단위·설계행렬


def component_values(design: MixtureDesign, coded: pd.DataFrame, units: str = "proportions") -> np.ndarray:
    if units not in UNITS:
        raise ValueError(f"분석 단위는 {UNITS} 중 하나입니다: {units!r}")
    P = coded[design.letters].values.astype(float)
    if units == "amounts":
        return P * design.total
    if units == "pseudocomponents":
        lo = np.array([c.lower for c in design.components])
        return (P - lo) / (1 - lo.sum())
    return P


def term_matrix(term: MixTerm, design: MixtureDesign, coded: pd.DataFrame, P: np.ndarray) -> tuple[np.ndarray, list[str]]:
    if term.kind == "blocks":
        ids = sorted(coded["Blocks"].unique())
        return _effect_coding(coded["Blocks"].values, ids), [f"Blocks {b}" for b in ids[:-1]]
    j = {L: i for i, L in enumerate(design.letters)}
    c = [P[:, j[L]] for L in term.comps]
    if term.kind == "linear":
        col = c[0]
    elif term.kind == "product":
        col = np.prod(np.column_stack(c), axis=1)
    elif term.kind == "cubic":
        col = c[0] * c[1] * (c[0] - c[1])
    elif term.kind == "quartic":
        col = c[0] * c[1] * (c[0] - c[1]) ** 2
    else:
        with np.errstate(divide="ignore"):
            col = 1.0 / c[0]
    for x in term.proc:
        col = col * coded[x].values.astype(float)
    return col[:, None], [term.name]


# ---------------------------------------------------------------- 분석 결과


@dataclass
class MixtureAnalysis:
    design: MixtureDesign
    response: str
    y: np.ndarray
    used_rows: np.ndarray
    terms: list[MixTerm]
    removed_terms: list[MixTerm]
    X: np.ndarray
    col_labels: list[str]
    col_term: list[int]
    units: str = "proportions"
    covariates: dict = field(default_factory=dict)
    beta: np.ndarray = field(init=False)
    cov_unscaled: np.ndarray = field(init=False)
    fitted: np.ndarray = field(init=False)
    resid: np.ndarray = field(init=False)
    hat: np.ndarray = field(init=False)

    two_level = False
    is_rs = False
    is_mixture = True

    def __post_init__(self):
        X, y = self.X, self.y
        self.cov_unscaled = np.linalg.inv(X.T @ X)
        self.beta = self.cov_unscaled @ X.T @ y
        self.fitted = X @ self.beta
        self.resid = y - self.fitted
        if float(self.resid @ self.resid) <= _ZERO * self.sst:      # 완전 적합: 수치 잡음을 0 으로
            self.resid = np.zeros_like(y)
            self.fitted = y.copy()
        self.hat = np.einsum("ij,jk,ik->i", X, self.cov_unscaled, X)

    def _clean(self, v: float) -> float:
        """제곱합의 수치 잡음(아주 작은 값·음수)을 0 으로."""
        return 0.0 if v <= _ZERO * max(self.sst, 1e-300) else float(v)

    # ------------------------------------------------------------ 기본 통계량
    @property
    def n(self) -> int:
        return len(self.y)

    @property
    def p(self) -> int:
        return self.X.shape[1]

    @property
    def df_error(self) -> int:
        return self.n - self.p

    @property
    def sse(self) -> float:
        return float(self.resid @ self.resid)

    @property
    def sst(self) -> float:
        d = self.y - self.y.mean()
        return float(d @ d)

    @property
    def mse(self) -> float | None:
        return self.sse / self.df_error if self.df_error > 0 else None

    @property
    def has_process_terms(self) -> bool:
        return any(t.proc for t in self.terms)

    def coef_cov(self) -> np.ndarray:
        if self.mse is None:
            return np.full((self.p, self.p), np.nan)
        return self.cov_unscaled * self.mse

    def se_coef(self) -> np.ndarray:
        if self.mse is None:
            return np.full(self.p, np.nan)
        return np.sqrt(np.diag(self.cov_unscaled) * self.mse)

    def vif(self) -> np.ndarray:
        return np.diag(self.cov_unscaled) * np.sum(self.X ** 2, axis=0)

    # ------------------------------------------------------------ 계수표
    def coefficients(self) -> pd.DataFrame:
        se = self.se_coef()
        with np.errstate(divide="ignore", invalid="ignore"):
            t = self.beta / se
        pv = 2 * stats.t.sf(np.abs(t), self.df_error) if self.df_error > 0 else np.full(self.p, np.nan)
        for j, ti in enumerate(self.col_term):
            if self.terms[ti].is_component_linear or not np.isfinite(t[j]):
                t[j], pv[j] = np.nan, np.nan
        return pd.DataFrame({"Term": self.col_labels, "Coef": self.beta, "SE Coef": se, "T-Value": t,
                             "P-Value": pv, "VIF": self.vif()})

    def coefficients_table(self) -> pd.DataFrame:
        rows = []
        for r in self.coefficients().itertuples(index=False):
            se = r[2]
            rows.append({"Term": r[0], "Coef": fmt.by_se(r[1], se), "SE Coef": fmt.se_text(se),
                         "T-Value": fmt.t_text(None if np.isnan(r[3]) else r[3]),
                         "P-Value": fmt.p_text(None if np.isnan(r[4]) else r[4]),
                         "VIF": "" if not np.isfinite(r[5]) else f"{r[5]:.2f}"})
        return pd.DataFrame(rows)

    def coefficients_title(self) -> str:
        return f"Estimated Regression Coefficients for {self.response} ({UNIT_LABEL[self.units]})"

    def coefficients_note(self) -> str | None:
        return "Coefficients are calculated for coded process variables." if self.has_process_terms else None

    def anova_title(self) -> str:
        return f"Analysis of Variance for {self.response} ({UNIT_LABEL[self.units]})"

    # ------------------------------------------------------------ 모형 요약
    def press(self) -> float | None:
        if np.any(self.hat > 1 - 1e-9):
            return None
        return float(np.sum((self.resid / (1 - self.hat)) ** 2))

    def summary(self) -> dict:
        r2 = 1 - self.sse / self.sst
        s = np.sqrt(self.mse) if self.mse is not None else None
        adj = max(0.0, 1 - self.mse / (self.sst / (self.n - 1))) if self.mse is not None else None
        press = self.press()
        pred = max(0.0, 1 - press / self.sst) if press is not None else None
        return {"S": s, "R-sq": r2, "R-sq(adj)": adj, "PRESS": press, "R-sq(pred)": pred}

    def summary_table(self) -> pd.DataFrame:
        s = self.summary()
        return pd.DataFrame([{"S": fmt.sig_text(s["S"]) if s["S"] is not None else fmt.MISSING,
                              "R-sq": fmt.pct_text(s["R-sq"]), "R-sq(adj)": fmt.pct_text(s["R-sq(adj)"]),
                              "PRESS": fmt.sig_text(s["PRESS"]) if s["PRESS"] is not None else fmt.MISSING,
                              "R-sq(pred)": fmt.pct_text(s["R-sq(pred)"])}])

    # ------------------------------------------------------------ 분산분석
    def _cols_of(self, idxs: set[int]) -> list[int]:
        return [j for j, ti in enumerate(self.col_term) if ti in idxs]

    def _adj_ss(self, idxs: set[int]) -> float:
        drop = set(self._cols_of(idxs))
        keep = [j for j in range(self.p) if j not in drop]
        return self._clean(_sse(self.X[:, keep], self.y) - self.sse)

    def _adj_ss_linear(self, idxs: set[int]) -> float:
        """선형 계수가 모두 같다는 가설: 선형 열들을 상수 열 하나로 바꾼 모형과 비교."""
        drop = set(self._cols_of(idxs))
        keep = [j for j in range(self.p) if j not in drop]
        Xr = np.hstack([np.ones((self.n, 1)), self.X[:, keep]])
        return self._clean(_sse(Xr, self.y) - self.sse)

    def _seq_ss(self) -> dict[int, float]:
        out, prev = {}, self.sst
        ones = np.ones((self.n, 1))
        for ti in range(len(self.terms)):
            cur = _sse(np.hstack([ones, self.X[:, self._cols_of(set(range(ti + 1)))]]), self.y)
            out[ti] = self._clean(prev - cur)
            prev = cur
        return out

    def _ftest(self, ss: float, df: int):
        ms = ss / df if df else None
        if ms is None or self.mse is None or self.mse <= 0:
            return ms, None, None
        f = ms / self.mse
        return ms, f, float(stats.f.sf(f, df, self.df_error))

    def _pure_error(self) -> tuple[float, int]:
        coded = self.design.coded.iloc[self.used_rows].reset_index(drop=True)
        key = coded[list(self.design.letters)].round(9)
        procs = sorted({x for t in self.terms for x in t.proc})
        for x in procs:
            key[x] = coded[x].values
        if any(t.kind == "blocks" for t in self.terms):
            key["_blk"] = coded["Blocks"].values
        g = key.groupby(list(key.columns), sort=False).ngroup().values
        ss, df = 0.0, 0
        for gid in np.unique(g):
            yy = self.y[g == gid]
            ss += float(np.sum((yy - yy.mean()) ** 2))
            df += len(yy) - 1
        return ss, df

    def anova_rows(self) -> list[AnovaRow]:
        rows: list[AnovaRow] = []
        seq = self._seq_ss()
        reg_df, reg_ss = self.p - 1, self.sst - self.sse
        ms, f, pv = self._ftest(reg_ss, reg_df)
        rows.append(AnovaRow("Regression", 0, reg_df, reg_ss, reg_ss, ms, f, pv))
        nm = _names(self.design)
        ti_all = list(enumerate(self.terms))

        def add_group(label, idxs, level, *, linear_component=False, members=True):
            if not idxs:
                return
            df = sum(len(self._cols_of({i})) for i in idxs) - (1 if linear_component else 0)
            if df <= 0:
                return
            ss = self._adj_ss_linear(set(idxs)) if linear_component else self._adj_ss(set(idxs))
            ms, f, pv = self._ftest(ss, df)
            rows.append(AnovaRow(label, level, df, sum(seq[i] for i in idxs), ss, ms, f, pv))
            if members and not linear_component:
                for i in idxs:
                    d = len(self._cols_of({i}))
                    s2 = self._adj_ss({i})
                    ms2, f2, p2 = self._ftest(s2, d)
                    rows.append(AnovaRow(self.terms[i].name, level + 1, d, seq[i], s2, ms2, f2, p2))

        add_group("Blocks", [i for i, t in ti_all if t.kind == "blocks"], 1, members=False)
        has_proc = self.has_process_terms
        base = 2 if has_proc else 1
        if has_proc:
            rows.append(AnovaRow("Component Only", 1, None))
        comp_only = [(i, t) for i, t in ti_all if t.kind != "blocks" and not t.proc]
        for b in BLENDS:
            idxs = [i for i, t in comp_only if t.blend == b]
            add_group(GROUP_LABEL[b], idxs, base, linear_component=(b == "linear"))
        words = [w for w in process_words(self.design, len(self.design.process))
                 if any(t.proc == w for t in self.terms)]
        for w in words:
            rows.append(AnovaRow("Component * " + " * ".join(nm[x] for x in w), 1, None))
            grp = [(i, t) for i, t in ti_all if t.proc == w]
            for b in BLENDS:
                add_group(GROUP_LABEL[b], [i for i, t in grp if t.blend == b], 2)

        dfe, sse = self.df_error, self.sse
        rows.append(AnovaRow("Residual Error", 0, dfe, sse, sse, sse / dfe if dfe > 0 else None))
        pe_ss, pe_df = self._pure_error()
        lof_df, lof_ss = dfe - pe_df, sse - pe_ss
        if pe_df > 0 and lof_df > 0:
            ms_lof, ms_pe = lof_ss / lof_df, pe_ss / pe_df
            f = ms_lof / ms_pe if ms_pe > 0 else None
            p = float(stats.f.sf(f, lof_df, pe_df)) if f is not None else None
            rows.append(AnovaRow("Lack-of-Fit", 1, lof_df, lof_ss, lof_ss, ms_lof, f, p))
            rows.append(AnovaRow("Pure Error", 1, pe_df, pe_ss, pe_ss, ms_pe))
        rows.append(AnovaRow("Total", 0, self.n - 1, self.sst, None))
        return rows

    def anova(self) -> pd.DataFrame:
        return pd.DataFrame([r.__dict__ for r in self.anova_rows()])

    def anova_table(self) -> pd.DataFrame:
        """Minitab 'Analysis of Variance' 표(문자열, Seq SS·Adj SS 모두)."""
        rows = self.anova_rows()
        seq_dec = fmt.column_decimals([r.seq_ss for r in rows])
        ss_dec = fmt.column_decimals([r.adj_ss for r in rows])
        ms_dec = fmt.column_decimals([r.adj_ms for r in rows])

        def star(r):    # 오차가 없어(DF 0 또는 완전 적합) 검정할 수 없는 모형 행
            return r.adj_ms is not None and r.source not in ("Residual Error", "Pure Error", "Total")                 and (self.mse is None or self.mse <= 0)

        out = []
        for r in rows:
            out.append({
                "Source": r.source, "DF": "" if r.df is None else str(r.df),
                "Seq SS": "" if r.seq_ss is None else fmt.fixed(r.seq_ss, seq_dec),
                "Adj SS": "" if r.adj_ss is None else fmt.fixed(r.adj_ss, ss_dec),
                "Adj MS": "" if r.adj_ms is None else fmt.fixed(r.adj_ms, ms_dec),
                "F-Value": fmt.t_text(r.f) if r.f is not None else (fmt.MISSING if star(r) else ""),
                "P-Value": fmt.p_text(r.p) if r.p is not None else (fmt.MISSING if star(r) else ""),
            })
        return pd.DataFrame(out)


# ---------------------------------------------------------------- 진입점


def analyze_mixture(
    design: MixtureDesign,
    y,
    *,
    response: str = "Y",
    model: str = "quadratic",
    units: str = "proportions",
    process_order: int | None = None,
    inverse: bool = False,
    terms: list[str] | None = None,
    include_blocks: bool | None = None,
) -> MixtureAnalysis:
    """design.coded 행 순서로 정렬된 반응 y 로 혼합물 설계를 분석한다(혼합물 회귀). 반응이 빈 행은 뺀다."""
    if not isinstance(design, MixtureDesign):
        raise TypeError("혼합물 설계가 아닙니다.")
    y = np.asarray(y, dtype=float)
    coded_all = design.coded.reset_index(drop=True)
    if len(y) != len(coded_all):
        raise ValueError(f"반응 길이({len(y)})가 런 수({len(coded_all)})와 다릅니다.")
    used = np.where(np.isfinite(y))[0]
    coded = coded_all.iloc[used].reset_index(drop=True)
    yv = y[used]
    tl = mixture_terms(design, model=model, process_order=process_order, inverse=inverse, terms=terms,
                       include_blocks=include_blocks, blocks_present=coded["Blocks"].nunique() > 1)
    if any(t.kind == "inverse" for t in tl):
        if units != "proportions":
            raise ValueError("역항은 비율 단위로 분석할 때만 쓸 수 있습니다.")
        if any(c.lower <= 0 for c in design.components):
            raise ValueError("역항은 모든 성분의 하한이 0 보다 클 때만 쓸 수 있습니다.")
    P = component_values(design, coded, units)
    X = np.empty((len(yv), 0))
    labels, col_term, kept, removed = [], [], [], []
    for t in tl:
        M, labs = term_matrix(t, design, coded, P)
        cand = np.hstack([X, M])
        if _rank(cand) == cand.shape[1]:
            X = cand
            labels += labs
            col_term += [len(kept)] * M.shape[1]
            kept.append(t)
        else:
            if t.kind == "linear" and not t.proc:
                raise ValueError(f"성분 선형항 {t.name} 을 추정할 수 없습니다(설계를 확인하세요).")
            removed.append(t)
    if X.shape[1] > len(yv):
        raise ValueError("추정할 계수가 관측치보다 많습니다.")
    return MixtureAnalysis(design, response, yv, used, kept, removed, X, labels, col_term, units)


def analyze_mixture_worksheet(ws, response: str, **kwargs) -> MixtureAnalysis:
    y = ws.column(response).astype(float).values
    return analyze_mixture(ws.design, y, response=response, **kwargs)
