"""
Finds real recipes from the web via Gemini's Google Search grounding,
skipping anything the user already has saved.

Not combined with structured output on purpose - Search grounding +
structured JSON output is flaky on longer prompts with this model
(sometimes just returns no text). So this gets plain text back
instead, plus a list of real source URLs pulled straight from the
response's grounding metadata, which stays accurate no matter how
messy the text formatting is.
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
from src.prompts.recipe_discovery_prompt import build_discovery_prompt
from src.observability import setup_observability


# Social/video sites that show up in search but rarely link to an
# actually-readable recipe page. The Search tool has an
# exclude_domains option, but it's not supported on API-key auth
# (Vertex-only), so this is a manual blocklist instead.
_EXCLUDED_SOURCE_DOMAINS = (
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "pinterest.com",
    "reddit.com",
    "youtube.com",
    "youtu.be",
    "twitter.com",
    "x.com",
)


def suggest_recipes_online(query: str, excluded_names: list[str]) -> dict:
    """Suggest ~3 real recipes matching query, skipping anything in
    excluded_names (the user's saved recipes)."""

    if not query or not query.strip():
        return _error("Please describe what kind of recipe you're looking for.")

    setup_observability()
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return _error("GOOGLE_API_KEY not found in environment variables.")

    client = genai.Client(api_key=api_key)

    prompt = build_discovery_prompt(query.strip(), excluded_names)

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )

            if not response.text:
                return _error(
                    "The assistant couldn't find recipe suggestions for "
                    "that request. Try rephrasing it."
                )

            sources = _extract_sources(response)

            return {
                "success": True,
                "error": None,
                "response_text": response.text,
                "sources": sources,
            }

        except errors.APIError as e:
            last_error = e

            if e.code not in RETRYABLE_STATUS_CODES:
                return _error(f"Search failed: {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY_SECONDS * (2 ** attempt))

        except Exception as e:
            last_error = e

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY_SECONDS * (2 ** attempt))

    return _error(f"Search failed after retrying: {last_error}")


def _extract_sources(response) -> list:
    """Pull the actually-cited source URLs out of the grounding
    metadata. grounding_chunks is every page the model looked at
    (often way more than it used); grounding_supports says which
    chunks back up which part of the answer, so we filter down to
    just those."""

    sources = []

    try:
        candidate = response.candidates[0]
        grounding_metadata = candidate.grounding_metadata

        if grounding_metadata is None or not grounding_metadata.grounding_chunks:
            return sources

        chunks = grounding_metadata.grounding_chunks
        supports = grounding_metadata.grounding_supports or []

        cited_indices = set()
        for support in supports:
            if support.grounding_chunk_indices:
                cited_indices.update(support.grounding_chunk_indices)

        # No per-segment citations at all? Show everything instead
        # of nothing.
        indices_to_show = cited_indices if cited_indices else range(len(chunks))

        for i in indices_to_show:
            if i >= len(chunks):
                continue

            chunk = chunks[i]

            if chunk.web is None:
                continue

            url = chunk.web.uri
            domain = chunk.web.domain or ""

            if _is_excluded_domain(url, domain):
                continue

            sources.append(
                {
                    "title": chunk.web.title or url,
                    "url": url,
                    "domain": domain,
                }
            )

    except (AttributeError, IndexError):
        pass

    return sources


def _is_excluded_domain(url: str, domain: str) -> bool:
    """Check a URL/domain against the social-media/video blocklist."""
    haystack = f"{url} {domain}".lower()
    return any(excluded in haystack for excluded in _EXCLUDED_SOURCE_DOMAINS)


def _error(message: str) -> dict:
    return {
        "success": False,
        "error": message,
        "response_text": None,
        "sources": None,
    }