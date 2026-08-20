"""
Structured schema for AI-extracted recipes.

Used as the response_schema for Gemini's structured output mode,
so extraction returns data matching this shape directly — no
manual JSON parsing or "please respond only in JSON" prompting
needed. Field descriptions here also guide the model on what to
extract for each field.
"""

from pydantic import BaseModel, Field


class ExtractedIngredient(BaseModel):
    quantity: float = Field(
        description="Numeric quantity. Use 0 if no number is "
        "given at all — this includes vague amounts like 'a "
        "little' or 'to taste' (put that phrase in unit instead) "
        "and ingredients listed with no amount language at all. "
        "0 signals 'not specified', not 'none of this'."
    )
    unit: str = Field(
        description="Unit of measurement (e.g. 'cup', 'tbsp', "
        "'g'). Use an empty string for countable items with no "
        "unit, like whole eggs or cloves of garlic. If the source "
        "used a vague amount phrase instead of a number (e.g. 'a "
        "little', 'to taste', 'a pinch'), put that phrase here."
    )
    name: str = Field(description="The ingredient's name.")


class ExtractedRecipe(BaseModel):
    name: str = Field(description="The recipe's title/name.")
    description: str = Field(
        default="",
        description="A short 1-2 sentence description, if one is "
        "clearly present or can be reasonably inferred. Leave "
        "empty rather than inventing one from nothing.",
    )
    servings: int = Field(
        default=0,
        description="Number of servings. Use 0 if not stated "
        "anywhere in the image.",
    )
    prep_time: int = Field(
        default=0, description="Prep time in minutes, 0 if not stated."
    )
    cook_time: int = Field(
        default=0, description="Cook time in minutes, 0 if not stated."
    )
    ingredients: list[ExtractedIngredient] = Field(
        description="All ingredients found, in the order listed."
    )
    instructions: list[str] = Field(
        description="Each instruction step as a separate string, "
        "in order. Split run-on paragraphs into individual steps "
        "where the source has clear step boundaries (numbers, "
        "line breaks); otherwise keep the original grouping."
    )
    tags: list[str] = Field(
        default_factory=list,
        description="A few relevant tags if obvious from context "
        "(e.g. cuisine type, meal type). Leave empty if unclear "
        "— do not guess.",
    )
    extraction_confidence: str = Field(
        description="One of: 'high', 'medium', 'low'. Use 'low' "
        "if the image is blurry, handwriting is hard to read, or "
        "significant guessing was required for any field."
    )
    extraction_notes: str = Field(
        default="",
        description="Note anything uncertain, illegible, or "
        "guessed — e.g. 'quantity for salt was illegible, "
        "assumed to taste'. Empty string if nothing to flag.",
    )