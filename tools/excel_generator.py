from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


def generate_excel(data: dict, output_path: str) -> str:
    """
    Generate an Inspection Approval Note in Excel format.

    Args:
        data: Structured analysis data.
        output_path: Path where the Excel file should be created.

    Returns:
        The output file path.
    """

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Inspection Approval"

    # Title
    worksheet["A1"] = data.get(
        "title",
        "Inspection Approval Note"
    )

    worksheet["A1"].font = Font(
        bold=True,
        size=16
    )

    # Equipment Details
    worksheet["A3"] = "Equipment Details"
    worksheet["A3"].font = Font(bold=True)

    equipment_details = [
        ("Equipment", data.get("equipment", "")),
        ("Equipment Type", data.get("equipment_type", "")),
        ("Location", data.get("location", "")),
        ("Severity", data.get("severity", "")),
    ]

    row = 4

    for label, value in equipment_details:
        worksheet.cell(
            row=row,
            column=1,
            value=label
        )

        worksheet.cell(
            row=row,
            column=2,
            value=str(value)
        )

        worksheet.cell(
            row=row,
            column=1
        ).font = Font(bold=True)

        row += 1

    # Inspection Finding
    worksheet.cell(
        row=row + 1,
        column=1,
        value="Inspection Finding"
    )

    worksheet.cell(
        row=row + 1,
        column=1
    ).font = Font(bold=True)

    worksheet.cell(
        row=row + 2,
        column=1,
        value=data.get("finding", "")
    )

    worksheet.merge_cells(
        start_row=row + 2,
        start_column=1,
        end_row=row + 2,
        end_column=2,
    )

    row += 4

    # AI Analysis
    worksheet.cell(
        row=row,
        column=1,
        value="AI Analysis"
    )

    worksheet.cell(
        row=row,
        column=1
    ).font = Font(bold=True)

    worksheet.cell(
        row=row + 1,
        column=1,
        value=data.get("analysis", "")
    )

    worksheet.merge_cells(
        start_row=row + 1,
        start_column=1,
        end_row=row + 1,
        end_column=2,
    )

    row += 3

    # Recommended Action
    worksheet.cell(
        row=row,
        column=1,
        value="Recommended Action"
    )

    worksheet.cell(
        row=row,
        column=1
    ).font = Font(bold=True)

    worksheet.cell(
        row=row + 1,
        column=1,
        value=data.get("recommendation", "")
    )

    worksheet.merge_cells(
        start_row=row + 1,
        start_column=1,
        end_row=row + 1,
        end_column=2,
    )

    row += 3

    # SOP / Knowledge Reference
    worksheet.cell(
        row=row,
        column=1,
        value="SOP / Knowledge Reference"
    )

    worksheet.cell(
        row=row,
        column=1
    ).font = Font(bold=True)

    worksheet.cell(
        row=row + 1,
        column=1,
        value=data.get("sop_reference", "")
    )

    worksheet.merge_cells(
        start_row=row + 1,
        start_column=1,
        end_row=row + 1,
        end_column=2,
    )

    row += 3

    # Source Traceability
    worksheet.cell(
        row=row,
        column=1,
        value="Source Traceability"
    )

    worksheet.cell(
        row=row,
        column=1
    ).font = Font(bold=True)

    # Source Document
    worksheet.cell(
        row=row + 1,
        column=1,
        value="Source Document"
    )

    worksheet.cell(
        row=row + 1,
        column=2,
        value=data.get("source_document", "")
    )

    # Source Pages
    source_pages = data.get("source_pages", [])

    worksheet.cell(
        row=row + 2,
        column=1,
        value="Source Pages"
    )

    worksheet.cell(
        row=row + 2,
        column=2,
        value=", ".join(map(str, source_pages))
    )

    # Column widths
    worksheet.column_dimensions["A"].width = 30
    worksheet.column_dimensions["B"].width = 80

    # Wrap long text and align cells
    for row_cells in worksheet.iter_rows():
        for cell in row_cells:
            cell.alignment = Alignment(
                wrap_text=True,
                vertical="top"
            )

    # Save workbook
    workbook.save(output_file)

    return str(output_file)