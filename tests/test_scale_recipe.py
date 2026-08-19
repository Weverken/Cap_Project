from src.tools.scale_recipe import scale_recipe
 
 
SAMPLE_RECIPE = {
    "servings": 4,
    "ingredients": [
        {"quantity": 2, "unit": "cups", "name": "flour"},
        {"quantity": 1, "unit": "tsp", "name": "salt"},
        {"quantity": 0.5, "unit": "cup", "name": "sugar"},
    ],
}
 
 
def test_scale_up_doubles_quantities():
    result = scale_recipe(SAMPLE_RECIPE, target_servings=8)
 
    assert result["success"] is True
    assert result["scale_factor"] == 2.0
    assert result["ingredients"][0]["quantity"] == 4.0
    assert result["ingredients"][1]["quantity"] == 2.0
 
 
def test_scale_down_halves_quantities():
    result = scale_recipe(SAMPLE_RECIPE, target_servings=2)
 
    assert result["success"] is True
    assert result["scale_factor"] == 0.5
    assert result["ingredients"][0]["quantity"] == 1.0
 
 
def test_same_servings_no_change():
    result = scale_recipe(SAMPLE_RECIPE, target_servings=4)
 
    assert result["scale_factor"] == 1.0
    assert result["ingredients"][0]["quantity"] == 2.0
 
 
def test_rejects_zero_target_servings():
    result = scale_recipe(SAMPLE_RECIPE, target_servings=0)
 
    assert result["success"] is False
    assert "greater than 0" in result["error"]
 
 
def test_rejects_negative_target_servings():
    result = scale_recipe(SAMPLE_RECIPE, target_servings=-3)
 
    assert result["success"] is False
 
 
def test_rejects_missing_ingredients_key():
    bad_recipe = {"servings": 4}
 
    result = scale_recipe(bad_recipe, target_servings=2)
 
    assert result["success"] is False
    assert "ingredients" in result["error"]
 
 
def test_rejects_empty_ingredients_list():
    bad_recipe = {"servings": 4, "ingredients": []}
 
    result = scale_recipe(bad_recipe, target_servings=2)
 
    assert result["success"] is False
 
 
def test_rejects_non_numeric_quantity():
    bad_recipe = {
        "servings": 4,
        "ingredients": [{"quantity": "a lot", "unit": "cups", "name": "flour"}],
    }
 
    result = scale_recipe(bad_recipe, target_servings=2)
 
    assert result["success"] is False
    assert "non-numeric" in result["error"]
 
 
def test_rejects_non_numeric_target_servings():
    result = scale_recipe(SAMPLE_RECIPE, target_servings="a lot")
 
    assert result["success"] is False
 
