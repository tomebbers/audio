"""Fletcher Index calculations and air-bone gap computation."""

from __future__ import annotations

from config import Config
from interpretation.models import EarThresholds


def best_ac_threshold(ear: EarThresholds, freq: int) -> float | None:
    """Return masked AC threshold if available, otherwise unmasked."""
    masked = ear.air_masked.get(freq)
    if masked is not None:
        return masked
    return ear.air_conduction.get(freq)


def best_bc_threshold(ear: EarThresholds, freq: int) -> float | None:
    """Return masked BC threshold if available, otherwise unmasked."""
    masked = ear.bone_masked.get(freq)
    if masked is not None:
        return masked
    return ear.bone_conduction.get(freq)


def calculate_fh(ear: EarThresholds) -> float | None:
    """FH (Fletcher Index) = mean of AC at 500, 1000, 2000 Hz."""
    values = [best_ac_threshold(ear, f) for f in Config.FH_FREQUENCIES]
    if any(v is None for v in values):
        return None
    return round(sum(values) / len(values), 1)


def calculate_fhi(ear: EarThresholds) -> float | None:
    """FHI (Fletcher Index High) = mean of AC at 1000, 2000, 4000 Hz."""
    values = [best_ac_threshold(ear, f) for f in Config.FHI_FREQUENCIES]
    if any(v is None for v in values):
        return None
    return round(sum(values) / len(values), 1)


def calculate_air_bone_gaps(ear: EarThresholds) -> dict[int, float]:
    """Compute air-bone gap at each frequency where both AC and BC exist."""
    gaps = {}
    for freq in Config.ALL_FREQUENCIES:
        ac = best_ac_threshold(ear, freq)
        bc = best_bc_threshold(ear, freq)
        if ac is not None and bc is not None:
            gaps[freq] = round(ac - bc, 1)
    return gaps
