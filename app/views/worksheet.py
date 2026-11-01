"""워크시트 화면: 결과(반응) 입력, 설계 수정(Modify Design), 저장."""
import numpy as np
import pandas as pd
import streamlit as st

from app.i18n import O, T
from app.state import require_ws, set_ws, show_table, worksheet_csv, worksheet_json, ws_caption
from doe_core.designs.factorial import TwoLevelDesign
from doe_core.designs.modify import (
    display_design, fold_design, randomize_design, renumber_design, replicate_design,
)
from doe_core.designs.plackett_burman import PlackettBurmanDesign
from doe_core.designs.response_surface import add_axial_points

st.title(T("워크시트", "Worksheet"))
ws = require_ws()
st.caption(ws_caption(ws))

order = st.segmented_control(T("표시 순서", "Display order"), ["런 순서", "표준 순서"], default="런 순서", required=True,
                             format_func=O)
table = ws.table("run" if order == "런 순서" else "std")
design_cols = list(ws.design.runs.columns)

with st.form("add_col", clear_on_submit=True, border=False):
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    new_name = c1.text_input(T("반응·공변량 열 추가 (예: Yield, 순도, 반응온도)",
                               "Add a response or covariate column (e.g. Yield, Purity)"))
    if c2.form_submit_button(T("열 추가", "Add column")) and new_name.strip():
        name = new_name.strip()
        if name in table.columns:
            st.warning(T(f"'{name}' 열이 이미 있습니다.", f"Column '{name}' already exists."))
        else:
            ws.add_column(name, [np.nan] * len(table))
            st.rerun()

st.write(T("설계 열은 고칠 수 없습니다. 반응 값은 표에 바로 입력하거나 엑셀에서 붙여 넣으세요.",
           "Design columns are locked. Type responses into the table or paste them from Excel."))
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
    st.toast(T("입력한 값을 저장했습니다.", "Saved your entries."))

c1, c2, _ = st.columns([1, 1, 3])
c1.download_button(T("워크시트 저장 (.json)", "Save worksheet (.json)"), worksheet_json(ws), "doe_worksheet.json",
                   "application/json")
c2.download_button(T("CSV 내보내기"), worksheet_csv(ws), "doe_worksheet.csv", "text/csv")

st.divider()
st.subheader(T("설계 수정 (Modify Design)"))
d = ws.design
names = dict(zip(d.letters, [f.name for f in d.factors]))
foldable = isinstance(d, (TwoLevelDesign, PlackettBurmanDesign)) and not d.folded_on
t1, t2, t3, t5, t4 = st.tabs([T("접기 (Fold)"), T("반복 추가 (Replicate)"), T("랜덤화 (Randomize)"),
                              T("축점 추가 (Add axial points)"), T("코드화 단위 보기", "Coded units")])
with t1:
    if not foldable:
        st.write(T("2수준 요인설계·Plackett-Burman 설계만, 한 번만 접을 수 있습니다.",
                   "Only 2-level factorial and Plackett-Burman designs can be folded, once."))
    else:
        st.write(T("모서리점을 복제해 아래에 붙이고 접는 요인의 부호를 바꿔 별칭을 줄입니다.",
                   "Copies the corner points, flips the signs of the folded factors and reduces aliasing."))
        on = st.selectbox(T("접는 요인", "Fold on"), ["all", *d.letters],
                          format_func=lambda v: T("모든 요인 (Fold on all factors)") if v == "all" else
                          T(f"{v} ({names[v]})만", f"{v} ({names[v]}) only"))
        if st.button(T("접기", "Fold")):
            try:
                set_ws(ws.with_design(fold_design(d, on)))
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(str(e))
with t2:
    n_add = st.number_input(T("추가할 반복 수", "Replicates to add"), 1, 10, 1)
    st.write(T("중앙점을 포함한 모든 런을 복제해 새 블록으로 붙입니다. 이후 랜덤화하세요.",
               "Copies every run (including center points) into new blocks. Randomize afterwards."))
    if st.button(T("반복 추가", "Add replicates")):
        try:
            set_ws(ws.with_design(replicate_design(d, int(n_add))))
            st.rerun()
        except ValueError as e:
            st.error(str(e))
with t3:
    blocks = sorted(int(b) for b in d.coded["Blocks"].unique())
    which = st.selectbox(T("대상", "Randomize"), [None, *blocks],
                         format_func=lambda b: T("전체 설계") if b is None else T(f"블록 {b}만", f"Block {b} only"))
    seed = st.number_input(T("난수 기준값"), 0, 10_000_000, 0, key="rseed")
    c1, c2 = st.columns(2)
    if c1.button(T("랜덤화", "Randomize")):
        try:
            set_ws(ws.with_design(randomize_design(d, block=which, seed=int(seed) or None)))
            st.rerun()
        except ValueError as e:
            st.error(str(e))
    if c2.button(T("런 번호 다시 매기기 (Renumber)")):
        set_ws(ws.with_design(renumber_design(d)))
        st.rerun()
with t5:
    can_axial = isinstance(d, (TwoLevelDesign, PlackettBurmanDesign)) and all(f.is_numeric for f in d.factors)
    if not can_axial:
        st.write(T("모든 요인이 숫자인 2수준 요인설계·Plackett-Burman 설계에만 축점을 추가할 수 있습니다. "
                   "추가하면 중심합성 반응표면 설계로 바뀝니다.",
                   "Axial points can be added only to 2-level factorial and Plackett-Burman designs with all numeric "
                   "factors. The design becomes a central composite response surface design."))
    else:
        st.write(T("축점(±α)을 새 블록으로 붙여 곡면(2차 효과)을 추정할 수 있는 중심합성설계로 바꿉니다.",
                   "Adds axial points (±α) in a new block to make a central composite design that estimates curvature."))
        a_mode = st.radio(T("α 값", "Value of alpha"), ["기본 (회전 가능)", "면 중심 (α = 1)", "직접 지정"], horizontal=True,
                          format_func=lambda v: T(v, {"기본 (회전 가능)": "Default (rotatable)", "면 중심 (α = 1)":
                                                      "Face centered (α = 1)", "직접 지정": "Custom"}[v]))
        alpha = "default" if a_mode.startswith("기본") else ("face" if a_mode.startswith("면") else
                                                             st.number_input("α", 0.1, 10.0, 1.414))
        n_c = st.number_input(T("축 블록에 추가할 중앙점 수", "Center points to add to the axial block"), 0, 20, 0)
        if st.button(T("축점 추가", "Add axial points")):
            set_ws(ws.with_design(add_axial_points(d, alpha=alpha, center_points=int(n_c))))
            st.rerun()
with t4:
    show_table(display_design(d, units="coded"))
