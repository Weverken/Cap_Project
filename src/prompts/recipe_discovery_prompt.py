"""Prompt for the web recipe search (src.discovery.recipe_finder)."""


def build_discovery_prompt(query: str, excluded_names: list[str]) -> str:
    """Build the discovery prompt. excluded_names is just a strong
    instruction to the model, not an enforced filter - it could still
    slip up and suggest something too similar under a different name."""

    if excluded_names:
        excluded_section = (
            "The user already has these recipes saved — do NOT "
            "suggest any of these, or near-duplicates of them:\n"
            + "\n".join(f"- {name}" for name in excluded_names)
        )
    else:
        excluded_section = "The user has no saved recipes yet."

    return f"""\
Using Google Search, find exactly 3 real, different recipes from
the web that match this request: "{query}"

{excluded_section}

Requirements:
- Every recipe must be a real recipe you actually found via
  search — never invent a recipe or a source. If you can't find
  3 good matches, return fewer rather than making one up.
- Prefer dedicated recipe websites and food blogs. Avoid citing
  social media posts (Facebook, Instagram, TikTok, Pinterest,
  Reddit, YouTube) as your source, even if one turns up in search
  — the actual recipe text on those platforms is often locked
  behind a login or buried in a video caption, so it's not a
  useful link for someone to actually open and read.
- For each recipe, give: a clear heading with the recipe name,
  which site it's from (name only — e.g. "from Allrecipes"), a
  1-2 sentence description of why it fits the request, and roughly
  how long it takes to make if that's stated on the source.
- Do NOT include any links, URLs, or a "Source:" line with a
  clickable link anywhere in your response. Verified source links
  are displayed separately below your response — mention the site
  by name only, in plain text, as part of your sentence.
- Keep each recipe's write-up short — a few lines, not a full
  recipe reproduction.
- Format your response as 3 clearly separated sections, one per
  recipe, each with a heading.
"""