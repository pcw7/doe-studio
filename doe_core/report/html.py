"""HTML 보고서 — 파일 하나로 열리는 문서(표 + 확대·마우스 정보가 되는 plotly 그래프). 브라우저에서 인쇄하면 PDF 로도 저장된다.

plotly.js 는 기본으로 파일 안에 넣는다(인터넷이 막힌 연구소 PC 에서도 열리도록). plotlyjs="cdn" 이면 파일이 작아진다.
"""
from __future__ import annotations

from html import escape

import pandas as pd

from .model import Report, cell_text, numeric_like

CSS = """
:root { --surface:#fcfcfb; --text:#0b0b0b; --text2:#52514e; --grid:#e8e7e3; --axis:#c9c8c2; --accent:#2a78d6;
        --head:#eef3fa; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--surface); color: var(--text);
       font-family: Pretendard, 'Noto Sans KR', 'Malgun Gothic', system-ui, sans-serif; font-size: 14px; line-height: 1.5; }
main { max-width: 1040px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 24px; margin: 0 0 4px; }
.sub { color: var(--text2); margin: 0; }
.stamp { color: var(--text2); font-size: 12px; margin: 4px 0 24px; }
h2 { font-size: 16px; color: var(--accent); margin: 28px 0 8px; padding-bottom: 4px; border-bottom: 1px solid var(--grid); }
h3 { font-size: 14px; margin: 16px 0 6px; }
p { margin: 6px 0; }
pre { background: #f4f4f2; border: 1px solid var(--grid); border-radius: 6px; padding: 10px 12px; overflow-x: auto;
      font-family: Consolas, 'D2Coding', monospace; font-size: 12.5px; white-space: pre-wrap; overflow-wrap: anywhere; }
.tbl { overflow-x: auto; margin: 6px 0 4px; }
table { border-collapse: collapse; font-size: 13px; font-variant-numeric: tabular-nums; }
th { background: var(--head); text-align: left; font-weight: 600; }
th, td { padding: 4px 10px; border-bottom: 1px solid var(--grid); white-space: pre; }
td.num, th.num { text-align: right; }
.note { color: var(--text2); font-size: 12px; margin: 2px 0 12px; }
figure { margin: 12px 0 20px; }
figcaption { color: var(--text2); font-size: 12px; margin-bottom: 4px; }
footer { color: var(--text2); font-size: 12px; margin-top: 40px; border-top: 1px solid var(--grid); padding-top: 8px; }
@media print { main { max-width: none; padding: 0; } h2 { break-after: avoid; } figure, .tbl { break-inside: avoid; } }
"""


def table_html(df: pd.DataFrame) -> str:
    right = [numeric_like(df[c]) for c in df.columns]
    head = "".join(f'<th class="num">{escape(str(c))}</th>' if r else f"<th>{escape(str(c))}</th>"
                   for c, r in zip(df.columns, right))
    rows = []
    for row in df.itertuples(index=False):
        rows.append("<tr>" + "".join(f'<td class="num">{escape(cell_text(v))}</td>' if r else
                                     f"<td>{escape(cell_text(v))}</td>" for v, r in zip(row, right)) + "</tr>")
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def to_html(report: Report, *, plotlyjs: str = "inline") -> str:
    import plotly.io as pio
    parts = [f"<h1>{escape(report.title)}</h1>"]
    if report.subtitle:
        parts.append(f'<p class="sub">{escape(report.subtitle)}</p>')
    parts.append(f'<p class="stamp">DOE Studio · {escape(report.stamp)}</p>')
    first_fig = True
    for b in report.blocks:
        if b.kind == "heading":
            parts.append(f"<h2>{escape(str(b.content))}</h2>")
        elif b.kind == "text":
            parts.append(f"<p>{escape(str(b.content))}</p>")
        elif b.kind == "mono":
            if b.title:
                parts.append(f"<h3>{escape(b.title)}</h3>")
            parts.append(f"<pre>{escape(str(b.content))}</pre>")
        elif b.kind == "table":
            if b.title:
                parts.append(f"<h3>{escape(b.title)}</h3>")
            parts.append(table_html(b.content))
            if b.note:
                parts.append(f'<p class="note">{escape(b.note)}</p>')
        elif b.kind == "figure":
            inc = (plotlyjs if first_fig else False) if plotlyjs in ("inline", "cdn") else False
            div = pio.to_html(b.content, full_html=False, include_plotlyjs=True if inc == "inline" else inc,
                              config={"displaylogo": False, "responsive": True})
            first_fig = False
            has_title = bool(getattr(getattr(b.content.layout, "title", None), "text", None))
            cap = f"<figcaption>{escape(b.title)}</figcaption>" if b.title and not has_title else ""
            parts.append(f"<figure>{cap}{div}</figure>")
    parts.append(f"<footer>DOE Studio 로 만든 보고서 · {escape(report.stamp)}</footer>")
    return ("<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{escape(report.title)}</title><style>{CSS}</style></head>"
            f"<body><main>{''.join(parts)}</main></body></html>")
