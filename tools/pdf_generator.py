from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf(data: dict, output_path: str) -> str:
    """
    Generate an Inspection Approval Note in PDF format.

    Args:
        data: Structured analysis data.
        output_path: Path where the PDF should be created.

    Returns:
        The output file path.
    """

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    document = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=15,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        spaceAfter=8,
    )

    story = []

    # Title
    story.append(
        Paragraph(
            data.get("title", "Inspection Approval Note"),
            title_style,
        )
    )

    # Equipment Details
    story.append(
        Paragraph("Equipment Details", heading_style)
    )

    equipment_data = [
        ["Field", "Details"],
        ["Equipment", data.get("equipment", "")],
        ["Equipment Type", data.get("equipment_type", "")],
        ["Location", data.get("location", "")],
        ["Severity", data.get("severity", "")],
    ]

    equipment_table = Table(
        equipment_data,
        colWidths=[45 * mm, 115 * mm],
    )

    equipment_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(equipment_table)
    story.append(Spacer(1, 8))

    # Inspection Finding
    story.append(
        Paragraph("Inspection Finding", heading_style)
    )
    story.append(
        Paragraph(
            data.get("finding", ""),
            body_style,
        )
    )

    # AI Analysis
    story.append(
        Paragraph("AI Analysis", heading_style)
    )
    story.append(
        Paragraph(
            data.get("analysis", ""),
            body_style,
        )
    )

    # Recommended Action
    story.append(
        Paragraph("Recommended Action", heading_style)
    )
    story.append(
        Paragraph(
            data.get("recommendation", ""),
            body_style,
        )
    )

    # SOP / Knowledge Reference
    story.append(
        Paragraph("SOP / Knowledge Reference", heading_style)
    )
    story.append(
        Paragraph(
            data.get("sop_reference", ""),
            body_style,
        )
    )

    # Source Traceability
    story.append(
        Paragraph("Source Traceability", heading_style)
    )

    source_document = data.get("source_document", "")
    source_pages = data.get("source_pages", [])

    story.append(
        Paragraph(
            f"Source Document: {source_document}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"Source Pages: {', '.join(map(str, source_pages))}",
            body_style,
        )
    )

    document.build(story)

    return str(output_file)