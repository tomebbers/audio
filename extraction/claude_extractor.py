"""Claude Vision API-based audiogram data extraction."""

from __future__ import annotations

import base64

import anthropic

from config import Config
from extraction.prompt_templates import AUDIOGRAM_EXTRACTION_PROMPT
from extraction.data_parser import build_audiogram_data, parse_json_response


def extract_audiogram_claude(image_bytes: bytes, mime_type: str):
    """Extract audiogram data from an image using Claude Vision.

    Args:
        image_bytes: Raw image bytes.
        mime_type: MIME type (e.g., "image/jpeg", "image/png").

    Returns:
        AudiogramData with extracted thresholds and speech data.
    """
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    message = client.messages.create(
        model=Config.ANTHROPIC_MODEL,
        max_tokens=Config.ANTHROPIC_MAX_TOKENS,
        messages=[
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
    )

    response_text = message.content[0].text
    raw_data = parse_json_response(response_text)
    return build_audiogram_data(raw_data)
