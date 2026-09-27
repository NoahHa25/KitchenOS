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


@pytest.mark.anyio
async def test_create_insight(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)

    data = RestaurantInsightCreate(
        insight_type="inventory_shortage",
        title="Tomato shortage",
        description="Tomatoes reached minimum stock.",
        severity="high",
        confidence="high",
        evidence="Stock reached minimum level 4 times.",
    )

    insight = await repository.create(
        restaurant_id=restaurant.id,
        data=data,
    )

    assert insight.id is not None
    assert insight.restaurant_id == restaurant.id
    assert insight.insight_type == "inventory_shortage"
    assert insight.title == "Tomato shortage"
    assert insight.severity == "high"
    assert insight.confidence == "high"


@pytest.mark.anyio
async def test_get_insight_by_id(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)

    insight = await repository.create(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="repeated_problem",
            title="Recurring issue",
            description="The same problem happened repeatedly.",
        ),
    )

    result = await repository.get_by_id(
        restaurant_id=restaurant.id,
        insight_id=insight.id,
    )

    assert result is not None
    assert result.id == insight.id


@pytest.mark.anyio
async def test_get_insight_respects_restaurant_scope(db_session):
    restaurant_a = Restaurant(
        name="Restaurant A",
        slug=f"restaurant-a-{uuid4()}",
    )

    restaurant_b = Restaurant(
        name="Restaurant B",
        slug=f"restaurant-b-{uuid4()}",
    )

    db_session.add_all([restaurant_a, restaurant_b])
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)

    insight = await repository.create(
        restaurant_id=restaurant_a.id,
        data=RestaurantInsightCreate(
            insight_type="supplier_delay",
            title="Supplier delay",
            description="Supplier delivered late.",
        ),
    )

    result = await repository.get_by_id(
        restaurant_id=restaurant_b.id,
        insight_id=insight.id,
    )

    assert result is None


@pytest.mark.anyio
async def test_list_insights(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)

    await repository.create(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="inventory_shortage",
            title="Low tomatoes",
            description="Tomatoes are running low.",
        ),
    )

    await repository.create(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="supplier_delay",
            title="Supplier delay",
            description="Supplier arrived late.",
        ),
    )

    insights = await repository.list(
        restaurant_id=restaurant.id,
    )

    assert len(insights) == 2


@pytest.mark.anyio
async def test_list_insights_filters_by_status(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)

    active = await repository.create(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="inventory_shortage",
            title="Active shortage",
            description="Current shortage.",
        ),
    )

    resolved = await repository.create(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="supplier_delay",
            title="Resolved delay",
            description="Previous supplier delay.",
        ),
    )

    await repository.update(
        restaurant_id=restaurant.id,
        insight_id=resolved.id,
        data=RestaurantInsightUpdate(
            status="resolved",
        ),
    )

    active_insights = await repository.list(
        restaurant_id=restaurant.id,
        status="active",
    )

    resolved_insights = await repository.list(
        restaurant_id=restaurant.id,
        status="resolved",
    )

    assert len(active_insights) == 1
    assert active_insights[0].id == active.id

    assert len(resolved_insights) == 1
    assert resolved_insights[0].id == resolved.id


@pytest.mark.anyio
async def test_update_insight(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)

    insight = await repository.create(
        restaurant_id=restaurant.id,
        data=RestaurantInsightCreate(
            insight_type="sales_anomaly",
            title="Sales anomaly",
            description="Sales changed unexpectedly.",
        ),
    )

    updated = await repository.update(
        restaurant_id=restaurant.id,
        insight_id=insight.id,
        data=RestaurantInsightUpdate(
            severity="critical",
            status="resolved",
            title="Major sales anomaly",
        ),
    )

    assert updated is not None
    assert updated.severity == "critical"
    assert updated.status == "resolved"
    assert updated.title == "Major sales anomaly"


@pytest.mark.anyio
async def test_update_nonexistent_insight_returns_none(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantInsightRepository(db_session)

    result = await repository.update(
        restaurant_id=restaurant.id,
        insight_id=uuid4(),
        data=RestaurantInsightUpdate(
            severity="high",
        ),
    )

    assert result is None