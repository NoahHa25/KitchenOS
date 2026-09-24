from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.sales_intelligence_service import (
    SalesIntelligenceService,
)


class FakeRecipe:
    def __init__(
        self,
        recipe_id,
        name,
    ):
        self.id = recipe_id
        self.name = name


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
        items,
    ):
        self.items = items


class FakeOrderRepository:
    def __init__(
        self,
        completed_orders=None,
    ):
        self.completed_orders = completed_orders or []

    async def get_completed_orders(
        self,
        restaurant_id,
    ):
        return self.completed_orders


class FakeRecipeRepository:
    def __init__(
        self,
        recipes=None,
    ):
        self.recipes = recipes or {}

    async def get_by_id(
        self,
        restaurant_id,
        recipe_id,
    ):
        return self.recipes.get(recipe_id)


def make_service(
    completed_orders,
    recipes,
):
    return SalesIntelligenceService(
        order_repository=FakeOrderRepository(
            completed_orders=completed_orders,
        ),
        recipe_repository=FakeRecipeRepository(
            recipes=recipes,
        ),
    )


@pytest.mark.asyncio
async def test_no_completed_orders_returns_empty_list():
    restaurant_id = uuid4()

    service = make_service(
        completed_orders=[],
        recipes={},
    )

    result = await service.get_top_selling_recipes(
        restaurant_id,
    )

    assert result == []


@pytest.mark.asyncio
async def test_single_recipe_sales_are_counted():
    restaurant_id = uuid4()
    recipe_id = uuid4()

    order = FakeOrder(
        items=[
            FakeOrderItem(
                recipe_id=recipe_id,
                quantity=Decimal("3"),
            ),
        ],
    )

    service = make_service(
        completed_orders=[order],
        recipes={
            recipe_id: FakeRecipe(
                recipe_id=recipe_id,
                name="Chicken Burger",
            ),
        },
    )

    result = await service.get_top_selling_recipes(
        restaurant_id,
    )

    assert len(result) == 1

    assert result[0]["recipe_id"] == recipe_id
    assert result[0]["recipe_name"] == "Chicken Burger"
    assert result[0]["quantity_sold"] == Decimal("3")


@pytest.mark.asyncio
async def test_recipe_quantities_are_aggregated():
    restaurant_id = uuid4()
    recipe_id = uuid4()

    order_one = FakeOrder(
        items=[
            FakeOrderItem(
                recipe_id=recipe_id,
                quantity=Decimal("2"),
            ),
        ],
    )

    order_two = FakeOrder(
        items=[
            FakeOrderItem(
                recipe_id=recipe_id,
                quantity=Decimal("4"),
            ),
        ],
    )

    service = make_service(
        completed_orders=[
            order_one,
            order_two,
        ],
        recipes={
            recipe_id: FakeRecipe(
                recipe_id=recipe_id,
                name="Pizza",
            ),
        },
    )

    result = await service.get_top_selling_recipes(
        restaurant_id,
    )

    assert len(result) == 1
    assert result[0]["recipe_id"] == recipe_id
    assert result[0]["recipe_name"] == "Pizza"
    assert result[0]["quantity_sold"] == Decimal("6")


@pytest.mark.asyncio
async def test_multiple_recipes_are_sorted_by_quantity():
    restaurant_id = uuid4()

    burger_id = uuid4()
    pizza_id = uuid4()
    salad_id = uuid4()

    order = FakeOrder(
        items=[
            FakeOrderItem(
                recipe_id=burger_id,
                quantity=Decimal("2"),
            ),
            FakeOrderItem(
                recipe_id=pizza_id,
                quantity=Decimal("7"),
            ),
            FakeOrderItem(
                recipe_id=salad_id,
                quantity=Decimal("4"),
            ),
        ],
    )

    service = make_service(
        completed_orders=[order],
        recipes={
            burger_id: FakeRecipe(
                recipe_id=burger_id,
                name="Burger",
            ),
            pizza_id: FakeRecipe(
                recipe_id=pizza_id,
                name="Pizza",
            ),
            salad_id: FakeRecipe(
                recipe_id=salad_id,
                name="Salad",
            ),
        },
    )

    result = await service.get_top_selling_recipes(
        restaurant_id,
    )

    assert [
        item["recipe_id"]
        for item in result
    ] == [
        pizza_id,
        salad_id,
        burger_id,
    ]

    assert [
        item["recipe_name"]
        for item in result
    ] == [
        "Pizza",
        "Salad",
        "Burger",
    ]

    assert [
        item["quantity_sold"]
        for item in result
    ] == [
        Decimal("7"),
        Decimal("4"),
        Decimal("2"),
    ]


@pytest.mark.asyncio
async def test_sales_are_aggregated_across_multiple_orders():
    restaurant_id = uuid4()

    burger_id = uuid4()
    pizza_id = uuid4()

    order_one = FakeOrder(
        items=[
            FakeOrderItem(
                burger_id,
                Decimal("3"),
            ),
            FakeOrderItem(
                pizza_id,
                Decimal("1"),
            ),
        ],
    )

    order_two = FakeOrder(
        items=[
            FakeOrderItem(
                burger_id,
                Decimal("5"),
            ),
            FakeOrderItem(
                pizza_id,
                Decimal("4"),
            ),
        ],
    )

    service = make_service(
        completed_orders=[
            order_one,
            order_two,
        ],
        recipes={
            burger_id: FakeRecipe(
                recipe_id=burger_id,
                name="Burger",
            ),
            pizza_id: FakeRecipe(
                recipe_id=pizza_id,
                name="Pizza",
            ),
        },
    )

    result = await service.get_top_selling_recipes(
        restaurant_id,
    )

    sales = {
        item["recipe_id"]: item["quantity_sold"]
        for item in result
    }

    assert sales[burger_id] == Decimal("8")
    assert sales[pizza_id] == Decimal("5")


@pytest.mark.asyncio
async def test_missing_recipe_is_skipped():
    restaurant_id = uuid4()
    recipe_id = uuid4()

    order = FakeOrder(
        items=[
            FakeOrderItem(
                recipe_id=recipe_id,
                quantity=Decimal("5"),
            ),
        ],
    )

    service = make_service(
        completed_orders=[order],
        recipes={},
    )

    result = await service.get_top_selling_recipes(
        restaurant_id,
    )

    assert result == []