"""보고서 내보내기 — 설계·분석·최적화 결과를 Excel(.xlsx)·HTML·PDF 로 저장."""
from .builders import analysis_report, design_report, optimization_report
from .html import to_html
from .model import Report
from .xlsx import to_xlsx

__all__ = ["Report", "analysis_report", "design_report", "optimization_report", "to_html", "to_xlsx", "to_pdf"]


def to_pdf(report: Report, **kw) -> bytes:
    """PDF(reportlab 필요). reportlab 이 없으면 ImportError."""
    from .pdf import to_pdf as _to_pdf
    return _to_pdf(report, **kw)
