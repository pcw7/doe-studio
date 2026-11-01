"""Excel(.xlsx) 읽기·쓰기 — 외부 패키지 없이 Office Open XML(ZIP + XML)을 직접 다룬다.

읽기: 통합 문서의 시트 이름·순서(workbook.xml + 관계 파일), 공유 문자열(서식 있는 글자는 조각을 이어 붙이고 윗주 rPh 는 뺌),
인라인 글자, 수식 결과 글자(t="str"), 불리언, 오류(결측), 숫자. 셀 주소(r)가 없거나 건너뛰어도 위치를 맞춘다.
첫 번째로 값이 있는 행을 머리글로 쓰고, 머리글이 빈 열은 'Column3' 처럼 이름을 붙인다. 완전히 빈 행·열은 뺀다.
날짜 서식은 해석하지 않는다(Excel 일련번호 숫자 그대로).

쓰기: 시트 이름 → 데이터프레임을 머리글 + 값으로(숫자는 숫자 칸). 보고서 작성기(report/xlsx.py)의 시트 구현을 쓴다.
"""
from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
_M = "{%s}" % NS["m"]
_REF = re.compile(r"^([A-Z]+)(\d+)$")


def _col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _si_text(si) -> str:
    parts = []
    for child in si:
        if child.tag == _M + "t":
            parts.append(child.text or "")
        elif child.tag == _M + "r":
            t = child.find("m:t", NS)
            if t is not None:
                parts.append(t.text or "")
    return "".join(parts)


def _open(src) -> zipfile.ZipFile:
    if isinstance(src, (bytes, bytearray)):
        return zipfile.ZipFile(io.BytesIO(src))
    if isinstance(src, (str, Path)):
        return zipfile.ZipFile(src)
    return zipfile.ZipFile(src)


def _sheet_paths(z: zipfile.ZipFile) -> list[tuple[str, str]]:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {}
    try:
        root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        for rel in root.findall("rel:Relationship", NS):
            target = rel.get("Target")
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            rels[rel.get("Id")] = target
    except KeyError:
        pass
    out = []
    for i, sh in enumerate(wb.find("m:sheets", NS)):
        rid = sh.get(f"{{{NS['r']}}}id")
        out.append((sh.get("name"), rels.get(rid, f"xl/worksheets/sheet{i + 1}.xml")))
    return out


def _grid(z: zipfile.ZipFile, path: str, shared: list[str]) -> list[list]:
    root = ET.fromstring(z.read(path))
    rows: dict[int, dict[int, object]] = {}
    next_row = 0
    for row in root.iter(_M + "row"):
        ri = int(row.get("r")) - 1 if row.get("r") else next_row
        next_row = ri + 1
        cells = rows.setdefault(ri, {})
        next_col = 0
        for c in row.findall("m:c", NS):
            ref = c.get("r")
            m = _REF.match(ref) if ref else None
            ci = _col_index(m.group(1)) if m else next_col
            next_col = ci + 1
            t = c.get("t")
            v = c.find("m:v", NS)
            val: object = None
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr":
                is_ = c.find("m:is", NS)
                val = _si_text(is_) if is_ is not None else None
            elif t == "str":
                val = v.text if v is not None else None
            elif t == "b" and v is not None:
                val = v.text == "1"
            elif t == "e":
                val = None
            elif v is not None and v.text is not None:
                try:
                    val = float(v.text)
                except ValueError:
                    val = v.text
            if val == "":
                val = None
            cells[ci] = val
    if not rows:
        return []
    n_rows = max(rows) + 1
    n_cols = max((max(r) + 1 for r in rows.values() if r), default=0)
    return [[rows.get(i, {}).get(j) for j in range(n_cols)] for i in range(n_rows)]


def _frame(grid: list[list]) -> pd.DataFrame:
    grid = [r for r in grid if any(v is not None for v in r)]
    if not grid:
        return pd.DataFrame()
    keep = [j for j in range(len(grid[0])) if any(r[j] is not None for r in grid)]
    grid = [[r[j] for j in keep] for r in grid]
    header, body = grid[0], grid[1:]
    names, seen = [], set()
    for j, h in enumerate(header):
        nm = (f"{h:g}" if isinstance(h, float) else str(h)).strip() if h is not None else f"Column{j + 1}"
        base, k = nm, 2
        while nm in seen:
            nm = f"{base}_{k}"
            k += 1
        seen.add(nm)
        names.append(nm)
    df = pd.DataFrame(body, columns=names)
    for c in df.columns:
        col = df[c]
        if col.map(lambda v: v is None or isinstance(v, (int, float)) and not isinstance(v, bool)).all():
            df[c] = pd.to_numeric(col, errors="coerce")
            if df[c].notna().any() and np.all(np.mod(df[c].dropna(), 1) == 0):
                df[c] = df[c].astype("Int64") if df[c].isna().any() else df[c].astype(np.int64)
    return df


def read_xlsx_sheets(src) -> dict[str, pd.DataFrame]:
    """.xlsx(경로·바이트·파일 객체) → {시트 이름: 데이터프레임} (통합 문서 순서)."""
    with _open(src) as z:
        try:
            shared_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = [_si_text(si) for si in shared_root.findall("m:si", NS)]
        except KeyError:
            shared = []
        return {name: _frame(_grid(z, path, shared)) for name, path in _sheet_paths(z)}


def read_xlsx(src, sheet: str | int = 0) -> pd.DataFrame:
    sheets = read_xlsx_sheets(src)
    if isinstance(sheet, int):
        return list(sheets.values())[sheet]
    return sheets[sheet]


def frames_to_xlsx(frames: dict[str, pd.DataFrame]) -> bytes:
    """{시트 이름: 데이터프레임} → .xlsx 바이트(머리글 굵게, 첫 행 고정, 숫자는 숫자 칸)."""
    from ..report.xlsx import _data_sheet, write_book
    return write_book([_data_sheet(name, df) for name, df in frames.items()])
