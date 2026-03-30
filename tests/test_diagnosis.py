"""Tests for differential diagnosis generation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interpretation.models import (
    AudiogramData, EarThresholds, EarInterpretation, FullInterpretation,
)
from interpretation.diagnosis import generate_diagnoses


def _make_interp(r_type="Normal", l_type="Normal", r_config="flat", l_config="flat",
                 r_fh=None, l_fh=None, r_disc_rating=None, l_disc_rating=None,
                 r_rollover=None, l_rollover=None, r_gaps=None, l_gaps=None):
    interp = FullInterpretation()
    interp.right = EarInterpretation(
        side="right", loss_type=r_type, configuration=r_config,
        fh=r_fh, discrimination_rating=r_disc_rating,
        rollover_index=r_rollover,
        air_bone_gaps=r_gaps or {},
    )
    interp.left = EarInterpretation(
        side="left", loss_type=l_type, configuration=l_config,
        fh=l_fh, discrimination_rating=l_disc_rating,
        rollover_index=l_rollover,
        air_bone_gaps=l_gaps or {},
    )
    return interp


def _make_data(r_ac=None, l_ac=None):
    data = AudiogramData()
    if r_ac:
        data.right_ear.air_conduction = r_ac
    if l_ac:
        data.left_ear.air_conduction = l_ac
    return data


class TestDiagnosis:
    def test_bilateral_sloping_snhl(self):
        interp = _make_interp(
            r_type="Sensorineural", l_type="Sensorineural",
            r_config="sloping", l_config="sloping",
        )
        data = _make_data(
            r_ac={500: 20, 1000: 30, 2000: 45, 4000: 60},
            l_ac={500: 25, 1000: 35, 2000: 50, 4000: 65},
        )
        diagnoses = generate_diagnoses(interp, data)
        assert len(diagnoses) >= 1
        names = [d.name for d in diagnoses]
        assert "Presbyacusis" in names

    def test_unilateral_conductive(self):
        interp = _make_interp(
            r_type="Conductive", l_type="Normal",
            r_config="flat",
            r_gaps={500: 25, 1000: 30, 2000: 25, 4000: 20},
        )
        data = _make_data(
            r_ac={500: 35, 1000: 40, 2000: 35, 4000: 30},
            l_ac={500: 10, 1000: 10, 2000: 15, 4000: 15},
        )
        diagnoses = generate_diagnoses(interp, data)
        names = [d.name for d in diagnoses]
        assert any("otitis" in n.lower() or "otosclerosis" in n.lower() for n in names)

    def test_noise_notch(self):
        interp = _make_interp(
            r_type="Sensorineural", l_type="Normal",
            r_config="noise-notch",
        )
        data = _make_data(
            r_ac={500: 10, 1000: 15, 2000: 20, 4000: 55},
            l_ac={500: 10, 1000: 10, 2000: 10, 4000: 10},
        )
        diagnoses = generate_diagnoses(interp, data)
        names = [d.name for d in diagnoses]
        assert "Noise-induced hearing loss" in names

    def test_poor_discrimination_retrocochlear(self):
        interp = _make_interp(
            r_type="Sensorineural", l_type="Normal",
            r_config="sloping", r_disc_rating="poor",
        )
        data = _make_data(
            r_ac={500: 30, 1000: 40, 2000: 55, 4000: 70},
            l_ac={500: 10, 1000: 10, 2000: 10, 4000: 10},
        )
        diagnoses = generate_diagnoses(interp, data)
        names = [d.name for d in diagnoses]
        assert "Vestibular schwannoma" in names

    def test_returns_max_3(self):
        interp = _make_interp(
            r_type="Mixed", l_type="Sensorineural",
            r_config="flat", l_config="sloping",
            r_gaps={500: 25, 1000: 30, 2000: 25, 4000: 20},
        )
        data = _make_data(
            r_ac={500: 60, 1000: 65, 2000: 60, 4000: 55},
            l_ac={500: 30, 1000: 40, 2000: 55, 4000: 70},
        )
        diagnoses = generate_diagnoses(interp, data)
        assert len(diagnoses) <= 3

    def test_normal_hearing_no_diagnoses(self):
        interp = _make_interp()
        data = _make_data(
            r_ac={500: 10, 1000: 10, 2000: 10, 4000: 10},
            l_ac={500: 10, 1000: 10, 2000: 10, 4000: 10},
        )
        diagnoses = generate_diagnoses(interp, data)
        assert len(diagnoses) == 0
