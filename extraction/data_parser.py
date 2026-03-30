"""Shared data parsing logic for audiogram extraction (used by all backends)."""

from __future__ import annotations

import json
import re

from config import Config
from interpretation.models import AudiogramData, EarThresholds, SpeechData


def parse_json_response(text: str) -> dict:
    """Extract JSON from an LLM response, handling markdown code fences."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)

    raise ValueError(f"Could not parse JSON from response: {text[:200]}...")


def build_audiogram_data(raw: dict) -> AudiogramData:
    """Convert raw JSON extraction into AudiogramData model."""
    pt = raw.get("pure_tone", {})
    sp = raw.get("speech", {})

    right_ear = _build_ear_thresholds("right", pt.get("right_ear", {}))
    left_ear = _build_ear_thresholds("left", pt.get("left_ear", {}))
    right_speech = _build_speech_data("right", sp.get("right_ear", {}))
    left_speech = _build_speech_data("left", sp.get("left_ear", {}))

    metadata = raw.get("metadata", {})
    confidence = raw.get("extraction_confidence", "medium")
    notes = raw.get("extraction_notes", [])

    data = AudiogramData(
        right_ear=right_ear,
        left_ear=left_ear,
        right_speech=right_speech,
        left_speech=left_speech,
        metadata=metadata if metadata else {},
        extraction_confidence=confidence,
        extraction_notes=notes if notes else [],
    )

    _validate_audiogram_data(data)
    return data


def _build_ear_thresholds(side: str, raw: dict) -> EarThresholds:
    ear = EarThresholds(side=side)
    ear.air_conduction = _parse_threshold_dict(raw.get("air_conduction", {}))
    ear.air_masked = _parse_threshold_dict(raw.get("air_masked", {}))
    ear.bone_conduction = _parse_threshold_dict(raw.get("bone_conduction", {}))
    ear.bone_masked = _parse_threshold_dict(raw.get("bone_masked", {}))

    nr_ac = raw.get("no_response_ac", [])
    nr_bc = raw.get("no_response_bc", [])
    ear.no_response = {
        "ac": set(int(f) for f in nr_ac) if nr_ac else set(),
        "bc": set(int(f) for f in nr_bc) if nr_bc else set(),
    }
    return ear


def _parse_threshold_dict(raw: dict) -> dict[int, float | None]:
    result = {}
    if not raw:
        return result
    for freq_str, value in raw.items():
        try:
            freq = int(freq_str)
        except (ValueError, TypeError):
            continue
        if value is not None:
            try:
                result[freq] = float(value)
            except (ValueError, TypeError):
                continue
    return result


def _build_speech_data(side: str, raw: dict) -> SpeechData:
    if not raw:
        return SpeechData(side=side)
    return SpeechData(
        side=side,
        srt=_safe_float(raw.get("srt")),
        max_discrimination=_safe_float(raw.get("max_discrimination")),
        db_at_max_discrimination=_safe_float(raw.get("db_at_max_discrimination")),
        discrimination_at_highest_level=_safe_float(raw.get("discrimination_at_highest_level")),
        db_at_highest_level=_safe_float(raw.get("db_at_highest_level")),
        masked=bool(raw.get("masked", False)),
    )


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _validate_audiogram_data(data: AudiogramData) -> None:
    for ear in [data.right_ear, data.left_ear]:
        for label, thresholds in [
            ("AC", ear.air_conduction),
            ("AC masked", ear.air_masked),
            ("BC", ear.bone_conduction),
            ("BC masked", ear.bone_masked),
        ]:
            for freq, val in list(thresholds.items()):
                if val is not None and (val < -10 or val > 130):
                    data.extraction_notes.append(
                        f"Implausible {label} threshold at {freq} Hz ({ear.side}): {val} dB"
                    )

        for freq in Config.ALL_FREQUENCIES:
            ac = ear.air_conduction.get(freq) or ear.air_masked.get(freq)
            bc = ear.bone_conduction.get(freq) or ear.bone_masked.get(freq)
            if ac is not None and bc is not None and bc > ac + 10:
                data.extraction_notes.append(
                    f"BC ({bc} dB) worse than AC ({ac} dB) at {freq} Hz ({ear.side} ear). "
                    "This is clinically unusual and may indicate extraction error."
                )
