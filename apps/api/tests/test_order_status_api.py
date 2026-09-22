import pytest
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from app.models.order import Order
from app.models.restaurant import Restaurant


@pytest.fixture
async def api_db_session(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield db_session
    finally:
        app.dependency_overrides.clear()


async def create_test_order(db_session, status="pending"):
    restaurant = Restaurant(
        name="API Test Restaurant",
        slug=f"api-test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    order = Order(
        restaurant_id=restaurant.id,
        status=status,
        total_amount=100,
    )

    db_session.add(order)
    await db_session.flush()

    return restaurant, order


@pytest.mark.anyio
async def test_update_order_status_api(
    api_db_session,
):
    restaurant, order = await create_test_order(
        api_db_session,
        "pending",
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.patch(
            f"/orders/{order.id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "preparing",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(order.id)
    assert data["restaurant_id"] == str(restaurant.id)
    assert data["status"] == "preparing"


@pytest.mark.anyio
async def test_invalid_order_status_transition_api(
    api_db_session,
):
    restaurant, order = await create_test_order(
        api_db_session,
        "pending",
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.patch(
            f"/orders/{order.id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "completed",
            },
        )

    assert response.status_code == 400

    data = response.json()

    assert "Cannot change order status" in data["detail"]


@pytest.mark.anyio
async def test_update_nonexistent_order_status_api(
    api_db_session,
):
    restaurant = Restaurant(
        name="API Test Restaurant",
        slug=f"api-test-restaurant-{uuid4()}",
    )

    api_db_session.add(restaurant)
    await api_db_session.flush()

    nonexistent_order_id = uuid4()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.patch(
            f"/orders/{nonexistent_order_id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "preparing",
            },
        )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Order not found"