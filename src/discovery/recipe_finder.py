"""
Suggests real recipes from the web using Gemini's Google Search
grounding tool, excluding recipes the user already has saved.

Deliberately does NOT combine this with structured output
(response_schema): Gemini 3.6 Flash — this project's configured
model — has a documented reliability issue where combining Google
Search grounding with structured JSON output on longer prompts can
return no text at all, or a TOO_MANY_TOOL_CALLS error. Instead,
this returns plain grounded text (which the prompt asks to be
formatted in clear sections) plus a verified list of real source
URLs pulled from the response's grounding metadata — the citations
are guaranteed real regardless of how well-formatted the text is.
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


# Domains that turn up in Google Search results but rarely link to
# an actually-readable recipe page — social/video platforms where
# the content is typically behind a login wall or buried in a
# video caption rather than a proper recipe page.
#
# Ideally this would be enforced via the Search tool's own
# exclude_domains option, but that field is explicitly documented
# as unsupported on the Gemini Developer API (API-key auth) — it
# only works on Vertex AI. So it's enforced here in code instead,
# as a deterministic backstop regardless of how well the model
# follows the prompt's own guidance to avoid these sources.
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
    """
    Suggest ~3 real recipes from the web matching a natural-
    language request, avoiding the user's already-saved recipes.

    Args:
        query: What the user is looking for, e.g. "easy recipes
            with pasta and chicken".
        excluded_names: Names of recipes the user already has
            saved, so the model can actively avoid suggesting them.

    Returns:
        dict: {
            "success": bool,
            "error": str | None,
            "response_text": str | None,
            "sources": list[dict] | None,
            # each source: {"title": str, "url": str, "domain": str}
        }
    """

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
    """
    Pull real, verified source URLs out of the response's grounding
    metadata — but only the ones actually cited in the final answer.

    grounding_chunks lists every page the model consulted during
    search, which is often far more than what it actually used —
    the model may run several searches and only cite a few results.
    grounding_supports maps specific text segments in the response
    to which chunk indices back them up, so filtering to only the
    chunks referenced there gives just the sources genuinely behind
    the 3 suggestions shown, not everything that was searched.
    """

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

        # Fall back to showing everything only if the model didn't
        # provide per-segment citations at all (rare, but possible) —
        # better to show extra sources than none.
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