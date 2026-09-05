from pathlib import Path

import openpyxl

def validate_analysis_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validate structured analysis data before document generation.
    """
    errors = []

    if not isinstance(data, dict):
        return False, ["Analysis data must be a dictionary."]

    has_sections = "sections" in data
    has_sheets = "sheets" in data
    
    if not has_sections and not has_sheets:
        errors.append("Data must contain either 'sections' (for PDF/DOCX) or 'sheets' (for Excel).")

    if has_sections:
        if "title" not in data:
            errors.append("Missing required field: title")
        if not isinstance(data["sections"], list):
            errors.append("Field 'sections' must be a list.")
        else:
            for idx, sec in enumerate(data["sections"]):
                if not isinstance(sec, dict):
                    errors.append(f"Section {idx} must be a dictionary.")
                    continue
                if "heading" not in sec or "content" not in sec:
                    errors.append(f"Section {idx} must have 'heading' and 'content'.")

    if has_sheets:
        if "filename" not in data:
            errors.append("Missing required field: filename for Excel generation")
        if not isinstance(data["sheets"], list):
            errors.append("Field 'sheets' must be a list.")
        else:
            sheet_names = set()
            for idx, sheet in enumerate(data["sheets"]):
                if not isinstance(sheet, dict):
                    errors.append(f"Sheet {idx} must be a dictionary.")
                    continue
                if "name" not in sheet or "columns" not in sheet or "rows" not in sheet:
                    errors.append(f"Sheet {idx} must have 'name', 'columns', and 'rows'.")
                    continue
                    
                name = sheet["name"]
                if not name or len(str(name)) > 31:
                    errors.append(f"Sheet {idx} name is invalid (empty or >31 chars).")
                if name in sheet_names:
                    errors.append(f"Duplicate sheet name: {name}")
                sheet_names.add(name)
                
                columns = sheet["columns"]
                if not columns or not isinstance(columns, list):
                    errors.append(f"Sheet {idx} must have at least one column in a list.")
                elif len(set(columns)) != len(columns):
                    errors.append(f"Sheet {idx} has duplicate columns.")
                    
                rows = sheet["rows"]
                if not isinstance(rows, list):
                    errors.append(f"Sheet {idx} 'rows' must be a list of dictionaries.")
                else:
                    for r_idx, r in enumerate(rows):
                        if not isinstance(r, dict):
                            errors.append(f"Sheet {idx} row {r_idx} must be a dictionary.")
                            
                formulas = sheet.get("formulas", [])
                if not isinstance(formulas, list):
                    errors.append(f"Sheet {idx} 'formulas' must be a list.")

    return len(errors) == 0, errors


def validate_output_file(output_path: str, data: dict = None) -> tuple[bool, str]:
    """
    Validate that a generated output file exists, is not empty, and is valid format.
    """
    output_file = Path(output_path)

    if not output_file.exists():
        return False, f"Output file does not exist: {output_path}"

    if not output_file.is_file():
        return False, f"Output path is not a file: {output_path}"

    if output_file.stat().st_size == 0:
        return False, f"Output file is empty: {output_path}"

    # Perform deeper validation for Excel
    if output_file.suffix == ".xlsx":
        try:
            workbook = openpyxl.load_workbook(output_path)
            if data and "sheets" in data:
                requested_sheets = [s.get("name") for s in data["sheets"] if isinstance(s, dict)]
                for sheet_name in requested_sheets:
                    if sheet_name and sheet_name not in workbook.sheetnames:
                        return False, f"Requested sheet '{sheet_name}' is missing in the generated Excel file."
        except Exception as e:
            return False, f"Failed to open Excel workbook (corruption check): {str(e)}"

    return True, "Output file is valid."