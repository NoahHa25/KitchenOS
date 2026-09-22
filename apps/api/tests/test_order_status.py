import pytest
from uuid import uuid4

from app.models.order import Order
from app.models.restaurant import Restaurant
from app.repositories.order_repository import OrderRepository
from app.services.order_service import OrderService


def build_order_service(db_session):
    return OrderService(
        order_repository=OrderRepository(db_session),
        order_item_repository=None,
        recipe_repository=None,
        recipe_ingredient_repository=None,
        ingredient_repository=None,
        inventory_movement_repository=None,
    )


async def create_test_order(db_session, status="pending"):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
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
async def test_pending_to_preparing(db_session):
    restaurant, order = await create_test_order(
        db_session,
        "pending",
    )

    service = build_order_service(db_session)

    updated_order = await service.update_status(
        restaurant_id=restaurant.id,
        order_id=order.id,
        new_status="preparing",
    )

    assert updated_order is not None
    assert updated_order.status == "preparing"


@pytest.mark.anyio
async def test_preparing_to_ready(db_session):
    restaurant, order = await create_test_order(
        db_session,
        "preparing",
    )

    service = build_order_service(db_session)

    updated_order = await service.update_status(
        restaurant_id=restaurant.id,
        order_id=order.id,
        new_status="ready",
    )

    assert updated_order is not None
    assert updated_order.status == "ready"


@pytest.mark.anyio
async def test_ready_to_completed(db_session):
    restaurant, order = await create_test_order(
        db_session,
        "ready",
    )

    service = build_order_service(db_session)

    updated_order = await service.update_status(
        restaurant_id=restaurant.id,
        order_id=order.id,
        new_status="completed",
    )

    assert updated_order is not None
    assert updated_order.status == "completed"


@pytest.mark.anyio
async def test_pending_to_cancelled(db_session):
    restaurant, order = await create_test_order(
        db_session,
        "pending",
    )

    service = build_order_service(db_session)

    updated_order = await service.update_status(
        restaurant_id=restaurant.id,
        order_id=order.id,
        new_status="cancelled",
    )

    assert updated_order is not None
    assert updated_order.status == "cancelled"


@pytest.mark.anyio
async def test_preparing_to_cancelled(db_session):
    restaurant, order = await create_test_order(
        db_session,
        "preparing",
    )

    service = build_order_service(db_session)

    updated_order = await service.update_status(
        restaurant_id=restaurant.id,
        order_id=order.id,
        new_status="cancelled",
    )

    assert updated_order is not None
    assert updated_order.status == "cancelled"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "current_status,new_status",
    [
        ("pending", "ready"),
        ("pending", "completed"),
        ("preparing", "completed"),
        ("preparing", "pending"),
        ("ready", "pending"),
        ("ready", "preparing"),
        ("completed", "preparing"),
        ("completed", "cancelled"),
        ("cancelled", "preparing"),
        ("cancelled", "pending"),
    ],
)
async def test_invalid_status_transitions(
    db_session,
    current_status,
    new_status,
):
    restaurant, order = await create_test_order(
        db_session,
        current_status,
    )

    service = build_order_service(db_session)

    with pytest.raises(ValueError):
        await service.update_status(
            restaurant_id=restaurant.id,
            order_id=order.id,
            new_status=new_status,
        )


@pytest.mark.anyio
async def test_invalid_status_value(db_session):
    restaurant, order = await create_test_order(
        db_session,
        "pending",
    )

    service = build_order_service(db_session)

    with pytest.raises(ValueError, match="Invalid order status"):
        await service.update_status(
            restaurant_id=restaurant.id,
            order_id=order.id,
            new_status="banana",
        )


@pytest.mark.anyio
async def test_nonexistent_order_returns_none(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug=f"test-restaurant-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    service = build_order_service(db_session)

    result = await service.update_status(
        restaurant_id=restaurant.id,
        order_id=uuid4(),
        new_status="preparing",
    )

    assert result is None