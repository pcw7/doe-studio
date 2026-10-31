"""설계 생성 화면 — Minitab 'Create Factorial Design' · 'Create Response Surface Design'."""
import pandas as pd
import streamlit as st

from app.state import set_ws, show_table, worksheet_csv, worksheet_json
from doe_core.designs.catalog import ROMAN, available_designs
from doe_core.designs.common import Factor, factor_letters
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.general_full import GeneralFactor, create_general_full_factorial
from doe_core.designs.plackett_burman import PB_RUNS, create_plackett_burman_design
from doe_core.designs.response_surface import BBD_CATALOG, available_ccd, create_box_behnken, create_ccd
from doe_core.io.worksheet import Worksheet

st.title("설계 생성")
st.caption("요인설계 생성 (Create Factorial Design) · 반응표면 설계 생성 (Create Response Surface Design)")

kind = st.segmented_control(
    "설계 유형 (Type of Design)",
    ["2수준 요인설계", "Plackett-Burman", "일반 완전요인설계", "반응표면 설계"],
    default="2수준 요인설계", required=True,
)


def factor_editor(n: int, key: str) -> pd.DataFrame:
    letters = factor_letters(n)
    base = pd.DataFrame({"요인": letters, "이름": letters, "유형": ["숫자"] * n, "낮음": ["-1"] * n, "높음": ["1"] * n})
    return st.data_editor(
        base, key=f"{key}_{n}", hide_index=True, width="stretch", disabled=["요인"],
        column_config={"유형": st.column_config.SelectboxColumn("유형", options=["숫자", "텍스트"], required=True)},
    )


def to_factors(df: pd.DataFrame) -> list[Factor]:
    out = []
    for r in df.itertuples(index=False):
        name = str(r[1]).strip() or str(r[0])
        if r[2] == "숫자":
            out.append(Factor(name, float(r[3]), float(r[4])))
        else:
            out.append(Factor(name, str(r[3]), str(r[4]), numeric=False))
    return out


design = None
error = None

if kind == "2수준 요인설계":
    c1, c2 = st.columns([1, 2])
    with c1:
        k = st.number_input("요인 수 (Number of factors)", 2, 15, 3)
        entries = available_designs(int(k))
        labels = {e.n_runs: f"{e.n_runs}런 · {e.fraction if e.fraction != 'full' else '완전요인'}"
                         + (f" · 해상도 {ROMAN[e.resolution]}" if e.resolution else "") for e in entries}
        runs = st.selectbox("설계 (Designs)", list(labels), index=len(labels) - 1, format_func=labels.get)
        entry = [e for e in entries if e.n_runs == runs][0]
        cp = st.number_input("블록당 중앙점 수 (Center points per block)", 0, 50, 0)
        reps = st.number_input("모서리점 반복 수 (Replicates)", 1, 10, 1)
        block_opts = sorted({1, *[b * int(reps) for b in [1, *entry.blocks]], *entry.blocks})
        blocks = st.selectbox("블록 수 (Number of blocks)", block_opts)
        randomize = st.checkbox("런 랜덤화 (Randomize runs)", True)
        seed = st.number_input("난수 기준값 (Base for random data generator)", 0, 10_000_000, 0,
                               help="같은 값이면 같은 런 순서가 나옵니다. 0 이면 매번 다릅니다.")
    with c2:
        st.write("**요인 (Factors)** — 수준을 실제 값으로 바꾸세요. 텍스트 요인은 수준 이름을 적습니다.")
        fdf = factor_editor(int(k), "f2")
        st.write("**사용 가능한 설계 (Display Available Designs)**")
        show_table(pd.DataFrame([{"런": e.n_runs, "부분": e.fraction, "해상도": ROMAN.get(e.resolution, "완전") if e.resolution else "완전",
                                  "가능한 블록": ", ".join(map(str, [1, *sorted(e.blocks)]))} for e in entries]))
    if st.button("설계 생성", type="primary"):
        try:
            design = create_two_level_design(int(k), int(runs), factors=to_factors(fdf), n_blocks=int(blocks),
                                             center_points=int(cp), replicates=int(reps), randomize=randomize,
                                             seed=int(seed) or None)
        except Exception as e:  # noqa: BLE001
            error = e

elif kind == "Plackett-Burman":
    c1, c2 = st.columns([1, 2])
    with c1:
        k = st.number_input("요인 수 (Number of factors)", 2, 47, 7)
        runs_ok = [n for n in PB_RUNS if n > k]
        runs = st.selectbox("런 수 (Number of runs)", runs_ok)
        cp = st.number_input("반복당 중앙점 수 (Center points per replicate)", 0, 50, 0)
        reps = st.number_input("반복 수 (Replicates)", 1, 10, 1)
        block_reps = st.checkbox("반복별 블록 (Block on replicates)", False, disabled=reps == 1)
        randomize = st.checkbox("런 랜덤화 (Randomize runs)", True)
        seed = st.number_input("난수 기준값", 0, 10_000_000, 0)
    with c2:
        st.write("**요인 (Factors)**")
        fdf = factor_editor(int(k), "fpb")
    if st.button("설계 생성", type="primary"):
        try:
            design = create_plackett_burman_design(int(k), int(runs), factors=to_factors(fdf), center_points=int(cp),
                                                   replicates=int(reps), block_on_replicates=block_reps,
                                                   randomize=randomize, seed=int(seed) or None)
        except Exception as e:  # noqa: BLE001
            error = e

elif kind == "반응표면 설계":
    rs_kind = st.segmented_control("반응표면 설계 종류", ["중심합성설계 (CCD)", "Box-Behnken"],
                                   default="중심합성설계 (CCD)", required=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        if rs_kind.startswith("중심합성"):
            k = st.number_input("연속 요인 수 (Number of continuous factors)", 2, 10, 3)
            entries = available_ccd(int(k))
            labels = {i: f"{e.runs}런 · {e.fraction} · 블록 {e.blocks} · α {e.alpha_text}" for i, e in enumerate(entries)}
            pick = st.selectbox("설계 (Designs)", list(labels), format_func=labels.get)
            e = entries[pick]
            cp_mode = st.radio("중앙점 수 (Number of center points)", ["기본 (Default)", "직접 지정 (Custom)"], horizontal=True)
            cp = None
            if cp_mode.startswith("직접"):
                if e.blocks == 1:
                    cp = int(st.number_input("중앙점 수", 0, 50, e.center))
                else:
                    cc = st.number_input("큐브 블록당 중앙점 (Cube block)", 0, 50, e.cube_center // max(e.cube_blocks, 1))
                    ca = st.number_input("축 블록 중앙점 (Axial block)", 0, 50, e.axial_center)
                    cp = (int(cc), int(ca))
            a_mode = st.radio("α 값 (Value of Alpha)", ["기본 (Default)", "면 중심 (Face Centered)", "직접 지정 (Custom)"])
            alpha = "default" if a_mode.startswith("기본") else ("face" if a_mode.startswith("면") else
                                                                 st.number_input("α", 0.1, 10.0, float(e.default_alpha)))
            levels_define = st.radio("요인 수준 정의 (Levels Define)", ["큐브점 (Cube points)", "축점 (Axial points)"],
                                     horizontal=True)
        else:
            k = st.number_input("연속 요인 수 (Number of continuous factors)", 3, 7, 3)
            runs, block_opts, default_cp = BBD_CATALOG[int(k)]
            st.caption(f"{runs}런 · 기본 중앙점 {default_cp}개")
            blocks_bb = st.selectbox("블록 수 (Number of blocks)", list(block_opts))
            cp_bb = st.number_input("블록당 중앙점 수 (0 이면 기본)", 0, 50, 0)
        reps = st.number_input("반복 수 (Replicates)", 1, 10, 1, key="rs_reps")
        block_reps = st.checkbox("반복별 블록 (Block on replicates)", False, disabled=reps == 1, key="rs_brep")
        randomize = st.checkbox("런 랜덤화 (Randomize runs)", True, key="rs_rand")
        seed = st.number_input("난수 기준값", 0, 10_000_000, 0, key="rs_seed")
    with c2:
        st.write("**연속 요인 (Continuous Factors)** — 낮음·높음은 " +
                 ("축점 값" if kind == "반응표면 설계" and rs_kind.startswith("중심합성") and levels_define.startswith("축점")
                  else "큐브점(±1) 값") + "입니다.")
        letters = factor_letters(int(k))
        base = pd.DataFrame({"요인": letters, "이름": letters, "낮음": [-1.0] * int(k), "높음": [1.0] * int(k)})
        rdf = st.data_editor(base, key=f"rs_{rs_kind}_{k}", hide_index=True, width="stretch", disabled=["요인"])
    if st.button("설계 생성", type="primary"):
        try:
            facs = [Factor(str(r[1]).strip() or str(r[0]), float(r[2]), float(r[3])) for r in rdf.itertuples(index=False)]
            if rs_kind.startswith("중심합성"):
                design = create_ccd(int(k), fraction=e.fraction, blocks=e.blocks, factors=facs, alpha=alpha,
                                    center_points=cp, replicates=int(reps), block_on_replicates=block_reps,
                                    levels_define="axial" if levels_define.startswith("축점") else "cube",
                                    randomize=randomize, seed=int(seed) or None)
            else:
                design = create_box_behnken(int(k), blocks=int(blocks_bb), factors=facs,
                                            center_points=int(cp_bb) or None, replicates=int(reps),
                                            block_on_replicates=block_reps, randomize=randomize, seed=int(seed) or None)
        except Exception as ex:  # noqa: BLE001
            error = ex

else:
    c1, c2 = st.columns([1, 2])
    with c1:
        k = st.number_input("요인 수 (Number of factors)", 2, 15, 2)
        reps = st.number_input("반복 수 (Replicates)", 1, 10, 1)
        block_reps = st.checkbox("반복별 블록 (Block on replicates)", False, disabled=reps == 1)
        randomize = st.checkbox("런 랜덤화 (Randomize runs)", True)
        seed = st.number_input("난수 기준값", 0, 10_000_000, 0)
    with c2:
        st.write("**요인과 수준 값** — 수준 값을 쉼표로 구분해 적습니다(예: 40, 60, 80 또는 MeOH, EtOH).")
        letters = factor_letters(int(k))
        base = pd.DataFrame({"요인": letters, "이름": letters, "수준 값": ["1, 2, 3"] * int(k)})
        gdf = st.data_editor(base, key=f"gff_{k}", hide_index=True, width="stretch", disabled=["요인"])
    if st.button("설계 생성", type="primary"):
        try:
            facs = []
            for r in gdf.itertuples(index=False):
                vals = [v.strip() for v in str(r[2]).split(",") if v.strip()]
                try:
                    vals = [float(v) for v in vals]
                except ValueError:
                    pass
                facs.append(GeneralFactor(str(r[1]).strip() or str(r[0]), vals))
            design = create_general_full_factorial(facs, replicates=int(reps), block_on_replicates=block_reps,
                                                   randomize=randomize, seed=int(seed) or None)
        except Exception as e:  # noqa: BLE001
            error = e

if error is not None:
    st.error(f"설계를 만들지 못했습니다: {error}")
if design is not None:
    set_ws(Worksheet(design))
    st.session_state["created_notice"] = True

ws = st.session_state.get("worksheet")
if ws is not None and st.session_state.get("created_notice"):
    d = ws.design
    st.divider()
    st.subheader("설계 요약 (Design Summary)")
    st.code(d.summary_text(), language=None)
    if hasattr(d, "alias_text"):
        st.subheader("별칭 구조 (Alias Structure)")
        st.code(d.alias_text(), language=None)
    st.subheader("실험 순서표 (Worksheet, 런 순서)")
    show_table(d.runs)
    c1, c2, _ = st.columns([1, 1, 3])
    c1.download_button("워크시트 저장 (.json)", worksheet_json(ws), "doe_worksheet.json", "application/json")
    c2.download_button("CSV 내보내기", worksheet_csv(ws), "doe_worksheet.csv", "text/csv")
    st.page_link("views/worksheet.py", label="워크시트에서 결과 입력하기", icon=":material/table:")
