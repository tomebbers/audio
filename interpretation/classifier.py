"""Hearing loss type and degree classification."""

from __future__ import annotations

from config import Config
from interpretation.models import EarThresholds
from interpretation.indices import best_ac_threshold, best_bc_threshold, calculate_air_bone_gaps


def classify_degree(fh: float | None) -> str:
    """Classify hearing loss degree based on Fletcher Index (FH).

    Based on audiologieboek.nl / ISO classification.
    """
    if fh is None:
        return "Unable to determine"
    if fh <= 20:
        return "Normal"
    elif fh <= 40:
        return "Mild"
    elif fh <= 55:
        return "Moderate"
    elif fh <= 70:
        return "Moderately severe"
    elif fh <= 90:
        return "Severe"
    else:
        return "Profound"


def classify_type(ear: EarThresholds) -> str:
    """Classify hearing loss type: Conductive, Sensorineural, Mixed, or Normal.

    Logic:
    - Compute air-bone gap at speech frequencies.
    - Significant gap: >= ABG_THRESHOLD (15 dB) at 2+ frequencies.
    - BC elevated: any BC > BC_ELEVATED_THRESHOLD (20 dB) at speech frequencies.
    - AC elevated: any AC > 20 dB at speech frequencies.
    """
    gaps = calculate_air_bone_gaps(ear)
    speech_freqs = [500, 1000, 2000, 4000]

    significant_gap_count = 0
    bc_elevated = False
    ac_elevated = False

    for freq in speech_freqs:
        ac = best_ac_threshold(ear, freq)
        bc = best_bc_threshold(ear, freq)

        if ac is not None and ac > Config.BC_ELEVATED_THRESHOLD:
            ac_elevated = True
        if bc is not None and bc > Config.BC_ELEVATED_THRESHOLD:
            bc_elevated = True
        if freq in gaps and gaps[freq] >= Config.ABG_THRESHOLD:
            significant_gap_count += 1

    if not ac_elevated:
        return "Normal"

    has_significant_gap = significant_gap_count >= 2

    if has_significant_gap and not bc_elevated:
        return "Conductive"
    elif has_significant_gap and bc_elevated:
        return "Mixed"
    else:
        return "Sensorineural"


def classify_configuration(ear: EarThresholds) -> str:
    """Determine audiogram configuration/shape.

    Returns one of: flat, sloping, rising, noise-notch, cookie-bite, precipitous, corner.
    """
    freqs = [250, 500, 1000, 2000, 4000, 8000]
    values = []
    for f in freqs:
        v = best_ac_threshold(ear, f)
        if v is not None:
            values.append((f, v))

    if len(values) < 3:
        return "insufficient data"

    thresholds = [v for _, v in values]
    freq_list = [f for f, _ in values]

    low_freq_avg = _mean([v for f, v in values if f <= 1000])
    high_freq_avg = _mean([v for f, v in values if f >= 2000])

    if low_freq_avg is None or high_freq_avg is None:
        return "insufficient data"

    diff = high_freq_avg - low_freq_avg

    # Check for noise notch at 4000 Hz (or 3000/6000)
    if _has_noise_notch(values):
        return "noise-notch"

    # Check for cookie-bite (mid-frequency loss)
    if _has_cookie_bite(values):
        return "cookie-bite"

    # Check for Carhart notch (BC dip at 2000 Hz)
    bc_2k = best_bc_threshold(ear, 2000)
    bc_1k = best_bc_threshold(ear, 1000)
    bc_4k = best_bc_threshold(ear, 4000)
    if bc_2k is not None and bc_1k is not None and bc_4k is not None:
        if bc_2k - bc_1k >= 15 and bc_2k - bc_4k >= 15:
            return "carhart-notch"

    # Check for corner audiogram (profound, only low-freq responses)
    if all(v > 90 for v in thresholds) or (len(values) <= 3 and all(f <= 1000 for f, _ in values)):
        return "corner"

    # Precipitous drop
    if diff >= 50:
        return "precipitous"

    # Sloping vs flat vs rising
    if diff >= 20:
        return "sloping"
    elif diff <= -20:
        return "rising"
    else:
        return "flat"


def _mean(values: list[float]) -> float | None:
    filtered = [v for v in values if v is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def _has_noise_notch(values: list[tuple[int, float]]) -> bool:
    """Check for a 4 kHz noise notch (dip at 3000-6000 Hz with recovery)."""
    val_dict = dict(values)
    notch_freqs = [3000, 4000, 6000]
    neighbor_freqs_low = [1000, 2000]
    neighbor_freqs_high = [6000, 8000]

    for nf in notch_freqs:
        if nf not in val_dict:
            continue
        notch_val = val_dict[nf]
        # Compare to neighbors
        low_neighbors = [val_dict[f] for f in neighbor_freqs_low if f in val_dict and f < nf]
        high_neighbors = [val_dict[f] for f in neighbor_freqs_high if f in val_dict and f > nf]

        if low_neighbors and high_neighbors:
            best_low = min(low_neighbors)
            best_high = min(high_neighbors)
            if notch_val - best_low >= 15 and notch_val - best_high >= 10:
                return True
    return False


def _has_cookie_bite(values: list[tuple[int, float]]) -> bool:
    """Check for cookie-bite pattern (mid-frequency loss worse than low and high)."""
    val_dict = dict(values)
    low = _mean([val_dict.get(f) for f in [250, 500] if f in val_dict])
    mid = _mean([val_dict.get(f) for f in [1000, 2000] if f in val_dict])
    high = _mean([val_dict.get(f) for f in [4000, 8000] if f in val_dict])

    if low is not None and mid is not None and high is not None:
        if mid - low >= 15 and mid - high >= 15:
            return True
    return False
