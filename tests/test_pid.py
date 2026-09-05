"""
tests/test_pid.py
=================
Tests for the P&ID detection module.
Runs real OCR output from the realistic sample P&ID image through the detection layer.
"""

import os
import sys

# Ensure the repo root is on sys.path so `vision` is importable.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def test_regression_document_number() -> None:
    from vision.ocr import OCRResult, OCRLine
    from vision.pid import detect_pid_elements

    # Create a synthetic OCRResult containing both the false-positive case and valid tags
    synthetic_result = OCRResult(
        image_path="synthetic.png",
        success=True,
        lines=[
            OCRLine(text="DOCUMENT NO: XXXX-PI-001-000", confidence=0.99),
            OCRLine(text="TAG: PI-001", confidence=0.99),
            OCRLine(text="PT-202", confidence=0.99),
            OCRLine(text="TI-401", confidence=0.99)
        ]
    )

    detected = detect_pid_elements(synthetic_result)
    instruments = [item['tag'] for item in detected['instruments']]
    
    print("\n--- Running Regression Test ---")
    print(f"Detected instruments: {instruments}")
    
    if "PI-001" not in instruments:
        print("FAIL: Valid PI-001 tag was not detected.")
        sys.exit(1)
        
    # We should have exactly 3 instruments detected. If it extracted from the document number, it would be 4, 
    # or if we check the original text we can ensure the document number wasn't caught.
    # We can check how many times "PI-001" appears in the result.
    pi_count = sum(1 for item in detected['instruments'] if item['tag'] == 'PI-001')
    if pi_count != 1:
        print(f"FAIL: Expected PI-001 to be detected exactly once, found {pi_count} times.")
        sys.exit(1)
        
    print("PASS: test_regression_document_number passed successfully.")

def test_detect_pid_elements() -> None:
    from vision.ocr import run_ocr
    from vision.pid import detect_pid_elements
    
    realistic_image = os.path.join(REPO_ROOT, "data", "sample_pid", "sample_pid_realistic.png")
    
    if not os.path.exists(realistic_image):
        print(f"SKIP: Realistic image not found at {realistic_image}")
        return
        
    print(f"Running OCR on {realistic_image}...")
    result = run_ocr(realistic_image)
    
    if not result.success:
        print(f"FAIL: OCR failed: {result.error}")
        if "paddlepaddle" in str(result.error):
            print("Note: paddlepaddle not installed. Skipping test.")
            return
        sys.exit(1)
        
    print("OCR successful. Running P&ID detection...")
    detected = detect_pid_elements(result)
    
    total_detected = 0
    print("\n--- Detected Elements ---")
    for category, items in detected.items():
        print(f"\n{category.upper()} ({len(items)} found):")
        total_detected += len(items)
        for item in items:
            print(f"  - {item['tag']} (Confidence: {item['confidence']:.2f}) [Orig: {item['original_text']}]")
            
    print(f"\nTotal elements detected: {total_detected}")
    
    # We should expect to find at least some elements on a text-heavy P&ID
    if total_detected == 0:
        print("FAIL: No P&ID elements detected. Check your regex patterns.")
        sys.exit(1)
        
    print("PASS: test_detect_pid_elements passed successfully.")

if __name__ == "__main__":
    test_regression_document_number()
    test_detect_pid_elements()
