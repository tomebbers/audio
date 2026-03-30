"""Tests for speech audiometry interpretation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interpretation.models import SpeechData
from interpretation.speech import interpret_speech


class TestSRTConcordance:
    def test_concordant(self):
        speech = SpeechData(side="right", srt=30)
        result = interpret_speech(speech, fh=28.0)
        assert result["srt_fh_concordance"] == "concordant"

    def test_discrepant(self):
        speech = SpeechData(side="right", srt=45)
        result = interpret_speech(speech, fh=25.0)
        assert result["srt_fh_concordance"] == "discrepant"

    def test_no_srt(self):
        speech = SpeechData(side="right")
        result = interpret_speech(speech, fh=30.0)
        assert result["srt_fh_concordance"] is None


class TestDiscrimination:
    def test_good(self):
        speech = SpeechData(side="right", max_discrimination=95)
        result = interpret_speech(speech, fh=30.0)
        assert result["discrimination_rating"] == "good"

    def test_moderate(self):
        speech = SpeechData(side="right", max_discrimination=75)
        result = interpret_speech(speech, fh=30.0)
        assert result["discrimination_rating"] == "moderate"

    def test_poor(self):
        speech = SpeechData(side="right", max_discrimination=50)
        result = interpret_speech(speech, fh=30.0)
        assert result["discrimination_rating"] == "poor"


class TestRollover:
    def test_significant_rollover(self):
        speech = SpeechData(
            side="right",
            max_discrimination=90,
            discrimination_at_highest_level=40,
        )
        result = interpret_speech(speech, fh=40.0)
        assert result["rollover_index"] is not None
        assert result["rollover_index"] > 0.45
        assert result["rollover_significant"] is True

    def test_no_rollover(self):
        speech = SpeechData(
            side="right",
            max_discrimination=92,
            discrimination_at_highest_level=88,
        )
        result = interpret_speech(speech, fh=30.0)
        assert result["rollover_significant"] is False
