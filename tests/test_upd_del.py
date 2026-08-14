from src.database.recipes import get_recipe, update_recipe


recipe_id = 1

print("Before update:")
print(get_recipe(recipe_id))


update_recipe(
    recipe_id=recipe_id,
    name="Chicken Teriyaki Bowl - Updated",
    description="An updated teriyaki chicken rice bowl.",
    servings=4,
    prep_time=15,
    cook_time=25,
    ingredients=[
        {
            "quantity": 600,
            "unit": "g",
            "name": "chicken breast",
        },
        {
            "quantity": 400,
            "unit": "g",
            "name": "sushi rice",
        },
    ],
    instructions=[
        "Cook the rice.",
        "Cook the chicken.",
        "Add the teriyaki sauce.",
    ],
    tags=[
        "chicken",
        "japanese",
    ],
)


print("\nAfter update:")
print(get_recipe(recipe_id))

from src.database.recipes import get_recipe, delete_recipe


recipe_id = 1

print("Before deletion:")
print(get_recipe(recipe_id))


delete_recipe(recipe_id)


print("\nAfter deletion:")
print(get_recipe(recipe_id))