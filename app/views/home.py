"""시작 화면: 소개, 현재 워크시트, 파일 불러오기(DOE Studio JSON, Minitab .MWX, CSV)."""
import io

import pandas as pd
import streamlit as st

from app.state import SAMPLES, get_ws, set_ws, worksheet_from_json, ws_caption
from doe_core.io.mwx import read_mwx
from doe_core.io.worksheet import define_custom_two_level

st.title("DOE Studio")
st.caption("화학 연구원을 위한 실험계획법 도구 · Minitab 의 DOE 메뉴와 같은 순서와 같은 통계 결과를 목표로 합니다.")

ws = get_ws()
if ws is not None:
    st.success(f"현재 워크시트: {ws_caption(ws)}")
else:
    st.info("현재 워크시트가 없습니다. 새 설계를 만들거나 파일을 불러오세요.")

c1, c2 = st.columns(2)
with c1:
    st.subheader("새 실험 설계")
    st.write("요인과 수준을 정하면 실험 순서표(런 순서)를 만들어 줍니다.")
    st.page_link("views/create.py", label="설계 생성", icon=":material/grid_on:")
    st.write("실험을 마치면 **워크시트** 화면에서 결과를 입력하고 **분석** 화면에서 분석합니다.")

with c2:
    st.subheader("파일 불러오기")
    up = st.file_uploader("DOE Studio 워크시트(.json), Minitab 워크시트(.mwx), CSV", type=["json", "mwx", "csv"])
    if up is not None:
        name = up.name.lower()
        if name.endswith(".json"):
            try:
                set_ws(worksheet_from_json(up.getvalue()))
                st.success("워크시트를 불러왔습니다.")
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"불러오지 못했습니다: {e}")
        else:
            try:
                df = read_mwx(io.BytesIO(up.getvalue())) if name.endswith(".mwx") else pd.read_csv(up)
            except Exception as e:  # noqa: BLE001
                st.error(f"파일을 읽지 못했습니다: {e}")
                st.stop()
            st.session_state["import_df"] = df

    df = st.session_state.get("import_df")
    if df is not None:
        st.write("**사용자 2수준 설계 정의** — 요인 열을 고르면 설계로 인식합니다(Define Custom Factorial Design).")
        st.dataframe(df.head(8), hide_index=True)
        reserved = {"StdOrder", "RunOrder", "CenterPt", "PtType", "Blocks"}
        candidates = [c for c in df.columns if c not in reserved]
        factors = st.multiselect("요인 열(순서대로 A, B, C …)", candidates)
        if st.button("설계로 정의", type="primary", disabled=len(factors) < 2):
            try:
                set_ws(define_custom_two_level(df, factors))
                st.session_state.pop("import_df", None)
                st.success("설계를 정의했습니다. 분석 화면으로 이동하세요.")
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"설계로 정의하지 못했습니다: {e}")

    sample = SAMPLES / "InsulationProperties.MWX"
    if sample.exists():
        st.divider()
        st.write("**예제 데이터** — Minitab 문서 예제(단열재 강도, 4요인 완전요인 16런)")
        if st.button("InsulationProperties 예제 불러오기"):
            set_ws(define_custom_two_level(read_mwx(sample), ["Material", "InjPress", "InjTemp", "CoolTemp"]))
            st.rerun()
