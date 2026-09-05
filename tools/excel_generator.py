from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


def generate_excel(data: dict, output_path: str) -> str:
    """
    Generate an Excel format report based on the provided sheets structure.
    """
    output_file = Path(output_path)
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
        ws = workbook.create_sheet(sheet_name)
        
        columns = sheet_data.get("columns", [])
        rows = sheet_data.get("rows", [])
        
        # Write Title
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(columns), 1))
        title_cell = ws.cell(row=1, column=1, value=data.get("title", "Report"))
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")
        
        # Write Columns
        col_idx = 1
        for col_name in columns:
            cell = ws.cell(row=2, column=col_idx, value=str(col_name))
            cell.font = Font(bold=True)
            col_idx += 1
            
        # Write Rows
        current_row = 3
        for row_data in rows:
            col_idx = 1
            for val in row_data:
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                # Ensure alignment wrapping
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                col_idx += 1
            current_row += 1
            
        # Freeze headers
        ws.freeze_panes = "A3"
        
        # Auto-size columns slightly
        for col in range(1, len(columns) + 1):
            column_letter = ws.cell(row=2, column=col).column_letter
            ws.column_dimensions[column_letter].width = 25

    workbook.save(output_file)
    return str(output_file)