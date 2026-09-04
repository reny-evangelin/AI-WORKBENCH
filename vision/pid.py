"""
vision/pid.py
=============
P&ID element detection module.
Identifies P&ID tags (equipment, valves, instruments, pipes) from OCR results.
"""

import re
import logging
from typing import Dict, List, Any

try:
    from .ocr import OCRResult
except ImportError:
    from vision.ocr import OCRResult

logger = logging.getLogger(__name__)

# Basic regex patterns for MVP P&ID tags
TAG_PATTERNS = {
    # TK=Tank, V=Vessel, HE=Heat Exchanger, T=Tower, E=Exchanger, C=Compressor, R=Reactor
    "equipment": r'\b(?:TK|V|HE|T|E|C|R)-\d{2,5}[A-Z]?\b',
    
    # P=Pump
    "pumps": r'\b(?:P|PUMP)-\d{2,5}[A-Z]?\b',
    
    # Common valves
    "valves": r'\b(?:XV|CV|HV|FCV|LCV|PCV|TCV|PSV|PRV|MOV|SOV|SDV|BDV|UV|FV)-\d{2,5}[A-Z]?\b',
    
    # Instruments (P=Pressure, T=Temperature, F=Flow, L=Level, A=Analyzer)
    "instruments": r'(?<!-)\b(?:TI|PI|FI|LI|AI|TE|PT|FT|LT|AT|TC|PC|FC|LC|AC|TIC|PIC|FIC|LIC|FIQ|PDIT|TIT|PIT|LIT|FIT)-\d{2,5}[A-Z]?\b(?!-)',
    
    # Pipes/Lines. e.g. 4"-CS-150-101, 2-PL-300, or 4-IA-SS-0012-A1A
    "pipes": r'\b(?:\d{1,2}"?-?[A-Z]{1,4}-[A-Z0-9-]{3,}|\d+-[A-Z]{2,4}-\d{3,5}(?:-[A-Z0-9]+)?)\b'
}

def detect_pid_elements(ocr_result: OCRResult) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses OCR results and categorizes elements into P&ID components.
    
    Args:
        ocr_result: The OCRResult object returned by vision.ocr.run_ocr.
        
    Returns:
        A dictionary mapping component categories ('equipment', 'pumps', 'valves', 
        'instruments', 'pipes') to a list of detected instances.
    """
    output = {
        "equipment": [],
        "pumps": [],
        "valves": [],
        "instruments": [],
        "pipes": []
    }
    
    if not ocr_result or not getattr(ocr_result, "success", False):
        logger.warning("Invalid or unsuccessful OCR result provided to P&ID detector.")
        return output
        
    for line in ocr_result.lines:
        text = line.text.upper()
        
        for category, pattern in TAG_PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                output[category].append({
                    "tag": match,
                    "confidence": line.confidence,
                    "polygon": line.polygon,
                    "original_text": line.text
                })
                
    return output
