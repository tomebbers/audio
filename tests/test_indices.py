"""Tests for Fletcher Index and air-bone gap calculations."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interpretation.models import EarThresholds
from interpretation.indices import calculate_fh, calculate_fhi, calculate_air_bone_gaps


def _make_ear(side="right", ac=None, bc=None, ac_masked=None, bc_masked=None):
    ear = EarThresholds(side=side)
    if ac:
        ear.air_conduction = ac
    if bc:
        ear.bone_conduction = bc
    if ac_masked:
        ear.air_masked = ac_masked
    if bc_masked:
        ear.bone_masked = bc_masked
    return ear


class TestFH:
    def test_normal_hearing(self):
        ear = _make_ear(ac={500: 10, 1000: 10, 2000: 15})
        assert calculate_fh(ear) == 11.7

    def test_moderate_loss(self):
        ear = _make_ear(ac={500: 40, 1000: 45, 2000: 50})
        assert calculate_fh(ear) == 45.0

    def test_missing_frequency(self):
        ear = _make_ear(ac={500: 20, 1000: 25})
        assert calculate_fh(ear) is None

    def test_prefers_masked(self):
        ear = _make_ear(
            ac={500: 30, 1000: 35, 2000: 40},
            ac_masked={500: 35, 1000: 40, 2000: 45},
        )
        # Should use masked values
        assert calculate_fh(ear) == 40.0

    def test_mixed_masked_unmasked(self):
        ear = _make_ear(
            ac={500: 30, 1000: 35, 2000: 40},
            ac_masked={1000: 40},
        )
        # 500: unmasked 30, 1000: masked 40, 2000: unmasked 40
        assert calculate_fh(ear) == round((30 + 40 + 40) / 3, 1)


class TestFHI:
    def test_normal(self):
        ear = _make_ear(ac={1000: 10, 2000: 15, 4000: 20})
        assert calculate_fhi(ear) == 15.0

    def test_high_freq_loss(self):
        ear = _make_ear(ac={1000: 30, 2000: 50, 4000: 70})
        assert calculate_fhi(ear) == 50.0

    def test_missing_4k(self):
        ear = _make_ear(ac={1000: 30, 2000: 50})
        assert calculate_fhi(ear) is None


class TestAirBoneGap:
    def test_conductive_gap(self):
        ear = _make_ear(
            ac={500: 40, 1000: 45, 2000: 50},
            bc={500: 10, 1000: 15, 2000: 20},
        )
        gaps = calculate_air_bone_gaps(ear)
        assert gaps[500] == 30
        assert gaps[1000] == 30
        assert gaps[2000] == 30

    def test_no_gap_sensorineural(self):
        ear = _make_ear(
            ac={500: 50, 1000: 55, 2000: 60},
            bc={500: 45, 1000: 50, 2000: 55},
        )
        gaps = calculate_air_bone_gaps(ear)
        assert all(g <= 10 for g in gaps.values())

    def test_partial_data(self):
        ear = _make_ear(
            ac={500: 40, 1000: 45},
            bc={500: 10},
        )
        gaps = calculate_air_bone_gaps(ear)
        assert 500 in gaps
        assert 1000 not in gaps
