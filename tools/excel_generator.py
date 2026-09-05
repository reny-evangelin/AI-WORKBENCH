import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


def generate_excel(data: dict, output_dir: str) -> str:
    """
    Generate an Excel format report based on the provided sheets structure.
    Expects data matching the ExcelPlan schema.
    """
    # Use the LLM's requested filename, sanitizing it to prevent path traversal
    filename = data.get("filename", "report.xlsx")
    filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'
        
    output_file = Path(output_dir) / filename
    output_file.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    
    # Remove default sheet
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    sheets = data.get("sheets", [])
    
    if not sheets:
        # Fallback if somehow empty
        ws = workbook.create_sheet("Report")
        ws["A1"] = data.get("title", "Report")
    
    for sheet_data in sheets:
        sheet_name = str(sheet_data.get("name", "Sheet"))
        # Ensure valid sheet name length
        sheet_name = sheet_name[:31] 
        ws = workbook.create_sheet(sheet_name)
        
        columns = sheet_data.get("columns", [])
        rows = sheet_data.get("rows", [])
        formulas = sheet_data.get("formulas", [])
        
        # Mapping column name to Excel column index (1-based)
        col_map = {col_name: idx + 1 for idx, col_name in enumerate(columns)}
        
        # Write Title
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(columns), 1))
        title_cell = ws.cell(row=1, column=1, value=data.get("title", "Report"))
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")
        
        # Write Column Headers
        for col_name, col_idx in col_map.items():
            cell = ws.cell(row=2, column=col_idx, value=str(col_name))
            cell.font = Font(bold=True)
            
        # Write Rows
        current_row = 3
        for row_dict in rows:
            # Write data values
            for col_name, col_idx in col_map.items():
                val = row_dict.get(col_name, "")
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                # Ensure alignment wrapping
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                
            # Write formulas for this row
            for f_data in formulas:
                f_col_name = f_data.get("column")
                f_str = f_data.get("formula", "")
                if f_col_name in col_map and f_str:
                    col_idx = col_map[f_col_name]
                    # Dynamically replace {row} with current_row
                    resolved_formula = f_str.replace("{row}", str(current_row))
                    ws.cell(row=current_row, column=col_idx, value=resolved_formula)
                    
            current_row += 1
            
        # Freeze headers
        ws.freeze_panes = "A3"
        
        # Auto-size columns slightly
        for col in range(1, len(columns) + 1):
            column_letter = get_column_letter(col)
            ws.column_dimensions[column_letter].width = 25

    workbook.save(output_file)
    return str(output_file)