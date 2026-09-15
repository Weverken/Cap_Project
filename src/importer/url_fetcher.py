"""
Recipe URL fetching.

Uses trafilatura to fetch a page and extract just the main
article content — stripping navigation, ads, sidebars, and
footers before anything gets sent to the model.

Also separately parses any schema.org Recipe JSON-LD embedded in
the page (most recipe sites include this for Google's own recipe
rich-results). This matters because prep time, cook time, and
servings are usually shown in a small metadata widget near the
top of the page, not in the flowing article prose — trafilatura's
boilerplate detection strips exactly that kind of widget out as
non-article content, so without this, that data never reaches the
model at all, regardless of how good the extraction prompt is.
"""

import json
import re

import trafilatura

MAX_TEXT_LENGTH = 15000  # keep the extraction prompt a reasonable size

_JSONLD_SCRIPT_PATTERN = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
_ISO8601_DURATION_PATTERN = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?")


def fetch_recipe_page_text(url: str) -> dict:
    """
    Fetch a URL and extract its main readable content, augmented
    with any structured Recipe metadata (prep/cook time, servings)
    found in the page's schema.org JSON-LD, if present.

    Returns:
        dict: {
            "success": bool,
            "error": str | None,
            "text": str | None,
        }
    """

    if not url or not url.strip():
        return _error("Please enter a URL.")

    url = url.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        downloaded = trafilatura.fetch_url(url)
    except Exception as e:
        return _error(f"Couldn't fetch that page: {e}")

    if downloaded is None:
        return _error(
            "Couldn't reach that page — check the URL, or the site may "
            "be blocking automated requests."
        )

    try:
        text = trafilatura.extract(downloaded)
    except Exception as e:
        return _error(f"Couldn't read that page's content: {e}")

    if not text or len(text.strip()) < 50:
        return _error(
            "Couldn't find readable recipe content on that page. It may "
            "be JavaScript-rendered or not actually contain a recipe."
        )

    structured_hints = _extract_structured_recipe_hints(downloaded)

    if structured_hints:
        text = structured_hints + "\n\n" + text

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    return {"success": True, "error": None, "text": text}


def _extract_structured_recipe_hints(html: str) -> str | None:
    """
    Look for schema.org Recipe JSON-LD in the raw page HTML and
    turn prepTime/cookTime/recipeYield into a short, unambiguous
    text block to prepend before the extracted prose — giving the
    model authoritative numbers instead of needing to infer them
    from text that may not contain them at all.
    """

    recipe_data = _find_recipe_jsonld(html)

    if recipe_data is None:
        return None

    lines = []

    prep_minutes = _parse_iso8601_duration_to_minutes(recipe_data.get("prepTime"))
    if prep_minutes:
        lines.append(f"Prep time: {prep_minutes} minutes")

    cook_minutes = _parse_iso8601_duration_to_minutes(recipe_data.get("cookTime"))
    if cook_minutes:
        lines.append(f"Cook time: {cook_minutes} minutes")

    servings = _parse_servings(recipe_data.get("recipeYield"))
    if servings:
        lines.append(f"Servings: {servings}")

    if not lines:
        return None

    return "Structured recipe data found on this page:\n" + "\n".join(lines)


def _find_recipe_jsonld(html: str) -> dict | None:
    """Find and parse the first schema.org Recipe JSON-LD block on the page."""

    for script_content in _JSONLD_SCRIPT_PATTERN.findall(html):
        try:
            data = json.loads(script_content.strip())
        except (json.JSONDecodeError, ValueError):
            continue

        candidates = data if isinstance(data, list) else [data]

        # Some sites wrap everything in an @graph array
        expanded = []
        for candidate in candidates:
            if isinstance(candidate, dict) and "@graph" in candidate:
                expanded.extend(candidate["@graph"])
            else:
                expanded.append(candidate)

        for item in expanded:
            if not isinstance(item, dict):
                continue

            item_type = item.get("@type")
            types = item_type if isinstance(item_type, list) else [item_type]

            if "Recipe" in types:
                return item

    return None


def _parse_iso8601_duration_to_minutes(duration) -> int | None:
    """Parse an ISO 8601 duration like 'PT15M' or 'PT1H30M' into minutes."""

    if not duration or not isinstance(duration, str):
        return None

    match = _ISO8601_DURATION_PATTERN.match(duration)

    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    total = hours * 60 + minutes

    return total if total > 0 else None


def _parse_servings(recipe_yield) -> int | None:
    """
    Extract a plain integer serving count from recipeYield, which
    schema.org allows to be a number, a string like "4 servings",
    or a list of such values.
    """

    if recipe_yield is None:
        return None

    if isinstance(recipe_yield, list):
        recipe_yield = recipe_yield[0] if recipe_yield else None

    if recipe_yield is None:
        return None

    match = re.search(r"\d+", str(recipe_yield))

    return int(match.group()) if match else None


def _error(message: str) -> dict:
    return {"success": False, "error": message, "text": None}