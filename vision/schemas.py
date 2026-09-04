"""
vision/schemas.py
=================
Pydantic v2 data models for the P&ID analysis pipeline (SIH 2026 MVP).

These models define the structure of the output produced by vision/parser.py
and will be returned directly by the FastAPI layer (api.py) once it is built.

Model hierarchy
---------------
TaggedElement          — a single detected P&ID element (tag + metadata)
PIDAnalysisResult      — the top-level response model for a full analysis
PIDAnalysisError       — returned when analysis fails (error details only)

Design principles
-----------------
- All list fields default to [] so partial/incomplete P&IDs do not fail.
- All string fields that could legitimately be absent default to "" or None.
- confidence is constrained to [-1.0, 1.0]; -1.0 means "unavailable".
- document_type has a sensible default ("P&ID") but is overridable.
- polygon is carried through as a list-of-[x,y] pairs; empty list is valid.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class TaggedElement(BaseModel):
    """A single detected P&ID element (instrument, valve, pipe, etc.).

    Attributes
    ----------
    tag : str
        The normalised tag string (e.g. ``"TI-401"``, ``"FCV-101"``).
    confidence : float
        OCR recognition confidence in ``[-1.0, 1.0]``.
        ``-1.0`` indicates that confidence information was unavailable.
    original_text : str
        The raw OCR text line from which the tag was extracted.
    polygon : list[list[float]]
        Bounding polygon as ``[[x1,y1], [x2,y2], ...]``.
        Empty list when coordinate data is unavailable.
    """

    tag: str = Field(..., min_length=1, description="Normalised P&ID tag string")
    confidence: float = Field(
        default=-1.0,
        ge=-1.0,
        le=1.0,
        description="OCR recognition confidence (-1.0 = unavailable)",
    )
    original_text: str = Field(
        default="",
        description="Raw OCR text line the tag was extracted from",
    )
    polygon: List[List[float]] = Field(
        default_factory=list,
        description="Bounding-box polygon [[x,y], ...]; empty when unavailable",
    )

    @field_validator("tag")
    @classmethod
    def tag_must_be_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("tag must not be blank after stripping whitespace")
        return v.upper()


# ---------------------------------------------------------------------------
# Top-level response models
# ---------------------------------------------------------------------------

class PIDAnalysisResult(BaseModel):
    """Structured result of a complete P&ID image analysis.

    Produced by ``vision/parser.py:parse_pid_output`` and validated here
    before being serialised by the FastAPI layer.

    Attributes
    ----------
    document_type : str
        Always ``"P&ID"`` for this pipeline. Kept as a configurable field
        so future document types (e.g. ``"PFD"``) can be accommodated.
    equipment : list[TaggedElement]
        Detected equipment tags (tanks, vessels, exchangers, …).
    pumps : list[TaggedElement]
        Detected pump tags.
    valves : list[TaggedElement]
        Detected valve tags (control valves, safety valves, …).
    instruments : list[TaggedElement]
        Detected instrument tags (transmitters, indicators, controllers, …).
    pipes : list[TaggedElement]
        Detected pipe / line tags.
    raw_text : list[str]
        Every unique OCR text line extracted from the image, in order.
    image_path : str | None
        The source image path if available; ``None`` otherwise.
    total_elements : int
        Computed total of all categorised elements (convenience field).
    """

    document_type: str = Field(
        default="P&ID",
        description="Document classification (e.g. 'P&ID', 'PFD')",
    )
    equipment:   List[TaggedElement] = Field(default_factory=list)
    pumps:       List[TaggedElement] = Field(default_factory=list)
    valves:      List[TaggedElement] = Field(default_factory=list)
    instruments: List[TaggedElement] = Field(default_factory=list)
    pipes:       List[TaggedElement] = Field(default_factory=list)
    raw_text:    List[str]           = Field(default_factory=list)
    image_path:  Optional[str]       = Field(default=None)
    total_elements: int              = Field(default=0)

    def model_post_init(self, __context) -> None:
        """Auto-compute total_elements after initialisation."""
        object.__setattr__(
            self,
            "total_elements",
            len(self.equipment) + len(self.pumps) + len(self.valves)
            + len(self.instruments) + len(self.pipes),
        )

    @classmethod
    def from_parser_dict(cls, parsed: dict, image_path: Optional[str] = None) -> "PIDAnalysisResult":
        """Build a ``PIDAnalysisResult`` directly from a ``parse_pid_output`` dict.

        Parameters
        ----------
        parsed:
            The dict returned by :func:`vision.parser.parse_pid_output`.
        image_path:
            Optional path of the source image.

        Returns
        -------
        PIDAnalysisResult
        """
        def _elements(key: str) -> List[TaggedElement]:
            return [TaggedElement(**item) for item in parsed.get(key, [])]

        return cls(
            document_type=parsed.get("document_type", "P&ID"),
            equipment=_elements("equipment"),
            pumps=_elements("pumps"),
            valves=_elements("valves"),
            instruments=_elements("instruments"),
            pipes=_elements("pipes"),
            raw_text=parsed.get("raw_text", []),
            image_path=image_path,
        )


class PIDAnalysisError(BaseModel):
    """Returned when the analysis pipeline cannot produce a valid result.

    Attributes
    ----------
    error : str
        Human-readable description of what went wrong.
    image_path : str | None
        Source image path if known.
    stage : str | None
        Pipeline stage where the failure occurred
        (``"ocr"``, ``"detection"``, ``"parsing"``, or ``"validation"``).
    """

    error: str = Field(..., min_length=1, description="Error description")
    image_path: Optional[str] = Field(default=None)
    stage: Optional[str] = Field(
        default=None,
        description="Pipeline stage where the failure occurred",
    )
