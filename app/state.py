"""화면 공통: 세션의 워크시트, 그래프 테마, 표 표시, 파일 내보내기."""
from __future__ import annotations

import io
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from doe_core.io.worksheet import Worksheet, load_worksheet, save_worksheet

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
}


def get_ws() -> Worksheet | None:
    return st.session_state.get(KEY)


def set_ws(ws: Worksheet | None) -> None:
    st.session_state[KEY] = ws
    st.session_state.pop("analysis", None)


def plot_mode() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:  # noqa: BLE001
        return "light"


def show_plot(fig) -> None:
    st.plotly_chart(fig, theme=None, width="stretch", config={"displaylogo": False})


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


def show_table(df: pd.DataFrame, *, max_rows: int = 40, **kw) -> None:
    """표를 행 수만큼 펼쳐(최대 max_rows 행) 보여 준다. 숫자로 읽히는 열은 오른쪽 정렬."""
    cfg = {c: st.column_config.Column(alignment="right") for c in df.columns if _numeric_like(df[c])}
    cfg.update(kw.pop("column_config", {}) or {})
    height = 35 * (min(len(df), max_rows) + 1) + 3
    st.dataframe(df, hide_index=True, width="stretch", height=height, column_config=cfg, **kw)


def kind_ko(design) -> str:
    return DESIGN_KIND_KO.get(type(design).__name__, type(design).__name__)


def worksheet_json(ws: Worksheet) -> bytes:
    with tempfile.TemporaryDirectory() as d:
        p = save_worksheet(ws, Path(d) / "w.json")
        return p.read_bytes()


def worksheet_from_json(data: bytes) -> Worksheet:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "w.json"
        p.write_bytes(data)
        return load_worksheet(p)


def worksheet_csv(ws: Worksheet) -> bytes:
    buf = io.StringIO()
    ws.table("run").to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8-sig")


def require_ws() -> Worksheet:
    ws = get_ws()
    if ws is None:
        st.info("아직 워크시트가 없습니다. **설계 생성**에서 설계를 만들거나 **시작** 화면에서 파일을 불러오세요.")
        st.page_link("views/create.py", label="설계 생성으로 가기", icon=":material/grid_on:")
        st.stop()
    return ws


def ws_caption(ws: Worksheet) -> str:
    d = ws.design
    extra = [c for c in ws.columns.columns]
    return (f"{kind_ko(d)} · 요인 {len(d.factors)}개 · 런 {d.n_runs}개"
            + (f" · 비설계 열: {', '.join(extra)}" if extra else ""))


def report_downloads(make_report, key: str, fname: str) -> None:
    """'보고서 만들기' 를 누르면 보고서를 만들어 Excel·HTML·PDF 내려받기 버튼을 보여 준다.

    make_report(figures: bool) -> doe_core.report.Report. 만든 파일은 key 로 세션에 둔다(분석이 바뀌면 key 도 바뀐다).
    """
    from doe_core.report import to_html, to_pdf, to_xlsx
    with st.expander("보고서 내려받기 (Excel · HTML · PDF)"):
        c0, c1, c2, c3 = st.columns([1.4, 1, 1, 1], vertical_alignment="bottom")
        figs = c0.checkbox("그래프 포함", True, key=f"{key}_figs",
                           help="PDF 의 그래프는 그림 파일로 만들어 넣으므로 몇 초 더 걸립니다.")
        if c0.button("보고서 만들기", key=f"{key}_make"):
            with st.spinner("보고서를 만드는 중…"):
                rep = make_report(figs)
                files = {"xlsx": to_xlsx(rep), "html": to_html(rep).encode("utf-8")}
                try:
                    files["pdf"] = to_pdf(rep, figures=figs)
                except Exception as e:  # noqa: BLE001
                    files["pdf_error"] = f"{type(e).__name__}: {e}"
            st.session_state[key] = files
        files = st.session_state.get(key)
        if not files:
            st.caption("Excel 에는 결과표와 원자료(워크시트·적합치)가, HTML·PDF 에는 표와 그래프가 들어갑니다.")
            return
        c1.download_button("Excel (.xlsx)", files["xlsx"], f"{fname}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{key}_x")
        c2.download_button("HTML", files["html"], f"{fname}.html", "text/html", key=f"{key}_h")
        if "pdf" in files:
            c3.download_button("PDF", files["pdf"], f"{fname}.pdf", "application/pdf", key=f"{key}_p")
        else:
            c3.caption("PDF 를 만들지 못했습니다(reportlab 필요): " + files["pdf_error"])
