from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.ingredient import Ingredient
from app.models.inventory_movement import InventoryMovement
from app.models.restaurant import Restaurant


@pytest.mark.anyio
async def test_analyze_restaurant_detects_repeated_waste(
    db_session,
):
    restaurant = Restaurant(
        name="Brain API Restaurant",
        slug=f"brain-api-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    for _ in range(4):
        movement = InventoryMovement(
            ingredient_id=ingredient.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Spoilage",
        )

        db_session.add(movement)

    await db_session.flush()

    async def override_get_db():
        yield db_session

    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/restaurants/{restaurant.id}/brain/analyze",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    insight = data[0]

    assert insight["restaurant_id"] == str(restaurant.id)
    assert insight["insight_type"] == "repeated_problem"
    assert insight["title"] == "Tomatoes waste is recurring"
    assert insight["severity"] == "high"
    assert insight["confidence"] == "medium"
    assert "occurred 4 times" in insight["description"]


@pytest.mark.anyio
async def test_analyze_restaurant_returns_empty_when_no_problem_detected(
    db_session,
):
    restaurant = Restaurant(
        name="Healthy Brain Restaurant",
        slug=f"healthy-brain-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    for _ in range(2):
        movement = InventoryMovement(
            ingredient_id=ingredient.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Small waste",
        )

        db_session.add(movement)

    await db_session.flush()

    async def override_get_db():
        yield db_session

    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/restaurants/{restaurant.id}/brain/analyze",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []