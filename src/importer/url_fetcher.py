"""
Recipe URL fetching.

Uses trafilatura to fetch a page and extract just the main
article content — stripping navigation, ads, sidebars, and
footers before anything gets sent to the model. This matters
because feeding raw HTML/boilerplate into the extraction prompt
both wastes tokens and gives the model more noise to potentially
get confused by.
"""

import trafilatura

MAX_TEXT_LENGTH = 15000  # keep the extraction prompt a reasonable size


def fetch_recipe_page_text(url: str) -> dict:
    """
    Fetch a URL and extract its main readable content.

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

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    return {"success": True, "error": None, "text": text}


def _error(message: str) -> dict:
    return {"success": False, "error": message, "text": None}