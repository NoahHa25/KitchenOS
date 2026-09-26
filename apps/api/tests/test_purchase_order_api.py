import pytest
from decimal import Decimal
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from app.models.ingredient import Ingredient
from app.models.restaurant import Restaurant
from app.models.supplier import Supplier


@pytest.fixture
async def api_db_session(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield db_session
    finally:
        app.dependency_overrides.clear()


async def create_test_data(db_session):
    restaurant = Restaurant(
        name="Purchase Order API Restaurant",
        slug=f"purchase-order-api-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    supplier = Supplier(
        restaurant_id=restaurant.id,
        name="Test Supplier",
    )

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Chicken",
        unit="kg",
        current_stock=Decimal("10"),
        minimum_stock=Decimal("5"),
        cost_per_unit=Decimal("8.00"),
    )

    db_session.add(supplier)
    db_session.add(ingredient)

    await db_session.flush()

    return restaurant, supplier, ingredient


async def create_purchase_order(
    client,
    restaurant,
    supplier,
    ingredient,
):
    response = await client.post(
        "/purchase-orders",
        json={
            "restaurant_id": str(restaurant.id),
            "supplier_id": str(supplier.id),
            "items": [
                {
                    "ingredient_id": str(ingredient.id),
                    "quantity": "20",
                    "unit_cost": "10.50",
                }
            ],
        },
    )

    return response


@pytest.mark.anyio
async def test_create_purchase_order_api(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == str(restaurant.id)
    assert data["supplier_id"] == str(supplier.id)
    assert data["status"] == "draft"

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["ingredient_id"] == str(ingredient.id)
    assert Decimal(item["quantity"]) == Decimal("20")
    assert Decimal(item["unit_cost"]) == Decimal("10.50")
    assert Decimal(item["total_cost"]) == Decimal("210.00")


@pytest.mark.anyio
async def test_list_purchase_orders_api(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create_response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

        assert create_response.status_code == 201

        response = await client.get(
            "/purchase-orders",
            params={
                "restaurant_id": str(restaurant.id),
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["restaurant_id"] == str(restaurant.id)


@pytest.mark.anyio
async def test_get_purchase_order_api(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create_response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

        purchase_order_id = create_response.json()["id"]

        response = await client.get(
            f"/purchase-orders/{purchase_order_id}",
            params={
                "restaurant_id": str(restaurant.id),
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == purchase_order_id
    assert data["restaurant_id"] == str(restaurant.id)


@pytest.mark.anyio
async def test_get_purchase_order_returns_404_for_wrong_restaurant(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    other_restaurant = Restaurant(
        name="Other Restaurant",
        slug=f"other-restaurant-{uuid4()}",
    )

    api_db_session.add(other_restaurant)
    await api_db_session.flush()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create_response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

        purchase_order_id = create_response.json()["id"]

        response = await client.get(
            f"/purchase-orders/{purchase_order_id}",
            params={
                "restaurant_id": str(other_restaurant.id),
            },
        )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Purchase order not found"


@pytest.mark.anyio
async def test_update_purchase_order_status_api(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create_response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

        purchase_order_id = create_response.json()["id"]

        response = await client.patch(
            f"/purchase-orders/{purchase_order_id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "sent",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == purchase_order_id
    assert data["status"] == "sent"


@pytest.mark.anyio
async def test_invalid_purchase_order_status_transition_api(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create_response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

        purchase_order_id = create_response.json()["id"]

        response = await client.patch(
            f"/purchase-orders/{purchase_order_id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "received",
            },
        )

    assert response.status_code == 400

    data = response.json()

    assert "Cannot change purchase order status" in data["detail"]


@pytest.mark.anyio
async def test_update_nonexistent_purchase_order_status_api(
    api_db_session,
):
    restaurant, _, _ = await create_test_data(
        api_db_session,
    )

    nonexistent_purchase_order_id = uuid4()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.patch(
            f"/purchase-orders/{nonexistent_purchase_order_id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "sent",
            },
        )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Purchase order not found"


@pytest.mark.anyio
async def test_receive_purchase_order_api(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    initial_stock = Decimal(str(ingredient.current_stock))

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create_response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

        purchase_order_id = create_response.json()["id"]

        send_response = await client.patch(
            f"/purchase-orders/{purchase_order_id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "sent",
            },
        )

        assert send_response.status_code == 200

        response = await client.post(
            f"/purchase-orders/{purchase_order_id}/receive",
            params={
                "restaurant_id": str(restaurant.id),
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == purchase_order_id
    assert data["status"] == "received"

    await api_db_session.refresh(ingredient)

    assert Decimal(str(ingredient.current_stock)) == (
        initial_stock + Decimal("20")
    )

    assert Decimal(str(ingredient.cost_per_unit)) == Decimal("10.50")


@pytest.mark.anyio
async def test_receive_purchase_order_cannot_be_received_twice(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create_response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

        purchase_order_id = create_response.json()["id"]

        await client.patch(
            f"/purchase-orders/{purchase_order_id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "sent",
            },
        )

        first_receive = await client.post(
            f"/purchase-orders/{purchase_order_id}/receive",
            params={
                "restaurant_id": str(restaurant.id),
            },
        )

        second_receive = await client.post(
            f"/purchase-orders/{purchase_order_id}/receive",
            params={
                "restaurant_id": str(restaurant.id),
            },
        )

    assert first_receive.status_code == 200
    assert second_receive.status_code == 400

    data = second_receive.json()

    assert data["detail"] == (
        "Only sent purchase orders can be received"
    )


@pytest.mark.anyio
async def test_cancelled_purchase_order_cannot_be_received_api(
    api_db_session,
):
    restaurant, supplier, ingredient = await create_test_data(
        api_db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create_response = await create_purchase_order(
            client,
            restaurant,
            supplier,
            ingredient,
        )

        purchase_order_id = create_response.json()["id"]

        cancel_response = await client.patch(
            f"/purchase-orders/{purchase_order_id}/status",
            params={
                "restaurant_id": str(restaurant.id),
            },
            json={
                "status": "cancelled",
            },
        )

        assert cancel_response.status_code == 200

        response = await client.post(
            f"/purchase-orders/{purchase_order_id}/receive",
            params={
                "restaurant_id": str(restaurant.id),
            },
        )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == (
        "Only sent purchase orders can be received"
    )