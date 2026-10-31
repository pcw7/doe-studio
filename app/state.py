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
