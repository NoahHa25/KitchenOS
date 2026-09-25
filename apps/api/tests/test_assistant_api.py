from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.assistant import (
    get_assistant_service,
    get_briefing_service,
)
from app.main import app


class FakeAssistantService:
    async def answer(self, restaurant_id, query):
        if query == "What sold the most?":
            return {
                "intent": "top_selling_recipes",
                "answer": (
                    "**Top Selling Recipes**\n\n"
                    "• Chicken Burger — 42 sold\n"
                    "• Margherita Pizza — 27 sold\n"
                    "• Caesar Salad — 18 sold"
                ),
            }

        return {
            "intent": "unknown",
            "answer": "Unknown request.",
        }


class FakeBriefingService:
    def __init__(self):
        self.calls = []

    async def get_morning_brief(self, restaurant_id):
        self.calls.append(restaurant_id)

        return {
            "sales": {
                "total_orders": 42,
                "total_revenue": 125000,
            },
            "low_stock": [
                {
                    "ingredient_id": str(uuid4()),
                    "ingredient_name": "Chicken",
                    "current_stock": 4,
                    "minimum_stock": 10,
                    "unit": "kg",
                }
            ],
            "recipe_impact": [
                {
                    "recipe_id": str(uuid4()),
                    "recipe_name": "Chicken Burger",
                    "affected_ingredients": [
                        {
                            "ingredient_id": str(uuid4()),
                            "ingredient_name": "Chicken",
                            "current_stock": 4,
                            "minimum_stock": 10,
                            "unit": "kg",
                            "required_quantity": 0.2,
                        }
                    ],
                }
            ],
            "purchase_recommendations": [
                {
                    "ingredient_id": str(uuid4()),
                    "ingredient_name": "Chicken",
                    "current_stock": 4,
                    "minimum_stock": 10,
                    "recommended_purchase": 6,
                    "unit": "kg",
                }
            ],
            "top_recipe": {
                "recipe_id": str(uuid4()),
                "recipe_name": "Chicken Burger",
                "quantity_sold": 42,
            },
            "demand_forecast": [
                {
                    "ingredient_id": str(uuid4()),
                    "ingredient_name": "Chicken",
                    "current_stock": 4,
                    "unit": "kg",
                    "average_daily_usage": 3,
                    "forecast_days": 7,
                    "forecasted_usage": 21,
                    "safety_stock": 0,
                    "suggested_purchase": 17,
                }
            ],
        }


@pytest.mark.asyncio
async def test_assistant_endpoint_is_available():
    app.dependency_overrides[get_assistant_service] = (
        lambda: FakeAssistantService()
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/assistant",
            json={
                "restaurant_id": str(uuid4()),
                "query": "Hello",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["intent"] == "unknown"


@pytest.mark.asyncio
async def test_assistant_top_selling_recipes_endpoint():
    app.dependency_overrides[get_assistant_service] = (
        lambda: FakeAssistantService()
    )

    restaurant_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/assistant",
            json={
                "restaurant_id": str(restaurant_id),
                "query": "What sold the most?",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "top_selling_recipes"
    assert "Chicken Burger" in data["answer"]
    assert "42 sold" in data["answer"]
    assert "Margherita Pizza" in data["answer"]
    assert "Caesar Salad" in data["answer"]


@pytest.mark.asyncio
async def test_morning_brief_endpoint_is_available():
    app.dependency_overrides[get_briefing_service] = (
        lambda: FakeBriefingService()
    )

    restaurant_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/assistant/briefing/morning/{restaurant_id}",
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_morning_brief_endpoint_returns_expected_sections():
    app.dependency_overrides[get_briefing_service] = (
        lambda: FakeBriefingService()
    )

    restaurant_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/assistant/briefing/morning/{restaurant_id}",
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert "sales" in data
    assert "low_stock" in data
    assert "recipe_impact" in data
    assert "purchase_recommendations" in data
    assert "top_recipe" in data
    assert "demand_forecast" in data


@pytest.mark.asyncio
async def test_morning_brief_endpoint_returns_sales_and_top_recipe():
    app.dependency_overrides[get_briefing_service] = (
        lambda: FakeBriefingService()
    )

    restaurant_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/assistant/briefing/morning/{restaurant_id}",
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["sales"]["total_orders"] == 42
    assert data["sales"]["total_revenue"] == 125000

    assert data["top_recipe"]["recipe_name"] == (
        "Chicken Burger"
    )
    assert data["top_recipe"]["quantity_sold"] == 42


@pytest.mark.asyncio
async def test_morning_brief_endpoint_returns_inventory_intelligence():
    app.dependency_overrides[get_briefing_service] = (
        lambda: FakeBriefingService()
    )

    restaurant_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/assistant/briefing/morning/{restaurant_id}",
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert len(data["low_stock"]) == 1
    assert data["low_stock"][0]["ingredient_name"] == "Chicken"

    assert len(data["purchase_recommendations"]) == 1
    assert (
        data["purchase_recommendations"][0][
            "recommended_purchase"
        ]
        == 6
    )

    assert len(data["recipe_impact"]) == 1
    assert data["recipe_impact"][0]["recipe_name"] == (
        "Chicken Burger"
    )


@pytest.mark.asyncio
async def test_morning_brief_endpoint_returns_demand_forecast():
    app.dependency_overrides[get_briefing_service] = (
        lambda: FakeBriefingService()
    )

    restaurant_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/assistant/briefing/morning/{restaurant_id}",
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert len(data["demand_forecast"]) == 1

    forecast = data["demand_forecast"][0]

    assert forecast["ingredient_name"] == "Chicken"
    assert forecast["forecast_days"] == 7
    assert forecast["forecasted_usage"] == 21
    assert forecast["suggested_purchase"] == 17


@pytest.mark.asyncio
async def test_morning_brief_endpoint_passes_restaurant_id():
    fake_service = FakeBriefingService()

    app.dependency_overrides[get_briefing_service] = (
        lambda: fake_service
    )

    restaurant_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/assistant/briefing/morning/{restaurant_id}",
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake_service.calls == [restaurant_id]