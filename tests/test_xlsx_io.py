"""Excel(.xlsx) 읽기·쓰기 검증.

- 직접 만든 통합 문서: 공유 문자열(서식 있는 조각 이어 붙이기, 윗주 rPh 제외), 인라인 글자, 수식 결과 글자, 불리언, 오류,
  셀 주소 건너뜀(빈 열·행), 관계 파일로 시트 순서·이름 찾기.
- 쓰기 → 읽기 왕복: 워크시트 표(숫자·글자·결측)가 그대로.
- 불러온 표로 사용자 설계 정의(2수준 요인) → 분석까지.
"""
import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from doe_core.io.xlsx import frames_to_xlsx, read_xlsx, read_xlsx_sheets

M = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def _book() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook {M} {R}><sheets>'
                   '<sheet name="설명" sheetId="1" r:id="rId7"/><sheet name="Data" sheetId="2" r:id="rId3"/>'
                   '</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId3" Type="x" Target="worksheets/sheetB.xml"/>'
                   '<Relationship Id="rId7" Type="x" Target="/xl/worksheets/sheetA.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<sst {M}>'
                   '<si><t>온도</t></si>'
                   '<si><r><t>압</t></r><r><rPr><b/></rPr><t>력</t></r><rPh sb="0" eb="1"><t>アツ</t></rPh></si>'
                   '<si><t>Formula1</t></si><si><t>Formula2</t></si><si><t>Yield</t></si></sst>')
        z.writestr("xl/worksheets/sheetA.xml", f'<worksheet {M}><sheetData>'
                   '<row r="2"><c r="B2" t="inlineStr"><is><t>메모</t></is></c></row></sheetData></worksheet>')
        z.writestr("xl/worksheets/sheetB.xml", f'<worksheet {M}><sheetData>'
                   '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>'
                   '<c r="D1" t="s"><v>4</v></c><c r="E1" t="str"><v>Ok</v></c></row>'
                   '<row r="2"><c r="A2"><v>150</v></c><c r="B2" t="s"><v>2</v></c><c r="D2"><v>12.5</v></c>'
                   '<c r="E2" t="b"><v>1</v></c></row>'
                   '<row r="3"><c r="A3"><v>200</v></c><c r="B3" t="s"><v>3</v></c><c r="D3" t="e"><v>#DIV/0!</v></c>'
                   '<c r="E3" t="b"><v>0</v></c></row>'
                   '<row r="5"><c r="A5"><v>175.5</v></c><c r="B5" t="s"><v>2</v></c><c r="D5"><v>13</v></c></row>'
                   '</sheetData></worksheet>')
    return buf.getvalue()


def test_read_handmade_workbook():
    sheets = read_xlsx_sheets(_book())
    assert list(sheets) == ["설명", "Data"]
    df = sheets["Data"]
    assert list(df.columns) == ["온도", "압력", "Yield", "Ok"]                # 빈 C 열은 빠짐, rPh 윗주 제외
    assert df["온도"].tolist() == [150.0, 200.0, 175.5]
    assert df["압력"].tolist() == ["Formula1", "Formula2", "Formula1"]
    assert df["Yield"].iloc[0] == 12.5 and pd.isna(df["Yield"].iloc[1]) and df["Yield"].iloc[2] == 13
    assert df["Ok"].tolist()[:2] == [True, False]
    assert read_xlsx(_book(), 0).columns.tolist() == ["메모"]
    assert read_xlsx(_book(), "Data").shape == (3, 4)


def test_write_read_roundtrip():
    src = pd.DataFrame({"StdOrder": [1, 2, 3], "Temp": [150.0, 200.25, np.nan], "Material": ["A", "B", None],
                        "Count": pd.array([1, None, 3], dtype="Int64")})
    back = read_xlsx(frames_to_xlsx({"Worksheet": src, "두번째": src.head(1)}))
    assert back["StdOrder"].tolist() == [1, 2, 3] and back["StdOrder"].dtype == np.int64
    assert back["Temp"].iloc[1] == 200.25 and pd.isna(back["Temp"].iloc[2])
    assert back["Material"].iloc[0] == "A" and pd.isna(back["Material"].iloc[2])
    assert back["Count"].iloc[0] == 1 and pd.isna(back["Count"].iloc[1])
    assert list(read_xlsx_sheets(frames_to_xlsx({"Worksheet": src, "두번째": src.head(1)}))) == ["Worksheet", "두번째"]


def test_define_design_from_excel_and_analyze():
    from doe_core.analysis.factorial import analyze_worksheet
    from doe_core.designs.factorial import create_two_level_design
    from doe_core.io.worksheet import Worksheet, define_custom_design
    d = create_two_level_design(3, randomize=True, seed=5)
    ws = Worksheet(d)
    rng = np.random.default_rng(0)
    ws.add_column("Y", list(10 + rng.normal(0, 1, len(d.coded))))
    data = frames_to_xlsx({"Sheet1": ws.table("run")})
    df = read_xlsx(data)
    w2 = define_custom_design(df, ["A", "B", "C"])
    a = analyze_worksheet(w2, "Y", order=2)
    b = analyze_worksheet(ws, "Y", order=2)
    assert np.allclose(sorted(a.beta), sorted(b.beta))


def test_worksheet_xlsx_download():
    from app.state import worksheet_xlsx
    from doe_core.designs.factorial import create_two_level_design
    from doe_core.io.worksheet import Worksheet
    ws = Worksheet(create_two_level_design(2, randomize=False))
    df = read_xlsx(worksheet_xlsx(ws))
    assert df.shape[0] == 4 and {"StdOrder", "RunOrder", "A", "B"} <= set(df.columns)
    with pytest.raises(Exception):
        read_xlsx(b"not a zip")
