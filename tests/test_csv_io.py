"""CSV·텍스트 읽기 검증 — 한글 윈도우 엑셀이 저장하는 형식들.

- 'CSV (쉼표로 분리)' = cp949, 'CSV UTF-8' = BOM 붙은 UTF-8, '유니코드 텍스트' = UTF-16 탭 구분, BOM 없는 UTF-8.
- 세미콜론 구분, 엑셀이 남기는 빈 행·빈 열(',,,') 제거, 머리글 없는 열 이름(Column4), 읽을 수 없는 인코딩은 한글 오류.
- 읽은 표로 사용자 설계 정의 → 분석까지(실사용 점검 시나리오: 온도·시간·촉매 2³ + 중앙점 3).
"""
import numpy as np
import pandas as pd
import pytest

from doe_core.analysis.factorial import analyze_worksheet
from doe_core.io.csvfile import decode_text, read_csv_bytes
from doe_core.io.worksheet import define_custom_design

ROWS = [(60, 1, 0.5, 53.4), (80, 1, 0.5, 69.7), (60, 3, 0.5, 64.6), (60, 3, 1.5, 71.5), (80, 1, 1.5, 78.2),
        (70, 2, 1, 75.3), (70, 2, 1, 74.6), (80, 3, 1.5, 79.3), (80, 3, 0.5, 70.6), (70, 2, 1, 75.1),
        (60, 1, 1.5, 61.1)]
HEAD = ["온도(C)", "시간(h)", "촉매(wt%)", "수율(%)"]


def _text(sep=",", nl="\r\n") -> str:
    return nl.join([sep.join(HEAD)] + [sep.join(str(v) for v in r) for r in ROWS]) + nl


def _check(df: pd.DataFrame) -> None:
    assert list(df.columns) == HEAD
    assert len(df) == len(ROWS)
    assert df["수율(%)"].tolist() == [r[3] for r in ROWS]
    assert pd.api.types.is_numeric_dtype(df["온도(C)"])


@pytest.mark.parametrize("data, enc", [
    (_text().encode("cp949"), "cp949"),
    (_text().encode("utf-8-sig"), "utf-8-sig"),
    (_text().encode("utf-8"), "utf-8"),
    (_text(sep="\t").encode("utf-16"), "utf-16"),
])
def test_excel_encodings(data, enc):
    df = read_csv_bytes(data)
    _check(df)
    assert df.attrs["encoding"] == enc


def test_semicolon_and_tab_delimiters():
    _check(read_csv_bytes(_text(sep=";").encode("utf-8")))
    _check(read_csv_bytes(_text(sep="\t", nl="\n").encode("cp949")))


def test_excel_blank_rows_and_columns():
    """엑셀이 서식만 남은 칸을 ',,,,' 로 내보내도 빈 행·빈 열은 빠지고, 머리글 없는 값 열은 Column5 가 된다."""
    lines = [",".join(HEAD) + ",,"] + [",".join(str(v) for v in r) + ",," for r in ROWS] + [",,,,,", ",,,,,"]
    df = read_csv_bytes("\n".join(lines).encode("cp949"))
    _check(df)
    lines = [",".join(HEAD) + ","] + [",".join(str(v) for v in r) + f",{i}" for i, r in enumerate(ROWS)]
    df = read_csv_bytes("\n".join(lines).encode("utf-8"))
    assert list(df.columns) == HEAD + ["Column5"]


def test_unreadable_encoding_message():
    with pytest.raises(ValueError, match="인코딩"):
        decode_text(b"a,b\n\x80\xff,1\n")
    with pytest.raises(ValueError, match="비어"):
        read_csv_bytes(b"\r\n  \r\n")


def test_korean_csv_to_analysis():
    """cp949 CSV → 사용자 2수준 설계(중앙점 3) → 요인 분석: 곡면성 항(Ct Pt)까지 나온다."""
    df = read_csv_bytes(_text().encode("cp949"))
    ws = define_custom_design(df, HEAD[:3])
    assert type(ws.design).__name__ == "TwoLevelDesign"
    a = analyze_worksheet(ws, "수율(%)", order=2)
    coef = a.coefficients_table()
    assert coef["Term"].tolist()[-1] == "Ct Pt"
    assert np.isclose(float(coef.loc[coef["Term"] == "Constant", "Coef"].iloc[0]), 68.55, atol=1e-3)
