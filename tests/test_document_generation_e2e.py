import os
import json
from pathlib import Path
from agent import process_request

def verify_file(filepath: str, ext: str):
    p = Path(filepath)
    assert p.exists(), f"File does not exist: {filepath}"
    assert p.stat().st_size > 0, f"File is empty: {filepath}"
    assert p.suffix == ext, f"Wrong extension {p.suffix} expected {ext}"
    
    if ext == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(p)
        assert len(wb.sheetnames) > 0
            
    elif ext == ".pdf":
        import fitz
        doc = fitz.open(p)
        assert len(doc) > 0

def test_excel_multi_sheet_generation():
    req = (
        "Create an Excel report for our AI project team.\n\n"
        "Create sheets:\n"
        "Team\n"
        "Tasks\n"
        "Comments\n\n"
        "The Team sheet should contain:\n"
        "Name\n"
        "Role\n"
        "Module\n"
        "Status\n\n"
        "The Tasks sheet should contain:\n"
        "Task\n"
        "Member\n"
        "Status\n\n"
        "The Comments sheet should contain:\n"
        "Member\n"
        "Comment"
    )
    
    res = process_request(req)
    assert res.status == "success"
    
    try:
        d = json.loads(res.answer)
        assert "path" in d
        verify_file(d["path"], ".xlsx")
    except Exception as e:
        assert False, f"Failed to verify Excel output: {e}"

def test_pdf_generation():
    req = "Create a PDF report of the same project with comments and recommendations."
    res = process_request(req)
    assert res.status == "success"
    
    try:
        d = json.loads(res.answer)
        assert "path" in d
        verify_file(d["path"], ".pdf")
    except Exception as e:
        assert False, f"Failed to verify PDF output: {e}"
