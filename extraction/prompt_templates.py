"""Prompt templates for Claude Vision audiogram extraction."""

AUDIOGRAM_EXTRACTION_PROMPT = """You are an expert audiologist analyzing an audiogram image. Extract ALL data from this audiogram precisely.

## Audiogram Symbol Legend (ISO 8253-1)

### Pure-Tone Audiogram:
- **Right ear air conduction (unmasked)**: O (red circle)
- **Left ear air conduction (unmasked)**: X (blue cross)
- **Right ear air conduction (masked)**: △ (red triangle)
- **Left ear air conduction (masked)**: □ (blue square)
- **Right ear bone conduction (unmasked)**: < (red, opening left)
- **Left ear bone conduction (unmasked)**: > (blue, opening right)
- **Right ear bone conduction (masked)**: [ (red bracket, opening right)
- **Left ear bone conduction (masked)**: ] (blue bracket, opening left)
- **No response**: any symbol with a downward arrow (↓) means no response at maximum output

### Axes:
- **X-axis (horizontal)**: Frequency in Hz, typically 125 to 8000 Hz (left to right)
- **Y-axis (vertical)**: Hearing level in dB HL, typically -10 to 120 dB (top = better hearing, bottom = worse)

### Speech Audiogram (if present):
- Usually a separate graph showing speech discrimination (%) on Y-axis vs. intensity (dB) on X-axis
- Right ear curves typically in red, left ear in blue
- Look for the maximum discrimination score and the dB level where it occurs
- Look for the SRT (Speech Reception Threshold) = the dB level at 50% discrimination

## Instructions

1. Examine the pure-tone audiogram carefully. For EACH ear, read threshold values at every tested frequency.
2. Distinguish between masked and unmasked symbols. Report them separately.
3. If a speech audiogram is present, extract SRT and maximum discrimination data.
4. Report frequencies where no response was obtained (symbol with arrow).
5. Note any metadata visible (patient info, date, equipment).
6. Rate your confidence in the extraction.

## Output Format

Return ONLY valid JSON in this exact structure (use null for missing/untested values):

```json
{
  "pure_tone": {
    "right_ear": {
      "air_conduction": {"250": null, "500": null, "1000": null, "2000": null, "4000": null, "8000": null},
      "air_masked": {"250": null, "500": null, "1000": null, "2000": null, "4000": null, "8000": null},
      "bone_conduction": {"250": null, "500": null, "1000": null, "2000": null, "4000": null, "8000": null},
      "bone_masked": {"250": null, "500": null, "1000": null, "2000": null, "4000": null, "8000": null},
      "no_response_ac": [],
      "no_response_bc": []
    },
    "left_ear": {
      "air_conduction": {"250": null, "500": null, "1000": null, "2000": null, "4000": null, "8000": null},
      "air_masked": {"250": null, "500": null, "1000": null, "2000": null, "4000": null, "8000": null},
      "bone_conduction": {"250": null, "500": null, "1000": null, "2000": null, "4000": null, "8000": null},
      "bone_masked": {"250": null, "500": null, "1000": null, "2000": null, "4000": null, "8000": null},
      "no_response_ac": [],
      "no_response_bc": []
    }
  },
  "speech": {
    "right_ear": {
      "srt": null,
      "max_discrimination": null,
      "db_at_max_discrimination": null,
      "discrimination_at_highest_level": null,
      "db_at_highest_level": null,
      "masked": false
    },
    "left_ear": {
      "srt": null,
      "max_discrimination": null,
      "db_at_max_discrimination": null,
      "discrimination_at_highest_level": null,
      "db_at_highest_level": null,
      "masked": false
    }
  },
  "metadata": {
    "patient_info": null,
    "date": null,
    "equipment": null,
    "notes": null
  },
  "extraction_confidence": "high",
  "extraction_notes": []
}
```

Important rules:
- Threshold values should be integers in dB HL (e.g., 10, 25, 40, 55)
- Read values as precisely as possible from the graph (round to nearest 5 dB)
- Include intermediate frequencies (750, 1500, 3000, 6000) if they are tested
- no_response_ac / no_response_bc: list of frequency integers where no response was obtained
- extraction_confidence: "high" if the image is clear and all symbols readable, "medium" if some ambiguity, "low" if poor image quality
- extraction_notes: list any ambiguities, overlapping symbols, unclear readings
- For speech audiometry: discrimination scores in percent (0-100), SRT in dB
- If speech audiogram is not present, leave all speech values as null
- If you see a single panel with both ears, extract both. If separate panels per ear, extract from each.
- ONLY return the JSON object, nothing else.
"""
