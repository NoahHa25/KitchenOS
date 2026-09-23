from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.assistant_service import AssistantService


class FakeIngredient:
    def __init__(
        self,
        name,
        unit,
        current_stock=0,
        minimum_stock=0,
        cost_per_unit=0,
        restaurant_id=None,
    ):
        self.id = uuid4()
        self.name = name
        self.unit = unit
        self.current_stock = current_stock
        self.minimum_stock = minimum_stock
        self.cost_per_unit = cost_per_unit
        self.restaurant_id = restaurant_id


class FakeRecipeIngredient:
    def __init__(
        self,
        ingredient,
        quantity,
    ):
        self.id = uuid4()
        self.ingredient = ingredient
        self.quantity = quantity


class FakeRecipe:
    def __init__(
        self,
        name,
        description=None,
        restaurant_id=None,
    ):
        self.id = uuid4()
        self.name = name
        self.description = description
        self.restaurant_id = restaurant_id


class FakeRecipeRepository:
    def __init__(
        self,
        recipes,
    ):
        self.recipes = recipes

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
    def __init__(
        self,
        ingredients_by_recipe,
    ):
        self.ingredients_by_recipe = ingredients_by_recipe

    async def get_by_recipe(
        self,
        recipe_id,
    ):
        return self.ingredients_by_recipe.get(
            recipe_id,
            [],
        )


class FakeFoodCostService:
    def __init__(
        self,
        result=None,
    ):
        self.result = result

    async def calculate_food_cost(
        self,
        restaurant_id,
        recipe_name,
    ):
        return self.result


class FakeIngredientService:
    def __init__(
        self,
        ingredients=None,
        low_stock=None,
    ):
        self.ingredients = ingredients or []
        self.low_stock = low_stock or []

    async def find_ingredient_by_name(
        self,
        restaurant_id,
        query,
    ):
        normalized_query = query.strip().lower()

        for ingredient in self.ingredients:
            if (
                ingredient.restaurant_id == restaurant_id
                and normalized_query in ingredient.name.lower()
            ):
                return ingredient

        return None

    async def get_low_stock(
        self,
        restaurant_id,
    ):
        return [
            ingredient
            for ingredient in self.low_stock
            if ingredient.restaurant_id == restaurant_id
        ]


class FakeSalesService:
    def __init__(
        self,
        summary=None,
    ):
        self.summary = summary or {
            "total_orders": 0,
            "total_revenue": Decimal("0.00"),
        }

    async def get_sales_summary(
        self,
        restaurant_id,
    ):
        return self.summary


def make_service(
    recipes,
    recipe_ingredients,
    food_cost_result=None,
    ingredients=None,
    low_stock=None,
    sales_summary=None,
):
    ingredient_service = FakeIngredientService(
        ingredients=ingredients,
        low_stock=low_stock,
    )

    sales_service = FakeSalesService(
        summary=sales_summary,
    )

    return AssistantService(
        recipe_repository=FakeRecipeRepository(
            recipes,
        ),
        recipe_ingredient_repository=FakeRecipeIngredientRepository(
            recipe_ingredients,
        ),
        food_cost_service=FakeFoodCostService(
            food_cost_result,
        ),
        ingredient_service=ingredient_service,
        sales_service=sales_service,
    )


@pytest.mark.asyncio
async def test_recipe_lookup_returns_recipe_and_ingredients():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
    )

    garlic = FakeIngredient(
        name="Garlic",
        unit="kg",
    )

    recipe = FakeRecipe(
        name="Caesar Sauce",
        description="Classic pasta",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [
                FakeRecipeIngredient(
                    tomato,
                    Decimal("1.5"),
                ),
                FakeRecipeIngredient(
                    garlic,
                    Decimal("0.2"),
                ),
            ],
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="What's the recipe for Caesar Sauce?",
    )

    assert result["intent"] == "recipe_lookup"
    assert "**Caesar Sauce**" in result["answer"]
    assert "Description: Classic pasta" in result["answer"]
    assert "Tomato — 1.5 kg" in result["answer"]
    assert "Garlic — 0.2 kg" in result["answer"]


@pytest.mark.asyncio
async def test_recipe_lookup_supports_recipe_for_phrase():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        name="Carbonara",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [],
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="recipe for Carbonara",
    )

    assert result["intent"] == "recipe_lookup"
    assert "**Carbonara**" in result["answer"]


@pytest.mark.asyncio
async def test_recipe_lookup_supports_how_do_i_make_phrase():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        name="Carbonara",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [],
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="How do I make Carbonara?",
    )

    assert result["intent"] == "recipe_lookup"
    assert "**Carbonara**" in result["answer"]


@pytest.mark.asyncio
async def test_ingredient_lookup_returns_recipe_ingredients():
    restaurant_id = uuid4()

    pasta = FakeIngredient(
        name="Pasta",
        unit="kg",
    )

    egg = FakeIngredient(
        name="Egg",
        unit="pcs",
    )

    recipe = FakeRecipe(
        name="Carbonara",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [
                FakeRecipeIngredient(
                    pasta,
                    Decimal("0.4"),
                ),
                FakeRecipeIngredient(
                    egg,
                    Decimal("2"),
                ),
            ],
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="What ingredients are in Carbonara?",
    )

    assert result["intent"] == "ingredient_lookup"
    assert "**Carbonara** uses:" in result["answer"]
    assert "Pasta — 0.4 kg" in result["answer"]
    assert "Egg — 2 pcs" in result["answer"]


@pytest.mark.asyncio
async def test_food_cost_returns_real_food_cost_and_margin():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        name="Tomato Pasta",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [],
        },
        food_cost_result={
            "recipe_name": "Tomato Pasta",
            "food_cost": Decimal("4.00"),
            "selling_price": Decimal("15.00"),
            "profit": Decimal("11.00"),
            "margin": Decimal("73.33"),
            "breakdown": [
                {
                    "ingredient_name": "Tomato",
                    "quantity": Decimal("0.5"),
                    "cost_per_unit": Decimal("4.00"),
                    "total_cost": Decimal("2.00"),
                },
                {
                    "ingredient_name": "Cheese",
                    "quantity": Decimal("0.2"),
                    "cost_per_unit": Decimal("10.00"),
                    "total_cost": Decimal("2.00"),
                },
            ],
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="What is the food cost of Tomato Pasta?",
    )

    assert result["intent"] == "food_cost"
    assert "**Tomato Pasta — Food Cost**" in result["answer"]
    assert "Food cost: 4.00" in result["answer"]
    assert "Selling price: 15.00" in result["answer"]
    assert "Estimated profit: 11.00" in result["answer"]
    assert "Margin: 73.33%" in result["answer"]
    assert "Tomato — 0.5 × 4.00 = 2.00" in result["answer"]
    assert "Cheese — 0.2 × 10.00 = 2.00" in result["answer"]


@pytest.mark.asyncio
async def test_food_cost_returns_message_when_recipe_does_not_exist():
    restaurant_id = uuid4()

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        food_cost_result=None,
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="What is the food cost of Sushi?",
    )

    assert result["intent"] == "food_cost"
    assert (
        result["answer"]
        == 'I couldn\'t find a recipe matching "Sushi".'
    )


@pytest.mark.asyncio
async def test_recipe_lookup_is_scoped_to_restaurant():
    restaurant_id = uuid4()
    other_restaurant_id = uuid4()

    recipe = FakeRecipe(
        name="Carbonara",
        restaurant_id=other_restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [],
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="recipe for Carbonara",
    )

    assert result["intent"] == "recipe_lookup"
    assert (
        result["answer"]
        == 'I couldn\'t find a recipe matching "Carbonara".'
    )


@pytest.mark.asyncio
async def test_empty_message_returns_unknown_intent():
    restaurant_id = uuid4()

    service = make_service(
        recipes=[],
        recipe_ingredients={},
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="",
    )

    assert result["intent"] == "unknown"
    assert (
        result["answer"]
        == "Please tell me what you would like to know."
    )


@pytest.mark.asyncio
async def test_whitespace_message_returns_unknown_intent():
    restaurant_id = uuid4()

    service = make_service(
        recipes=[],
        recipe_ingredients={},
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="   ",
    )

    assert result["intent"] == "unknown"
    assert (
        result["answer"]
        == "Please tell me what you would like to know."
    )


@pytest.mark.asyncio
async def test_unknown_question_returns_capability_message():
    restaurant_id = uuid4()

    service = make_service(
        recipes=[],
        recipe_ingredients={},
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="What is the weather?",
    )

    assert result["intent"] == "unknown"
    assert "recipes" in result["answer"]
    assert "ingredients" in result["answer"]
    assert "food costs" in result["answer"]


@pytest.mark.asyncio
async def test_recipe_without_ingredients_returns_clear_message():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        name="Empty Recipe",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [],
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="recipe for Empty Recipe",
    )

    assert result["intent"] == "recipe_lookup"
    assert (
        result["answer"]
        == "**Empty Recipe**\n\n"
        "No ingredients have been added yet."
    )


@pytest.mark.asyncio
async def test_inventory_status_returns_stock():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=Decimal("5"),
        minimum_stock=Decimal("2"),
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        ingredients=[tomato],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="Do we have tomatoes?",
    )

    assert result["intent"] == "inventory_status"
    assert "**Tomato**" in result["answer"]
    assert "Stock: 5 kg" in result["answer"]
    assert "Minimum stock: 2 kg" in result["answer"]
    assert "Status: In stock" in result["answer"]


@pytest.mark.asyncio
async def test_inventory_status_returns_low_stock():
    restaurant_id = uuid4()

    cheese = FakeIngredient(
        name="Cheese",
        unit="kg",
        current_stock=Decimal("0.5"),
        minimum_stock=Decimal("1"),
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        ingredients=[cheese],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="How much cheese do we have?",
    )

    assert result["intent"] == "inventory_status"
    assert "Stock: 0.5 kg" in result["answer"]
    assert "Minimum stock: 1 kg" in result["answer"]
    assert "Status: Low stock" in result["answer"]


@pytest.mark.asyncio
async def test_inventory_status_returns_not_found():
    restaurant_id = uuid4()

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        ingredients=[],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="Do we have truffles?",
    )

    assert result["intent"] == "inventory_status"
    assert (
        result["answer"]
        == 'I couldn\'t find an ingredient matching "truffles".'
    )


@pytest.mark.asyncio
async def test_inventory_status_is_scoped_to_restaurant():
    restaurant_id = uuid4()
    other_restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=5,
        minimum_stock=2,
        restaurant_id=other_restaurant_id,
    )

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        ingredients=[tomato],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="Do we have tomatoes?",
    )

    assert result["intent"] == "inventory_status"
    assert (
        result["answer"]
        == 'I couldn\'t find an ingredient matching "tomatoes".'
    )


@pytest.mark.asyncio
async def test_low_stock_returns_items():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=Decimal("1"),
        minimum_stock=Decimal("2"),
        restaurant_id=restaurant_id,
    )

    cheese = FakeIngredient(
        name="Cheese",
        unit="kg",
        current_stock=Decimal("0.5"),
        minimum_stock=Decimal("1"),
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        low_stock=[
            tomato,
            cheese,
        ],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="Which ingredients are running low?",
    )

    assert result["intent"] == "low_stock"
    assert "**Low Stock**" in result["answer"]
    assert "Tomato — 1 kg (minimum: 2 kg)" in result["answer"]
    assert "Cheese — 0.5 kg (minimum: 1 kg)" in result["answer"]


@pytest.mark.asyncio
async def test_low_stock_returns_clear_message_when_none():
    restaurant_id = uuid4()

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        low_stock=[],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="Which ingredients are low?",
    )

    assert result["intent"] == "low_stock"
    assert (
        result["answer"]
        == "No ingredients are currently below their "
        "minimum stock level."
    )


@pytest.mark.asyncio
async def test_low_stock_is_scoped_to_restaurant():
    restaurant_id = uuid4()
    other_restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=1,
        minimum_stock=2,
        restaurant_id=other_restaurant_id,
    )

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        low_stock=[tomato],
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="Show me low stock ingredients",
    )

    assert result["intent"] == "low_stock"
    assert (
        result["answer"]
        == "No ingredients are currently below their "
        "minimum stock level."
    )


@pytest.mark.asyncio
async def test_sales_summary_returns_completed_orders_and_revenue():
    restaurant_id = uuid4()

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        sales_summary={
            "total_orders": 5,
            "total_revenue": Decimal("123.45"),
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="How much have we sold?",
    )

    assert result["intent"] == "sales_summary"
    assert "**Sales Summary**" in result["answer"]
    assert "Completed orders: 5" in result["answer"]
    assert "Total revenue: 123.45" in result["answer"]


@pytest.mark.asyncio
async def test_sales_summary_returns_zero_when_no_completed_orders():
    restaurant_id = uuid4()

    service = make_service(
        recipes=[],
        recipe_ingredients={},
        sales_summary={
            "total_orders": 0,
            "total_revenue": Decimal("0.00"),
        },
    )

    result = await service.answer(
        restaurant_id=restaurant_id,
        query="Show me sales summary",
    )

    assert result["intent"] == "sales_summary"
    assert "Completed orders: 0" in result["answer"]
    assert "Total revenue: 0.00" in result["answer"]
