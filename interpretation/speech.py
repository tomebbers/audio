"""Speech audiometry interpretation."""

from __future__ import annotations

from interpretation.models import SpeechData


def interpret_speech(speech: SpeechData, fh: float | None) -> dict:
    """Interpret speech audiometry results.

    Returns dict with:
      - srt_fh_concordance: "concordant" | "discrepant" | None
      - discrimination_rating: "good" | "moderate" | "poor" | None
      - rollover_index: float | None
      - rollover_significant: bool
      - notes: list[str]
    """
    result = {
        "srt_fh_concordance": None,
        "discrimination_rating": None,
        "rollover_index": None,
        "rollover_significant": False,
        "notes": [],
    }

    # SRT vs FH concordance
    if speech.srt is not None and fh is not None:
        diff = abs(speech.srt - fh)
        if diff <= 6:
            result["srt_fh_concordance"] = "concordant"
        else:
            result["srt_fh_concordance"] = "discrepant"
            result["notes"].append(
                f"SRT ({speech.srt} dB) differs from FH ({fh} dB) by {diff:.0f} dB. "
                "Discrepancy >6 dB may indicate unreliable test or non-organic hearing loss."
            )

    # Max discrimination rating
    if speech.max_discrimination is not None:
        score = speech.max_discrimination
        if score >= 90:
            result["discrimination_rating"] = "good"
        elif score >= 70:
            result["discrimination_rating"] = "moderate"
            result["notes"].append(
                f"Moderate discrimination loss ({score}%). Consider retrocochlear evaluation."
            )
        else:
            result["discrimination_rating"] = "poor"
            result["notes"].append(
                f"Poor discrimination ({score}%). Suspect retrocochlear pathology. "
                "Further evaluation recommended (ABR, MRI)."
            )

    # Discrimination vs FH mismatch (per audiologieboek.nl)
    if speech.max_discrimination is not None and fh is not None:
        expected_min = _expected_discrimination_for_fh(fh)
        if speech.max_discrimination < expected_min:
            result["notes"].append(
                f"Speech discrimination ({speech.max_discrimination}%) is worse than expected "
                f"for FH of {fh} dB (expected ≥{expected_min}%). "
                "This mismatch raises suspicion for retrocochlear pathology."
            )

    # Rollover index
    if (
        speech.max_discrimination is not None
        and speech.discrimination_at_highest_level is not None
        and speech.max_discrimination > 0
    ):
        rollover = (
            (speech.max_discrimination - speech.discrimination_at_highest_level)
            / speech.max_discrimination
        )
        result["rollover_index"] = round(rollover, 2)
        if rollover > 0.45:
            result["rollover_significant"] = True
            result["notes"].append(
                f"Significant rollover index ({rollover:.2f} > 0.45). "
                "Suspect retrocochlear lesion (e.g., vestibular schwannoma)."
            )

    return result


def _expected_discrimination_for_fh(fh: float) -> float:
    """Estimate minimum expected discrimination based on FH.

    Rough guideline: for cochlear/conductive losses, discrimination
    is typically preserved. Significant drop suggests retrocochlear.
    """
    if fh <= 30:
        return 88
    elif fh <= 50:
        return 76
    elif fh <= 70:
        return 60
    elif fh <= 90:
        return 40
    else:
        return 20
