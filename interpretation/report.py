"""Dutch clinical report generator for patient dossier."""

from __future__ import annotations

from interpretation.models import FullInterpretation, EarInterpretation


# --- Dutch translation mappings ---

CONFIGURATION_NL = {
    "flat": "vlak",
    "sloping": "hoogfrequent",
    "precipitous": "steil",
    "rising": "laagfrequent",
    "noise-notch": "noise-notch",
    "cookie-bite": "midfrequent",
    "carhart-notch": "carhart-notch",
    "corner": "hoekaudiogram",
    "insufficient data": "",
}

DEGREE_NL = {
    "Normal": "normaal gehoor",
    "Mild": "mild",
    "Moderate": "matig",
    "Moderately severe": "matig-ernstig",
    "Severe": "ernstig",
    "Profound": "zeer ernstig",
    "Unable to determine": "",
}

TYPE_NL = {
    "Normal": "normaal gehoor",
    "Sensorineural": "perceptief",
    "Conductive": "conductief",
    "Mixed": "gemengd",
    "Unable to determine": "",
}

SIDE_NL = {"right": "AD", "left": "AS"}


def generate_report(interp: FullInterpretation) -> str:
    """Generate a Dutch clinical report for copy-paste into patient dossier."""
    r = interp.right
    l = interp.left

    lines = []

    # --- Line 1: Tone audiometry description ---
    tone_line = _build_tone_line(r, l)
    if tone_line:
        lines.append(tone_line)

    # --- Line 2: Speech audiometry ---
    speech_line = _build_speech_line(r, l)
    if speech_line:
        lines.append(speech_line)

    return "\n".join(lines)


def _build_tone_line(r: EarInterpretation, l: EarInterpretation) -> str:
    """Build the tone audiometry description line."""
    symmetric = _is_symmetric(r, l)

    if r.loss_type == "Normal" and l.loss_type == "Normal":
        part = "Normaal gehoor beiderzijds"
    elif symmetric:
        desc = _ear_description(r)
        part = f"{desc} beiderzijds"
    else:
        r_desc = _ear_description(r)
        l_desc = _ear_description(l)

        if r.loss_type == "Normal":
            part = f"Normaal gehoor AD en een {l_desc} AS"
        elif l.loss_type == "Normal":
            part = f"{r_desc} AD en normaal gehoor AS"
        else:
            part = f"{r_desc} AD en een {l_desc} AS"

    # Capitalize first letter
    part = part[0].upper() + part[1:]

    # Add indices
    indices_parts = []

    # PTA (FH)
    if r.fh is not None or l.fh is not None:
        r_pta = f"{r.fh:.0f}dB AD" if r.fh is not None else ""
        l_pta = f"{l.fh:.0f}dB AS" if l.fh is not None else ""
        pta_str = " en ".join(filter(None, [r_pta, l_pta]))
        indices_parts.append(f"PTA van {pta_str}")

    # FHI
    if r.fhi is not None or l.fhi is not None:
        r_fhi = f"{r.fhi:.0f}dB AD" if r.fhi is not None else ""
        l_fhi = f"{l.fhi:.0f}dB AS" if l.fhi is not None else ""
        fhi_str = " en ".join(filter(None, [r_fhi, l_fhi]))
        indices_parts.append(f"FHI van {fhi_str}")

    # Average air-bone gap (only if there is a conductive/mixed component)
    r_abg = r.avg_air_bone_gap
    l_abg = l.avg_air_bone_gap
    has_gap = (r.loss_type in ("Conductive", "Mixed") and r_abg is not None) or \
              (l.loss_type in ("Conductive", "Mixed") and l_abg is not None)
    if has_gap:
        abg_parts = []
        if r_abg is not None and r.loss_type in ("Conductive", "Mixed"):
            abg_parts.append(f"{r_abg:.0f}dB AD")
        if l_abg is not None and l.loss_type in ("Conductive", "Mixed"):
            abg_parts.append(f"{l_abg:.0f}dB AS")
        if abg_parts:
            indices_parts.append(f"gemiddeld air-bone gap van {' en '.join(abg_parts)}")

    if indices_parts:
        part += " met een " + ", ".join(indices_parts)

    return part + "."


def _build_speech_line(r: EarInterpretation, l: EarInterpretation) -> str:
    """Build the speech audiometry line."""
    r_disc = r.max_discrimination
    l_disc = l.max_discrimination

    if r_disc is None and l_disc is None:
        return ""

    # Determine concordance
    r_concordant = r.srt_fh_concordance == "concordant" if r.srt_fh_concordance else None
    l_concordant = l.srt_fh_concordance == "concordant" if l.srt_fh_concordance else None

    # Default to checking discrimination rating as proxy
    if r_concordant is None and l_concordant is None:
        # If good discrimination, assume conform
        r_concordant = r.discrimination_rating in ("good", None)
        l_concordant = l.discrimination_rating in ("good", None)

    if r_concordant and l_concordant:
        concordance = "conform"
    elif r_concordant is False or l_concordant is False:
        concordance = "niet congruent met"
    else:
        concordance = "conform"

    disc_parts = []
    if r_disc is not None:
        disc_parts.append(f"{r_disc:.0f}% AD")
    if l_disc is not None:
        disc_parts.append(f"{l_disc:.0f}% AS")

    disc_str = " en ".join(disc_parts)

    return f"Spraakaudiometrie {concordance} toonaudiometrie met maximale discriminatie van {disc_str}."


def _ear_description(ear: EarInterpretation) -> str:
    """Generate description for a single ear: '{vorm} {ernst} {type} verlies'."""
    if ear.loss_type == "Normal":
        return "normaal gehoor"

    config_nl = CONFIGURATION_NL.get(ear.configuration, "")
    degree_nl = DEGREE_NL.get(ear.degree, "")
    type_nl = TYPE_NL.get(ear.loss_type, "")

    parts = []
    if config_nl:
        parts.append(config_nl)
    if degree_nl and degree_nl != "normaal gehoor":
        parts.append(degree_nl)
    if type_nl and type_nl != "normaal gehoor":
        parts.append(type_nl)

    if parts:
        return " ".join(parts) + " verlies"
    return "gehoorverlies"


def _is_symmetric(r: EarInterpretation, l: EarInterpretation) -> bool:
    """Check if both ears are substantially symmetric."""
    if r.loss_type != l.loss_type:
        return False
    if r.degree != l.degree:
        return False
    if r.configuration != l.configuration:
        return False
    return True
