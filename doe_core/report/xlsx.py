"""의존성 없는 Excel(.xlsx) 쓰기 — Office Open XML(ZIP + XML)을 직접 만든다.

- 시트 '보고서': 제목·소제목·글·표를 위에서 아래로 쌓는다. 결과표의 값은 Minitab 표시 형식을 지키도록 글자로 두고
  숫자처럼 보이는 열은 오른쪽 정렬. 그래프는 넣지 않는다(HTML·PDF 보고서에 있음).
- 원자료 시트(예: 워크시트, 적합치·진단): 머리글 + 값. 숫자는 숫자 칸으로 저장해 Excel 에서 바로 계산할 수 있다.
"""
from __future__ import annotations

import io
import math
import re
import zipfile
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd

from .model import Report, cell_text, numeric_like

_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
NORMAL, HEADER, TITLE, MONO, RIGHT, SUBTITLE, NOTE = range(7)

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="6">
<font><sz val="10"/><name val="Malgun Gothic"/></font>
<font><b/><sz val="10"/><name val="Malgun Gothic"/></font>
<font><b/><sz val="14"/><name val="Malgun Gothic"/></font>
<font><sz val="10"/><name val="Consolas"/></font>
<font><b/><sz val="11"/><color rgb="FF2A78D6"/><name val="Malgun Gothic"/></font>
<font><i/><sz val="9"/><color rgb="FF52514E"/><name val="Malgun Gothic"/></font>
</fonts>
<fills count="3">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFEEF3FA"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border><left/><right/><top/><bottom style="thin"><color rgb="FFC9C8C2"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="7">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment horizontal="right"/></xf>
<xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="0" fontId="5" fillId="0" borderId="0" xfId="0" applyFont="1"/>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def col_name(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def _cell(row: int, col: int, value, style: int = NORMAL) -> str:
    ref = f"{col_name(col)}{row}"
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return f'<c r="{ref}" s="{style}"/>' if style else ""
    if isinstance(value, (bool, np.bool_)):
        value = str(bool(value))
    if isinstance(value, (int, float, np.integer, np.floating)) and math.isfinite(float(value)):
        return f'<c r="{ref}" s="{style}"><v>{repr(float(value)) if isinstance(value, (float, np.floating)) else int(value)}</v></c>'
    text = _ILLEGAL.sub("", str(value))
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{escape(text)}</t></is></c>'


class _Sheet:
    def __init__(self, name: str):
        self.name = name
        self.rows: list[tuple[int, list[str]]] = []
        self.r = 0
        self.widths: dict[int, float] = {}
        self.freeze = False

    def put(self, values: list, styles=None):
        self.r += 1
        cells = []
        for c, v in enumerate(values):
            st = styles[c] if isinstance(styles, list) else (styles or NORMAL)
            xml = _cell(self.r, c, v, st)
            if xml:
                cells.append(xml)
            w = len(cell_text(v)) + sum(1 for ch in cell_text(v) if ord(ch) > 0x2E80) * 0.8   # 한글은 넓게
            if st not in (TITLE, SUBTITLE, NOTE, MONO):
                self.widths[c] = max(self.widths.get(c, 6), min(60, w + 2))
        self.rows.append((self.r, cells))

    def blank(self):
        self.r += 1

    def xml(self) -> str:
        cols = "".join(f'<col min="{c + 1}" max="{c + 1}" width="{w:.1f}" customWidth="1"/>'
                       for c, w in sorted(self.widths.items()))
        views = ('<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" '
                 'state="frozen"/></sheetView></sheetViews>') if self.freeze else ""
        rows = "".join(f'<row r="{r}">{"".join(c)}</row>' for r, c in self.rows)
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f'{views}{"<cols>" + cols + "</cols>" if cols else ""}<sheetData>{rows}</sheetData></worksheet>')


def _sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\[\]:*?/\\]", "_", name)[:31] or "Sheet"
    base, k = s, 2
    while s in used:
        s = f"{base[:28]}({k})"
        k += 1
    used.add(s)
    return s


def _report_sheet(rep: Report) -> _Sheet:
    sh = _Sheet("보고서")
    sh.put([rep.title], TITLE)
    if rep.subtitle:
        sh.put([rep.subtitle], NOTE)
    sh.put([f"DOE Studio · {rep.stamp}"], NOTE)
    for b in rep.blocks:
        if b.kind == "heading":
            sh.blank()
            sh.put([b.content], SUBTITLE)
        elif b.kind == "text":
            sh.put([b.content])
        elif b.kind == "mono":
            if b.title:
                sh.put([b.title], HEADER)
            for line in str(b.content).splitlines():
                sh.put([line], MONO)
        elif b.kind == "table":
            df: pd.DataFrame = b.content
            if b.title:
                sh.put([b.title], HEADER)
            right = [numeric_like(df[c]) for c in df.columns]
            sh.put([str(c) for c in df.columns], HEADER)
            for row in df.itertuples(index=False):
                vals = [v if isinstance(v, (int, float, np.integer, np.floating)) else cell_text(v) for v in row]
                sh.put(vals, [RIGHT if r else NORMAL for r in right])
            if b.note:
                sh.put([b.note], NOTE)
            sh.blank()
        elif b.kind == "figure":
            sh.put([f"[그래프] {b.title or ''} — HTML·PDF 보고서에서 볼 수 있습니다."], NOTE)
    return sh


def _data_sheet(name: str, df: pd.DataFrame) -> _Sheet:
    sh = _Sheet(name)
    sh.freeze = True
    sh.put([str(c) for c in df.columns], HEADER)
    for row in df.itertuples(index=False):
        sh.put([v.item() if isinstance(v, np.generic) else v for v in row])
    return sh


def to_xlsx(report: Report) -> bytes:
    """보고서를 .xlsx 바이트로."""
    sheets = [_report_sheet(report)] + [_data_sheet(n, df) for n, df in report.data_sheets.items()]
    used: set = set()
    names = [_sheet_name(s.name, used) for s in sheets]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" '
                   'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" '
                   'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
                             'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(len(sheets)))
                   + '</Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" '
                   'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                   'Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{escape(n, {chr(34): "&quot;"})}" sheetId="{i + 1}" r:id="rId{i + 1}"/>'
                             for i, n in enumerate(names))
                   + '</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i + 1}" '
                             'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                             f'Target="worksheets/sheet{i + 1}.xml"/>' for i in range(len(sheets)))
                   + f'<Relationship Id="rId{len(sheets) + 1}" '
                   'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                   'Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", STYLES)
        for i, s in enumerate(sheets):
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", s.xml())
    return buf.getvalue()


def read_xlsx_cells(data: bytes) -> dict[str, dict[str, object]]:
    """검사용: {시트 이름: {셀 주소: 값}} (inlineStr 은 글자, 숫자는 float)."""
    import xml.etree.ElementTree as ET
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    out = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        for i, sh in enumerate(wb.find("m:sheets", ns)):
            root = ET.fromstring(z.read(f"xl/worksheets/sheet{i + 1}.xml"))
            cells = {}
            for c in root.iter(f"{{{ns['m']}}}c"):
                t = c.get("t")
                if t == "inlineStr":
                    cells[c.get("r")] = "".join(x.text or "" for x in c.iter(f"{{{ns['m']}}}t"))
                else:
                    v = c.find("m:v", ns)
                    if v is not None:
                        cells[c.get("r")] = float(v.text)
            out[sh.get("name")] = cells
    return out
