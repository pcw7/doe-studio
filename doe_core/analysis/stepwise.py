"""단계적 모형 선택 — Minitab 'Analyze Factorial / Response Surface / Screening Design > Stepwise'.

방법(문서 'Perform stepwise regression', 'Methods and formulas for stepwise')
- Stepwise: 빈 모형(또는 E·I 항)에서 시작. 단계마다 먼저 제거(모형 안 항 중 p 가 가장 큰 항, p > α_remove),
  제거할 항이 없으면 추가(밖 항 중 p 가 가장 작은 항, p < α_enter). 둘 다 없으면 멈춘다.
- Forward selection: 추가만(한 번 들어간 항은 빠지지 않음). Backward elimination: 모든 후보에서 시작해 제거만.
- Forward information criteria: 단계마다 p 가 가장 작은 항을 넣으며 AICc 또는 BIC 를 계산하고, 값이 가장 작은 모형을 고른다.
  멈춤: 8단계 연속 새 최솟값 없음 / 완전 모형 / 오차 DF 1 인 모형. '매 단계 계층 + 한 번에 한 항' 이면 8단계 규칙 없이
  완전 모형 또는 오차 DF 1 까지 간다. 'Add terms at the end' 와 함께 쓰면 오류.
- 제거 F = [SSE(j − x_r) − SSE_j] / df_r / MSE_j, 추가 F = [SSE_j − SSE(j + x_a)] / df_a / MSE(j + x_a).
- 포화 모형(요인설계 분석의 Stepwise·Backward): 후보 모형의 오차 DF 가 0 이면 항의 ¼(반올림, 최대 9)을 Adj SS 가
  작은 순서로 계층을 지키며 먼저 빼고, 이후 단계에서 다시 고려하지 않는다. 반응표면·선별 설계는 시작 모형이 포화면 진행하지 않는다.
- 정보 기준(문서 공식): −2lnL = n·ln(SSE/n) + n + n·ln(2π), AICc = −2lnL + 2(p+1) + 2(p+1)(p+2)/(n−p−2)
  (n−p−2 ≤ 0 이면 계산 안 함), BIC = −2lnL + (p+1)·ln n, Mallows' Cp = SSE_p/MSE_m − (n − 2p).
  p = 상수 포함 계수 수, MSE_m = 모든 후보 항을 넣은 모형의 MSE.
- E(Include term in every model) 항은 늘 모형에 있고, I(Include term in the initial model) 항은 Stepwise 의 시작 모형에만 들어간다.

문서에 없어 정한 것
- 기본 α: Stepwise 0.15/0.15, Forward 0.25, Backward 0.1(Minitab 기본값으로 알려진 값).
- p 가 같으면(유효숫자 12자리) 추가는 F 가 큰 항 → 후보 순서가 앞선 항, 제거는 F 가 작은 항 → 후보 순서가 뒤인 항.
- 'Extra terms can enter' 에서 항의 p 는 그 항 하나만 넣은(비계층) 모형으로 계산하고, 필요한 하위 항을 함께 넣는다.
- 계층은 요인 항에만 적용(블록·공변량·중앙점 항은 자유롭게 들어가고 빠진다). 'Terms with categorical predictors' 는
  텍스트 요인이나 일반 완전요인설계 요인이 든 항. 후보 목록에 없는 하위 항은 요구하지 않는다.
- 단계 표의 1단계는 시작 모형이 비어 있지 않을 때(Backward 는 완전 모형) 시작 모형이다. Forward 정보 기준은 상수만 있는
  모형도 비교 대상이며 늘 첫 단계로 보인다.
- 같은 모형이 다시 나오면(α_enter > α_remove 일 때 생길 수 있는 순환) 멈춘다.
- 가중 회귀(가중치·산포 분석)도 같은 규칙: SS 는 모두 가중, 정보 기준의 −2lnL 에 −Σln w.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from . import fmt
from .factorial import FactorialAnalysis, _build, _rank, info_criteria
from .model import Term, term_matrix

METHODS = ("none", "stepwise", "forward", "backward", "forward_ic")
METHOD_TITLE = {"stepwise": "Stepwise Selection of Terms", "forward": "Forward Selection of Terms",
                "backward": "Backward Elimination of Terms", "forward_ic": "Forward Selection of Terms"}
METHOD_TITLE_KO = {"stepwise": "단계적 항 선택", "forward": "전진 항 선택", "backward": "후진 항 제거",
                   "forward_ic": "정보 기준 전진 항 선택"}
METHOD_NAME = {"none": "None", "stepwise": "Stepwise", "forward": "Forward selection",
               "backward": "Backward elimination", "forward_ic": "Forward information criteria"}
DEFAULT_ALPHA = {"stepwise": (0.15, 0.15), "forward": (0.25, None), "backward": (None, 0.1),
                 "forward_ic": (None, None), "none": (None, None)}
HIERARCHY = ("each_step", "at_end", "none")
CRITERIA = {"aicc": "AICc", "bic": "BIC"}
NO_IMPROVE_STEPS = 8
MAX_PRE_REMOVE = 9


@dataclass(frozen=True)
class StepwiseOptions:
    method: str = "stepwise"
    alpha_enter: float | None = None
    alpha_remove: float | None = None
    criterion: str = "aicc"                 # forward_ic 만
    hierarchy: str = "each_step"            # each_step | at_end | none
    scope: str = "all"                      # all | categorical
    extra_terms: bool = False               # each_step 에서 하위 항을 함께 넣어 고차 항이 들어올 수 있게
    force: tuple[str, ...] = ()             # E: 모든 모형에 포함
    initial: tuple[str, ...] = ()           # I: 시작 모형에 포함(Stepwise 만)

    def __post_init__(self):
        if self.method not in METHODS:
            raise ValueError(f"방법은 {METHODS} 중 하나여야 합니다.")
        if self.hierarchy not in HIERARCHY:
            raise ValueError(f"계층 설정은 {HIERARCHY} 중 하나여야 합니다.")
        if self.criterion not in CRITERIA:
            raise ValueError("정보 기준은 aicc 또는 bic 입니다.")
        if self.method == "forward_ic" and self.hierarchy == "at_end":
            raise ValueError("Forward information criteria 에는 'Add terms at the end' 계층 설정을 쓸 수 없습니다. "
                             "'매 단계 계층 모형' 을 고르세요.")
        for a in (self.alpha_enter, self.alpha_remove):
            if a is not None and not 0 < a < 1:
                raise ValueError("α 는 0 과 1 사이여야 합니다.")

    @property
    def active(self) -> bool:
        return self.method != "none"

    def alphas(self) -> tuple[float | None, float | None]:
        de, dr = DEFAULT_ALPHA[self.method]
        ae = (self.alpha_enter if self.alpha_enter is not None else de) if de is not None else None
        ar = (self.alpha_remove if self.alpha_remove is not None else dr) if dr is not None else None
        return ae, ar


# ---------------------------------------------------------------- 단계별 적합


@dataclass
class StepFit:
    terms: tuple[int, ...]
    labels: list[str]
    col_term: list[int]
    beta: np.ndarray
    se: np.ndarray
    term_p: dict[int, float | None]
    sse: float
    sst: float
    n: int
    press: float | None
    mse_full: float | None
    log_w: float = 0.0
    has_constant: bool = True                 # 혼합물 모형은 상수항이 없다

    @property
    def p(self) -> int:
        return len(self.beta)

    @property
    def df_error(self) -> int:
        return self.n - self.p

    @property
    def mse(self) -> float | None:
        return self.sse / self.df_error if self.df_error > 0 else None

    def stats(self) -> dict:
        mse = self.mse
        r2 = 1 - self.sse / self.sst if self.sst > 0 else None
        adj = max(0.0, 1 - mse / (self.sst / (self.n - 1))) if mse is not None and self.sst > 0 else None
        pred = max(0.0, 1 - self.press / self.sst) if self.press is not None and self.sst > 0 else None
        tiny = 1e-14 * max(self.sst, 1e-300)
        cp = (self.sse / self.mse_full - (self.n - 2 * self.p)) if self.mse_full and self.mse_full > tiny else None
        ic = info_criteria(self.sse, self.n, self.p, self.log_w)
        return {"S": math.sqrt(mse) if mse is not None else None, "R-sq": r2, "R-sq(adj)": adj, "R-sq(pred)": pred,
                "Mallows' Cp": cp, "AICc": ic["AICc"], "BIC": ic["BIC"]}

    def stat_rows(self) -> list[tuple[str, str]]:
        """단계 표 아래쪽 통계 행(이름, 글자)."""
        st = self.stats()
        return [("S", fmt.sig_text(st["S"]) if st["S"] is not None else fmt.MISSING),
                ("R-sq", fmt.pct_text(st["R-sq"])), ("R-sq(adj)", fmt.pct_text(st["R-sq(adj)"])),
                ("R-sq(pred)", fmt.pct_text(st["R-sq(pred)"])), ("Mallows' Cp", fmt.fixed(st["Mallows' Cp"], 2)),
                ("AICc", fmt.fixed(st["AICc"], 2)), ("BIC", fmt.fixed(st["BIC"], 2))]


@dataclass
class Step:
    terms: tuple[int, ...]
    entered: tuple[int, ...] = ()
    removed: tuple[int, ...] = ()
    p_value: float | None = None
    note: str = ""                          # "start" | "hierarchy"
    fit: StepFit | None = None


class _Engine:
    """후보 항의 열 묶음으로 부분 모형을 적합하고 추가·제거 F 검정을 한다."""

    def __init__(self, cands: list[Term], mats: list[np.ndarray], labels: list[list[str]], y: np.ndarray,
                 categorical: set[str], opts: StepwiseOptions, weights: np.ndarray | None = None):
        self.cands, self.mats, self.labels, self.y = cands, mats, labels, y
        self.n = len(y)
        self.w = np.ones(self.n) if weights is None else np.asarray(weights, dtype=float)
        self.sw = np.sqrt(self.w)
        self.log_w = float(np.sum(np.log(self.w))) if weights is not None else 0.0
        d = y - float(np.sum(self.w * y) / np.sum(self.w))
        self.sst = float(np.sum(self.w * d ** 2))
        self.opts = opts
        self.excluded: set[int] = set()         # 포화 모형에서 먼저 뺀 항(다시 고려하지 않음)
        self._cache: dict[tuple[int, ...], tuple[float, int] | None] = {}
        words = {t.letters: i for i, t in enumerate(cands) if t.kind == "factor"}
        self.needs: list[frozenset[int]] = []
        for t in cands:
            req: set[int] = set()
            applies = t.kind == "factor" and t.order > 1 and opts.hierarchy != "none" and (
                opts.scope == "all" or any(L in categorical for L in t.letters))
            if applies:
                for r in range(1, t.order):
                    for sub in combinations(t.letters, r):
                        if sub in words:
                            req.add(words[sub])
            self.needs.append(frozenset(req))
        # 포화 모형 선제거는 opts.hierarchy 와 상관없이 계층을 지킨다
        self.sub_terms: list[frozenset[int]] = []
        for t in cands:
            req = set()
            if t.kind == "factor" and t.order > 1:
                for r in range(1, t.order):
                    for sub in combinations(t.letters, r):
                        if sub in words:
                            req.add(words[sub])
            self.sub_terms.append(frozenset(req))

    # ---------------------------------------------------------- 적합
    def X(self, idx) -> np.ndarray:
        cols = [np.ones((self.n, 1))] + [self.mats[i] for i in sorted(idx)]
        return np.hstack(cols)

    def df_of(self, i: int) -> int:
        return self.mats[i].shape[1]

    def ncoef(self, idx) -> int:
        return 1 + sum(self.df_of(i) for i in idx)

    def sse(self, idx) -> float | None:
        """적합할 수 없으면(열이 선형 종속이거나 관측치보다 많음) None."""
        key = tuple(sorted(idx))
        if key not in self._cache:
            X = self.X(key)
            if X.shape[1] > self.n or _rank(X) < X.shape[1]:
                self._cache[key] = None
            else:
                beta, *_ = np.linalg.lstsq(X * self.sw[:, None], self.y * self.sw, rcond=None)
                r = self.y - X @ beta
                self._cache[key] = (float(np.sum(self.w * r ** 2)), X.shape[1])
        v = self._cache[key]
        return None if v is None else v[0]

    def df_error(self, idx) -> int:
        return self.n - self.ncoef(idx)

    def _f(self, ss: float, df: int, sse_big: float, dfe_big: int) -> tuple[float, float]:
        ss = max(ss, 0.0)
        mse = sse_big / dfe_big
        if mse <= 1e-14 * max(self.sst, 1e-300):
            return (math.inf, 0.0) if ss > 1e-12 * max(self.sst, 1e-300) else (0.0, 1.0)
        f = ss / df / mse
        return f, float(stats.f.sf(f, df, dfe_big))

    def removal_test(self, model: set[int], i: int) -> tuple[float, float] | None:
        dfe = self.df_error(model)
        s_full = self.sse(model)
        s_red = self.sse(model - {i})
        if dfe <= 0 or s_full is None or s_red is None:
            return None
        return self._f(s_red - s_full, self.df_of(i), s_full, dfe)

    def addition_test(self, model: set[int], i: int) -> tuple[float, float] | None:
        new = model | {i}
        dfe = self.df_error(new)
        s_new = self.sse(new)
        s_old = self.sse(model)
        if dfe <= 0 or s_new is None or s_old is None:
            return None
        return self._f(s_old - s_new, self.df_of(i), s_new, dfe)

    # ---------------------------------------------------------- 후보 고르기
    def removable(self, model: set[int], forced: set[int]) -> list[int]:
        out = []
        for i in sorted(model):
            if i in forced:
                continue
            if self.opts.hierarchy == "each_step" and any(i in self.needs[j] for j in model if j != i):
                continue
            out.append(i)
        return out

    def addable(self, model: set[int]) -> list[tuple[int, frozenset[int]]]:
        """(항, 함께 들어갈 항 묶음)."""
        out = []
        for i in range(len(self.cands)):
            if i in model:
                continue
            missing = self.needs[i] - model if self.opts.hierarchy == "each_step" else frozenset()
            if missing and not self.opts.extra_terms:
                continue
            group = frozenset({i}) | missing
            if group & self.excluded:
                continue
            if self.df_error(model | group) < 1 or self.sse(model | group) is None:
                continue
            out.append((i, group))
        return out

    def best_removal(self, model: set[int], forced: set[int]) -> tuple[int, float] | None:
        best = None
        for i in self.removable(model, forced):
            r = self.removal_test(model, i)
            if r is None:
                continue
            f, p = r
            key = (_round(p), -_round(f), i)           # p 큰 것 → F 작은 것 → 뒤의 항
            if best is None or key > best[0]:
                best = (key, i, p)
        return None if best is None else (best[1], best[2])

    def best_addition(self, model: set[int]) -> tuple[int, frozenset[int], float] | None:
        best = None
        for i, group in self.addable(model):
            r = self.addition_test(model, i)
            if r is None:
                continue
            f, p = r
            key = (_round(p), -_round(f), i)           # p 작은 것 → F 큰 것 → 앞의 항
            if best is None or key < best[0]:
                best = (key, i, group, p)
        return None if best is None else (best[1], best[2], best[3])

    family = "normal"

    def criterion(self, model, crit: str) -> float:
        """정보 기준(AICc/BIC) — 계산할 수 없으면 inf."""
        ic = info_criteria(self.sse(model), self.n, self.ncoef(model), self.log_w)[crit]
        return math.inf if ic is None else ic

    def hierarchy_closure(self, model: set[int]) -> set[int]:
        out = set(model)
        for i in model:
            out |= self.needs[i]
        return out

    # ---------------------------------------------------------- 단계 결과
    def fit(self, idx, mse_full: float | None) -> StepFit:
        key = tuple(sorted(idx))
        X = self.X(key)
        labels, col_term = ["Constant"], [-1]
        for i in key:
            labels += self.labels[i]
            col_term += [i] * self.df_of(i)
        Xw = X * self.w[:, None]
        XtX_inv = np.linalg.inv(X.T @ Xw)
        beta = XtX_inv @ Xw.T @ self.y
        r = self.y - X @ beta
        sse = float(np.sum(self.w * r ** 2))
        if sse <= 1e-14 * max(self.sst, 1e-300):     # 완전 적합: 수치 잡음을 0 으로, SE 는 '*'
            sse = 0.0
        dfe = self.n - X.shape[1]
        se = np.sqrt(np.diag(XtX_inv) * sse / dfe) if dfe > 0 and sse > 0 else np.full(X.shape[1], np.nan)
        hat = self.w * np.einsum("ij,jk,ik->i", X, XtX_inv, X)
        press = None if np.any(hat > 1 - 1e-9) else float(np.sum(self.w * (r / (1 - hat)) ** 2))
        term_p: dict[int, float | None] = {}
        for i in key:
            t = self.removal_test(set(key), i)
            term_p[i] = None if t is None else t[1]
        return StepFit(key, labels, col_term, beta, se, term_p, sse, self.sst, self.n, press, mse_full, self.log_w)


def _round(x: float) -> float:
    return float(f"{x:.12g}")


# ---------------------------------------------------------------- 결과


@dataclass
class StepwiseResult:
    options: StepwiseOptions
    candidates: list[Term]
    pre_removed: list[Term]
    steps: list[Step]
    chosen: int                              # 최종 모형이 된 단계(steps 인덱스)
    alpha_enter: float | None
    alpha_remove: float | None
    full_estimable: bool = True
    notes: list[str] = field(default_factory=list)

    @property
    def method(self) -> str:
        return self.options.method

    def title(self) -> str:
        return METHOD_TITLE[self.method]

    def method_lines(self) -> list[str]:
        """방법 세부(Details about the method)."""
        ae, ar = self.alpha_enter, self.alpha_remove
        if self.method == "stepwise":
            lines = [f"α to enter = {ae:g}, α to remove = {ar:g}"]
        elif self.method == "forward":
            lines = [f"α to enter = {ae:g}"]
        elif self.method == "backward":
            lines = [f"α to remove = {ar:g}"]
        else:
            lines = [f"Criterion: {CRITERIA[self.options.criterion]}"]
        if self.pre_removed:
            lines.append("Terms removed from the saturated model: " + ", ".join(t.name for t in self.pre_removed))
        return lines

    def candidate_line(self) -> str:
        return "Candidate terms: " + ", ".join(t.name for t in self.candidates)

    def final_terms(self) -> list[Term]:
        return [self.candidates[i] for i in self.steps[self.chosen].terms] if self.steps else []

    def effects_alpha(self, default: float) -> float:
        """효과도 유의수준: Backward·Stepwise 는 α to remove, Forward 는 α to enter."""
        if self.method in ("stepwise", "backward"):
            return float(self.alpha_remove)
        if self.method == "forward":
            return float(self.alpha_enter)
        return default

    def details_table(self, first: int = 0, count: int | None = None) -> pd.DataFrame:
        """단계별 계수·P 와 모형 요약(Include details for each step). first·count 로 일부 단계만(보고서 쪼개기)."""
        chosen_steps = list(enumerate(self.steps, start=1))[first:None if count is None else first + count]
        shown = sorted({i for _, s in chosen_steps for i in s.terms})
        label_rows: list[tuple[int, int, str]] = []          # (항, 열 순번, 이름)
        for i in shown:
            fit = next(s.fit for _, s in chosen_steps if i in s.terms)
            labs = [lab for lab, ti in zip(fit.labels, fit.col_term) if ti == i]
            label_rows += [(i, k, lab) for k, lab in enumerate(labs)]
        const = getattr(chosen_steps[0][1].fit, "has_constant", True) if chosen_steps else True
        off = 1 if const else 0
        rows = ([{"Term": "Constant"}] if const else []) + [{"Term": lab} for _, _, lab in label_rows]
        stat_names = ["S", "R-sq", "R-sq(adj)", "R-sq(pred)", "Mallows' Cp", "AICc", "BIC"]
        stat_names = [nm for nm, _ in chosen_steps[0][1].fit.stat_rows()] if chosen_steps else stat_names
        rows += [{"Term": s} for s in stat_names]
        for k, s in chosen_steps:
            ccol, pcol = f"Step {k} Coef", f"Step {k} P"
            fit = s.fit
            if const:
                rows[0][ccol] = fmt.by_se(fit.beta[0], fit.se[0])
                rows[0][pcol] = ""
            pos = {}
            for j, ti in enumerate(fit.col_term):
                if ti >= 0:
                    pos.setdefault(ti, []).append(j)
            for r, (i, kk, _) in enumerate(label_rows, start=off):
                if i in pos:
                    j = pos[i][kk]
                    rows[r][ccol] = fmt.by_se(fit.beta[j], fit.se[j])
                    pv = fit.term_p[i]
                    if kk or pv == "":
                        rows[r][pcol] = ""                    # 혼합물 성분 선형 항은 P 를 보이지 않는다
                    else:
                        rows[r][pcol] = fmt.p_text(pv) if pv is not None else fmt.MISSING
                else:
                    rows[r][ccol] = rows[r][pcol] = ""
            base = off + len(label_rows)
            vals = [v for _, v in fit.stat_rows()]
            for r, v in enumerate(vals):
                rows[base + r][ccol] = ""
                rows[base + r][pcol] = v
        return pd.DataFrame(rows).fillna("")

    def footer_lines(self) -> list[str]:
        out = []
        if self.method in ("stepwise", "forward", "backward"):
            out.append(self.method_lines()[0])
        else:
            out.append(f"Model with minimum {CRITERIA[self.options.criterion]}: Step {self.chosen + 1}")
        return out

    def step_notes(self, en: bool = False) -> list[str]:
        """단계마다 한 줄 설명."""
        out = []
        for k, s in enumerate(self.steps, start=1):
            names = lambda ids: ", ".join(self.candidates[i].name for i in ids)  # noqa: E731
            pv = f" (P = {fmt.p_text(s.p_value)})" if s.p_value is not None else ""
            if s.note == "start":
                body = (f"start: {names(s.terms)}" if s.terms else "start: constant only") if en else \
                       (f"시작 모형 — {names(s.terms)}" if s.terms else "시작 모형 — 상수만")
            elif s.note == "hierarchy":
                body = f"added for hierarchy: {names(s.entered)}" if en else f"계층을 위해 추가 — {names(s.entered)}"
            elif s.removed:
                body = f"removed {names(s.removed)}{pv}" if en else f"{names(s.removed)} 제거{pv}"
            else:
                main = s.entered[0]
                extra = [i for i in s.entered if i != main]
                body = (f"entered {self.candidates[main].name}{pv}" if en else f"{self.candidates[main].name} 추가{pv}")
                if extra:
                    body += (f" with {names(extra)}" if en else f" — 계층 유지로 {names(extra)} 함께 추가")
            mark = (" ← selected" if en else " ← 선택") if (self.method == "forward_ic" and k - 1 == self.chosen) else ""
            out.append(f"Step {k}: {body}{mark}" if en else f"{k}단계: {body}{mark}")
        return out


# ---------------------------------------------------------------- 실행


def _categorical_letters(design) -> set[str]:
    from ..designs.general_full import GeneralFullFactorialDesign
    if isinstance(design, GeneralFullFactorialDesign):
        return set(design.letters)
    return {L for L, f in zip(design.letters, design.factors) if not getattr(f, "is_numeric", True)}


def _resolve(names, cands: list[Term], what: str) -> set[int]:
    out = set()
    for nm in names:
        keys = lambda t: {t.name, getattr(t, "word", t.name), getattr(t, "short", t.name)}  # noqa: E731
        hit = [i for i, t in enumerate(cands) if nm in keys(t) or nm.replace(" ", "") == t.name.replace(" ", "")]
        if not hit:
            raise ValueError(f"{what} 항 '{nm}' 이 후보 항에 없습니다.")
        out.add(hit[0])
    return out


def _candidates(design, coded, cov, tl: list[Term], factorial: bool):
    """후보 항과 열. 요인설계는 앞 항과 완전 별칭인 항을 빼고, 반응표면·선별 설계는 열 수가 런 수 이하일 때만 뺀다."""
    n = len(coded)
    mats, labels = [], []
    for t in tl:
        M, labs = term_matrix(t, design, coded, cov)
        mats.append(M)
        labels.append(labs)
    total = 1 + sum(m.shape[1] for m in mats)
    if not factorial and total > n:
        return list(tl), mats, labels, []
    X = np.ones((n, 1))
    keep, removed = [], []
    for k, (t, M) in enumerate(zip(tl, mats)):
        cand = np.hstack([X, M])
        if _rank(cand) == cand.shape[1]:
            X = cand
            keep.append(k)
        else:
            removed.append(t)
    return [tl[k] for k in keep], [mats[k] for k in keep], [labels[k] for k in keep], removed


def select_model(design, response, coded, yv, used, tl: list[Term], cov, opts: StepwiseOptions,
                 *, factorial: bool, weights: np.ndarray | None = None, engine_factory=None, builder=None,
                 candidates=None):
    """단계적 선택으로 고른 모형의 분석 결과(.selection 에 단계 정보). weights 가 있으면 가중 회귀.

    engine_factory(cands, mats, labels, categorical, opts) 로 다른 가족(이항)의 엔진을, builder(항 목록) 로 최종 분석을
    바꿔 끼울 수 있다."""
    if candidates is not None:                # (항, 열, 이름, 별칭으로 뺀 항) — 혼합물 등 다른 항 체계
        cands, mats, labels, aliased = candidates
    else:
        cands, mats, labels, aliased = _candidates(design, coded, cov, tl, factorial)
    try:
        categorical = _categorical_letters(design)
    except AttributeError:
        categorical = set()
    if engine_factory is None:
        eng = _Engine(cands, mats, labels, yv, categorical, opts, weights)
    else:
        eng = engine_factory(cands, mats, labels, categorical, opts)
    ae, ar = opts.alphas()
    forced = _resolve(opts.force, cands, "모든 모형에 포함할")
    initial = _resolve(opts.initial, cands, "시작 모형에 포함할") if opts.method == "stepwise" else set()
    if opts.hierarchy == "each_step":
        forced_closure = eng.hierarchy_closure(forced)
    else:
        forced_closure = set(forced)
    all_idx = set(range(len(cands)))
    notes: list[str] = []

    # --- 포화 모형 선제거
    pre_removed: list[int] = []
    full_ok = eng.sse(all_idx) is not None
    if opts.method in ("stepwise", "backward") and full_ok and eng.df_error(all_idx) == 0:
        if not factorial or eng.family != "normal":
            if opts.method == "backward":
                raise ValueError("시작 모형이 자유도를 모두 써서 Backward elimination 을 진행할 수 없습니다.")
        else:
            k = min(MAX_PRE_REMOVE, max(1, int(math.floor(len(cands) / 4 + 0.5))))
            cur = set(all_idx)
            for _ in range(k):
                options = [i for i in sorted(cur) if i not in forced_closure
                           and not any(i in eng.sub_terms[j] for j in cur if j != i)]
                if not options:
                    break
                base = eng.sse(cur)
                scored = []
                for i in options:
                    s = eng.sse(cur - {i})
                    if s is not None:
                        scored.append((_round(s - base), -i, i))
                if not scored:
                    break
                drop = min(scored)[2]
                cur.discard(drop)
                pre_removed.append(drop)
            all_idx = cur
    if opts.method == "backward" and not full_ok:
        raise ValueError("후보 항이 런 수보다 많거나 서로 종속이라 완전 모형을 적합할 수 없습니다. "
                         "Backward elimination 대신 Forward 방법을 쓰세요.")
    pool = all_idx
    eng.excluded = set(range(len(cands))) - pool
    mse_full = None
    s_full = eng.sse(pool)
    if s_full is not None and eng.df_error(pool) > 0:
        mse_full = s_full / eng.df_error(pool)

    steps: list[Step] = []
    seen: set[frozenset[int]] = set()

    def record(model, **kw):
        steps.append(Step(tuple(sorted(model)), **kw))
        seen.add(frozenset(model))

    if opts.method in ("stepwise", "forward", "backward"):
        if opts.method == "backward":
            start = set(pool)
        else:
            start = set(forced_closure) | (eng.hierarchy_closure(initial) if opts.hierarchy == "each_step" else set(initial))
        if start:
            if eng.sse(start) is None or eng.df_error(start) <= 0:
                raise ValueError("시작 모형이 자유도를 모두 써서 단계적 선택을 진행할 수 없습니다.")
            record(start, note="start")
        model = set(start)
        for _ in range(1000):
            if opts.method in ("stepwise", "backward"):
                r = eng.best_removal(model, forced)
                if r is not None and r[1] > ar:
                    model = model - {r[0]}
                    if frozenset(model) in seen:
                        notes.append("cycle")
                        break
                    record(model, removed=(r[0],), p_value=r[1])
                    continue
            if opts.method in ("stepwise", "forward"):
                a = eng.best_addition(model)
                if a is not None and a[2] < ae:
                    i, group, p = a
                    model = model | group
                    if frozenset(model) in seen:
                        notes.append("cycle")
                        break
                    record(model, entered=(i, *sorted(group - {i})), p_value=p)
                    continue
            break
        if opts.hierarchy == "at_end":
            closure = eng.hierarchy_closure(model)
            missing = closure - model
            if missing:
                model = closure
                record(model, entered=tuple(sorted(missing)), note="hierarchy")
        chosen = len(steps) - 1
        if not steps:                     # 아무 항도 들어가지 않음
            record(set(), note="start")
            chosen = 0
    else:                                 # forward_ic
        start = set(forced_closure)
        if eng.sse(start) is None or eng.df_error(start) <= 0:
            raise ValueError("시작 모형이 자유도를 모두 써서 단계적 선택을 진행할 수 없습니다.")
        record(start, note="start")
        model = set(start)
        eight = not (opts.hierarchy == "each_step" and not opts.extra_terms)
        best = math.inf
        since = 0
        crit = CRITERIA[opts.criterion]

        def score(m):
            return eng.criterion(m, crit)

        best = score(model)
        while True:
            if model >= pool or eng.df_error(model) <= 1:
                break
            a = eng.best_addition(model)
            if a is None:
                break
            i, group, p = a
            model = model | group
            record(model, entered=(i, *sorted(group - {i})), p_value=p)
            c = score(model)
            if c < best:
                best, since = c, 0
            else:
                since += 1
            if eight and since >= NO_IMPROVE_STEPS:
                break
        scores = [score(set(s.terms)) for s in steps]
        chosen = int(np.argmin(scores)) if any(math.isfinite(v) for v in scores) else len(steps) - 1

    for s in steps:
        s.fit = eng.fit(s.terms, mse_full)
    result = StepwiseResult(opts, cands, [cands[i] for i in pre_removed], steps, chosen, ae, ar,
                            full_estimable=full_ok, notes=notes)
    final = [cands[i] for i in steps[chosen].terms]
    if builder is not None:
        a = builder(final)
    else:
        a = _build(design, response, coded, yv, used, final, cov, weights=weights)
    a.removed_terms = list(aliased) + a.removed_terms
    a.selection = result
    return a
