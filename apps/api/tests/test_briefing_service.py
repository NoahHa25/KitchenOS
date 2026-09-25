from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.briefing_service import BriefingService


class FakeSalesService:
    def __init__(self, sales=None):
        self.sales = sales or {}

    async def get_sales_summary(self, restaurant_id):
        return self.sales


class FakeIngredientService:
    def __init__(self, low_stock=None):
        self.low_stock = low_stock or []

    async def get_low_stock(self, restaurant_id):
        return self.low_stock


class FakeRecipeImpactService:
    def __init__(self, recipe_impact=None):
        self.recipe_impact = recipe_impact or []

    async def get_low_stock_recipe_impact(self, restaurant_id):
        return self.recipe_impact


class FakePurchaseRecommendationService:
    def __init__(self, recommendations=None):
        self.recommendations = recommendations or []

    async def get_purchase_recommendations(self, restaurant_id):
        return self.recommendations


class FakeSalesIntelligenceService:
    def __init__(self, top_selling=None):
        self.top_selling = top_selling or []

    async def get_top_selling_recipes(self, restaurant_id):
        return self.top_selling


class FakeDemandForecastService:
    def __init__(self, forecasts=None):
        self.forecasts = forecasts or {}
        self.calls = []

    async def get_forecast(
        self,
        restaurant_id,
        ingredient_name,
        forecast_days=7,
        safety_stock=Decimal("0"),
        lookback_days=30,
    ):
        self.calls.append(
            {
                "restaurant_id": restaurant_id,
                "ingredient_name": ingredient_name,
                "forecast_days": forecast_days,
                "safety_stock": safety_stock,
                "lookback_days": lookback_days,
            }
        )

        return self.forecasts.get(ingredient_name)


class FakeRecipeIngredientRepository:
    def __init__(self, recipe_ingredients=None):
        self.recipe_ingredients = recipe_ingredients or {}

    async def get_by_recipe(self, recipe_id):
        return self.recipe_ingredients.get(recipe_id, [])


def build_briefing_service(
    *,
    sales=None,
    low_stock=None,
    recipe_impact=None,
    purchase_recommendations=None,
    top_selling=None,
    demand_forecasts=None,
    recipe_ingredients=None,
):
    return BriefingService(
        sales_service=FakeSalesService(
            sales=sales,
        ),
        ingredient_service=FakeIngredientService(
            low_stock=low_stock,
        ),
        recipe_impact_service=FakeRecipeImpactService(
            recipe_impact=recipe_impact,
        ),
        purchase_recommendation_service=(
            FakePurchaseRecommendationService(
                recommendations=purchase_recommendations,
            )
        ),
        sales_intelligence_service=(
            FakeSalesIntelligenceService(
                top_selling=top_selling,
            )
        ),
        demand_forecast_service=(
            FakeDemandForecastService(
                forecasts=demand_forecasts,
            )
        ),
        recipe_ingredient_repository=(
            FakeRecipeIngredientRepository(
                recipe_ingredients=recipe_ingredients,
            )
        ),
    )


@pytest.mark.asyncio
async def test_morning_brief_includes_sales():
    sales = {
        "total_sales": Decimal("1500.00"),
        "order_count": 25,
    }

    service = build_briefing_service(
        sales=sales,
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["sales"] == sales


@pytest.mark.asyncio
async def test_morning_brief_includes_low_stock():
    low_stock = [
        {
            "ingredient_id": uuid4(),
            "ingredient_name": "Chicken",
            "current_stock": 5,
            "minimum_stock": 10,
        }
    ]

    service = build_briefing_service(
        low_stock=low_stock,
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["low_stock"] == low_stock


@pytest.mark.asyncio
async def test_morning_brief_includes_recipe_impact():
    recipe_impact = [
        {
            "recipe_id": uuid4(),
            "recipe_name": "Chicken Burger",
            "affected_ingredients": [
                {
                    "ingredient_name": "Chicken",
                }
            ],
        }
    ]

    service = build_briefing_service(
        recipe_impact=recipe_impact,
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["recipe_impact"] == recipe_impact


@pytest.mark.asyncio
async def test_morning_brief_includes_purchase_recommendations():
    recommendations = [
        {
            "ingredient_id": uuid4(),
            "ingredient_name": "Chicken",
            "recommended_purchase": 20,
        }
    ]

    service = build_briefing_service(
        purchase_recommendations=recommendations,
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["purchase_recommendations"] == recommendations


@pytest.mark.asyncio
async def test_morning_brief_selects_top_selling_recipe():
    top_selling = [
        {
            "recipe_id": uuid4(),
            "recipe_name": "Chicken Burger",
            "quantity_sold": 100,
        },
        {
            "recipe_id": uuid4(),
            "recipe_name": "Beef Burger",
            "quantity_sold": 80,
        },
    ]

    service = build_briefing_service(
        top_selling=top_selling,
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["top_recipe"] == top_selling[0]


@pytest.mark.asyncio
async def test_morning_brief_returns_none_when_there_are_no_sales():
    service = build_briefing_service(
        top_selling=[],
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["top_recipe"] is None


@pytest.mark.asyncio
async def test_morning_brief_handles_no_low_stock_items():
    service = build_briefing_service(
        low_stock=[],
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["low_stock"] == []


@pytest.mark.asyncio
async def test_morning_brief_handles_no_purchase_recommendations():
    service = build_briefing_service(
        purchase_recommendations=[],
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["purchase_recommendations"] == []


@pytest.mark.asyncio
async def test_morning_brief_handles_no_recipe_impact():
    service = build_briefing_service(
        recipe_impact=[],
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["recipe_impact"] == []


@pytest.mark.asyncio
async def test_morning_brief_contains_all_expected_sections():
    service = build_briefing_service()

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert "sales" in result
    assert "low_stock" in result
    assert "recipe_impact" in result
    assert "purchase_recommendations" in result
    assert "top_recipe" in result
    assert "demand_forecast" in result


@pytest.mark.asyncio
async def test_morning_brief_preserves_empty_sections():
    service = build_briefing_service(
        sales={},
        low_stock=[],
        recipe_impact=[],
        purchase_recommendations=[],
        top_selling=[],
        demand_forecasts={},
        recipe_ingredients={},
    )

    result = await service.get_morning_brief(
        restaurant_id=uuid4(),
    )

    assert result["sales"] == {}
    assert result["low_stock"] == []
    assert result["recipe_impact"] == []
    assert result["purchase_recommendations"] == []
    assert result["top_recipe"] is None
    assert result["demand_forecast"] == []


@pytest.mark.asyncio
async def test_morning_brief_forecasts_top_recipe_ingredients():
    restaurant_id = uuid4()
    recipe_id = uuid4()

    chicken_id = uuid4()
    bun_id = uuid4()

    chicken = type(
        "Ingredient",
        (),
        {
            "id": chicken_id,
            "name": "Chicken",
        },
    )()

    bun = type(
        "Ingredient",
        (),
        {
            "id": bun_id,
            "name": "Burger Bun",
        },
    )()

    recipe_ingredients = {
        recipe_id: [
            type(
                "RecipeIngredient",
                (),
                {
                    "ingredient_id": chicken_id,
                    "ingredient": chicken,
                    "quantity": Decimal("0.2"),
                },
            )(),
            type(
                "RecipeIngredient",
                (),
                {
                    "ingredient_id": bun_id,
                    "ingredient": bun,
                    "quantity": Decimal("1"),
                },
            )(),
        ]
    }

    demand_forecasts = {
        "Chicken": {
            "ingredient_name": "Chicken",
            "forecasted_usage": Decimal("42"),
            "suggested_purchase": Decimal("20"),
        },
        "Burger Bun": {
            "ingredient_name": "Burger Bun",
            "forecasted_usage": Decimal("85"),
            "suggested_purchase": Decimal("40"),
        },
    }

    service = build_briefing_service(
        top_selling=[
            {
                "recipe_id": recipe_id,
                "recipe_name": "Chicken Burger",
                "quantity_sold": 100,
            }
        ],
        demand_forecasts=demand_forecasts,
        recipe_ingredients=recipe_ingredients,
    )

    result = await service.get_morning_brief(
        restaurant_id=restaurant_id,
    )

    assert len(result["demand_forecast"]) == 2

    ingredient_names = {
        item["ingredient_name"]
        for item in result["demand_forecast"]
    }

    assert ingredient_names == {
        "Chicken",
        "Burger Bun",
    }


@pytest.mark.asyncio
async def test_morning_brief_calls_demand_forecast_for_each_top_recipe_ingredient():
    restaurant_id = uuid4()
    recipe_id = uuid4()

    chicken_id = uuid4()
    bun_id = uuid4()

    chicken = type(
        "Ingredient",
        (),
        {
            "id": chicken_id,
            "name": "Chicken",
        },
    )()

    bun = type(
        "Ingredient",
        (),
        {
            "id": bun_id,
            "name": "Burger Bun",
        },
    )()

    recipe_ingredients = {
        recipe_id: [
            type(
                "RecipeIngredient",
                (),
                {
                    "ingredient_id": chicken_id,
                    "ingredient": chicken,
                    "quantity": Decimal("0.2"),
                },
            )(),
            type(
                "RecipeIngredient",
                (),
                {
                    "ingredient_id": bun_id,
                    "ingredient": bun,
                    "quantity": Decimal("1"),
                },
            )(),
        ]
    }

    demand_forecasts = {
        "Chicken": {
            "ingredient_name": "Chicken",
        },
        "Burger Bun": {
            "ingredient_name": "Burger Bun",
        },
    }

    service = build_briefing_service(
        top_selling=[
            {
                "recipe_id": recipe_id,
                "recipe_name": "Chicken Burger",
                "quantity_sold": 100,
            }
        ],
        demand_forecasts=demand_forecasts,
        recipe_ingredients=recipe_ingredients,
    )

    await service.get_morning_brief(
        restaurant_id=restaurant_id,
    )

    demand_forecast_service = (
        service.demand_forecast_service
    )

    assert len(demand_forecast_service.calls) == 2

    called_ingredients = {
        call["ingredient_name"]
        for call in demand_forecast_service.calls
    }

    assert called_ingredients == {
        "Chicken",
        "Burger Bun",
    }


@pytest.mark.asyncio
async def test_morning_brief_returns_empty_demand_forecast_without_top_selling_recipe():
    restaurant_id = uuid4()

    service = build_briefing_service(
        top_selling=[],
    )

    result = await service.get_morning_brief(
        restaurant_id=restaurant_id,
    )

    assert result["demand_forecast"] == []

    demand_forecast_service = (
        service.demand_forecast_service
    )

    assert demand_forecast_service.calls == []

