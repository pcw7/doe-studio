"""분석 화면에서 적합한 모형을 반응별로 기억해 최적화·예측 화면이 그대로 쓴다(Minitab 의 '저장 모형').

Minitab 의 Response Optimizer 는 반응마다 마지막으로 분석한 모형(stored model)을 쓴다. 분석 화면에서 항을 빼거나
단계적 선택을 했다면 최적화도 그 모형으로 해야 결과가 서로 맞는다.

정한 규칙(문서에 없는 부분)
- 같은 설계 객체일 때만 쓴다(설계를 바꾸면 — 축점 추가·반복·접기·다른 파일 — 다시 분석해야 한다).
- 분석 뒤 반응·공변량·가중치 열 값이 바뀌었으면 같은 설정으로 다시 적합한다.
- 중앙점 항(Ct Pt)이 있으면 최적화는 요인 수준 사이를 보간할 수 없으므로(문서: Ct Pt 가 모형에 있으면 등고선을 그리지
  않고 최적화기는 보간하지 않는다), 같은 요인 항·블록·공변량·Box-Cox λ·가중치로 Ct Pt 만 빼고 다시 적합한다.
- 분석하지 않은 반응은 최적화 화면에서 고른 공통 모형으로 적합한다.
"""
from __future__ import annotations

import hashlib

import numpy as np
import streamlit as st

from doe_core.analysis.factorial import analyze_worksheet

KEY = "fitted_models"

# 메모 코드 → (한글, 영어)
NOTES = {
    "analysis": ("분석 화면의 모형", "model from the Analyze page"),
    "refit_data": ("분석 뒤 값이 바뀌어 같은 설정으로 다시 적합", "refit with the same settings because the data changed"),
    "no_center": ("중앙점 항(Ct Pt)을 빼고 같은 항으로 다시 적합", "refit with the same terms without the center point term"),
    "common": ("공통 모형(분석 화면에서 분석하지 않은 반응)", "common model (response not analyzed on the Analyze page)"),
}


def _data_key(ws, response: str, kwargs: dict) -> str:
    cols = [response, *(kwargs.get("covariates") or ())]
    if kwargs.get("weights"):
        cols.append(kwargs["weights"])
    h = hashlib.sha1()
    for c in cols:
        h.update(c.encode("utf-8"))
        h.update(np.asarray(ws.column(c), dtype=float).tobytes())
    return h.hexdigest()


def remember(ws, response: str, a, kwargs: dict) -> None:
    """분석 화면에서 적합한 모형과 그 설정(analyze_worksheet 인자)을 기억한다."""
    st.session_state.setdefault(KEY, {})[response] = {"model": a, "kwargs": dict(kwargs),
                                                      "data": _data_key(ws, response, kwargs)}


def forget() -> None:
    st.session_state.pop(KEY, None)


def _without_center(ws, response: str, a, kwargs: dict):
    kw = {k: v for k, v in kwargs.items() if k in ("covariates", "weights", "units")}
    kw["terms"] = [t.word for t in a.terms if t.kind == "factor"]
    kw["include_blocks"] = any(t.kind == "blocks" for t in a.terms)
    kw["include_center"] = False
    if getattr(a, "boxcox", None) is not None:
        kw["boxcox"] = a.boxcox.lam
    return analyze_worksheet(ws, response, **kw)


def stored(ws, response: str):
    """(모형, [메모 코드]) — 쓸 수 있는 분석 화면 모형이 없으면 (None, [])."""
    rec = st.session_state.get(KEY, {}).get(response)
    if rec is None or rec["model"].design is not ws.design:
        return None, []
    notes = ["analysis"]
    if rec["data"] != _data_key(ws, response, rec["kwargs"]):
        rec["model"] = analyze_worksheet(ws, response, **rec["kwargs"])
        rec["data"] = _data_key(ws, response, rec["kwargs"])
        notes.append("refit_data")
    a = rec["model"]
    if any(getattr(t, "kind", None) == "center" for t in a.terms):
        a = _without_center(ws, response, a, rec["kwargs"])
        notes.append("no_center")
    return a, notes


def model_terms(a) -> str:
    """모형 항 이름(상수 제외)을 쉼표로."""
    return ", ".join(getattr(t, "name", None) or str(t) for t in a.terms)
