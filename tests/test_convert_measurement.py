from src.tools.convert_measurement import convert_measurement


def test_cups_to_tbsp():
    result = convert_measurement(1, "cup", "tbsp")

    assert result["success"] is True
    assert result["converted_quantity"] == 16.0


def test_tsp_to_ml():
    result = convert_measurement(1, "tsp", "ml")

    assert result["success"] is True
    assert round(result["converted_quantity"], 2) == 4.93


def test_grams_to_kg():
    result = convert_measurement(1500, "g", "kg")

    assert result["success"] is True
    assert result["converted_quantity"] == 1.5


def test_lb_to_oz():
    result = convert_measurement(1, "lb", "oz")

    assert result["success"] is True
    assert round(result["converted_quantity"], 2) == 16.0


def test_same_unit_returns_same_value():
    result = convert_measurement(5, "cup", "cup")

    assert result["converted_quantity"] == 5.0


def test_accepts_aliases_and_plurals():
    result = convert_measurement(2, "tablespoons", "teaspoon")

    assert result["success"] is True
    assert round(result["converted_quantity"], 1) == 6.0


def test_case_insensitive():
    result = convert_measurement(1, "CUP", "Tbsp")

    assert result["success"] is True


def test_rejects_cross_category_conversion():
    result = convert_measurement(1, "cup", "g")

    assert result["success"] is False
    assert "density" in result["error"]


def test_rejects_unrecognized_unit():
    result = convert_measurement(1, "banana", "cup")

    assert result["success"] is False
    assert "Unrecognized unit" in result["error"]


def test_rejects_negative_quantity():
    result = convert_measurement(-1, "cup", "tbsp")

    assert result["success"] is False


def test_rejects_non_numeric_quantity():
    result = convert_measurement("a lot", "cup", "tbsp")

    assert result["success"] is False