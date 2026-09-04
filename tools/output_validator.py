from pathlib import Path


REQUIRED_FIELDS = [
    "title",
    "equipment",
    "equipment_type",
    "finding",
    "severity",
    "location",
    "analysis",
    "recommendation",
    "sop_reference",
    "source_document",
    "source_pages",
]


def validate_analysis_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validate structured analysis data before document generation.

    Args:
        data: Structured analysis dictionary.

    Returns:
        A tuple containing:
        - True/False indicating whether the data is valid.
        - A list of validation error messages.
    """

    errors = []

    if not isinstance(data, dict):
        return False, ["Analysis data must be a dictionary."]

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")
            continue

        value = data[field]

        if value is None:
            errors.append(f"Field cannot be null: {field}")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"Field cannot be empty: {field}")

    # Validate source_pages
    if "source_pages" in data:
        source_pages = data["source_pages"]

        if not isinstance(source_pages, list):
            errors.append("source_pages must be a list.")
        elif not all(isinstance(page, int) for page in source_pages):
            errors.append("source_pages must contain only integers.")

    return len(errors) == 0, errors


def validate_output_file(output_path: str) -> tuple[bool, str]:
    """
    Validate that a generated output file exists and is not empty.

    Args:
        output_path: Path to the generated file.

    Returns:
        A tuple containing:
        - True/False indicating whether the file is valid.
        - A validation message.
    """

    output_file = Path(output_path)

    if not output_file.exists():
        return False, f"Output file does not exist: {output_path}"

    if not output_file.is_file():
        return False, f"Output path is not a file: {output_path}"

    if output_file.stat().st_size == 0:
        return False, f"Output file is empty: {output_path}"

    return True, "Output file is valid."