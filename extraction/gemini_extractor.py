"""Google Gemini Vision API-based audiogram data extraction (free tier).

Uses the lightweight REST API directly instead of the heavy gRPC SDK
to minimize memory usage on free hosting tiers.
"""

from __future__ import annotations

import base64
import json
import re

import httpx

from config import Config
from extraction.prompt_templates import AUDIOGRAM_EXTRACTION_PROMPT
from extraction.data_parser import build_audiogram_data, parse_json_response

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def extract_audiogram_gemini(image_bytes: bytes, mime_type: str):
    """Extract audiogram data from an image using Google Gemini Vision (free).

    Uses REST API directly — no heavy SDK dependencies.
    """
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    url = GEMINI_API_URL.format(model=Config.GEMINI_MODEL)
    url += f"?key={Config.GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_b64,
                        }
                    },
                    {
                        "text": AUDIOGRAM_EXTRACTION_PROMPT,
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
        },
    }

    response = httpx.post(url, json=payload, timeout=60.0)
    response.raise_for_status()

    result = response.json()

    # Extract text from Gemini response
    try:
        response_text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected Gemini response structure: {result}") from e

    raw_data = parse_json_response(response_text)
    return build_audiogram_data(raw_data)
