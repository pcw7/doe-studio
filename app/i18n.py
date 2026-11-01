"""화면 언어(한국어·English) 전환.

- T(ko, en): 화면 글자. 영어 모드면 en, en 을 주지 않았으면 '한글 (English)' 꼴의 괄호 속 영어를 쓴다
  ('**요인 (Factors)**' → '**Factors**'). 둘 다 없으면 한글 그대로.
- O(value): 선택지 표시용(값은 한글 그대로 두고 보이는 글자만 바꿈). OPTIONS 사전을 쓴다.
- figure(fig): 그래프의 제목·축·범례·주석·마우스 정보를 영어로. 그래프 함수는 '한글 제목 + 영어 부제'로 만들므로
  영어 모드에서는 부제의 첫 부분을 제목으로 올린다.
결과표(계수표·분산분석표 등)는 Minitab 과 같은 영어라 바꾸지 않는다.
"""
from __future__ import annotations

import streamlit as st

from doe_core.plots.lang import english_of, to_english

LANGS = {"ko": "한국어", "en": "English"}


_LAST = {"lang": "ko"}     # 앱 실행 문맥 밖(테스트 도구가 표시 함수를 다시 부를 때)에서 쓸 마지막 언어


def _in_run() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ImportError:  # pragma: no cover
        return True
    return get_script_run_ctx() is not None


def lang() -> str:
    if not _in_run():
        return _LAST["lang"]
    try:
        value = st.session_state.get("lang", "ko")
    except Exception:  # noqa: BLE001
        return _LAST["lang"]
    _LAST["lang"] = value
    return value


def is_en() -> bool:
    return lang() == "en"


def T(ko: str, en: str | None = None) -> str:
    if not is_en():
        return ko
    if en is not None:
        return en
    return english_of(ko) or OPTIONS.get(ko) or ko


def O(value) -> str:
    """선택지 표시 글자."""
    s = str(value)
    return T(s, OPTIONS.get(s))


# 여러 화면에서 쓰는 선택지·짧은 말
OPTIONS = {
    # 설계 종류
    "2수준 요인설계": "2-level factorial", "분할구 설계": "Split-plot", "Plackett-Burman": "Plackett-Burman",
    "확정적 선별설계": "Definitive screening", "일반 완전요인설계": "General full factorial",
    "반응표면 설계": "Response surface", "혼합물 설계": "Mixture", "2수준 분할구 설계": "2-level split-plot",
    "Plackett-Burman 설계": "Plackett-Burman design",
    "Taguchi 설계": "Taguchi", "2-level": "2-level", "3-level": "3-level", "4-level": "4-level", "5-level": "5-level",
    "mixed 2-3": "Mixed 2-3 level", "mixed 2-4": "Mixed 2-4 level", "mixed 2-8": "Mixed 2-8 level",
    "mixed 3-6": "Mixed 3-6 level",
    "중심합성설계 (CCD)": "Central composite (CCD)", "Box-Behnken": "Box-Behnken",
    "단순 중심 (Simplex centroid)": "Simplex centroid", "단순 격자 (Simplex lattice)": "Simplex lattice",
    "극꼭지점 (Extreme vertices)": "Extreme vertices",
    # 요인 유형·목표
    "숫자": "Numeric", "텍스트": "Text", "최대화": "Maximize", "최소화": "Minimize", "목표값": "Target",
    # 모형
    "linear": "Linear", "linear+squares": "Linear + squares", "linear+interactions": "Linear + interactions",
    "full quadratic": "Full quadratic", "quadratic": "Quadratic", "special cubic": "Special cubic",
    "full cubic": "Full cubic", "special quartic": "Special quartic", "full quartic": "Full quartic",
    "선형": "Linear", "선형 + 제곱": "Linear + squares", "선형 + 교호작용": "Linear + interactions",
    "완전 2차": "Full quadratic", "2차": "Quadratic", "특수 3차": "Special cubic", "완전 3차": "Full cubic",
    "특수 4차": "Special quartic", "완전 4차": "Full quartic",
    "proportions": "Proportions", "pseudocomponents": "Pseudocomponents", "amounts": "Amounts",
    # 잔차·방향·순서
    "regular": "Regular", "standardized": "Standardized", "deleted": "Deleted", "일반": "Regular",
    "표준화": "Standardized", "삭제": "Deleted", "cox": "Cox (proportion)", "piepel": "Piepel (pseudocomponent)",
    "런 순서": "Run order", "표준 순서": "Standard order",
    # 자주 쓰는 말
    "모형 종류로 지정": "By model type", "차수로 지정": "By order", "항 직접 선택": "Select terms",
    "기본 (Default)": "Default", "직접 지정 (Custom)": "Custom", "면 중심 (Face Centered)": "Face centered",
    "큐브점 (Cube points)": "Cube points", "축점 (Axial points)": "Axial points",
    "전체 설계": "Entire design", "결과": "Results", "분석": "Analyze", "최적화": "Optimize", "실행": "Run",
    "설계 생성": "Create design", "난수 기준값": "Base for random data generator", "X 축": "X axis", "Y 축": "Y axis",
    "등고선 수": "Number of contours", "유의 수준 α": "Significance level α", "잔차 종류": "Residual type",
    "그래프 포함": "Include graphs", "보고서 만들기": "Build report", "CSV 내보내기": "Export CSV",
    "워크시트로 가기": "Go to worksheet", "설계 생성으로 가기": "Go to Create design",
    "설계 선택 (Select)": "Select design", "설계 증강·개선 (Augment/improve)": "Augment/improve design",
    "설계 평가 (Evaluate)": "Evaluate design", "D-최적성 (D-optimality)": "D-optimality",
    "거리 기반 (Distance-based)": "Distance-based", "교환 (Exchange)": "Exchange", "Fedorov": "Fedorov",
    "개선 안 함": "No improvement", "한국어": "한국어", "English": "English",
}


def figure(fig):
    """영어 모드면 그래프 글자를 영어로 바꾼 사본, 아니면 그대로."""
    return to_english(fig) if is_en() else fig
