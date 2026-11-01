"""화면 공통: 세션의 워크시트, 그래프 테마, 표 표시, 파일 내보내기."""
from __future__ import annotations

import html
import io
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from app.i18n import O, T
from app.i18n import figure as _figure_lang
from doe_core.io import autosave
from doe_core.io.worksheet import Worksheet, file_stem, worksheet_from_dict, worksheet_to_dict

KEY = "worksheet"
ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "minitab_samples"

DESIGN_KIND_KO = {
    "TwoLevelDesign": "2수준 요인설계",
    "PlackettBurmanDesign": "Plackett-Burman 설계",
    "GeneralFullFactorialDesign": "일반 완전요인설계",
    "ResponseSurfaceDesign": "반응표면 설계",
    "MixtureDesign": "혼합물 설계",
    "DefinitiveScreeningDesign": "확정적 선별설계",
    "SplitPlotDesign": "2수준 분할구 설계",
    "TaguchiDesign": "Taguchi 설계",
}
# 저장 형식의 design.type → 클래스 이름(자동 저장 목록 표시용)
SAVED_TYPE_CLASS = {"two_level": "TwoLevelDesign", "plackett_burman": "PlackettBurmanDesign",
                    "general_full": "GeneralFullFactorialDesign", "response_surface": "ResponseSurfaceDesign",
                    "mixture": "MixtureDesign", "definitive_screening": "DefinitiveScreeningDesign",
                    "split_plot": "SplitPlotDesign", "taguchi": "TaguchiDesign"}


def get_ws() -> Worksheet | None:
    return st.session_state.get(KEY)


def set_ws(ws: Worksheet | None, *, new: bool = True) -> None:
    """현재 워크시트를 바꾼다. new=True(새 설계·다른 파일)면 자동 저장 칸을 새로 잡고, 설계 수정은 new=False."""
    st.session_state[KEY] = ws
    st.session_state.pop("analysis", None)
    st.session_state.pop("fitted_models", None)
    if new:
        st.session_state["autosave_slot"] = autosave.new_slot()
        st.session_state.pop("autosave_hash", None)


def autosave_current() -> None:
    """화면을 다 그린 뒤(main.py) 워크시트가 바뀌었으면 이 컴퓨터에 저장한다. 실패해도 화면은 막지 않는다."""
    ws = get_ws()
    if ws is None or autosave.autosave_dir() is None:
        return
    try:
        h = autosave.fingerprint(ws)
        if st.session_state.get("autosave_hash") == h:
            return
        if "autosave_slot" not in st.session_state:
            st.session_state["autosave_slot"] = autosave.new_slot()
        autosave.save(st.session_state["autosave_slot"], ws)
        st.session_state["autosave_hash"] = h
        st.session_state["autosave_time"] = datetime.now()
    except Exception as e:  # noqa: BLE001
        st.session_state["autosave_error"] = f"{type(e).__name__}: {e}"


def restore_autosave(slot: str) -> None:
    """자동 저장한 작업을 현재 워크시트로 되살리고 같은 칸에 이어서 저장한다."""
    ws = autosave.load(slot)
    set_ws(ws, new=False)
    st.session_state["autosave_slot"] = slot
    st.session_state["autosave_hash"] = autosave.fingerprint(ws)


def plot_mode() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:  # noqa: BLE001
        return "light"


def show_plot(fig) -> None:
    st.plotly_chart(_figure_lang(fig), theme=None, width="stretch", config={"displaylogo": False})


def _numeric_like(col: pd.Series) -> bool:
    """숫자 열이거나, 글자 열이라도 값이 모두 숫자·구간·백분율 꼴(예: '(29.45, 35.22)', '98.02%', '*')이면 참."""
    if pd.api.types.is_numeric_dtype(col):
        return True
    vals = [str(v).strip() for v in col if str(v).strip() not in ("", "nan", "None")]
    if not vals:
        return True
    for v in vals:
        s = v.replace("(", "").replace(")", "").replace("%", "").replace(",", " ").replace("*", "")
        try:
            [float(x) for x in s.split()] or [0.0]
        except ValueError:
            return False
    return True


def boxcox_input(key: str, *, allow_custom: bool = True):
    """Box-Cox 변환 선택(Options > Box-Cox transformation). (boxcox 인자, 반올림 여부)."""
    KO = {"none": ("변환 없음", "No transformation"), "optimal": ("최적 λ", "Optimal λ"),
          "0": ("λ = 0 (자연로그)", "λ = 0 (natural log)"), "0.5": ("λ = 0.5 (제곱근)", "λ = 0.5 (square root)"),
          "custom": ("λ 직접 입력", "λ")}
    opts = list(KO) if allow_custom else ["none", "optimal", "0", "0.5"]
    c1, c2 = st.columns(2)
    choice = c1.selectbox(T("Box-Cox 변환 (Box-Cox transformation)"), opts, format_func=lambda v: T(*KO[v]), key=key)
    rounded = True
    if choice == "none":
        return None, True
    if choice == "optimal":
        rounded = c2.checkbox(T("반올림한 λ 사용(0.5 단위) (Use rounded λ)"), value=True, key=f"{key}_round")
        return "optimal", rounded
    if choice == "custom":
        return float(c2.number_input("λ", -2.0, 2.0, 1.0, step=0.5, key=f"{key}_lam")), True
    return float(choice), True


# 표 행 높이(px). 글자 크기(본문 14px)에 맞춰 행·머리 높이를 정하고 표 높이를 행 수로 계산한다
# — 기본 행 높이를 가정하면 글자 크기를 바꿀 때 표 아래에 빈 행이 남는다.
ROW_HEIGHT = 34


def table_height(rows: int) -> int:
    return ROW_HEIGHT * (rows + 1) + 1


def show_table(df: pd.DataFrame, *, max_rows: int = 40, **kw) -> None:
    """표를 행 수만큼 펼쳐(최대 max_rows 행) 보여 준다. 숫자로 읽히는 열은 오른쪽 정렬."""
    cfg = {c: st.column_config.Column(alignment="right") for c in df.columns if _numeric_like(df[c])}
    cfg.update(kw.pop("column_config", {}) or {})
    st.dataframe(df, hide_index=True, width="stretch", height=table_height(min(len(df), max_rows)),
                 row_height=ROW_HEIGHT, column_config=cfg, **kw)


def kind_ko(design) -> str:
    return O(DESIGN_KIND_KO.get(type(design).__name__, type(design).__name__))


def worksheet_json(ws: Worksheet) -> bytes:
    return json.dumps(worksheet_to_dict(ws), ensure_ascii=False, indent=1).encode("utf-8")


def worksheet_from_json(data: bytes) -> Worksheet:
    return worksheet_from_dict(json.loads(data.decode("utf-8-sig")))


def worksheet_xlsx(ws: Worksheet) -> bytes:
    """워크시트(런 순서)를 Excel 파일로."""
    from doe_core.io.xlsx import frames_to_xlsx
    return frames_to_xlsx({"Worksheet": ws.table("run")})


def worksheet_csv(ws: Worksheet) -> bytes:
    buf = io.StringIO()
    ws.table("run").to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8-sig")


def require_ws() -> Worksheet:
    ws = get_ws()
    if ws is None:
        st.info(T("아직 워크시트가 없습니다. **설계 생성**에서 설계를 만들거나 **시작** 화면에서 파일을 불러오세요.",
                  "No worksheet yet. Create a design in **Create design** or open a file on the **Home** page."))
        st.page_link("views/create.py", label=T("설계 생성으로 가기"), icon=":material/grid_on:")
        st.stop()
    return ws


def run_states(ws: Worksheet) -> pd.DataFrame:
    """런 순서별 결과 입력 상태: RunOrder·StdOrder·Blocks·state(done = 숫자 열 모두 입력, part = 일부, none = 없음)."""
    t = ws.table("run")
    cols = [c for c in ws.columns.columns if pd.api.types.is_numeric_dtype(ws.columns[c])]
    if cols:
        have = t[cols].notna()
        state = ["done" if a else ("part" if b else "none") for a, b in zip(have.all(axis=1), have.any(axis=1))]
    else:
        state = ["none"] * len(t)
    return pd.DataFrame({"RunOrder": t["RunOrder"].astype(int), "StdOrder": t["StdOrder"].astype(int),
                         "Blocks": t["Blocks"].astype(int), "state": state})


def run_progress(ws: Worksheet) -> None:
    """실험 진행 표시: 런 순서대로 칸 하나씩(결과 다 입력 = 채움, 일부 = 옅게, 아직 = 빈 칸), 블록마다 띄운다."""
    r = run_states(ws)
    n, done, part = len(r), int((r["state"] == "done").sum()), int((r["state"] == "part").sum())
    names = {"done": T("결과 있음", "results in"), "part": T("일부 입력", "partly entered"), "none": T("아직", "not yet")}
    style = {"done": "background:#2a78d6",
             "part": "background:rgba(42,120,214,.35)",
             "none": "box-shadow:inset 0 0 0 1px rgba(128,128,128,.6)"}
    cells, last = [], None
    for row in r.itertuples(index=False):
        gap = "margin-left:10px;" if last is not None and row.Blocks != last else ""
        last = row.Blocks
        tip = T(f"런 {row.RunOrder} · 표준 순서 {row.StdOrder} · 블록 {row.Blocks} · {names[row.state]}",
                f"Run {row.RunOrder} · std order {row.StdOrder} · block {row.Blocks} · {names[row.state]}")
        cells.append(f'<span title="{tip}" style="{gap}display:inline-block;width:10px;height:16px;border-radius:2px;'
                     f'{style[row.state]}"></span>')
    summary = T(f"결과 입력 {done} / {n}런", f"Results entered for {done} of {n} runs")
    if part:
        summary += T(f" · 일부 입력 {part}런", f" · {part} partly entered")
    st.html(f'<div style="margin:2px 0 8px 0">'
            f'<div style="font-size:13px;display:flex;gap:10px;align-items:baseline">'
            f'<span style="font-weight:600">{T("실험 진행", "Progress")}</span>'
            f'<span style="font-variant-numeric:tabular-nums;opacity:.75">{summary}</span></div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:3px;margin-top:6px">{"".join(cells)}</div></div>')


def download_stem(default: str) -> str:
    """내려받을 파일 이름(확장자 앞). 현재 작업에 이름이 있으면 '이름_기본이름', 없으면 기본이름."""
    ws = get_ws()
    name = ws.name if ws is not None else ""
    return file_stem(f"{name}_{default}" if name else default, "doe_studio")


def md_text(text: str) -> str:
    """사용자가 쓴 글자를 마크다운 안에 그대로 보이게(기호 앞에 역슬래시)."""
    return "".join("\\" + ch if ch in "\\`*_{}[]<>()#+-.!|~$" else ch for ch in text)


def work_state(ws: Worksheet | None) -> dict | None:
    """'현재 작업' 띠에 보일 내용(바뀌었는지 비교하려고 사전으로)."""
    if ws is None:
        return None
    r = run_states(ws)
    return {"name": ws.name, "kind": kind_ko(ws.design), "factors": len(ws.design.factors), "runs": ws.design.n_runs,
            "columns": list(ws.columns.columns), "done": int((r["state"] == "done").sum()),
            "part": int((r["state"] == "part").sum()), "lang": st.session_state.get("lang")}


def current_work_bar(s: dict, *, link: bool, key: str = "current_work") -> None:
    """모든 화면 맨 위의 '현재 작업' 띠: 이름(없으면 설계 종류)을 크게, 아래에 설계·요인·런·열과 결과 입력 진행."""
    e = html.escape
    title = s["name"] or s["kind"]
    detail = ([s["kind"]] if s["name"] else []) + [T(f"요인 {s['factors']}개", f"{s['factors']} factors"),
                                                   T(f"런 {s['runs']}개", f"{s['runs']} runs")]
    if s["columns"]:
        cols = ", ".join(s["columns"][:4]) + (" …" if len(s["columns"]) > 4 else "")
        detail.append(T("열: ", "columns: ") + cols)
    n, done = s["runs"], s["done"]
    progress = T(f"결과 입력 {done} / {n}런", f"results {done} / {n} runs")
    if s["part"]:
        progress += T(f" · 일부 {s['part']}런", f" · {s['part']} partly")
    pct = 100 * done / n if n else 0
    label = T("현재 작업", "Current work") + ("" if s["name"] else T(" · 이름 없음", " · unnamed"))
    with st.container(border=True, key=key):
        c1, c2 = st.columns([5, 1.2], vertical_alignment="center")
        c1.html(
            f'<div style="font-size:12px;opacity:.6">{e(label)}</div>'
            f'<div style="font-size:18px;font-weight:650;line-height:1.35;margin-top:2px;overflow-wrap:anywhere">'
            f'{e(title)}</div>'
            f'<div style="font-size:13.5px;margin-top:4px;display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center;'
            f'font-variant-numeric:tabular-nums"><span style="opacity:.75">{e(" · ".join(detail))}</span>'
            f'<span style="display:inline-flex;align-items:center;gap:8px"><span style="opacity:.75">{e(progress)}</span>'
            f'<span style="display:inline-block;width:88px;height:4px;border-radius:2px;background:rgba(128,128,128,.25)">'
            f'<span style="display:block;height:4px;border-radius:2px;width:{pct:.0f}%;background:#2a78d6"></span>'
            f'</span></span></div>')
        if link:
            c2.page_link("views/worksheet.py", label=T("워크시트 열기", "Open worksheet"), icon=":material/table:")


def key_results(a, alpha: float = 0.05) -> None:
    """분석 결과 위의 '주요 결과 요약'(숫자에서 바로 나오는 사실). 요약을 만들 수 없는 분석이면 그리지 않는다."""
    from doe_core.analysis.summary import key_findings, supports
    if not supports(a):
        return
    with st.expander(T("주요 결과 요약", "Key results"), expanded=True):
        icons = {"good": ":green[:material/check_circle:]", "warn": ":orange[:material/warning:]",
                 "info": ":blue[:material/info:]"}
        for f in key_findings(a, alpha):          # 항 이름의 '*'(물*에탄올)가 기울임이 되지 않게 기호는 글자 그대로
            st.markdown(f"{icons[f.level]} {md_text(T(f.ko, f.en))}")
        st.caption(T("숫자에서 바로 나오는 사실만 적었습니다. 판단은 아래 표·그래프와 실험 지식으로 함께 하세요.",
                     "Only facts that follow directly from the numbers. Judge them together with the tables, "
                     "graphs and your process knowledge."))


def report_downloads(make_report, key: str, fname: str) -> None:
    """'보고서 만들기' 를 누르면 보고서를 만들어 Excel·HTML·PDF 내려받기 버튼을 보여 준다.

    make_report(figures: bool) -> doe_core.report.Report. 만든 파일은 key 로 세션에 둔다(분석이 바뀌면 key 도 바뀐다).
    """
    from doe_core.report import to_html, to_pdf, to_xlsx
    with st.expander(T("보고서 내려받기 (Excel · HTML · PDF)", "Download report (Excel · HTML · PDF)")):
        c0, c1, c2, c3 = st.columns([1.4, 1, 1, 1], vertical_alignment="bottom")
        figs = c0.checkbox(T("그래프 포함"), True, key=f"{key}_figs",
                           help=T("PDF 의 그래프는 그림 파일로 만들어 넣으므로 몇 초 더 걸립니다.",
                                  "Graphs in the PDF are rendered as images, which takes a few more seconds."))
        if c0.button(T("보고서 만들기"), key=f"{key}_make"):
            with st.spinner(T("보고서를 만드는 중…", "Building the report…")):
                rep = make_report(figs)
                files = {"xlsx": to_xlsx(rep), "html": to_html(rep).encode("utf-8")}
                try:
                    files["pdf"] = to_pdf(rep, figures=figs)
                except Exception as e:  # noqa: BLE001
                    files["pdf_error"] = f"{type(e).__name__}: {e}"
            st.session_state[key] = files
        files = st.session_state.get(key)
        if not files:
            st.caption(T("Excel 에는 결과표와 원자료(워크시트·적합치)가, HTML·PDF 에는 표와 그래프가 들어갑니다.",
                         "Excel holds the result tables and raw data (worksheet, fits); HTML and PDF hold tables and graphs."))
            return
        fname = download_stem(fname)
        c1.download_button("Excel (.xlsx)", files["xlsx"], f"{fname}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{key}_x")
        c2.download_button("HTML", files["html"], f"{fname}.html", "text/html", key=f"{key}_h")
        if "pdf" in files:
            c3.download_button("PDF", files["pdf"], f"{fname}.pdf", "application/pdf", key=f"{key}_p")
        else:
            c3.caption(T("PDF 를 만들지 못했습니다(reportlab 필요): ", "Could not build the PDF (needs reportlab): ")
                       + files["pdf_error"])
