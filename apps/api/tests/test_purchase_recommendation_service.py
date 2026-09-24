from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.purchase_recommendation_service import (
    PurchaseRecommendationService,
)


class FakeIngredient:
    def __init__(
        self,
        name,
        unit,
        current_stock,
        minimum_stock,
        restaurant_id,
    ):
        self.id = uuid4()
        self.name = name
        self.unit = unit
        self.current_stock = current_stock
        self.minimum_stock = minimum_stock
        self.restaurant_id = restaurant_id


class FakeIngredientService:
    def __init__(
        self,
        low_stock=None,
    ):
        self.low_stock = low_stock or []

    async def get_low_stock(
        self,
        restaurant_id,
    ):
        return [
            ingredient
            for ingredient in self.low_stock
            if ingredient.restaurant_id == restaurant_id
        ]


def make_service(low_stock):
    return PurchaseRecommendationService(
        ingredient_service=FakeIngredientService(
            low_stock=low_stock,
        ),
    )


@pytest.mark.asyncio
async def test_empty_low_stock_returns_empty_list():
    restaurant_id = uuid4()

    service = make_service([])

    result = await service.get_purchase_recommendations(
        restaurant_id,
    )

    assert result == []


@pytest.mark.asyncio
async def test_single_low_stock_generates_purchase_amount():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=Decimal("0.5"),
        minimum_stock=Decimal("2"),
        restaurant_id=restaurant_id,
    )

    service = make_service([tomato])

    result = await service.get_purchase_recommendations(
        restaurant_id,
    )

    assert len(result) == 1

    recommendation = result[0]

    assert recommendation["ingredient_name"] == "Tomato"
    assert recommendation["recommended_purchase"] == Decimal("1.5")
    assert recommendation["unit"] == "kg"


@pytest.mark.asyncio
async def test_multiple_low_stock_items_return_all_recommendations():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        "Tomato",
        "kg",
        Decimal("0.5"),
        Decimal("2"),
        restaurant_id,
    )

    cheese = FakeIngredient(
        "Cheese",
        "kg",
        Decimal("1"),
        Decimal("3"),
        restaurant_id,
    )

    service = make_service(
        [
            tomato,
            cheese,
        ]
    )

    result = await service.get_purchase_recommendations(
        restaurant_id,
    )

    assert len(result) == 2

    purchases = {
        item["ingredient_name"]: item[
            "recommended_purchase"
        ]
        for item in result
    }

    assert purchases["Tomato"] == Decimal("1.5")
    assert purchases["Cheese"] == Decimal("2")


@pytest.mark.asyncio
async def test_recommendations_are_scoped_to_restaurant():
    restaurant_id = uuid4()
    other_restaurant = uuid4()

    tomato = FakeIngredient(
        "Tomato",
        "kg",
        Decimal("0.5"),
        Decimal("2"),
        other_restaurant,
    )

    service = make_service([tomato])

    result = await service.get_purchase_recommendations(
        restaurant_id,
    )

    assert result == []
