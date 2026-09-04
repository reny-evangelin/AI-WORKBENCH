import json
from pathlib import Path

from tools.output_generator import generate_outputs


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "sample_analysis.json"
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def main():
    # Load sample analysis data
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Generate all supported output formats
    generated_files = generate_outputs(
        data=data,
        output_dir=str(OUTPUT_DIR)
    )

    print("\nMember 4 Output Generation Successful!\n")

    for file_type, file_path in generated_files.items():
        print(f"{file_type.upper()}: {file_path}")


if __name__ == "__main__":
    main()