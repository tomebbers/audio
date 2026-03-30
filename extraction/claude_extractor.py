"""Claude Vision API-based audiogram data extraction.

Uses httpx REST API directly to avoid heavy anthropic SDK dependency.
"""

from __future__ import annotations

import base64

import httpx

from config import Config
from extraction.prompt_templates import AUDIOGRAM_EXTRACTION_PROMPT
from extraction.data_parser import build_audiogram_data, parse_json_response

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def extract_audiogram_claude(image_bytes: bytes, mime_type: str):
    """Extract audiogram data from an image using Claude Vision."""
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": Config.ANTHROPIC_MODEL,
        "max_tokens": Config.ANTHROPIC_MAX_TOKENS,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": AUDIOGRAM_EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    }

    response = httpx.post(
        ANTHROPIC_API_URL,
        json=payload,
        headers={
            "x-api-key": Config.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        timeout=60.0,
    )
    response.raise_for_status()

    result = response.json()
    response_text = result["content"][0]["text"]
    raw_data = parse_json_response(response_text)
    return build_audiogram_data(raw_data)
