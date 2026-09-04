from pathlib import Path

from tools.docx_generator import generate_docx
from tools.pdf_generator import generate_pdf
from tools.excel_generator import generate_excel
from tools.output_validator import (
    validate_analysis_data,
    validate_output_file,
)


def generate_outputs(
    data: dict,
    output_dir: str,
    formats: list[str] | None = None,
) -> dict:
    """
    Validate analysis data and generate requested output formats.

    Args:
        data: Structured analysis data received from the AI agent.
        output_dir: Directory where generated files should be stored.
        formats: List of requested formats.
                 Supported: docx, pdf, xlsx.
                 If omitted, all formats are generated.

    Returns:
        Dictionary containing generated file paths.

    Raises:
        ValueError: If the input analysis data is invalid.
        ValueError: If an unsupported format is requested.
    """

    # Default: generate all supported formats
    if formats is None:
        formats = ["docx", "pdf", "xlsx"]

    # Validate input data before generation
    is_valid, errors = validate_analysis_data(data)

    if not is_valid:
        raise ValueError(
            "Invalid analysis data:\n" +
            "\n".join(f"- {error}" for error in errors)
        )

    # Validate requested formats
    supported_formats = {"docx", "pdf", "xlsx"}

    invalid_formats = set(formats) - supported_formats

    if invalid_formats:
        raise ValueError(
            f"Unsupported output format(s): "
            f"{', '.join(sorted(invalid_formats))}"
        )

    output_directory = Path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    generated_files = {}

    # Generate DOCX
    if "docx" in formats:
        docx_path = output_directory / "Approval_Note.docx"

        result = generate_docx(
            data,
            str(docx_path)
        )

        is_valid, message = validate_output_file(result)

        if not is_valid:
            raise RuntimeError(message)

        generated_files["docx"] = result

    # Generate PDF
    if "pdf" in formats:
        pdf_path = output_directory / "Approval_Note.pdf"

        result = generate_pdf(
            data,
            str(pdf_path)
        )

        is_valid, message = validate_output_file(result)

        if not is_valid:
            raise RuntimeError(message)

        generated_files["pdf"] = result

    # Generate Excel
    if "xlsx" in formats:
        excel_path = output_directory / "Approval_Note.xlsx"

        result = generate_excel(
            data,
            str(excel_path)
        )

        is_valid, message = validate_output_file(result)

        if not is_valid:
            raise RuntimeError(message)

        generated_files["xlsx"] = result

    return generated_files