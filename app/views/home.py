"""시작 화면: 소개, 현재 워크시트, 파일 불러오기(DOE Studio JSON, Minitab .MWX, CSV)."""
import io

import pandas as pd
import streamlit as st

from app.i18n import O, T
from app.state import SAMPLES, get_ws, set_ws, worksheet_from_json, ws_caption
from doe_core.io.mwx import read_mwx
from doe_core.io.worksheet import define_custom_design, design_kind_of, load_mwx_worksheet

st.title("DOE Studio")
st.caption(T("화학 연구원을 위한 실험계획법 도구 · Minitab 의 DOE 메뉴와 같은 순서와 같은 통계 결과를 목표로 합니다.",
             "Design of experiments for chemical researchers · same workflow and statistics as Minitab's DOE menu."))

ws = get_ws()
if ws is not None:
    st.success(T("현재 워크시트: ", "Current worksheet: ") + ws_caption(ws))
else:
    st.info(T("현재 워크시트가 없습니다. 새 설계를 만들거나 파일을 불러오세요.",
              "No current worksheet. Create a new design or open a file."))

c1, c2 = st.columns(2)
with c1:
    st.subheader(T("새 실험 설계", "New experiment"))
    st.write(T("요인과 수준을 정하면 실험 순서표(런 순서)를 만들어 줍니다.",
               "Choose factors and levels to get a run sheet in run order."))
    st.page_link("views/create.py", label=T("설계 생성", "Create design"), icon=":material/grid_on:")
    st.write(T("실험을 마치면 **워크시트** 화면에서 결과를 입력하고 **분석** 화면에서 분석합니다.",
               "After the runs, enter results on the **Worksheet** page and analyze them on the **Analyze** page."))

with c2:
    st.subheader(T("파일 불러오기", "Open a file"))
    up = st.file_uploader(T("DOE Studio 워크시트(.json), Minitab 워크시트(.mwx), CSV",
                            "DOE Studio worksheet (.json), Minitab worksheet (.mwx), CSV"), type=["json", "mwx", "csv"])
    if up is not None:
        name = up.name.lower()
        if name.endswith(".json"):
            try:
                set_ws(worksheet_from_json(up.getvalue()))
                st.success(T("워크시트를 불러왔습니다.", "Worksheet loaded."))
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(T("불러오지 못했습니다: ", "Could not load: ") + str(e))
        else:
            try:
                df = read_mwx(io.BytesIO(up.getvalue())) if name.endswith(".mwx") else pd.read_csv(up)
            except Exception as e:  # noqa: BLE001
                st.error(T("파일을 읽지 못했습니다: ", "Could not read the file: ") + str(e))
                st.stop()
            st.session_state["import_df"] = df

    df = st.session_state.get("import_df")
    if df is not None:
        st.write(T("**사용자 설계 정의** — 요인(혼합물이면 성분) 열을 고르면 2수준 요인·반응표면·확정적 선별·혼합물 "
                   "설계 가운데 무엇인지 알아봅니다(Define Custom … Design).",
                   "**Define custom design** — pick the factor (or component) columns and the design type is detected: "
                   "2-level factorial, response surface, definitive screening or mixture."))
        st.dataframe(df.head(8), hide_index=True)
        reserved = {"StdOrder", "RunOrder", "CenterPt", "PtType", "Blocks"}
        candidates = [c for c in df.columns if c not in reserved]
        factors = st.multiselect(T("요인·성분 열(순서대로 A, B, C …)", "Factor / component columns (A, B, C … in order)"),
                                 candidates)
        process = st.multiselect(T("공정 변수 열(혼합물 설계일 때)", "Process variable columns (mixture designs)"),
                                 [c for c in candidates if c not in factors])
        kind_ko = {"mixture": "혼합물 설계", "dsd": "확정적 선별설계", "response_surface": "반응표면 설계",
                   "two_level": "2수준 요인설계"}
        if len(factors) >= 2:
            try:
                st.caption(T("인식한 설계 종류: ", "Detected design: ") + O(kind_ko[design_kind_of(df, factors, process)]))
            except Exception:  # noqa: BLE001
                pass
        if st.button(T("설계로 정의", "Define design"), type="primary", disabled=len(factors) < 2):
            try:
                set_ws(define_custom_design(df, factors, **({"process": process} if process else {})))
                st.session_state.pop("import_df", None)
                st.success(T("설계를 정의했습니다. 분석 화면으로 이동하세요.", "Design defined. Go to the Analyze page."))
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(T("설계로 정의하지 못했습니다: ", "Could not define the design: ") + str(e))

    examples = [
        ("InsulationProperties.MWX", T("단열재 강도 — 4요인 2수준 완전요인 16런", "Insulation strength — 4-factor 2-level full factorial, 16 runs"),
         ["Material", "InjPress", "InjTemp", "CoolTemp"]),
        ("SealStrength.MWX", T("포장 밀봉 강도 — 4요인 중심합성설계 31런", "Seal strength — 4-factor central composite, 31 runs"),
         ["HotBarT", "DwelTime", "HotBarP", "MatTemp"]),
        ("FondueRecipe.MWX", T("퐁듀 맛 — 3성분 극꼭지점 혼합물 + 공정 변수 Temperature 18런",
                               "Fondue flavor — 3-component extreme vertices mixture + process variable Temperature, 18 runs"),
         ["Emmenthaler", "Gruyere", "Broth"], {"process": ["Temperature"]}),
        ("ultrasonic_cleaner.MWX", T("초음파 세척기 출력 — 7요인 확정적 선별설계 17런",
                                     "Ultrasonic cleaner power — 7-factor definitive screening, 17 runs"),
         ["Train", "Degas", "Burst", "Quiet", "Center", "Bandwidth", "Sweep"]),
        ("CrystalGrowth.MWX", T("결정 성장 — 4요인 2블록 중심합성설계 30런(최적 설계 후보점)",
                                "Crystal growth — 4-factor 2-block central composite, 30 runs (optimal design candidates)"),
         ["A", "B", "C", "D"]),
    ]
    available = [e for e in examples if (SAMPLES / e[0]).exists()]
    if available:
        st.divider()
        st.write(T("**예제 데이터** — Minitab 문서 예제", "**Example data** — Minitab documentation examples"))
        for fname, desc, facs, *extra in available:
            if st.button(T(f"{fname.removesuffix('.MWX')} 예제 불러오기", f"Load {fname.removesuffix('.MWX')} example"),
                         help=desc):
                set_ws(load_mwx_worksheet(SAMPLES / fname, facs, **(extra[0] if extra else {})))
                st.rerun()
