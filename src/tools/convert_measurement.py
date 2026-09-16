"""
Converts between units, but only within the same category (volume-to-
volume or weight-to-weight). Won't do cups-to-grams - that needs
ingredient density, which this doesn't know about.
"""


# All conversion factors are relative to a base unit per category.
# Volume base unit: milliliter (ml)
VOLUME_TO_ML = {
    "ml": 1.0,
    "l": 1000.0,
    "tsp": 4.92892,
    "tbsp": 14.7868,
    "cup": 236.588,
    "fl_oz": 29.5735,
}

# Weight base unit: gram (g)
WEIGHT_TO_G = {
    "g": 1.0,
    "kg": 1000.0,
    "oz": 28.3495,
    "lb": 453.592,
}

# Friendly aliases -> canonical unit keys
UNIT_ALIASES = {
    "milliliter": "ml", "milliliters": "ml", "millilitre": "ml",
    "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    "teaspoon": "tsp", "teaspoons": "tsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp",
    "cups": "cup",
    "fl oz": "fl_oz", "fluid ounce": "fl_oz", "fluid ounces": "fl_oz",
    "gram": "g", "grams": "g",
    "kilogram": "kg", "kilograms": "kg",
    "ounce": "oz", "ounces": "oz",
    "pound": "lb", "pounds": "lb",
}


def convert_measurement(quantity: float, from_unit: str, to_unit: str) -> dict:
    """Convert quantity from from_unit to to_unit - same category only
    (volume or weight). Units are case-insensitive and accept common
    plurals/full words (see UNIT_ALIASES). Mismatched categories (e.g.
    cups to grams) return an error rather than a guess, since that
    actually depends on the ingredient's density."""

    # ---- Input validation ----

    if not isinstance(quantity, (int, float)):
        return _error(quantity, from_unit, to_unit, "quantity must be a number.")

    if quantity < 0:
        return _error(quantity, from_unit, to_unit, "quantity cannot be negative.")

    if not isinstance(from_unit, str) or not isinstance(to_unit, str):
        return _error(quantity, from_unit, to_unit, "units must be strings.")

    from_key = _normalize_unit(from_unit)
    to_key = _normalize_unit(to_unit)

    from_category = _category_of(from_key)
    to_category = _category_of(to_key)

    if from_category is None:
        return _error(
            quantity, from_unit, to_unit,
            f"Unrecognized unit: '{from_unit}'."
        )

    if to_category is None:
        return _error(
            quantity, from_unit, to_unit,
            f"Unrecognized unit: '{to_unit}'."
        )

    if from_category != to_category:
        return _error(
            quantity, from_unit, to_unit,
            f"Cannot convert '{from_unit}' ({from_category}) to "
            f"'{to_unit}' ({to_category}) without knowing the "
            f"ingredient's density."
        )

    # ---- Conversion ----

    if from_category == "volume":
        base_amount = quantity * VOLUME_TO_ML[from_key]
        converted = base_amount / VOLUME_TO_ML[to_key]
    else:
        base_amount = quantity * WEIGHT_TO_G[from_key]
        converted = base_amount / WEIGHT_TO_G[to_key]

    return {
        "success": True,
        "error": None,
        "original_quantity": quantity,
        "from_unit": from_key,
        "converted_quantity": round(converted, 3),
        "to_unit": to_key,
    }


def _normalize_unit(unit: str) -> str:
    """Lowercase, strip, and resolve aliases to a canonical unit key."""
    cleaned = unit.strip().lower()
    return UNIT_ALIASES.get(cleaned, cleaned)


def _category_of(unit_key: str) -> str | None:
    """Return 'volume', 'weight', or None if the unit isn't recognized."""
    if unit_key in VOLUME_TO_ML:
        return "volume"
    if unit_key in WEIGHT_TO_G:
        return "weight"
    return None


def _error(quantity, from_unit, to_unit, message: str) -> dict:
    """Build a standard error response."""
    return {
        "success": False,
        "error": message,
        "original_quantity": quantity,
        "from_unit": from_unit,
        "converted_quantity": None,
        "to_unit": to_unit,
    }