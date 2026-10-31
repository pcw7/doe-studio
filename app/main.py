"""DOE Studio 진입점: `streamlit run app/main.py`"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="DOE Studio", page_icon="🧪", layout="wide")

VIEWS = Path(__file__).parent / "views"
pages = {
    "DOE Studio": [
        st.Page(VIEWS / "home.py", title="시작", icon=":material/home:", default=True),
    ],
    "요인 설계 (Factorial)": [
        st.Page(VIEWS / "create.py", title="설계 생성", icon=":material/grid_on:", url_path="create"),
        st.Page(VIEWS / "worksheet.py", title="워크시트·설계 수정", icon=":material/table:", url_path="worksheet"),
        st.Page(VIEWS / "analyze.py", title="분석·그래프", icon=":material/monitoring:", url_path="analyze"),
    ],
}
st.navigation(pages).run()
