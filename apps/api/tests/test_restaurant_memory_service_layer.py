from uuid import uuid4

import pytest

from app.models.restaurant import Restaurant
from app.repositories.restaurant_memory import RestaurantMemoryRepository
from app.services.restaurant_memory_service import RestaurantMemoryService


async def create_restaurant(db_session) -> Restaurant:
    restaurant = Restaurant(
        name="Memory Service Restaurant",
        slug=f"memory-service-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    return restaurant


@pytest.mark.anyio
async def test_service_creates_memory(db_session):
    restaurant = await create_restaurant(db_session)

    repository = RestaurantMemoryRepository(db_session)
    service = RestaurantMemoryService(repository)

    memory = await service.create_memory(
        restaurant_id=restaurant.id,
        memory_type="equipment",
        title="Oven failure",
        description="Oven #2 stopped heating.",
        importance="high",
        tags="oven,equipment",
    )

    await db_session.commit()

    assert memory.id is not None
    assert memory.restaurant_id == restaurant.id
    assert memory.memory_type == "equipment"
    assert memory.title == "Oven failure"
    assert memory.importance == "high"


@pytest.mark.anyio
async def test_service_gets_memory(db_session):
    restaurant = await create_restaurant(db_session)

    repository = RestaurantMemoryRepository(db_session)
    service = RestaurantMemoryService(repository)

    memory = await service.create_memory(
        restaurant_id=restaurant.id,
        memory_type="supplier",
        title="Late delivery",
        description="Supplier arrived two hours late.",
    )

    await db_session.commit()

    found = await service.get_memory(
        restaurant_id=restaurant.id,
        memory_id=memory.id,
    )

    assert found is not None
    assert found.id == memory.id


@pytest.mark.anyio
async def test_service_lists_memories(db_session):
    restaurant = await create_restaurant(db_session)

    repository = RestaurantMemoryRepository(db_session)
    service = RestaurantMemoryService(repository)

    await service.create_memory(
        restaurant_id=restaurant.id,
        memory_type="inventory",
        title="Low tomato stock",
        description="Tomatoes dropped below minimum stock.",
    )

    await service.create_memory(
        restaurant_id=restaurant.id,
        memory_type="sales",
        title="Burger sales increased",
        description="Burger sales increased this week.",
    )

    await db_session.commit()

    memories = await service.list_memories(
        restaurant_id=restaurant.id,
    )

    assert len(memories) == 2


@pytest.mark.anyio
async def test_service_updates_memory(db_session):
    restaurant = await create_restaurant(db_session)

    repository = RestaurantMemoryRepository(db_session)
    service = RestaurantMemoryService(repository)

    memory = await service.create_memory(
        restaurant_id=restaurant.id,
        memory_type="equipment",
        title="Freezer issue",
        description="Freezer temperature increased.",
    )

    await db_session.commit()

    updated = await service.update_memory(
        memory,
        title="Freezer #1 issue",
        importance="critical",
        tags="freezer,equipment",
    )

    await db_session.commit()

    assert updated.title == "Freezer #1 issue"
    assert updated.importance == "critical"
    assert updated.tags == "freezer,equipment"


@pytest.mark.anyio
async def test_service_deletes_memory(db_session):
    restaurant = await create_restaurant(db_session)

    repository = RestaurantMemoryRepository(db_session)
    service = RestaurantMemoryService(repository)

    memory = await service.create_memory(
        restaurant_id=restaurant.id,
        memory_type="waste",
        title="Food waste increased",
        description="Waste increased this week.",
    )

    memory_id = memory.id

    await db_session.commit()

    await service.delete_memory(memory)
    await db_session.commit()

    found = await service.get_memory(
        restaurant_id=restaurant.id,
        memory_id=memory_id,
    )

    assert found is None