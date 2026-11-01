"""보고서 내보내기 검증: Excel(.xlsx) 구조·값, HTML 내용, PDF 글자(pypdf 로 추출)."""
import io
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import pytest

from doe_core.analysis.factorial import analyze_worksheet
from doe_core.designs.definitive_screening import create_definitive_screening
from doe_core.designs.factorial import create_two_level_design
from doe_core.designs.general_full import GeneralFactor, create_general_full_factorial
from doe_core.designs.mixture import create_simplex_centroid
from doe_core.designs.plackett_burman import create_plackett_burman_design
from doe_core.designs.response_surface import create_ccd
from doe_core.designs.split_plot import create_split_plot_design
from doe_core.io.worksheet import Worksheet, load_mwx_worksheet
from doe_core.optimize.optimizer import default_goal, optimize
from doe_core.report import Report, analysis_report, design_report, optimization_report, to_html, to_pdf, to_xlsx
from doe_core.report.builders import optimal_design_report
from doe_core.report.xlsx import col_name, read_xlsx_cells
from tests.helpers import SAMPLES

INSUL = SAMPLES / "InsulationProperties.MWX"


def insulation():
    if not INSUL.exists():
        pytest.skip("InsulationProperties.MWX 없음")
    ws = load_mwx_worksheet(INSUL, ["Material", "InjPress", "InjTemp", "CoolTemp"])
    return ws, analyze_worksheet(ws, "Strength", covariates=["MeasTemp"])


def test_xlsx_structure_and_values():
    ws, a = insulation()
    data = to_xlsx(analysis_report(ws, a, figures=False))
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        assert {"[Content_Types].xml", "_rels/.rels", "xl/workbook.xml", "xl/styles.xml",
                "xl/_rels/workbook.xml.rels", "xl/worksheets/sheet1.xml"} <= names
        for n in names:                                                    # 모든 XML 이 올바른 형식
            ET.fromstring(z.read(n))
    cells = read_xlsx_cells(data)
    assert list(cells) == ["보고서", "워크시트", "적합치·진단"]
    rep = cells["보고서"]
    vals = list(rep.values())
    assert rep["A1"] == "Strength 분석 보고서"
    assert "52.7 - 1.229 MeasTemp" in " ".join(str(v) for v in vals)
    assert "1.51005" in vals and "98.02%" in vals                          # Minitab 형식 그대로(글자)
    raw = cells["워크시트"]
    assert raw["A1"] == "StdOrder" and isinstance(raw["A2"], float)          # 원자료는 숫자 칸
    diag = cells["적합치·진단"]
    assert diag["A1"] == "Obs" and len([k for k in diag if k.startswith("A")]) == 17
    assert [col_name(i) for i in (0, 25, 26, 27, 701, 702)] == ["A", "Z", "AA", "AB", "ZZ", "AAA"]


def test_html_and_pdf_contents():
    ws, a = insulation()
    rep = analysis_report(ws, a)
    html = to_html(rep, plotlyjs="cdn")
    assert html.startswith("<!doctype html>") and "Strength 분석 보고서" in html
    assert "<td class=\"num\">0.007</td>" in html and "Plotly.newPlot" in html
    pdf = to_pdf(analysis_report(ws, a, figures=False), figures=False)
    assert pdf[:5] == b"%PDF-"
    from pypdf import PdfReader
    text = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
    for s in ["Strength 분석 보고서", "코드화된 계수", "451.357", "Regression Equation in Uncoded Units", "Formula1"]:
        assert s in text, s


def test_escaping_and_odd_values():
    r = Report("<시험> & 보고서", "부제")
    r.table(pd.DataFrame({"a<b": ["x&y", None, np.nan], "n": [1.5, 2, np.inf]}), "표 <1>")
    r.mono("  들여쓴  줄\n<둘째>")
    html = to_html(r)
    assert "&lt;시험&gt; &amp; 보고서" in html and "x&amp;y" in html and "<시험>" not in html
    cells = read_xlsx_cells(to_xlsx(r))["보고서"]
    assert cells["A1"] == "<시험> & 보고서" and "x&y" in cells.values()
    assert to_pdf(r)[:5] == b"%PDF-"


@pytest.mark.parametrize("make", [
    lambda: create_two_level_design(4, 8, seed=1),
    lambda: create_plackett_burman_design(7, 12, seed=1),
    lambda: create_general_full_factorial([GeneralFactor("A", [1, 2, 3]), GeneralFactor("B", ["x", "y"])], seed=1),
    lambda: create_ccd(3, seed=1),
    lambda: create_simplex_centroid(3, seed=1),
    lambda: create_definitive_screening(6, seed=1),
    lambda: create_split_plot_design(3, 1, seed=1),
])
def test_design_and_analysis_reports_for_every_design(make):
    d = make()
    ws = Worksheet(d)
    rng = np.random.default_rng(0)
    ws.add_column("Y", rng.normal(10, 1, d.n_runs), order="worksheet")
    rep = design_report(ws, figures=False)
    assert rep.blocks and "워크시트" in rep.data_sheets
    a = analyze_worksheet(ws, "Y")
    arep = analysis_report(ws, a, figures=False)
    for out in (to_xlsx(rep), to_xlsx(arep)):
        assert read_xlsx_cells(out)["보고서"]["A1"]
    assert "분석 보고서" in to_html(arep)


def test_optimization_and_optimal_design_reports():
    ws, a = insulation()
    goals = [default_goal(a, "maximize")]
    res = optimize([a], goals)
    rep = optimization_report({"Strength": a}, goals, res)
    cells = read_xlsx_cells(to_xlsx(rep))["보고서"]
    assert "CompositeDesirability" in cells.values()
    from doe_core.designs.optimal import select_optimal_design
    d = create_ccd(3, seed=1)
    r = select_optimal_design(d, 12)
    orep = optimal_design_report(r, Worksheet(d))
    sheets = read_xlsx_cells(to_xlsx(orep))
    assert "후보점·지시자" in sheets and "Condition number:" in sheets["보고서"].values()
