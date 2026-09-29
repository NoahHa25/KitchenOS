from uuid import uuid4

import pytest

from app.models.restaurant import Restaurant
from app.repositories.restaurant_insight_repository import (
    RestaurantInsightRepository,
)
from app.schemas.restaurant_insight import (
    RestaurantInsightCreate,
    RestaurantInsightUpdate,
)
from app.services.restaurant_brain_service import (
    RestaurantBrainService,
)
from app.repositories.restaurant_memory import RestaurantMemoryRepository


@pytest.mark.anyio
async def test_create_insight(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)
    service = RestaurantBrainService(repository)

    data = RestaurantInsightCreate(
        insight_type="inventory_shortage",
        title="Tomato shortage",
        description="Tomatoes reached minimum stock.",
        severity="high",
        confidence="high",
    )

    insight = await service.create_insight(
        restaurant_id=restaurant.id,
        data=data,
    )

    assert insight.id is not None
    assert insight.restaurant_id == restaurant.id
    assert insight.insight_type == "inventory_shortage"


@pytest.mark.anyio
async def test_duplicate_active_insight_is_not_created(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)
    service = RestaurantBrainService(repository)

    data = RestaurantInsightCreate(
        insight_type="inventory_shortage",
        title="Tomato shortage",
        description="Tomatoes reached minimum stock.",
    )

    first = await service.create_insight(
        restaurant_id=restaurant.id,
        data=data,
    )

    second = await service.create_insight(
        restaurant_id=restaurant.id,
        data=data,
    )

    assert first.id == second.id

    insights = await repository.list(
        restaurant_id=restaurant.id,
        status="active",
    )

    assert len(insights) == 1


@pytest.mark.anyio
async def test_different_insight_can_be_created(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)
    service = RestaurantBrainService(repository)

    first = await service.create_insight(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="inventory_shortage",
            title="Tomato shortage",
            description="Tomatoes are running low.",
        ),
    )

    second = await service.create_insight(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="supplier_delay",
            title="Supplier delay",
            description="Supplier delivered late.",
        ),
    )

    assert first.id != second.id


@pytest.mark.anyio
async def test_get_insight(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)
    service = RestaurantBrainService(repository)

    created = await service.create_insight(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="sales_anomaly",
            title="Sales anomaly",
            description="Sales changed unexpectedly.",
        ),
    )

    result = await service.get_insight(
        restaurant_id=restaurant.id,
        insight_id=created.id,
    )

    assert result is not None
    assert result.id == created.id


@pytest.mark.anyio
async def test_list_active_insights(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)
    service = RestaurantBrainService(repository)

    active = await service.create_insight(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="inventory_shortage",
            title="Low stock",
            description="Ingredient stock is low.",
        ),
    )

    resolved = await service.create_insight(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="supplier_delay",
            title="Old delay",
            description="Supplier was late.",
        ),
    )

    await service.resolve_insight(
        restaurant_id=restaurant.id,
        insight_id=resolved.id,
    )

    insights = await service.list_insights(
        restaurant_id=restaurant.id,
    )

    assert len(insights) == 1
    assert insights[0].id == active.id


@pytest.mark.anyio
async def test_update_insight(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)
    service = RestaurantBrainService(repository)

    insight = await service.create_insight(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="food_cost_change",
            title="Food cost increased",
            description="Food cost increased significantly.",
        ),
    )

    updated = await service.update_insight(
        restaurant_id=restaurant.id,
        insight_id=insight.id,
        data=RestaurantInsightUpdate(
            severity="high",
        ),
    )

    assert updated is not None
    assert updated.severity == "high"


@pytest.mark.anyio
async def test_resolve_insight(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)
    service = RestaurantBrainService(repository)

    insight = await service.create_insight(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="equipment_issue",
            title="Equipment issue",
            description="Kitchen equipment requires attention.",
        ),
    )

    resolved = await service.resolve_insight(
        restaurant_id=restaurant.id,
        insight_id=insight.id,
    )

    assert resolved is not None
    assert resolved.status == "resolved"


@pytest.mark.anyio
async def test_resolve_nonexistent_insight_returns_none(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)
    service = RestaurantBrainService(repository)

    result = await service.resolve_insight(
        restaurant_id=restaurant.id,
        insight_id=uuid4(),
    )

    assert result is None