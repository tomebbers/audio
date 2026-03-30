"""Google Gemini Vision API-based audiogram data extraction (free tier)."""

from __future__ import annotations

import json
import re

import google.generativeai as genai
from PIL import Image
import io

from config import Config
from extraction.prompt_templates import AUDIOGRAM_EXTRACTION_PROMPT
from extraction.data_parser import build_audiogram_data, parse_json_response


def extract_audiogram_gemini(image_bytes: bytes, mime_type: str):
    """Extract audiogram data from an image using Google Gemini Vision (free).

    Args:
        image_bytes: Raw image bytes.
        mime_type: MIME type (e.g., "image/jpeg", "image/png").

    Returns:
        AudiogramData with extracted thresholds and speech data.
    """
    genai.configure(api_key=Config.GEMINI_API_KEY)

    model = genai.GenerativeModel(Config.GEMINI_MODEL)

    # Create PIL image for Gemini
    img = Image.open(io.BytesIO(image_bytes))

    response = model.generate_content(
        [AUDIOGRAM_EXTRACTION_PROMPT, img],
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
        ),
    )

    response_text = response.text
    raw_data = parse_json_response(response_text)
    return build_audiogram_data(raw_data)
