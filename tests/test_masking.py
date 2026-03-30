"""Tests for masking error detection."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interpretation.models import AudiogramData, EarThresholds
from interpretation.masking import detect_masking_errors


def _make_data(right_ac=None, right_bc=None, right_ac_m=None, right_bc_m=None,
               left_ac=None, left_bc=None, left_ac_m=None, left_bc_m=None):
    data = AudiogramData()
    if right_ac:
        data.right_ear.air_conduction = right_ac
    if right_bc:
        data.right_ear.bone_conduction = right_bc
    if right_ac_m:
        data.right_ear.air_masked = right_ac_m
    if right_bc_m:
        data.right_ear.bone_masked = right_bc_m
    if left_ac:
        data.left_ear.air_conduction = left_ac
    if left_bc:
        data.left_ear.bone_conduction = left_bc
    if left_ac_m:
        data.left_ear.air_masked = left_ac_m
    if left_bc_m:
        data.left_ear.bone_masked = left_bc_m
    return data


class TestUnmaskedBC:
    def test_flags_unmasked_bc_with_gap(self):
        data = _make_data(
            right_ac={1000: 50},
            right_bc={1000: 10},  # 40 dB gap, unmasked BC
        )
        right_errors, _ = detect_masking_errors(data)
        assert any("Unmasked bone conduction at 1000 Hz" in e for e in right_errors)

    def test_no_flag_when_masked(self):
        data = _make_data(
            right_ac={1000: 50},
            right_bc_m={1000: 15},  # Only masked BC, no unmasked
        )
        right_errors, _ = detect_masking_errors(data)
        assert not any("1000 Hz" in e for e in right_errors)


class TestMissingACMasking:
    def test_flags_large_interaural_difference(self):
        data = _make_data(
            right_ac={1000: 70},  # Poorer ear, unmasked
            left_bc={1000: 10},   # Better ear BC
        )
        right_errors, _ = detect_masking_errors(data)
        assert any("AC masking was required" in e for e in right_errors)

    def test_no_flag_small_difference(self):
        data = _make_data(
            right_ac={1000: 30},
            left_bc={1000: 10},  # Difference = 20, below 40 threshold
        )
        right_errors, _ = detect_masking_errors(data)
        assert not any("AC masking was required" in e for e in right_errors)


class TestShadowCurve:
    def test_detects_shadow(self):
        # Poorer ear AC tracks ~50 dB above better ear BC across many frequencies
        data = _make_data(
            right_ac={500: 60, 1000: 65, 2000: 70, 4000: 75},
            left_bc={500: 10, 1000: 10, 2000: 15, 4000: 15},
        )
        # Right ear AC - Left ear BC = ~50 dB at each freq
        right_errors, _ = detect_masking_errors(data)
        assert any("shadow curve" in e.lower() for e in right_errors)


class TestOvermasking:
    def test_detects_overmasking(self):
        data = _make_data(
            right_ac={1000: 40},
            right_ac_m={1000: 60},  # Masked 20 dB worse than unmasked
        )
        right_errors, _ = detect_masking_errors(data)
        assert any("overmasking" in e.lower() for e in right_errors)


class TestMaskingDilemma:
    def test_bilateral_conductive(self):
        data = _make_data(
            right_ac={500: 60, 1000: 65, 2000: 60, 4000: 55},
            right_bc={500: 20, 1000: 20, 2000: 20, 4000: 20},
            left_ac={500: 55, 1000: 60, 2000: 55, 4000: 50},
            left_bc={500: 15, 1000: 15, 2000: 15, 4000: 15},
        )
        right_errors, left_errors = detect_masking_errors(data)
        assert any("masking dilemma" in e.lower() for e in right_errors)
        assert any("masking dilemma" in e.lower() for e in left_errors)
