"""Data models for audiogram extraction and interpretation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EarThresholds:
    """Pure-tone threshold values for one ear."""

    side: str  # "right" or "left"
    # freq (Hz) -> dB HL; None means not tested
    air_conduction: dict[int, float | None] = field(default_factory=dict)
    bone_conduction: dict[int, float | None] = field(default_factory=dict)
    air_masked: dict[int, float | None] = field(default_factory=dict)
    bone_masked: dict[int, float | None] = field(default_factory=dict)
    # Frequencies where no response was obtained at max output
    no_response: dict[str, set[int]] = field(default_factory=lambda: {"ac": set(), "bc": set()})


@dataclass
class SpeechData:
    """Speech audiometry data for one ear."""

    side: str
    srt: float | None = None  # Speech Reception Threshold (dB)
    max_discrimination: float | None = None  # Best phoneme/word score (%)
    db_at_max_discrimination: float | None = None  # dB level where max was achieved
    discrimination_at_highest_level: float | None = None  # Score at max presentation level (%)
    db_at_highest_level: float | None = None  # The max presentation level (dB)
    masked: bool = False


@dataclass
class AudiogramData:
    """Complete extracted data from an audiogram image."""

    right_ear: EarThresholds = field(default_factory=lambda: EarThresholds(side="right"))
    left_ear: EarThresholds = field(default_factory=lambda: EarThresholds(side="left"))
    right_speech: SpeechData = field(default_factory=lambda: SpeechData(side="right"))
    left_speech: SpeechData = field(default_factory=lambda: SpeechData(side="left"))
    metadata: dict = field(default_factory=dict)
    extraction_confidence: str = "medium"  # "high", "medium", "low"
    extraction_notes: list[str] = field(default_factory=list)


@dataclass
class EarInterpretation:
    """Clinical interpretation for one ear."""

    side: str
    # Indices
    fh: float | None = None
    fhi: float | None = None
    # Classification
    degree: str = "Unable to determine"
    loss_type: str = "Unable to determine"
    # Per-frequency data
    air_bone_gaps: dict[int, float] = field(default_factory=dict)
    # Speech
    srt: float | None = None
    max_discrimination: float | None = None
    srt_fh_concordance: str | None = None  # "concordant", "discrepant", None
    discrimination_rating: str | None = None  # "good", "moderate", "poor"
    rollover_index: float | None = None
    # Thresholds for display
    ac_thresholds: dict[int, float | None] = field(default_factory=dict)
    bc_thresholds: dict[int, float | None] = field(default_factory=dict)
    # Masking
    masking_errors: list[str] = field(default_factory=list)
    # Audiogram configuration
    configuration: str = "flat"  # "flat", "sloping", "rising", "notch", "cookie-bite", etc.


@dataclass
class Diagnosis:
    """A probable diagnosis with reasoning."""

    name: str
    reasoning: str
    confidence: str = "moderate"  # "high", "moderate", "low"


@dataclass
class FullInterpretation:
    """Complete audiogram interpretation."""

    right: EarInterpretation = field(default_factory=lambda: EarInterpretation(side="right"))
    left: EarInterpretation = field(default_factory=lambda: EarInterpretation(side="left"))
    diagnoses: list[Diagnosis] = field(default_factory=list)
    bilateral_notes: list[str] = field(default_factory=list)
    extraction_confidence: str = "medium"
    extraction_notes: list[str] = field(default_factory=list)
