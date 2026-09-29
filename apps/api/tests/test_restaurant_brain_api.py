from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.ingredient import Ingredient
from app.models.inventory_movement import InventoryMovement
from app.models.restaurant import Restaurant
from app.models.restaurant_memory import RestaurantMemory


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


@pytest.mark.anyio
async def test_analyze_restaurant_detects_repeated_memories(
    db_session,
):
    restaurant = Restaurant(
        name="Memory Brain Restaurant",
        slug=f"memory-brain-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    for _ in range(3):
        memory = RestaurantMemory(
            restaurant_id=restaurant.id,
            memory_type="equipment",
            title="Oven overheating",
            description="The main oven overheated during service.",
            importance="high",
        )

        db_session.add(memory)

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
    assert insight["title"] == "Oven overheating is recurring"
    assert insight["severity"] == "medium"
    assert insight["confidence"] == "medium"
    assert "occurred 3 times" in insight["description"]


@pytest.mark.anyio
async def test_analyze_restaurant_does_not_combine_memories_across_restaurants(
    db_session,
):
    restaurant_a = Restaurant(
        name="Memory Restaurant A",
        slug=f"memory-a-{uuid4()}",
    )

    restaurant_b = Restaurant(
        name="Memory Restaurant B",
        slug=f"memory-b-{uuid4()}",
    )

    db_session.add_all([restaurant_a, restaurant_b])
    await db_session.flush()

    db_session.add_all(
        [
            RestaurantMemory(
                restaurant_id=restaurant_a.id,
                memory_type="equipment",
                title="Oven overheating",
                description="The oven overheated.",
                importance="high",
            ),
            RestaurantMemory(
                restaurant_id=restaurant_a.id,
                memory_type="equipment",
                title="Oven overheating",
                description="The oven overheated again.",
                importance="high",
            ),
            RestaurantMemory(
                restaurant_id=restaurant_b.id,
                memory_type="equipment",
                title="Oven overheating",
                description="The oven overheated.",
                importance="high",
            ),
        ]
    )

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
            response_a = await client.post(
                f"/restaurants/{restaurant_a.id}/brain/analyze",
            )

            response_b = await client.post(
                f"/restaurants/{restaurant_b.id}/brain/analyze",
            )
    finally:
        app.dependency_overrides.clear()

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    assert response_a.json() == []
    assert response_b.json() == []


@pytest.mark.anyio
async def test_analyze_restaurant_does_not_create_duplicate_memory_insight(
    db_session,
):
    restaurant = Restaurant(
        name="Duplicate Memory Brain Restaurant",
        slug=f"duplicate-memory-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    for _ in range(3):
        memory = RestaurantMemory(
            restaurant_id=restaurant.id,
            memory_type="equipment",
            title="Freezer failing",
            description="The freezer failed during service.",
            importance="critical",
        )

        db_session.add(memory)

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
            first_response = await client.post(
                f"/restaurants/{restaurant.id}/brain/analyze",
            )

            second_response = await client.post(
                f"/restaurants/{restaurant.id}/brain/analyze",
            )
    finally:
        app.dependency_overrides.clear()

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert len(first_data) == 1
    assert len(second_data) == 1

    assert first_data[0]["id"] == second_data[0]["id"]
    assert first_data[0]["title"] == "Freezer failing is recurring"