from uuid import uuid4

import pytest

from app.models.restaurant import Restaurant
from app.repositories.restaurant_memory import RestaurantMemoryRepository


async def create_restaurant(db_session, name: str, slug: str) -> Restaurant:
    restaurant = Restaurant(
        name=name,
        slug=slug,
    )

    db_session.add(restaurant)
    await db_session.flush()

    return restaurant


@pytest.mark.anyio
async def test_create_memory(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Memory Test Restaurant",
        slug=f"memory-test-{uuid4()}",
    )

    repository = RestaurantMemoryRepository(db_session)

    memory = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="equipment",
        title="Oven #2 broke",
        description="Oven #2 stopped heating during dinner service.",
        importance="high",
        tags="oven,equipment,breakdown",
    )

    await db_session.commit()

    assert memory.id is not None
    assert memory.restaurant_id == restaurant.id
    assert memory.memory_type == "equipment"
    assert memory.title == "Oven #2 broke"
    assert memory.description == "Oven #2 stopped heating during dinner service."
    assert memory.importance == "high"
    assert memory.tags == "oven,equipment,breakdown"
    assert memory.created_at is not None
    assert memory.resolved_at is None


@pytest.mark.anyio
async def test_get_memory_by_id_is_scoped_to_restaurant(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Primary Restaurant",
        slug=f"primary-{uuid4()}",
    )

    another_restaurant = await create_restaurant(
        db_session,
        name="Another Restaurant",
        slug=f"another-{uuid4()}",
    )

    repository = RestaurantMemoryRepository(db_session)

    memory = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="supplier",
        title="Supplier delivered late",
        description="Vegetable delivery arrived two hours late.",
    )

    await db_session.commit()

    found = await repository.get_by_id(
        restaurant_id=restaurant.id,
        memory_id=memory.id,
    )

    not_found = await repository.get_by_id(
        restaurant_id=another_restaurant.id,
        memory_id=memory.id,
    )

    assert found is not None
    assert found.id == memory.id
    assert not_found is None


@pytest.mark.anyio
async def test_list_memories_is_scoped_to_restaurant(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Primary Restaurant",
        slug=f"primary-list-{uuid4()}",
    )

    another_restaurant = await create_restaurant(
        db_session,
        name="Another Restaurant",
        slug=f"another-list-{uuid4()}",
    )

    repository = RestaurantMemoryRepository(db_session)

    first = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="inventory",
        title="Tomatoes running low",
        description="Tomato stock dropped below the minimum level.",
    )

    second = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="sales",
        title="Burger sales increased",
        description="Burger sales increased significantly this week.",
    )

    other = await repository.create(
        restaurant_id=another_restaurant.id,
        memory_type="inventory",
        title="Flour running low",
        description="Flour stock dropped below the minimum level.",
    )

    await db_session.commit()

    memories = await repository.list(
        restaurant_id=restaurant.id,
    )

    memory_ids = {memory.id for memory in memories}

    assert first.id in memory_ids
    assert second.id in memory_ids
    assert other.id not in memory_ids


@pytest.mark.anyio
async def test_update_memory(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Update Test Restaurant",
        slug=f"update-{uuid4()}",
    )

    repository = RestaurantMemoryRepository(db_session)

    memory = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="equipment",
        title="Freezer issue",
        description="Freezer temperature increased.",
        importance="medium",
    )

    await db_session.commit()

    updated = await repository.update(
        memory,
        title="Freezer #1 issue",
        description="Freezer #1 temperature increased repeatedly.",
        importance="high",
        tags="freezer,equipment",
    )

    await db_session.commit()

    assert updated.title == "Freezer #1 issue"
    assert updated.description == "Freezer #1 temperature increased repeatedly."
    assert updated.importance == "high"
    assert updated.tags == "freezer,equipment"


@pytest.mark.anyio
async def test_delete_memory(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Delete Test Restaurant",
        slug=f"delete-{uuid4()}",
    )

    repository = RestaurantMemoryRepository(db_session)

    memory = await repository.create(
        restaurant_id=restaurant.id,
        memory_type="waste",
        title="High food waste",
        description="Food waste increased this week.",
    )

    memory_id = memory.id

    await db_session.commit()

    await repository.delete(memory)
    await db_session.commit()

    deleted = await repository.get_by_id(
        restaurant_id=restaurant.id,
        memory_id=memory_id,
    )

    assert deleted is None