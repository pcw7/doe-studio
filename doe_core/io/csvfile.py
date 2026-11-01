"""CSV·텍스트 표 읽기 — 한글 윈도우 엑셀이 저장한 파일까지 받아들인다.

엑셀의 'CSV (쉼표로 분리)' 는 한글 윈도우에서 cp949(EUC-KR 확장)로, 'CSV UTF-8' 은 BOM 붙은 UTF-8 로,
'유니코드 텍스트' 는 BOM 붙은 UTF-16 탭 구분으로 저장된다. 인코딩은 BOM → UTF-8 → cp949 순서로 판별하고,
구분자는 첫 줄에 가장 많이 나오는 쉼표·세미콜론·탭으로 정한다. 완전히 빈 행·열(엑셀이 남기는 ',,,')은 뺀다.
"""
from __future__ import annotations

import io

import pandas as pd

ENCODINGS = ("utf-8", "cp949")


def decode_text(data: bytes) -> tuple[str, str]:
    """(본문, 인코딩 이름). BOM 이 있으면 그대로 따르고, 없으면 UTF-8 → cp949 순서로 시험한다."""
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8"), "utf-8-sig"
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16"
    for enc in ENCODINGS:
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError("파일의 글자 인코딩을 알 수 없습니다. 엑셀에서 'CSV UTF-8(쉼표로 분리)' 형식으로 다시 저장해 보세요.")


def _delimiter(text: str) -> str:
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    counts = {d: first.count(d) for d in (",", ";", "\t")}
    best = max(counts, key=counts.get)
    return best if counts[best] else ","


def read_csv_bytes(data: bytes) -> pd.DataFrame:
    """CSV·탭 구분 텍스트 바이트를 데이터프레임으로. df.attrs['encoding'] 에 판별한 인코딩을 남긴다."""
    text, enc = decode_text(data)
    if not text.strip():
        raise ValueError("파일이 비어 있습니다.")
    df = pd.read_csv(io.StringIO(text), sep=_delimiter(text), skipinitialspace=True)
    unnamed = [c for c in df.columns if str(c).startswith("Unnamed:")]
    df = df.drop(columns=[c for c in unnamed if df[c].isna().all()]).dropna(how="all").reset_index(drop=True)
    # 머리글이 빈 열은 엑셀 읽기와 같이 'Column3' 처럼 이름을 붙인다(위치는 1부터).
    df.columns = [f"Column{int(str(c).split(':')[1]) + 1}" if str(c).startswith("Unnamed:") else str(c).strip()
                  for c in df.columns]
    df.attrs["encoding"] = enc
    return df
