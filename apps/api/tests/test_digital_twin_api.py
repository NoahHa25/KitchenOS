from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.ingredient import Ingredient
from app.models.order import Order
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.restaurant import Restaurant
from app.models.restaurant_insight import RestaurantInsight
from app.models.restaurant_memory import RestaurantMemory
from app.models.supplier import Supplier


async def create_restaurant(
    db_session,
    name: str,
    slug: str,
) -> Restaurant:
    restaurant = Restaurant(
        name=name,
        slug=slug,
    )

    db_session.add(restaurant)
    await db_session.flush()

    return restaurant


async def create_supplier(
    db_session,
    restaurant_id,
    name: str,
) -> Supplier:
    supplier = Supplier(
        restaurant_id=restaurant_id,
        name=name,
    )

    db_session.add(supplier)
    await db_session.flush()

    return supplier


@pytest.mark.anyio
async def test_get_digital_twin_api_returns_complete_state(
    db_session,
):
    restaurant = await create_restaurant(
        db_session,
        name="Digital Twin Restaurant",
        slug=f"digital-twin-{uuid4()}",
    )

    supplier = await create_supplier(
        db_session,
        restaurant_id=restaurant.id,
        name="Test Supplier",
    )

    db_session.add_all(
        [
            Order(
                restaurant_id=restaurant.id,
                status="pending",
                total_amount=Decimal("25.00"),
            ),
            Order(
                restaurant_id=restaurant.id,
                status="preparing",
                total_amount=Decimal("30.00"),
            ),
            Ingredient(
                restaurant_id=restaurant.id,
                name="Tomato",
                unit="kg",
                current_stock=2,
                minimum_stock=5,
                cost_per_unit=Decimal("4.00"),
            ),
            Ingredient(
                restaurant_id=restaurant.id,
                name="Flour",
                unit="kg",
                current_stock=10,
                minimum_stock=5,
                cost_per_unit=Decimal("2.00"),
            ),
            RestaurantMemory(
                restaurant_id=restaurant.id,
                memory_type="equipment",
                title="Oven issue",
                description="Oven #2 stopped heating.",
                importance="high",
            ),
            RestaurantInsight(
                restaurant_id=restaurant.id,
                insight_type="waste",
                title="Repeated tomato waste",
                description="Tomato waste is recurring.",
                severity="medium",
                confidence="high",
                status="active",
            ),
        ]
    )

    db_session.add(
        PurchaseOrder(
            restaurant_id=restaurant.id,
            supplier_id=supplier.id,
            status=PurchaseOrderStatus.DRAFT,
        )
    )

    await db_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/restaurants/{restaurant.id}/digital-twin",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == str(restaurant.id)

    assert "generated_at" in data

    assert data["operations"]["open_orders"] == 2
    assert data["operations"]["orders_today"] == 2

    assert data["sales"]["revenue_today"] == "0.00"
    assert data["sales"]["completed_orders_today"] == 0

    assert data["inventory"]["ingredient_count"] == 2
    assert data["inventory"]["low_stock_count"] == 1
    assert data["inventory"]["inventory_value"] == "28.00"

    assert data["purchasing"]["draft_orders"] == 1
    assert data["purchasing"]["sent_orders"] == 0
    assert data["purchasing"]["pending_orders"] == 1

    assert data["intelligence"]["active_memories"] == 1
    assert data["intelligence"]["active_insights"] == 1


@pytest.mark.anyio
async def test_get_digital_twin_api_returns_zero_state(
    db_session,
):
    restaurant = await create_restaurant(
        db_session,
        name="Empty Digital Twin Restaurant",
        slug=f"empty-twin-{uuid4()}",
    )

    await db_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/restaurants/{restaurant.id}/digital-twin",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == str(restaurant.id)

    assert data["operations"]["open_orders"] == 0
    assert data["operations"]["orders_today"] == 0

    assert data["sales"]["revenue_today"] == "0.00"
    assert data["sales"]["completed_orders_today"] == 0

    assert data["inventory"]["ingredient_count"] == 0
    assert data["inventory"]["low_stock_count"] == 0
    assert data["inventory"]["inventory_value"] == "0.00"

    assert data["purchasing"]["draft_orders"] == 0
    assert data["purchasing"]["sent_orders"] == 0
    assert data["purchasing"]["pending_orders"] == 0

    assert data["intelligence"]["active_memories"] == 0
    assert data["intelligence"]["active_insights"] == 0


@pytest.mark.anyio
async def test_get_digital_twin_api_is_scoped_to_restaurant(
    db_session,
):
    restaurant = await create_restaurant(
        db_session,
        name="Primary Digital Twin Restaurant",
        slug=f"primary-twin-{uuid4()}",
    )

    another_restaurant = await create_restaurant(
        db_session,
        name="Another Digital Twin Restaurant",
        slug=f"another-twin-{uuid4()}",
    )

    db_session.add_all(
        [
            Order(
                restaurant_id=restaurant.id,
                status="pending",
                total_amount=Decimal("50.00"),
            ),
            Ingredient(
                restaurant_id=restaurant.id,
                name="Tomato",
                unit="kg",
                current_stock=5,
                minimum_stock=2,
                cost_per_unit=Decimal("3.00"),
            ),
            Order(
                restaurant_id=another_restaurant.id,
                status="pending",
                total_amount=Decimal("999.00"),
            ),
            Ingredient(
                restaurant_id=another_restaurant.id,
                name="Flour",
                unit="kg",
                current_stock=100,
                minimum_stock=10,
                cost_per_unit=Decimal("20.00"),
            ),
        ]
    )

    await db_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/restaurants/{restaurant.id}/digital-twin",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == str(restaurant.id)

    assert data["operations"]["open_orders"] == 1
    assert data["inventory"]["ingredient_count"] == 1
    assert data["inventory"]["inventory_value"] == "15.00"