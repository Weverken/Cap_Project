from src.database.recipes import (
    initialize_database,
    create_recipe,
    get_recipe,
    get_all_recipes,
    search_recipes,
    update_recipe,
    delete_recipe,
)


initialize_database()


# -----------------------------------------
# Create
# -----------------------------------------

recipe_id = create_recipe(
    user_id=1,
    name="Chicken Teriyaki Bowl",
    description="A quick teriyaki chicken rice bowl.",
    servings=2,
    prep_time=10,
    cook_time=20,
    ingredients=[
        {
            "quantity": 300,
            "unit": "g",
            "name": "chicken breast",
        },
        {
            "quantity": 200,
            "unit": "g",
            "name": "sushi rice",
        },
        {
            "quantity": 3,
            "unit": "tbsp",
            "name": "teriyaki sauce",
        },
    ],
    instructions=[
        "Cook the sushi rice.",
        "Cut the chicken into cubes.",
        "Cook the chicken.",
        "Add the teriyaki sauce.",
        "Assemble the bowl.",
    ],
    tags=[
        "chicken",
        "japanese",
        "quick",
    ],
)

print("Created recipe:", recipe_id)


# -----------------------------------------
# Get
# -----------------------------------------

recipe = get_recipe(recipe_id)

print("\nRetrieved recipe:")
print(recipe)


# -----------------------------------------
# Get all
# -----------------------------------------

recipes = get_all_recipes(user_id=1)

print("\nAll recipes:")
for recipe in recipes:
    print(recipe["name"])


# -----------------------------------------
# Search
# -----------------------------------------

results = search_recipes(
    user_id=1,
    search_term="chicken",
)

print("\nSearch results:")
for recipe in results:
    print(recipe["name"])


# -----------------------------------------
# Delete
# -----------------------------------------

# delete_recipe(recipe_id)