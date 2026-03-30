"""Masking error detection in audiometric data."""

from __future__ import annotations

from config import Config
from interpretation.models import AudiogramData, EarThresholds
from interpretation.indices import best_ac_threshold, best_bc_threshold


def detect_masking_errors(data: AudiogramData) -> tuple[list[str], list[str]]:
    """Detect masking errors for both ears.

    Returns (right_ear_errors, left_ear_errors).
    """
    right_errors = []
    left_errors = []

    right_errors.extend(_check_unmasked_bc(data.right_ear))
    left_errors.extend(_check_unmasked_bc(data.left_ear))

    right_errors.extend(_check_missing_ac_masking(data.right_ear, data.left_ear))
    left_errors.extend(_check_missing_ac_masking(data.left_ear, data.right_ear))

    right_errors.extend(_check_shadow_curve(data.right_ear, data.left_ear))
    left_errors.extend(_check_shadow_curve(data.left_ear, data.right_ear))

    right_errors.extend(_check_overmasking(data.right_ear))
    left_errors.extend(_check_overmasking(data.left_ear))

    dilemma = _check_masking_dilemma(data)
    if dilemma:
        right_errors.append(dilemma)
        left_errors.append(dilemma)

    return right_errors, left_errors


def _check_unmasked_bc(ear: EarThresholds) -> list[str]:
    """Check 1: Unmasked bone conduction is always unreliable (IA ≈ 0 dB for BC).

    Flag any frequency where BC is present but only unmasked.
    """
    errors = []
    for freq in Config.ALL_FREQUENCIES:
        has_unmasked = ear.bone_conduction.get(freq) is not None
        has_masked = ear.bone_masked.get(freq) is not None
        if has_unmasked and not has_masked:
            # Also check if there is an air-bone gap making this especially problematic
            ac = best_ac_threshold(ear, freq)
            bc = ear.bone_conduction.get(freq)
            if ac is not None and bc is not None:
                gap = ac - bc
                if gap >= Config.ABG_THRESHOLD:
                    errors.append(
                        f"Unmasked bone conduction at {freq} Hz ({ear.side} ear) with "
                        f"{gap:.0f} dB air-bone gap. Masking is required; this BC value "
                        f"may reflect the contralateral cochlea."
                    )
                else:
                    errors.append(
                        f"Bone conduction at {freq} Hz ({ear.side} ear) is unmasked. "
                        f"BC masking is always recommended (interaural attenuation ≈ 0 dB)."
                    )
    return errors


def _check_missing_ac_masking(test_ear: EarThresholds, non_test_ear: EarThresholds) -> list[str]:
    """Check 2: Missing AC masking when interaural difference >= 40 dB."""
    errors = []
    for freq in Config.ALL_FREQUENCIES:
        test_ac = test_ear.air_conduction.get(freq)
        nte_bc = best_bc_threshold(non_test_ear, freq)

        if test_ac is None or nte_bc is None:
            continue

        diff = test_ac - nte_bc
        has_masked = test_ear.air_masked.get(freq) is not None

        if diff >= Config.IA_SUPRAURAL and not has_masked:
            errors.append(
                f"Air conduction at {freq} Hz ({test_ear.side} ear) is {test_ac:.0f} dB, "
                f"but contralateral BC is {nte_bc:.0f} dB (difference: {diff:.0f} dB ≥ "
                f"{Config.IA_SUPRAURAL} dB). AC masking was required but not performed."
            )
    return errors


def _check_shadow_curve(
    poorer_ear: EarThresholds, better_ear: EarThresholds
) -> list[str]:
    """Check 3: Shadow curve detection.

    If the poorer ear's unmasked AC tracks ~40-65 dB above the better ear's BC
    across 3+ frequencies, this suggests cross-hearing.
    """
    shadow_freqs = []
    for freq in Config.ALL_FREQUENCIES:
        poorer_ac = poorer_ear.air_conduction.get(freq)
        better_bc = best_bc_threshold(better_ear, freq)

        if poorer_ac is None or better_bc is None:
            continue

        diff = poorer_ac - better_bc
        if 35 <= diff <= 70:
            shadow_freqs.append(freq)

    if len(shadow_freqs) >= 3:
        freq_str = ", ".join(f"{f} Hz" for f in shadow_freqs)
        return [
            f"Possible shadow curve in {poorer_ear.side} ear. Unmasked AC thresholds "
            f"at {freq_str} track approximately 40-65 dB above the contralateral BC, "
            f"suggesting cross-hearing. These thresholds may not represent true "
            f"{poorer_ear.side} ear hearing."
        ]
    return []


def _check_overmasking(ear: EarThresholds) -> list[str]:
    """Check 4: Overmasking indicators.

    If masked threshold is >= 15 dB worse than unmasked at the same frequency.
    """
    errors = []
    # Check AC
    for freq in Config.ALL_FREQUENCIES:
        unmasked = ear.air_conduction.get(freq)
        masked = ear.air_masked.get(freq)
        if unmasked is not None and masked is not None:
            diff = masked - unmasked
            if diff >= 15:
                errors.append(
                    f"Possible overmasking at {freq} Hz ({ear.side} ear, AC): "
                    f"masked threshold ({masked:.0f} dB) is {diff:.0f} dB worse than "
                    f"unmasked ({unmasked:.0f} dB)."
                )

    # Check BC
    for freq in Config.ALL_FREQUENCIES:
        unmasked = ear.bone_conduction.get(freq)
        masked = ear.bone_masked.get(freq)
        if unmasked is not None and masked is not None:
            diff = masked - unmasked
            if diff >= 15:
                errors.append(
                    f"Possible overmasking at {freq} Hz ({ear.side} ear, BC): "
                    f"masked threshold ({masked:.0f} dB) is {diff:.0f} dB worse than "
                    f"unmasked ({unmasked:.0f} dB)."
                )
    return errors


def _check_masking_dilemma(data: AudiogramData) -> str | None:
    """Check 5: Masking dilemma - bilateral conductive components.

    If both ears show significant air-bone gaps, effective masking may
    be impossible.
    """
    right_gaps = 0
    left_gaps = 0

    for freq in [500, 1000, 2000, 4000]:
        r_ac = best_ac_threshold(data.right_ear, freq)
        r_bc = best_bc_threshold(data.right_ear, freq)
        l_ac = best_ac_threshold(data.left_ear, freq)
        l_bc = best_bc_threshold(data.left_ear, freq)

        if r_ac is not None and r_bc is not None and (r_ac - r_bc) >= Config.ABG_THRESHOLD:
            right_gaps += 1
        if l_ac is not None and l_bc is not None and (l_ac - l_bc) >= Config.ABG_THRESHOLD:
            left_gaps += 1

    if right_gaps >= 2 and left_gaps >= 2:
        return (
            "Masking dilemma: bilateral conductive components detected. "
            "Effective masking may be impossible due to risk of overmasking "
            "in both ears. Interpret masked values with caution. "
            "Consider ABR or other objective measures."
        )
    return None
