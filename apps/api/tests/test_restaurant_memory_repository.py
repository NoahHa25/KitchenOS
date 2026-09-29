from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.restaurant import Restaurant
from app.models.restaurant_memory import RestaurantMemory
from app.repositories.restaurant_memory import RestaurantMemoryRepository


@pytest.mark.anyio
async def test_create_memory(db_session):
    restaurant = Restaurant(
        name="Memory Repository Restaurant",
        slug=f"memory-repository-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    repository = RestaurantMemoryRepository(db_session)

    memory = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="supplier",
        title="Supplier delay",
        description="Vegetable delivery arrived late.",
        importance="medium",
        tags="supplier,delay",
    )

    assert memory.id is not None
    assert memory.restaurant_id == restaurant.id
    assert memory.memory_type == "supplier"
    assert memory.title == "Supplier delay"


@pytest.mark.anyio
async def test_get_by_id_is_restaurant_scoped(db_session):
    restaurant = Restaurant(
        name="Memory Scope Restaurant",
        slug=f"memory-scope-{uuid4()}",
    )

    other_restaurant = Restaurant(
        name="Other Restaurant",
        slug=f"other-memory-scope-{uuid4()}",
    )

    db_session.add_all([restaurant, other_restaurant])
    await db_session.flush()

    repository = RestaurantMemoryRepository(db_session)

    memory = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="inventory",
        title="Low stock",
        description="Tomatoes are running low.",
    )

    result = await repository.get_by_id(
        restaurant_id=restaurant.id,
        memory_id=memory.id,
    )

    assert result is not None
    assert result.id == memory.id

    wrong_restaurant_result = await repository.get_by_id(
        restaurant_id=other_restaurant.id,
        memory_id=memory.id,
    )

    assert wrong_restaurant_result is None


@pytest.mark.anyio
async def test_list_is_restaurant_scoped(db_session):
    restaurant = Restaurant(
        name="Memory List Restaurant",
        slug=f"memory-list-{uuid4()}",
    )

    other_restaurant = Restaurant(
        name="Other List Restaurant",
        slug=f"other-memory-list-{uuid4()}",
    )

    db_session.add_all([restaurant, other_restaurant])
    await db_session.flush()

    repository = RestaurantMemoryRepository(db_session)

    first = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="supplier",
        title="Supplier delay",
        description="Delivery was late.",
    )

    second = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="waste",
        title="Food waste",
        description="Vegetables were discarded.",
    )

    await repository.create(
        restaurant_id=other_restaurant.id,
        memory_type="supplier",
        title="Other supplier issue",
        description="Other restaurant supplier issue.",
    )

    memories = await repository.list(
        restaurant_id=restaurant.id,
    )

    memory_ids = {memory.id for memory in memories}

    assert memory_ids == {first.id, second.id}


@pytest.mark.anyio
async def test_list_recent_returns_only_recent_memories(db_session):
    restaurant = Restaurant(
        name="Recent Memory Restaurant",
        slug=f"recent-memory-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    old_memory = RestaurantMemory(
        restaurant_id=restaurant.id,
        memory_type="supplier",
        title="Old supplier delay",
        description="This happened earlier.",
        created_at=datetime.now(timezone.utc) - timedelta(days=40),
    )

    recent_memory = RestaurantMemory(
        restaurant_id=restaurant.id,
        memory_type="supplier",
        title="Recent supplier delay",
        description="This happened recently.",
        created_at=datetime.now(timezone.utc) - timedelta(days=5),
    )

    db_session.add_all([old_memory, recent_memory])
    await db_session.flush()

    repository = RestaurantMemoryRepository(db_session)

    created_after = datetime.now(timezone.utc) - timedelta(days=30)

    memories = await repository.list_recent(
        restaurant_id=restaurant.id,
        created_after=created_after,
    )

    memory_ids = {memory.id for memory in memories}

    assert recent_memory.id in memory_ids
    assert old_memory.id not in memory_ids


@pytest.mark.anyio
async def test_list_recent_is_restaurant_scoped(db_session):
    restaurant = Restaurant(
        name="Recent Scope Restaurant",
        slug=f"recent-scope-{uuid4()}",
    )

    other_restaurant = Restaurant(
        name="Other Recent Scope Restaurant",
        slug=f"other-recent-scope-{uuid4()}",
    )

    db_session.add_all([restaurant, other_restaurant])
    await db_session.flush()

    repository = RestaurantMemoryRepository(db_session)

    memory = await repository.create(
        restaurant_id=other_restaurant.id,
        memory_type="supplier",
        title="Other restaurant memory",
        description="Should not be returned.",
    )

    created_after = datetime.now(timezone.utc) - timedelta(days=1)

    memories = await repository.list_recent(
        restaurant_id=restaurant.id,
        created_after=created_after,
    )

    assert memory.id not in {item.id for item in memories}

