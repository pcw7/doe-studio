"""설계 생성 화면 — Minitab 'Create Factorial / Screening / Response Surface / Mixture Design'."""
import pandas as pd
import streamlit as st

from app.state import set_ws, show_table, worksheet_csv, worksheet_json
from doe_core.designs.catalog import ROMAN, available_designs
from doe_core.designs.common import Factor, factor_letters
from doe_core.designs.definitive_screening import MAX_FACTORS as DSD_MAX, base_runs_for, create_definitive_screening
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.general_full import GeneralFactor, create_general_full_factorial
from doe_core.designs.mixture import (
    LATTICE_MAX_Q, Component, LinearConstraint, MixtureDesign, create_extreme_vertices, create_simplex_centroid,
    create_simplex_lattice, mix_letters,
)
from doe_core.designs.plackett_burman import PB_RUNS, create_plackett_burman_design
from doe_core.designs.response_surface import BBD_CATALOG, available_ccd, create_box_behnken, create_ccd
from doe_core.designs.split_plot import MAX_FACTORS as SP_MAX, available_split_plot, create_split_plot_design
from doe_core.io.worksheet import Worksheet

st.title("설계 생성")
st.caption("요인설계 · 선별 설계 · 반응표면 설계 · 혼합물 설계 생성 (Create … Design)")

kind = st.segmented_control(
    "설계 유형 (Type of Design)",
    ["2수준 요인설계", "분할구 설계", "Plackett-Burman", "확정적 선별설계", "일반 완전요인설계", "반응표면 설계",
     "혼합물 설계"],
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

elif kind == "분할구 설계":
    c1, c2 = st.columns([1, 2])
    with c1:
        k = st.number_input("총 요인 수 (Total number of factors)", 2, SP_MAX, 4)
        h = st.number_input("바꾸기 어려운 요인 수 (Number of hard-to-change factors)", 1, int(k) - 1, 1)
        opts = available_split_plot(int(k), int(h))
        if not opts:
            st.warning("이 조합으로 만들 수 있는 설계가 없습니다.")
            st.stop()
        pick = st.selectbox("설계 (Designs)", range(len(opts)), index=len(opts) - 1,
                            format_func=lambda i: opts[i].label
                            + (f" · 해상도 {ROMAN[opts[i].resolution]}" if opts[i].resolution else ""))
        wp_reps = st.number_input("전구 반복 수 (Number of whole-plot replicates)", 1, 10, 2,
                                  help="1 이면 바꾸기 어려운 요인의 유의성을 검정할 수 없는 설계가 많아 기본값이 2 입니다.")
        sp_reps = st.number_input("하위구 반복 수 (Number of subplot replicates)", 1, 10, 1)
        block_reps = st.checkbox("반복별 블록 (Block on replicates)", False, disabled=wp_reps == 1, key="sp_brep")
        randomize = st.checkbox("런 랜덤화 (Randomize runs)", True, key="sp_rand",
                                help="전구 순서와 전구 안의 런 순서를 각각 섞습니다.")
        seed = st.number_input("난수 기준값", 0, 10_000_000, 0, key="sp_seed")
    with c2:
        st.write(f"**요인 (Factors)** — 앞의 {int(h)}개(A…)가 바꾸기 어려운 요인입니다.")
        fdf = factor_editor(int(k), "fsp")
    if st.button("설계 생성", type="primary"):
        try:
            design = create_split_plot_design(int(k), int(h), opts[pick].n_runs, factors=to_factors(fdf),
                                              wp_replicates=int(wp_reps), subplot_replicates=int(sp_reps),
                                              block_on_replicates=block_reps, randomize=randomize,
                                              seed=int(seed) or None)
        except Exception as e:  # noqa: BLE001
            error = e

elif kind == "확정적 선별설계":
    c1, c2 = st.columns([1, 2])
    with c1:
        k = st.number_input("요인 수 (Number of factors)", 2, DSD_MAX, 6)
        reps = st.number_input("반복 수 (Number of replicates)", 1, 10, 1, key="dsd_reps")
        divisors = [b for b in range(1, int(reps) + 1) if int(reps) % b == 0]
        blocks = st.selectbox("블록 수 (Number of blocks)", divisors, help="블록마다 같은 수의 반복이 들어갑니다.")
        randomize = st.checkbox("런 랜덤화 (Randomize runs)", True, key="dsd_rand")
        seed = st.number_input("난수 기준값", 0, 10_000_000, 0, key="dsd_seed")
    with c2:
        st.write("**요인 (Factors)** — 텍스트 요인은 2수준만 씁니다(반복당 중앙점이 2개가 됩니다).")
        fdf = factor_editor(int(k), "fdsd")
        n_text = int((fdf["유형"] == "텍스트").sum())
        st.caption(f"기본 런 수 {base_runs_for(int(k), n_text)} (요인 {int(k)}개"
                   + (f", 텍스트 요인 {n_text}개" if n_text else "") + ")")
    if st.button("설계 생성", type="primary"):
        try:
            design = create_definitive_screening(int(k), factors=to_factors(fdf), replicates=int(reps),
                                                 n_blocks=int(blocks), randomize=randomize, seed=int(seed) or None)
        except Exception as e:  # noqa: BLE001
            error = e

elif kind == "혼합물 설계":
    mix_kind = st.segmented_control("혼합물 설계 종류", ["단순 중심 (Simplex centroid)", "단순 격자 (Simplex lattice)",
                                                   "극꼭지점 (Extreme vertices)"],
                                    default="단순 중심 (Simplex centroid)", required=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        q = int(st.number_input("성분 수 (Number of components)", 2, 20, 3))
        degree = 1
        if mix_kind.startswith("단순 격자"):
            max_deg = max(m for m, mq in LATTICE_MAX_Q.items() if mq >= q)
            degree = int(st.number_input("격자 차수 (Degree of lattice)", 1, max_deg, min(2, max_deg)))
        elif mix_kind.startswith("극꼭지점"):
            degree = int(st.number_input("설계 차수 (Degree of design)", 1, max(1, q - 1), 1))
        center = st.checkbox("중앙점 추가 (Augment the design with a center point)", True,
                             disabled=mix_kind.startswith("단순 중심"), help="단순 중심 설계에는 이미 중심점이 있습니다.")
        axial = st.checkbox("축점 추가 (Augment the design with axial points)", True)
        total = st.number_input("혼합 총량 (Total mixture amount)", 0.0001, 1_000_000.0, 1.0, format="%.4f")
        n_proc = int(st.number_input("공정 변수 수 (Process variables, 2수준)", 0, 7, 0))
        reps = st.number_input("반복 수 (Replicates)", 1, 10, 1, key="mix_reps")
        randomize = st.checkbox("런 랜덤화 (Randomize runs)", True, key="mix_rand")
        seed = st.number_input("난수 기준값", 0, 10_000_000, 0, key="mix_seed")
    with c2:
        st.write("**성분 (Components)** — 하한·상한은 혼합 총량 기준의 양으로 적습니다.")
        letters = mix_letters(q)
        cbase = pd.DataFrame({"성분": letters, "이름": letters, "하한": [0.0] * q, "상한": [float(total)] * q})
        cdf = st.data_editor(cbase, key=f"mixc_{q}_{total}", hide_index=True, width="stretch", disabled=["성분"])
        cons_df = None
        if mix_kind.startswith("극꼭지점"):
            st.write("**선형 제약 (Linear Constraints)** — 행마다 계수와 하한·상한(빈 칸은 제한 없음), 최대 10개.")
            cons_df = st.data_editor(pd.DataFrame(columns=[*letters, "하한", "상한"], dtype=float), key=f"mixlc_{q}",
                                     num_rows="dynamic", hide_index=True, width="stretch")
        pdf = None
        if n_proc:
            st.write("**공정 변수 (Process Variables)**")
            pbase = pd.DataFrame({"변수": [f"X{i + 1}" for i in range(n_proc)], "이름": [f"X{i + 1}" for i in range(n_proc)],
                                  "낮음": [-1.0] * n_proc, "높음": [1.0] * n_proc})
            pdf = st.data_editor(pbase, key=f"mixp_{n_proc}", hide_index=True, width="stretch", disabled=["변수"])
    if st.button("설계 생성", type="primary"):
        try:
            comps = [Component(str(r[1]).strip() or str(r[0]), float(r[2]) / float(total), float(r[3]) / float(total))
                     for r in cdf.itertuples(index=False)]
            procs = [Factor(str(r[1]).strip() or str(r[0]), float(r[2]), float(r[3]))
                     for r in pdf.itertuples(index=False)] if pdf is not None else None
            common = dict(components=comps, process=procs, axial=axial, total=float(total), replicates=int(reps),
                          randomize=randomize, seed=int(seed) or None)
            if mix_kind.startswith("단순 중심"):
                design = create_simplex_centroid(q, **common)
            elif mix_kind.startswith("단순 격자"):
                design = create_simplex_lattice(q, degree, center=center, **common)
            else:
                cons = []
                for r in (cons_df.dropna(how="all").itertuples(index=False) if cons_df is not None else []):
                    coefs = {L: float(v) if pd.notna(v) else 0.0 for L, v in zip(letters, r[:q])}
                    lo, hi = r[q], r[q + 1]
                    cons.append(LinearConstraint(coefs, None if pd.isna(lo) else float(lo) / float(total),
                                                 None if pd.isna(hi) else float(hi) / float(total)))
                design = create_extreme_vertices(q, constraints=cons, degree=degree, center=center, **common)
        except Exception as e:  # noqa: BLE001
            error = e

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
    if isinstance(d, MixtureDesign):
        c1, c2 = st.columns(2)
        with c1:
            if d.boundaries:
                st.markdown("**경계 수 (Number of Boundaries for Each Dimension)**")
                show_table(d.boundaries_table())
            st.markdown("**점 유형별 설계점 수 (Number of Design Points for Each Type)**")
            show_table(d.points_table())
        with c2:
            st.markdown("**성분 범위 (Bounds of Mixture Components)**")
            show_table(d.bounds_table())
            if d.constraints:
                st.markdown("**선형 제약 (Linear Constraints of Mixture Components)**")
                show_table(d.constraints_table())
        if d.q >= 3:
            from app.state import plot_mode, show_plot
            from doe_core.plots.mixture_plots import simplex_design_plot
            show_plot(simplex_design_plot(d, mode=plot_mode()))
    if hasattr(d, "design_table"):
        with st.expander("설계표 (Design Table)"):
            show_table(d.design_table())
    st.subheader("실험 순서표 (Worksheet, 런 순서)")
    show_table(d.runs)
    c1, c2, _ = st.columns([1, 1, 3])
    c1.download_button("워크시트 저장 (.json)", worksheet_json(ws), "doe_worksheet.json", "application/json")
    c2.download_button("CSV 내보내기", worksheet_csv(ws), "doe_worksheet.csv", "text/csv")
    st.page_link("views/worksheet.py", label="워크시트에서 결과 입력하기", icon=":material/table:")
