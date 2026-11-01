"""PDF 보고서 — reportlab 으로 A4 문서를 만든다.

- 한글 글꼴: 시스템의 맑은 고딕·나눔고딕 등 TTF 를 찾아 넣는다(없으면 reportlab 내장 CID 글꼴 HYGothic-Medium).
- 표: 머리글 반복, 숫자처럼 보이는 열 오른쪽 정렬, 쪽 너비를 넘으면 글자 크기를 줄여(최소 6pt) 맞춘다.
- 그래프: kaleido 로 PNG 를 만들어 쪽 너비에 맞춰 넣는다. kaleido 가 없거나 실패하면 그 자리에 안내 문구.
- 쪽 아래에 보고서 제목과 쪽 번호.
"""
from __future__ import annotations

import io
import re
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd

from .model import Report, cell_text, numeric_like

FONT_CANDIDATES = [
    ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"),
    ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
    ("/usr/share/fonts/nanum/NanumGothic.ttf", "/usr/share/fonts/nanum/NanumGothicBold.ttf"),
    ("/Library/Fonts/NanumGothic.ttf", "/Library/Fonts/NanumGothicBold.ttf"),
]
_FONTS: tuple[str, str] | None = None


def register_fonts() -> tuple[str, str]:
    """(본문 글꼴, 굵은 글꼴) 이름. 한 번만 등록한다."""
    global _FONTS
    if _FONTS:
        return _FONTS
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for reg, bold in FONT_CANDIDATES:
        if Path(reg).exists():
            pdfmetrics.registerFont(TTFont("KR", reg))
            if Path(bold).exists():
                pdfmetrics.registerFont(TTFont("KR-Bold", bold))
                _FONTS = ("KR", "KR-Bold")
            else:
                _FONTS = ("KR", "KR")
            return _FONTS
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont("HYGothic-Medium"))
    _FONTS = ("HYGothic-Medium", "HYGothic-Medium")
    return _FONTS


def _para_text(s: str) -> str:
    return escape(s).replace("\n", "<br/>")


def _mono_text(s: str) -> str:
    """고정폭 글: 줄 앞 공백과 연속 공백은 지키고, 낱개 공백에서는 줄바꿈이 되게 한다."""
    out = []
    for line in str(s).splitlines():
        lead = len(line) - len(line.lstrip(" "))
        body = re.sub(r" {2,}", lambda m: "&nbsp;" * (len(m.group()) - 1) + " ", escape(line.lstrip(" ")))
        out.append("&nbsp;" * lead + body)
    return "<br/>".join(out)


def _has_title(fig) -> bool:
    try:
        return bool(fig.layout.title.text)
    except Exception:  # noqa: BLE001
        return False


def _table(df: pd.DataFrame, width: float, font: str, bold: str):
    from reportlab.lib import colors
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.platypus import Table, TableStyle
    data = [[str(c) for c in df.columns]] + [[cell_text(v) for v in row] for row in df.itertuples(index=False)]
    ncol = len(df.columns)
    size = 8.5
    while True:
        widths = [max(stringWidth(str(r[j]), bold if i == 0 else font, size) for i, r in enumerate(data)) + 8
                  for j in range(ncol)]
        if sum(widths) <= width or size <= 6:
            break
        size -= 0.5
    if sum(widths) > width:                                 # 그래도 넓으면 비율대로 줄인다(글자가 잘릴 수 있음)
        k = width / sum(widths)
        widths = [w * k for w in widths]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    style = [("FONTNAME", (0, 0), (-1, -1), font), ("FONTNAME", (0, 0), (-1, 0), bold),
             ("FONTSIZE", (0, 0), (-1, -1), size), ("LEADING", (0, 0), (-1, -1), size + 2),
             ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3fa")),
             ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e8e7e3")),
             ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for j, c in enumerate(df.columns):
        if numeric_like(df[c]):
            style.append(("ALIGN", (j, 0), (j, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def _figure(fig, width: float):
    from reportlab.platypus import Image
    h = int(fig.layout.height or 480)
    png = fig.to_image(format="png", width=1000, height=h, scale=2)
    return Image(io.BytesIO(png), width=width, height=width * h / 1000)


def to_pdf(report: Report, *, figures: bool = True) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import CondPageBreak, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

    font, bold = register_fonts()
    st = {
        "title": ParagraphStyle("t", fontName=bold, fontSize=17, leading=22, spaceAfter=2),
        "sub": ParagraphStyle("s", fontName=font, fontSize=10, leading=14, textColor=colors.HexColor("#52514e")),
        "h2": ParagraphStyle("h2", fontName=bold, fontSize=12, leading=16, spaceBefore=12, spaceAfter=4,
                             textColor=colors.HexColor("#2a78d6")),
        "h3": ParagraphStyle("h3", fontName=bold, fontSize=9.5, leading=13, spaceBefore=6, spaceAfter=2,
                             keepWithNext=1),
        "body": ParagraphStyle("b", fontName=font, fontSize=9.5, leading=14),
        "mono": ParagraphStyle("m", fontName=font, fontSize=8.5, leading=11.5, backColor=colors.HexColor("#f4f4f2"),
                               borderPadding=5, spaceBefore=4, spaceAfter=8),
        "note": ParagraphStyle("n", fontName=font, fontSize=8, leading=11, textColor=colors.HexColor("#52514e"),
                               spaceAfter=6),
    }
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm,
                            bottomMargin=16 * mm, title=report.title, author="DOE Studio")
    width = doc.width
    story = [Paragraph(_para_text(report.title), st["title"])]
    if report.subtitle:
        story.append(Paragraph(_para_text(report.subtitle), st["sub"]))
    story.append(Paragraph(f"DOE Studio · {report.stamp}", st["sub"]))
    story.append(Spacer(1, 6))
    heading = None                                       # 소제목은 다음 내용과 함께 놓는다

    def emit(flows: list, keep: bool):
        nonlocal heading
        if heading is not None:
            if keep:                                     # 짧은 내용: 소제목과 한 묶음으로 쪽을 넘김
                flows = [heading, *flows]
            else:                                        # 긴 표: 쪽 끝에 소제목만 남지 않을 만큼만 확인
                story.extend([CondPageBreak(45 * mm), heading])
            heading = None
        story.append(KeepTogether(flows) if keep else flows[0])
        if not keep:
            story.extend(flows[1:])

    for b in report.blocks:
        if b.kind == "heading":
            if heading is not None:
                emit([], True)
            heading = Paragraph(_para_text(str(b.content)), st["h2"])
        elif b.kind == "text":
            emit([Paragraph(_para_text(str(b.content)), st["body"])], True)
        elif b.kind == "mono":
            title = [Paragraph(_para_text(b.title), st["h3"])] if b.title else []
            emit([*title, Paragraph(_mono_text(b.content), st["mono"])], str(b.content).count("\n") < 40)
        elif b.kind == "table":
            parts = []
            if b.title:
                parts.append(Paragraph(_para_text(b.title), st["h3"]))
            parts.append(_table(b.content, width, font, bold))
            if b.note:
                parts.append(Paragraph(_para_text(b.note), st["note"]))
            parts.append(Spacer(1, 6))
            emit(parts, len(b.content) <= 25)
        elif b.kind == "figure" and figures:
            try:
                img = _figure(b.content, width)
                cap = [] if _has_title(b.content) or not b.title else [Paragraph(_para_text(b.title), st["h3"])]
                emit([*cap, img, Spacer(1, 8)], True)
            except Exception as e:  # noqa: BLE001
                emit([Paragraph(_para_text(report.t(f"[그래프] {b.title or ''} — 그림을 만들 수 없습니다(kaleido 필요): ",
                                                     f"[Graph] {b.title or ''} — could not render (needs kaleido): ")
                                            + type(e).__name__), st["note"])], True)
    if heading is not None:
        story.append(heading)

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#52514e"))
        canvas.drawString(15 * mm, 9 * mm, report.title)
        canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, f"{doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
