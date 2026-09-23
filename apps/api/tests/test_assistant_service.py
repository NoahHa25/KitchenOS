from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.assistant_service import AssistantService


class FakeIngredient:
    def __init__(
        self,
        name="Tomato",
        unit="kg",
    ):
        self.id = uuid4()
        self.name = name
        self.unit = unit


class FakeRecipeIngredient:
    def __init__(
        self,
        recipe_id,
        ingredient,
        quantity=1.5,
    ):
        self.id = uuid4()
        self.recipe_id = recipe_id
        self.ingredient_id = ingredient.id
        self.quantity = quantity
        self.ingredient = ingredient


class FakeRecipe:
    def __init__(
        self,
        restaurant_id,
        name="Pasta",
        selling_price=Decimal("12.00"),
    ):
        self.id = uuid4()
        self.restaurant_id = restaurant_id
        self.name = name
        self.description = "Classic pasta"
        self.selling_price = selling_price
        self.portion_size = 1.0
        self.portion_unit = "portion"
        self.is_active = True


class FakeRecipeRepository:
    def __init__(self, recipes=None):
        self.recipes = recipes or []

    async def find_by_name(
        self,
        restaurant_id,
        query,
    ):
        normalized_query = query.strip().lower()

        for recipe in self.recipes:
            if (
                recipe.restaurant_id == restaurant_id
                and normalized_query in recipe.name.lower()
            ):
                return recipe

        return None


class FakeRecipeIngredientRepository:
    def __init__(self, ingredients=None):
        self.ingredients = ingredients or []

    async def get_by_recipe(
        self,
        recipe_id,
    ):
        return [
            item
            for item in self.ingredients
            if item.recipe_id == recipe_id
        ]


class FakeFoodCostService:
    def __init__(self, results=None):
        self.results = results or {}

    async def calculate_food_cost(
        self,
        restaurant_id,
        recipe_id,
    ):
        return self.results.get(recipe_id)


def make_service(
    recipes=None,
    recipe_ingredients=None,
    food_costs=None,
):
    recipe_repository = FakeRecipeRepository(
        recipes=recipes,
    )

    recipe_ingredient_repository = (
        FakeRecipeIngredientRepository(
            ingredients=recipe_ingredients,
        )
    )

    food_cost_service = FakeFoodCostService(
        results=food_costs,
    )

    service = AssistantService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        food_cost_service=food_cost_service,
    )

    return service


@pytest.mark.anyio
async def test_recipe_lookup_returns_recipe_and_ingredients():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Caesar Sauce",
    )

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
    )

    garlic = FakeIngredient(
        name="Garlic",
        unit="kg",
    )

    tomato_ingredient = FakeRecipeIngredient(
        recipe_id=recipe.id,
        ingredient=tomato,
        quantity=1.5,
    )

    garlic_ingredient = FakeRecipeIngredient(
        recipe_id=recipe.id,
        ingredient=garlic,
        quantity=0.2,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients=[
            tomato_ingredient,
            garlic_ingredient,
        ],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="What is the recipe for Caesar Sauce?",
    )

    assert result["intent"] == "recipe_lookup"
    assert "**Caesar Sauce**" in result["answer"]
    assert "Ingredients:" in result["answer"]
    assert "Tomato — 1.5 kg" in result["answer"]
    assert "Garlic — 0.2 kg" in result["answer"]


@pytest.mark.anyio
async def test_recipe_lookup_supports_recipe_for_phrase():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Margherita Pizza",
    )

    service = make_service(
        recipes=[recipe],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="recipe for margherita pizza",
    )

    assert result["intent"] == "recipe_lookup"
    assert "**Margherita Pizza**" in result["answer"]


@pytest.mark.anyio
async def test_recipe_lookup_supports_how_do_i_make_phrase():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Tomato Sauce",
    )

    service = make_service(
        recipes=[recipe],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="How do I make tomato sauce?",
    )

    assert result["intent"] == "recipe_lookup"
    assert "**Tomato Sauce**" in result["answer"]


@pytest.mark.anyio
async def test_ingredient_lookup_returns_recipe_ingredients():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Carbonara",
    )

    pasta = FakeIngredient(
        name="Pasta",
        unit="kg",
    )

    egg = FakeIngredient(
        name="Egg",
        unit="pcs",
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients=[
            FakeRecipeIngredient(
                recipe_id=recipe.id,
                ingredient=pasta,
                quantity=0.4,
            ),
            FakeRecipeIngredient(
                recipe_id=recipe.id,
                ingredient=egg,
                quantity=2,
            ),
        ],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="What ingredients are in Carbonara?",
    )

    assert result["intent"] == "ingredient_lookup"
    assert "**Carbonara** uses:" in result["answer"]
    assert "Pasta — 0.4 kg" in result["answer"]
    assert "Egg — 2 pcs" in result["answer"]


@pytest.mark.anyio
async def test_food_cost_returns_real_food_cost_and_margin():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Tomato Pasta",
        selling_price=Decimal("15.00"),
    )

    food_cost = {
        "recipe_id": recipe.id,
        "recipe_name": recipe.name,
        "food_cost": Decimal("4.00"),
        "breakdown": [
            {
                "ingredient": "Tomato",
                "quantity": Decimal("0.5"),
                "cost_per_unit": Decimal("4.00"),
                "total_cost": Decimal("2.00"),
            },
            {
                "ingredient": "Cheese",
                "quantity": Decimal("0.2"),
                "cost_per_unit": Decimal("10.00"),
                "total_cost": Decimal("2.00"),
            },
        ],
    }

    service = make_service(
        recipes=[recipe],
        food_costs={
            recipe.id: food_cost,
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="What is the food cost of Tomato Pasta?",
    )

    assert result["intent"] == "food_cost"

    assert "Food cost: 4.00" in result["answer"]
    assert "Selling price: 15.00" in result["answer"]
    assert "Estimated profit: 11.00" in result["answer"]
    assert "Margin: 73.33%" in result["answer"]

    assert "Tomato — 0.5 × 4.00 = 2.00" in result["answer"]
    assert "Cheese — 0.2 × 10.00 = 2.00" in result["answer"]


@pytest.mark.anyio
async def test_food_cost_returns_message_when_recipe_does_not_exist():
    restaurant_id = uuid4()

    service = make_service()

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="What is the food cost of sushi?",
    )

    assert result["intent"] == "food_cost"
    assert 'I couldn\'t find a recipe matching "sushi".' in (
        result["answer"]
    )


@pytest.mark.anyio
async def test_recipe_lookup_is_scoped_to_restaurant():
    restaurant_a = uuid4()
    restaurant_b = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_a,
        name="Pizza",
    )

    service = make_service(
        recipes=[recipe],
    )

    result = await service.answer(
        restaurant_id=restaurant_b,
        message="recipe for pizza",
    )

    assert result["intent"] == "recipe_lookup"
    assert (
        'I couldn\'t find a recipe matching "pizza".'
        in result["answer"]
    )


@pytest.mark.anyio
async def test_empty_message_returns_unknown_intent():
    restaurant_id = uuid4()

    service = make_service()

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="",
    )

    assert result["intent"] == "unknown"
    assert result["answer"] == (
        "Please tell me what you would like to know."
    )


@pytest.mark.anyio
async def test_whitespace_message_returns_unknown_intent():
    restaurant_id = uuid4()

    service = make_service()

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="   ",
    )

    assert result["intent"] == "unknown"
    assert result["answer"] == (
        "Please tell me what you would like to know."
    )


@pytest.mark.anyio
async def test_unknown_question_returns_capability_message():
    restaurant_id = uuid4()

    service = make_service()

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="What is the weather today?",
    )

    assert result["intent"] == "unknown"
    assert "recipes" in result["answer"]
    assert "ingredients" in result["answer"]
    assert "food costs" in result["answer"]


@pytest.mark.anyio
async def test_recipe_without_ingredients_returns_clear_message():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Plain Rice",
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients=[],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        message="recipe for plain rice",
    )

    assert result["intent"] == "recipe_lookup"
    assert "**Plain Rice**" in result["answer"]
    assert "No ingredients have been added yet." in result["answer"]