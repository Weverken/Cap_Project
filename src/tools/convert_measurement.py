"""
Tool: convert_measurement

Converts a quantity from one unit of measurement to another,
within the same category (volume-to-volume or weight-to-weight).

Does NOT convert between volume and weight (e.g. cups to grams),
since that requires ingredient-specific density data which is out
of scope for this tool. See docstring below for rationale.
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
    """
    Convert a quantity from one unit to another within the same
    category (volume or weight).

    Args:
        quantity (float): The numeric amount to convert. Must be
            a non-negative number.
        from_unit (str): The unit to convert from (e.g. "cup",
            "tbsp", "g", "oz"). Case-insensitive, common plurals
            and full words are accepted (see UNIT_ALIASES).
        to_unit (str): The unit to convert to.

    Returns:
        dict: {
            "success": bool,
            "error": str | None,
            "original_quantity": float,
            "from_unit": str,
            "converted_quantity": float | None,
            "to_unit": str,
        }

    Note:
        Conversions between volume and weight (e.g. cups -> grams)
        are intentionally unsupported. That conversion depends on
        ingredient density (flour, sugar, and butter all convert
        differently), which this tool has no way to know. Calling
        with mismatched categories returns a clear error instead
        of a guessed/incorrect number.
    """

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