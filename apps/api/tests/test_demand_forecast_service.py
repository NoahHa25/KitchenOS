from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.demand_forecast_service import (
    DemandForecastService,
)


class FakeOrderItem:
    def __init__(
        self,
        recipe_id,
        quantity,
    ):
        self.recipe_id = recipe_id
        self.quantity = quantity


class FakeOrder:
    def __init__(
        self,
        created_at,
        items,
        status="completed",
    ):
        self.created_at = created_at
        self.items = items
        self.status = status


class FakeIngredient:
    def __init__(
        self,
        ingredient_id,
        name,
        current_stock,
        unit,
    ):
        self.id = ingredient_id
        self.name = name
        self.current_stock = current_stock
        self.unit = unit


class FakeRecipe:
    def __init__(
        self,
        recipe_id,
        name,
        restaurant_id,
    ):
        self.id = recipe_id
        self.name = name
        self.restaurant_id = restaurant_id


class FakeRecipeIngredient:
    def __init__(
        self,
        recipe_id,
        ingredient_id,
        quantity,
    ):
        self.recipe_id = recipe_id
        self.ingredient_id = ingredient_id
        self.quantity = quantity


class FakeOrderRepository:
    def __init__(self, orders):
        self.orders = orders

    async def get_completed_orders(
        self,
        restaurant_id,
    ):
        return self.orders


class FakeRecipeRepository:
    def __init__(self, recipes):
        self.recipes = recipes

    async def get_by_id(
        self,
        restaurant_id,
        recipe_id,
    ):
        recipe = self.recipes.get(recipe_id)

        if recipe is None:
            return None

        if recipe.restaurant_id != restaurant_id:
            return None

        return recipe


class FakeRecipeIngredientRepository:
    def __init__(self, recipe_ingredients):
        self.recipe_ingredients = recipe_ingredients

    async def get_by_recipe(
        self,
        recipe_id,
    ):
        return self.recipe_ingredients.get(
            recipe_id,
            [],
        )


class FakeIngredientService:
    def __init__(self, ingredients):
        self.ingredients = ingredients

    async def find_ingredient_by_name(
        self,
        restaurant_id,
        query,
    ):
        normalized_query = query.lower()

        for ingredient in self.ingredients:
            if ingredient.name.lower() == normalized_query:
                return ingredient

        return None


def make_service(
    orders,
    recipes,
    recipe_ingredients,
    ingredients,
):
    return DemandForecastService(
        order_repository=FakeOrderRepository(
            orders,
        ),
        recipe_repository=FakeRecipeRepository(
            recipes,
        ),
        recipe_ingredient_repository=(
            FakeRecipeIngredientRepository(
                recipe_ingredients,
            )
        ),
        ingredient_service=FakeIngredientService(
            ingredients,
        ),
    )


@pytest.mark.asyncio
async def test_forecast_calculates_average_daily_usage():
    restaurant_id = uuid4()

    recipe_id = uuid4()
    ingredient_id = uuid4()

    now = datetime.now(timezone.utc)

    orders = [
        FakeOrder(
            created_at=now - timedelta(days=2),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now - timedelta(days=1),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now,
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
    ]

    recipes = {
        recipe_id: FakeRecipe(
            recipe_id=recipe_id,
            name="Chicken Burger",
            restaurant_id=restaurant_id,
        ),
    }

    recipe_ingredients = {
        recipe_id: [
            FakeRecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
                quantity=Decimal("0.2"),
            ),
        ],
    }

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=Decimal("20"),
            unit="kg",
        ),
    ]

    service = make_service(
        orders=orders,
        recipes=recipes,
        recipe_ingredients=recipe_ingredients,
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
        lookback_days=3,
    )

    assert result["ingredient_name"] == "Chicken"
    assert result["average_daily_usage"] == Decimal("2")
    assert result["forecast_days"] == 7


@pytest.mark.asyncio
async def test_forecast_calculates_seven_day_demand():
    restaurant_id = uuid4()

    recipe_id = uuid4()
    ingredient_id = uuid4()

    now = datetime.now(timezone.utc)

    orders = [
        FakeOrder(
            created_at=now - timedelta(days=2),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now - timedelta(days=1),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now,
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
    ]

    recipes = {
        recipe_id: FakeRecipe(
            recipe_id=recipe_id,
            name="Chicken Burger",
            restaurant_id=restaurant_id,
        ),
    }

    recipe_ingredients = {
        recipe_id: [
            FakeRecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
                quantity=Decimal("0.2"),
            ),
        ],
    }

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=Decimal("20"),
            unit="kg",
        ),
    ]

    service = make_service(
        orders=orders,
        recipes=recipes,
        recipe_ingredients=recipe_ingredients,
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
        lookback_days=3,
    )

    assert result["forecasted_usage"] == Decimal("14")


@pytest.mark.asyncio
async def test_forecast_calculates_suggested_purchase():
    restaurant_id = uuid4()

    recipe_id = uuid4()
    ingredient_id = uuid4()

    now = datetime.now(timezone.utc)

    orders = [
        FakeOrder(
            created_at=now - timedelta(days=2),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now - timedelta(days=1),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now,
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
    ]

    recipes = {
        recipe_id: FakeRecipe(
            recipe_id=recipe_id,
            name="Chicken Burger",
            restaurant_id=restaurant_id,
        ),
    }

    recipe_ingredients = {
        recipe_id: [
            FakeRecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
                quantity=Decimal("0.2"),
            ),
        ],
    }

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=Decimal("5"),
            unit="kg",
        ),
    ]

    service = make_service(
        orders=orders,
        recipes=recipes,
        recipe_ingredients=recipe_ingredients,
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
        safety_stock=Decimal("5"),
        lookback_days=3,
    )

    assert result["forecasted_usage"] == Decimal("14")
    assert result["safety_stock"] == Decimal("5")
    assert result["suggested_purchase"] == Decimal("14")


@pytest.mark.asyncio
async def test_forecast_returns_zero_purchase_when_stock_is_sufficient():
    restaurant_id = uuid4()

    recipe_id = uuid4()
    ingredient_id = uuid4()

    now = datetime.now(timezone.utc)

    orders = [
        FakeOrder(
            created_at=now - timedelta(days=2),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now - timedelta(days=1),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now,
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
    ]

    recipes = {
        recipe_id: FakeRecipe(
            recipe_id=recipe_id,
            name="Chicken Burger",
            restaurant_id=restaurant_id,
        ),
    }

    recipe_ingredients = {
        recipe_id: [
            FakeRecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
                quantity=Decimal("0.2"),
            ),
        ],
    }

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=Decimal("50"),
            unit="kg",
        ),
    ]

    service = make_service(
        orders=orders,
        recipes=recipes,
        recipe_ingredients=recipe_ingredients,
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
        safety_stock=Decimal("5"),
    )

    assert result["suggested_purchase"] == Decimal("0")


@pytest.mark.asyncio
async def test_forecast_returns_zero_usage_when_there_are_no_sales():
    restaurant_id = uuid4()
    ingredient_id = uuid4()

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=20,
            unit="kg",
        ),
    ]

    service = make_service(
        orders=[],
        recipes={},
        recipe_ingredients={},
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
    )

    assert result["average_daily_usage"] == Decimal("0")
    assert result["forecasted_usage"] == Decimal("0")
    assert result["suggested_purchase"] == Decimal("0")


@pytest.mark.asyncio
async def test_forecast_returns_none_when_ingredient_is_not_found():
    restaurant_id = uuid4()

    service = make_service(
        orders=[],
        recipes={},
        recipe_ingredients={},
        ingredients=[],
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Truffles",
        forecast_days=7,
    )

    assert result is None


@pytest.mark.asyncio
async def test_forecast_ignores_unknown_recipes():
    restaurant_id = uuid4()

    recipe_id = uuid4()
    ingredient_id = uuid4()

    now = datetime.now(timezone.utc)

    orders = [
        FakeOrder(
            created_at=now,
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
    ]

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=20,
            unit="kg",
        ),
    ]

    service = make_service(
        orders=orders,
        recipes={},
        recipe_ingredients={},
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
    )

    assert result["average_daily_usage"] == Decimal("0")
    assert result["forecasted_usage"] == Decimal("0")


@pytest.mark.asyncio
async def test_forecast_is_scoped_to_requested_restaurant():
    restaurant_id = uuid4()
    other_restaurant_id = uuid4()

    recipe_id = uuid4()
    ingredient_id = uuid4()

    now = datetime.now(timezone.utc)

    orders = [
        FakeOrder(
            created_at=now,
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=100,
                ),
            ],
        ),
    ]

    recipes = {
        recipe_id: FakeRecipe(
            recipe_id=recipe_id,
            name="Chicken Burger",
            restaurant_id=other_restaurant_id,
        ),
    }

    recipe_ingredients = {
        recipe_id: [
            FakeRecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
                quantity=Decimal("0.2"),
            ),
        ],
    }

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=20,
            unit="kg",
        ),
    ]

    service = make_service(
        orders=orders,
        recipes=recipes,
        recipe_ingredients=recipe_ingredients,
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
    )

    assert result["average_daily_usage"] == Decimal("0")
    assert result["forecasted_usage"] == Decimal("0")

@pytest.mark.asyncio
async def test_forecast_ignores_orders_outside_lookback_window():
    restaurant_id = uuid4()

    recipe_id = uuid4()
    ingredient_id = uuid4()

    now = datetime.now(timezone.utc)

    orders = [
        FakeOrder(
            created_at=now - timedelta(days=10),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=100,
                ),
            ],
        ),
        FakeOrder(
            created_at=now - timedelta(days=2),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now - timedelta(days=1),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now,
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
    ]

    recipes = {
        recipe_id: FakeRecipe(
            recipe_id=recipe_id,
            name="Chicken Burger",
            restaurant_id=restaurant_id,
        ),
    }

    recipe_ingredients = {
        recipe_id: [
            FakeRecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
                quantity=Decimal("0.2"),
            ),
        ],
    }

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=Decimal("20"),
            unit="kg",
        ),
    ]

    service = make_service(
        orders=orders,
        recipes=recipes,
        recipe_ingredients=recipe_ingredients,
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
        lookback_days=3,
    )

    assert result["average_daily_usage"] == Decimal("2")
    assert result["forecasted_usage"] == Decimal("14")
    
@pytest.mark.asyncio
async def test_forecast_includes_order_at_lookback_boundary():
    restaurant_id = uuid4()

    recipe_id = uuid4()
    ingredient_id = uuid4()

    now = datetime.now(timezone.utc)

    orders = [
        FakeOrder(
            created_at=now - timedelta(days=3),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now - timedelta(days=2),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
        FakeOrder(
            created_at=now - timedelta(days=1),
            items=[
                FakeOrderItem(
                    recipe_id=recipe_id,
                    quantity=10,
                ),
            ],
        ),
    ]

    recipes = {
        recipe_id: FakeRecipe(
            recipe_id=recipe_id,
            name="Chicken Burger",
            restaurant_id=restaurant_id,
        ),
    }

    recipe_ingredients = {
        recipe_id: [
            FakeRecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
                quantity=Decimal("0.2"),
            ),
        ],
    }

    ingredients = [
        FakeIngredient(
            ingredient_id=ingredient_id,
            name="Chicken",
            current_stock=Decimal("20"),
            unit="kg",
        ),
    ]

    service = make_service(
        orders=orders,
        recipes=recipes,
        recipe_ingredients=recipe_ingredients,
        ingredients=ingredients,
    )

    result = await service.get_forecast(
        restaurant_id=restaurant_id,
        ingredient_name="Chicken",
        forecast_days=7,
        lookback_days=3,
    )

    assert result["average_daily_usage"] == Decimal("2")
    assert result["forecasted_usage"] == Decimal("14")