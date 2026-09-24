from uuid import uuid4
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.assistant import get_assistant_service


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