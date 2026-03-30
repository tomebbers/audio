"""Tests for hearing loss classification."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interpretation.models import EarThresholds
from interpretation.classifier import classify_degree, classify_type, classify_configuration


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


class TestDegree:
    def test_normal(self):
        assert classify_degree(15.0) == "Normal"

    def test_mild(self):
        assert classify_degree(30.0) == "Mild"

    def test_moderate(self):
        assert classify_degree(50.0) == "Moderate"

    def test_moderately_severe(self):
        assert classify_degree(65.0) == "Moderately severe"

    def test_severe(self):
        assert classify_degree(80.0) == "Severe"

    def test_profound(self):
        assert classify_degree(100.0) == "Profound"

    def test_none(self):
        assert classify_degree(None) == "Unable to determine"

    def test_boundary_20(self):
        assert classify_degree(20.0) == "Normal"

    def test_boundary_21(self):
        assert classify_degree(21.0) == "Mild"


class TestType:
    def test_normal(self):
        ear = _make_ear(
            ac={500: 10, 1000: 15, 2000: 10, 4000: 15},
            bc={500: 5, 1000: 10, 2000: 5, 4000: 10},
        )
        assert classify_type(ear) == "Normal"

    def test_conductive(self):
        ear = _make_ear(
            ac={500: 40, 1000: 45, 2000: 40, 4000: 35},
            bc={500: 10, 1000: 10, 2000: 10, 4000: 10},
        )
        assert classify_type(ear) == "Conductive"

    def test_sensorineural(self):
        ear = _make_ear(
            ac={500: 50, 1000: 55, 2000: 60, 4000: 65},
            bc={500: 45, 1000: 50, 2000: 55, 4000: 60},
        )
        assert classify_type(ear) == "Sensorineural"

    def test_mixed(self):
        ear = _make_ear(
            ac={500: 60, 1000: 65, 2000: 70, 4000: 75},
            bc={500: 30, 1000: 35, 2000: 40, 4000: 45},
        )
        assert classify_type(ear) == "Mixed"

    def test_conductive_needs_two_freqs(self):
        """Only one frequency with gap should not be classified as conductive."""
        ear = _make_ear(
            ac={500: 40, 1000: 25, 2000: 25, 4000: 25},
            bc={500: 10, 1000: 20, 2000: 20, 4000: 20},
        )
        # Only 500 Hz has gap >= 15 (30 dB), others have 5 dB gap
        assert classify_type(ear) == "Sensorineural"


class TestConfiguration:
    def test_flat(self):
        ear = _make_ear(ac={250: 40, 500: 40, 1000: 45, 2000: 40, 4000: 45, 8000: 40})
        assert classify_configuration(ear) == "flat"

    def test_sloping(self):
        ear = _make_ear(ac={250: 15, 500: 20, 1000: 25, 2000: 40, 4000: 55, 8000: 65})
        assert classify_configuration(ear) == "sloping"

    def test_rising(self):
        ear = _make_ear(ac={250: 60, 500: 55, 1000: 45, 2000: 30, 4000: 25, 8000: 20})
        assert classify_configuration(ear) == "rising"
