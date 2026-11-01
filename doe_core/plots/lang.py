"""그래프·보고서 글자의 영어 변환(화면 언어 전환과 영어 보고서가 함께 쓴다).

그래프 함수는 '한글 제목 + 영어 부제', 축 제목은 '한글 (English)' 꼴로 만든다. 영어로 바꿀 때는 부제의 첫 부분을
제목으로 올리고, 괄호 속 영어를 쓰며, 범례·마우스 정보의 짧은 한글 말은 사전으로 바꾼다.
"""
from __future__ import annotations

import re

HANGUL = re.compile(r"[가-힣]")
_PAIR = re.compile(r"^(\**)(.*?)\s*\(([^()]*)\)(\**)$", re.S)

FIG_PHRASES = {
    "회색이 아닌 영역 = 모든 반응이 범위 안": "non-grey region = all responses within limits",
    "기준 혼합물에서의 편차 (비율)": "Deviation from reference blend (proportion)",
    "기준 혼합물": "reference blend", "고정값: ": "Hold: ", "고정: ": "Hold: ", "적합치 ": "Fitted ",
    "유의하지 않음": "Not significant", "유의함": "Significant", "효과 0 기준선": "Zero effect",
    "설계 영역": "Design region", "설계점": "Design points", "모서리 중점": "Edge midpoint", "3성분 혼합": "Triple blend",
    "꼭지점": "Vertex", "중심점": "Center point", "축점": "Axial point", "중앙점 적합 평균": "Center point fitted mean",
    "적합 평균": "Fitted mean", "관측치": "Obs", "잔차": "Residual", "빈도": "Frequency", "편차": "Deviation",
    "효과": "Effect", "중앙": "Center", "런 ": "Runs ", "개": "", "유형 ": "Type ",
    "평균": "Mean", "반복, 중앙점": "Reps, Center Points", "반복": "Reps", "검정력": "Power",
    "최대 차이": "Maximum Difference",
}


def english_of(ko: str) -> str | None:
    """'한글 (English)' 꼴이면 English(마크다운 굵게 유지), 아니면 None."""
    m = _PAIR.match(ko.strip())
    if m and not HANGUL.search(m.group(3)) and re.search(r"[A-Za-z]", m.group(3)) and HANGUL.search(m.group(2)):
        return f"{m.group(1)}{m.group(3)}{m.group(4)}"
    return None


def fig_text(s):
    if not isinstance(s, str) or not HANGUL.search(s):
        return s
    e = english_of(s)
    if e:
        return e
    for k in sorted(FIG_PHRASES, key=len, reverse=True):
        s = s.replace(k, FIG_PHRASES[k])
    return s


def to_english(fig):
    """그래프 글자를 영어로 바꾼 사본."""
    import plotly.graph_objects as go
    fig = go.Figure(fig)
    title = fig.layout.title
    sub = title.subtitle.text if title and title.subtitle and title.subtitle.text else None
    if sub:
        parts = sub.split(" · ")
        fig.update_layout(title_text=fig_text(parts[0]), title_subtitle_text=fig_text(" · ".join(parts[1:])))
    elif title and title.text:
        fig.update_layout(title_text=fig_text(title.text))
    for ax in [k for k in fig.layout if k.startswith(("xaxis", "yaxis"))]:
        a = fig.layout[ax]
        if a.title and a.title.text:
            a.title.text = fig_text(a.title.text)
    if fig.layout.scene:
        for ax in ("xaxis", "yaxis", "zaxis"):
            a = fig.layout.scene[ax]
            if a.title and a.title.text:
                a.title.text = fig_text(a.title.text)
    for ann in fig.layout.annotations or []:
        ann.text = fig_text(ann.text)
    for tr in fig.data:
        if getattr(tr, "name", None):
            tr.name = fig_text(tr.name)
        if getattr(tr, "hovertemplate", None):
            tr.hovertemplate = fig_text(tr.hovertemplate)
        if isinstance(getattr(tr, "text", None), (list, tuple)):
            tr.text = [fig_text(x) for x in tr.text]
    return fig
