"""보고서 내용 모델: 제목 + 블록(소제목·문단·고정폭 글·표·그래프) + 원자료 시트."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass
class Block:
    kind: str                       # "heading" | "text" | "mono" | "table" | "figure"
    content: object                 # 글(str), 표(DataFrame), 그래프(plotly Figure)
    title: str | None = None        # 표·그래프 제목
    note: str | None = None         # 표 아래 주석


@dataclass
class Report:
    title: str
    subtitle: str = ""
    blocks: list[Block] = field(default_factory=list)
    data_sheets: dict[str, pd.DataFrame] = field(default_factory=dict)   # Excel 에만 들어가는 원자료(숫자)
    created: datetime = field(default_factory=datetime.now)

    def heading(self, text: str) -> "Report":
        self.blocks.append(Block("heading", text))
        return self

    def text(self, text: str) -> "Report":
        self.blocks.append(Block("text", text))
        return self

    def mono(self, text: str, title: str | None = None) -> "Report":
        self.blocks.append(Block("mono", text, title))
        return self

    def table(self, df: pd.DataFrame, title: str | None = None, note: str | None = None) -> "Report":
        self.blocks.append(Block("table", df, title, note))
        return self

    def figure(self, fig, title: str | None = None) -> "Report":
        self.blocks.append(Block("figure", fig, title))
        return self

    @property
    def stamp(self) -> str:
        return self.created.strftime("%Y-%m-%d %H:%M")


def numeric_like(col: pd.Series) -> bool:
    """숫자 열이거나 값이 모두 숫자·구간·백분율·'*' 꼴이면 참(오른쪽 정렬용)."""
    if pd.api.types.is_numeric_dtype(col):
        return True
    vals = [str(v).strip() for v in col if str(v).strip() not in ("", "nan", "None")]
    if not vals:
        return True
    for v in vals:
        s = v.replace("(", "").replace(")", "").replace("%", "").replace(",", " ").replace("*", "")
        try:
            [float(x) for x in s.split()]
        except ValueError:
            return False
    return True


def cell_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        if v != v:                  # NaN
            return ""
        return f"{v:.6g}"
    return str(v)
