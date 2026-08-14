from src.database.recipes import create_recipe


recipe_id = create_recipe(
    user_id=1,
    name="Lemon Garlic Salmon",
    description="Pan-seared salmon with lemon, garlic, and roasted vegetables.",
    servings=2,
    prep_time=10,
    cook_time=20,
    ingredients=[
        {
            "quantity": 2,
            "unit": "fillets",
            "name": "salmon",
        },
        {
            "quantity": 2,
            "unit": "cloves",
            "name": "garlic",
        },
        {
            "quantity": 1,
            "unit": "whole",
            "name": "lemon",
        },
        {
            "quantity": 1,
            "unit": "tbsp",
            "name": "olive oil",
        },
        {
            "quantity": 300,
            "unit": "g",
            "name": "broccoli",
        },
        {
            "quantity": 200,
            "unit": "g",
            "name": "baby potatoes",
        },
    ],
    instructions=[
        "Preheat the oven to 200°C.",
        "Cut the baby potatoes in half and toss them with olive oil.",
        "Roast the potatoes for 15 minutes.",
        "Season the salmon with salt, pepper, garlic, and lemon juice.",
        "Add the salmon and broccoli to the baking tray.",
        "Bake for another 10–12 minutes, until the salmon is cooked through.",
        "Serve the salmon with the roasted vegetables and lemon wedges.",
    ],
    tags=[
        "salmon",
        "fish",
        "healthy",
        "quick",
        "dinner",
    ],
)

print("Created recipe:", recipe_id)