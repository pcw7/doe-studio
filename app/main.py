"""DOE Studio 진입점: `streamlit run app/main.py`"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="DOE Studio", page_icon="🧪", layout="wide")

from app.i18n import LANGS, T, install_placeholders  # noqa: E402
from app.state import autosave_current  # noqa: E402

install_placeholders()
if st.session_state.get("lang") not in LANGS:
    st.session_state["lang"] = "ko"
with st.sidebar:
    st.segmented_control("언어 · Language", list(LANGS), key="lang", format_func=LANGS.get, required=True)
    if st.session_state.get("autosave_time") is not None:
        st.caption(T(f"작업 자동 저장 {st.session_state['autosave_time']:%H:%M:%S} · 이 컴퓨터",
                     f"Work autosaved {st.session_state['autosave_time']:%H:%M:%S} · this computer"),
                   help=T("새로 고치거나 창을 닫아도 시작 화면의 '이전 작업 이어서 하기' 로 되살릴 수 있습니다.",
                          "After a reload or closing the window, restore it with 'Continue previous work' on the Home page."))

VIEWS = Path(__file__).parent / "views"
pages = {
    "DOE Studio": [
        st.Page(VIEWS / "home.py", title=T("시작", "Home"), icon=":material/home:", default=True),
        st.Page(VIEWS / "help.py", title=T("도움말", "Help"), icon=":material/help:", url_path="help"),
    ],
    T("실험계획 (DOE)", "Design of Experiments"): [
        st.Page(VIEWS / "create.py", title=T("설계 생성", "Create design"), icon=":material/grid_on:", url_path="create"),
        st.Page(VIEWS / "worksheet.py", title=T("워크시트·설계 수정", "Worksheet & modify design"), icon=":material/table:",
                url_path="worksheet"),
        st.Page(VIEWS / "analyze.py", title=T("분석·그래프", "Analyze & graphs"), icon=":material/monitoring:",
                url_path="analyze"),
        st.Page(VIEWS / "optimize.py", title=T("반응 최적화·예측", "Response optimizer & predict"), icon=":material/tune:",
                url_path="optimize"),
        st.Page(VIEWS / "variability.py", title=T("산포 분석", "Analyze variability"), icon=":material/stacked_line_chart:",
                url_path="variability"),
        st.Page(VIEWS / "binary.py", title=T("이항 반응 분석", "Analyze binary response"), icon=":material/rule:",
                url_path="binary"),
        st.Page(VIEWS / "optimal.py", title=T("최적 설계", "Optimal design"), icon=":material/filter_alt:",
                url_path="optimal"),
        st.Page(VIEWS / "power.py", title=T("검정력·표본 크기", "Power & sample size"), icon=":material/speed:",
                url_path="power"),
    ],
}
try:
    st.navigation(pages).run()
finally:                     # st.rerun()·st.stop() 으로 끝나도 바뀐 워크시트를 저장한다
    autosave_current()
