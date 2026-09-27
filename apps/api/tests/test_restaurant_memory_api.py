from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.restaurant import Restaurant


async def create_restaurant(db_session, name: str, slug: str) -> Restaurant:
    restaurant = Restaurant(
        name=name,
        slug=slug,
    )

    db_session.add(restaurant)
    await db_session.flush()

    return restaurant


@pytest.mark.anyio
async def test_create_memory_api(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="API Test Restaurant",
        slug=f"api-test-{uuid4()}",
    )

    await db_session.commit()

    payload = {
        "memory_type": "equipment",
        "title": "Oven #2 broke",
        "description": "Oven #2 stopped heating during dinner service.",
        "importance": "high",
        "tags": "oven,equipment,breakdown",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/memories",
            params={"restaurant_id": str(restaurant.id)},
            json=payload,
        )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == str(restaurant.id)
    assert data["memory_type"] == "equipment"
    assert data["title"] == "Oven #2 broke"
    assert data["description"] == (
        "Oven #2 stopped heating during dinner service."
    )
    assert data["importance"] == "high"
    assert data["tags"] == "oven,equipment,breakdown"
    assert data["resolved_at"] is None


@pytest.mark.anyio
async def test_list_memories_api_is_scoped_to_restaurant(db_session):
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

    await db_session.commit()

    create_payload = {
        "memory_type": "inventory",
        "title": "Tomatoes running low",
        "description": "Tomato stock dropped below the minimum level.",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first_response = await client.post(
            "/memories",
            params={"restaurant_id": str(restaurant.id)},
            json=create_payload,
        )

        second_response = await client.post(
            "/memories",
            params={"restaurant_id": str(another_restaurant.id)},
            json={
                "memory_type": "inventory",
                "title": "Flour running low",
                "description": "Flour stock dropped below the minimum level.",
            },
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 201

        response = await client.get(
            "/memories",
            params={"restaurant_id": str(restaurant.id)},
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["restaurant_id"] == str(restaurant.id)
    assert data[0]["title"] == "Tomatoes running low"


@pytest.mark.anyio
async def test_get_memory_api(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Get Test Restaurant",
        slug=f"get-{uuid4()}",
    )

    await db_session.commit()

    payload = {
        "memory_type": "supplier",
        "title": "Supplier delivered late",
        "description": "Vegetable delivery arrived two hours late.",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/memories",
            params={"restaurant_id": str(restaurant.id)},
            json=payload,
        )

        assert create_response.status_code == 201

        memory_id = create_response.json()["id"]

        response = await client.get(
            f"/memories/{memory_id}",
            params={"restaurant_id": str(restaurant.id)},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == memory_id
    assert data["title"] == "Supplier delivered late"


@pytest.mark.anyio
async def test_get_memory_api_returns_404_for_wrong_restaurant(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Owner Restaurant",
        slug=f"owner-{uuid4()}",
    )

    another_restaurant = await create_restaurant(
        db_session,
        name="Other Restaurant",
        slug=f"other-{uuid4()}",
    )

    await db_session.commit()

    payload = {
        "memory_type": "equipment",
        "title": "Freezer issue",
        "description": "Freezer temperature increased.",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/memories",
            params={"restaurant_id": str(restaurant.id)},
            json=payload,
        )

        assert create_response.status_code == 201

        memory_id = create_response.json()["id"]

        response = await client.get(
            f"/memories/{memory_id}",
            params={"restaurant_id": str(another_restaurant.id)},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant memory not found"


@pytest.mark.anyio
async def test_update_memory_api(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Update API Restaurant",
        slug=f"update-api-{uuid4()}",
    )

    await db_session.commit()

    create_payload = {
        "memory_type": "equipment",
        "title": "Freezer issue",
        "description": "Freezer temperature increased.",
        "importance": "medium",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/memories",
            params={"restaurant_id": str(restaurant.id)},
            json=create_payload,
        )

        assert create_response.status_code == 201

        memory_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/memories/{memory_id}",
            params={"restaurant_id": str(restaurant.id)},
            json={
                "title": "Freezer #1 issue",
                "description": "Freezer #1 temperature increased repeatedly.",
                "importance": "high",
                "tags": "freezer,equipment",
            },
        )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["title"] == "Freezer #1 issue"
    assert data["description"] == (
        "Freezer #1 temperature increased repeatedly."
    )
    assert data["importance"] == "high"
    assert data["tags"] == "freezer,equipment"


@pytest.mark.anyio
async def test_delete_memory_api(db_session):
    restaurant = await create_restaurant(
        db_session,
        name="Delete API Restaurant",
        slug=f"delete-api-{uuid4()}",
    )

    await db_session.commit()

    payload = {
        "memory_type": "waste",
        "title": "High food waste",
        "description": "Food waste increased this week.",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/memories",
            params={"restaurant_id": str(restaurant.id)},
            json=payload,
        )

        assert create_response.status_code == 201

        memory_id = create_response.json()["id"]

        delete_response = await client.delete(
            f"/memories/{memory_id}",
            params={"restaurant_id": str(restaurant.id)},
        )

        assert delete_response.status_code == 204

        get_response = await client.get(
            f"/memories/{memory_id}",
            params={"restaurant_id": str(restaurant.id)},
        )

    assert get_response.status_code == 404