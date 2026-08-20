"""
Recipe image extraction.

Sends an uploaded image to Gemini with structured output mode
(response_schema=ExtractedRecipe), so the model's response is
parsed directly into a validated ExtractedRecipe object — no
manual JSON parsing, no "please only respond in JSON" prompting.
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

from src.config import (
    GEMINI_MODEL,
    MAX_RETRIES,
    RETRY_BASE_DELAY_SECONDS,
    RETRYABLE_STATUS_CODES,
)
from src.importer.schema import ExtractedRecipe
from src.prompts.recipe_extraction_prompt import RECIPE_EXTRACTION_PROMPT
from src.observability import setup_observability


def extract_recipe_from_image(image_bytes: bytes, mime_type: str) -> dict:
    """
    Extract a structured recipe from a photo of a recipe (screen-
    shot, cookbook page, or handwritten card).

    Args:
        image_bytes: Raw image file bytes.
        mime_type: The image's MIME type (e.g. "image/png",
            "image/jpeg").

    Returns:
        dict: {
            "success": bool,
            "error": str | None,
            "recipe": dict | None,  # matches ExtractedRecipe shape
        }
    """

    if not image_bytes:
        return _error("No image data received.")

    if mime_type not in ("image/png", "image/jpeg"):
        return _error(f"Unsupported image type: {mime_type}")

    setup_observability()
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return _error("GOOGLE_API_KEY not found in environment variables.")

    client = genai.Client(api_key=api_key)

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[RECIPE_EXTRACTION_PROMPT, image_part],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedRecipe,
                ),
            )

            extracted: ExtractedRecipe = response.parsed

            if extracted is None:
                return _error(
                    "The model's response didn't match the expected "
                    "recipe structure. Try a clearer image."
                )

            return {
                "success": True,
                "error": None,
                "recipe": extracted.model_dump(),
            }

        except errors.APIError as e:
            last_error = e

            if e.code not in RETRYABLE_STATUS_CODES:
                return _error(f"Extraction failed: {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY_SECONDS * (2 ** attempt))

        except Exception as e:
            last_error = e

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY_SECONDS * (2 ** attempt))

    return _error(f"Extraction failed after retrying: {last_error}")


def _error(message: str) -> dict:
    return {"success": False, "error": message, "recipe": None}