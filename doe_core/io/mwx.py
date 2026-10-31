"""Minitab 워크시트 파일(.MWX) 읽기.

.MWX 는 zip 이고 안에 JSON 이 들어 있다.
  /sheet_metadata_20.json          워크시트 이름 등
  /sheets/<n>/sheet.json           실제 데이터. Data.Columns[*].WorksheetVarBody 에 열 이름과 값
    - 숫자 열: VarData.VarDataBody.NumericData (결측은 Minitab 의 '*' 를 뜻하는 큰 수로 저장될 수 있어 NaN 처리)
    - 텍스트 열: VarData.VarDataBody.TextData
  Data.DOE 에는 설계·분석·그래프 보유 여부 플래그가 있다(HasDesign, HasAnalysis …).

쓰기는 지원하지 않는다(우리 저장 형식은 io/worksheet.py 에서 따로 정의).
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# Minitab 이 결측('*')을 숫자 배열에 저장할 때 쓰는 값의 크기. 이보다 크면 결측으로 본다.
_MISSING_THRESHOLD = 1e30


def _sheet_members(z: zipfile.ZipFile) -> list[str]:
    names = [n for n in z.namelist() if n.endswith("/sheet.json")]
    return sorted(names, key=lambda n: int(n.split("/sheets/")[1].split("/")[0]))


def _column_to_series(col: dict) -> tuple[str, pd.Series]:
    body = col["WorksheetVarBody"]
    name = body["Name"]
    vd = body["VarData"]["VarDataBody"]
    if vd.get("HasTextData"):
        return name, pd.Series(vd.get("TextData", []), dtype="object")
    values = vd.get("NumericData", [])
    arr = np.array([np.nan if v is None else float(v) for v in values], dtype=float)
    arr[np.abs(arr) > _MISSING_THRESHOLD] = np.nan
    return name, pd.Series(arr)


def _frame_from_sheet(sheet: dict) -> pd.DataFrame:
    cols = [c for c in sheet["Data"]["Columns"] if c.get("WorksheetVarBody")]
    series = dict(_column_to_series(c) for c in cols)
    n = max((len(s) for s in series.values()), default=0)
    out = pd.DataFrame({k: s.reindex(range(n)) for k, s in series.items()})
    return out


def read_mwx_sheets(path) -> dict[str, pd.DataFrame]:
    """파일 안의 모든 워크시트를 {이름: DataFrame} 으로 돌려준다. path 는 경로 또는 바이너리 파일 객체."""
    if isinstance(path, str):
        path = Path(path)
    out: dict[str, pd.DataFrame] = {}
    with zipfile.ZipFile(path) as z:
        for i, member in enumerate(_sheet_members(z)):
            sheet = json.loads(z.read(member))
            title = sheet.get("Data", {}).get("PrivateTitle") or f"Worksheet {i + 1}"
            out[title] = _frame_from_sheet(sheet)
    return out


def read_mwx(path: str | Path) -> pd.DataFrame:
    """첫 번째 워크시트를 DataFrame 으로 돌려준다(열 순서 유지)."""
    sheets = read_mwx_sheets(path)
    if not sheets:
        raise ValueError(f"워크시트가 없습니다: {path}")
    return next(iter(sheets.values()))


def mwx_doe_flags(path: str | Path) -> dict[str, bool]:
    """Data.DOE 의 Has* 플래그(설계·분석·그래프 보유 여부)."""
    with zipfile.ZipFile(path) as z:
        sheet = json.loads(z.read(_sheet_members(z)[0]))
    doe = sheet.get("Data", {}).get("DOE", {}) or {}
    return {k: bool(v) for k, v in doe.items() if k.startswith("Has")}
