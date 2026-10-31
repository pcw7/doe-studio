"""워크시트 화면: 결과(반응) 입력, 설계 수정(Modify Design), 저장."""
import numpy as np
import pandas as pd
import streamlit as st

from app.state import require_ws, set_ws, show_table, worksheet_csv, worksheet_json, ws_caption
from doe_core.designs.factorial import TwoLevelDesign
from doe_core.designs.modify import (
    display_design, fold_design, randomize_design, renumber_design, replicate_design,
)
from doe_core.designs.plackett_burman import PlackettBurmanDesign

st.title("워크시트")
ws = require_ws()
st.caption(ws_caption(ws))

order = st.segmented_control("표시 순서", ["런 순서", "표준 순서"], default="런 순서", required=True)
table = ws.table("run" if order == "런 순서" else "std")
design_cols = list(ws.design.runs.columns)

with st.form("add_col", clear_on_submit=True, border=False):
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    new_name = c1.text_input("반응·공변량 열 추가 (예: Yield, 순도, 반응온도)")
    if c2.form_submit_button("열 추가") and new_name.strip():
        name = new_name.strip()
        if name in table.columns:
            st.warning(f"'{name}' 열이 이미 있습니다.")
        else:
            ws.add_column(name, [np.nan] * len(table))
            st.rerun()

st.write("설계 열은 고칠 수 없습니다. 반응 값은 표에 바로 입력하거나 엑셀에서 붙여 넣으세요.")
edited = st.data_editor(
    table, key=f"editor_{order}_{len(ws.columns.columns)}_{ws.design.n_runs}", hide_index=True, width="stretch",
    disabled=design_cols, num_rows="fixed",
)
extra = [c for c in edited.columns if c not in design_cols]


def _clean(col: pd.Series) -> pd.Series:
    """빈 칸은 결측, 모두 숫자로 읽히면 숫자 열, 아니면 텍스트 열."""
    s = col.replace("", np.nan)
    num = pd.to_numeric(s, errors="coerce")
    return num if num.notna().sum() == s.notna().sum() else s


if extra and not edited[extra].equals(table[extra]):
    for c in extra:
        ws.add_column(c, _clean(edited[c]).tolist(), order="run" if order == "런 순서" else "std")
    st.toast("입력한 값을 저장했습니다.")

c1, c2, _ = st.columns([1, 1, 3])
c1.download_button("워크시트 저장 (.json)", worksheet_json(ws), "doe_worksheet.json", "application/json")
c2.download_button("CSV 내보내기", worksheet_csv(ws), "doe_worksheet.csv", "text/csv")

st.divider()
st.subheader("설계 수정 (Modify Design)")
d = ws.design
foldable = isinstance(d, (TwoLevelDesign, PlackettBurmanDesign)) and not d.folded_on
t1, t2, t3, t4 = st.tabs(["접기 (Fold)", "반복 추가 (Replicate)", "랜덤화 (Randomize)", "코드화 단위 보기"])
with t1:
    if not foldable:
        st.write("2수준 요인설계·Plackett-Burman 설계만, 한 번만 접을 수 있습니다.")
    else:
        st.write("모서리점을 복제해 아래에 붙이고 접는 요인의 부호를 바꿔 별칭을 줄입니다.")
        on = st.selectbox("접는 요인", ["all", *d.letters],
                          format_func=lambda v: "모든 요인 (Fold on all factors)" if v == "all" else
                          f"{v} ({dict(zip(d.letters, [f.name for f in d.factors]))[v]})만")
        if st.button("접기"):
            try:
                set_ws(ws.with_design(fold_design(d, on)))
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(str(e))
with t2:
    n_add = st.number_input("추가할 반복 수", 1, 10, 1)
    st.write("중앙점을 포함한 모든 런을 복제해 새 블록으로 붙입니다. 이후 랜덤화하세요.")
    if st.button("반복 추가"):
        set_ws(ws.with_design(replicate_design(d, int(n_add))))
        st.rerun()
with t3:
    blocks = sorted(int(b) for b in d.coded["Blocks"].unique())
    which = st.selectbox("대상", ["전체 설계", *[f"블록 {b}만" for b in blocks]])
    seed = st.number_input("난수 기준값", 0, 10_000_000, 0, key="rseed")
    c1, c2 = st.columns(2)
    if c1.button("랜덤화"):
        blk = None if which == "전체 설계" else int(which.split()[1].rstrip("만"))
        set_ws(ws.with_design(randomize_design(d, block=blk, seed=int(seed) or None)))
        st.rerun()
    if c2.button("런 번호 다시 매기기 (Renumber)"):
        set_ws(ws.with_design(renumber_design(d)))
        st.rerun()
with t4:
    show_table(display_design(d, units="coded"))
