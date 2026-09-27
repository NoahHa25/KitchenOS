from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.ingredient import Ingredient
from app.models.inventory_movement import InventoryMovement
from app.models.restaurant import Restaurant
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)


@pytest.mark.anyio
async def test_get_restaurant_movements_returns_only_restaurant_movements(
    db_session,
):
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

    ingredient_a = Ingredient(
        restaurant_id=restaurant_a.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    ingredient_b = Ingredient(
        restaurant_id=restaurant_b.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add_all([ingredient_a, ingredient_b])
    await db_session.flush()

    movement_a = InventoryMovement(
        ingredient_id=ingredient_a.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        unit_cost=Decimal("2.50"),
        reason="Restaurant A waste",
    )

    movement_b = InventoryMovement(
        ingredient_id=ingredient_b.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        unit_cost=Decimal("2.50"),
        reason="Restaurant B waste",
    )

    db_session.add_all([movement_a, movement_b])
    await db_session.flush()

    repository = InventoryMovementRepository(db_session)

    movements = await repository.get_restaurant_movements(
        restaurant_id=restaurant_a.id,
    )

    assert len(movements) == 1
    assert movements[0].ingredient_id == ingredient_a.id
    assert movements[0].ingredient.restaurant_id == restaurant_a.id


@pytest.mark.anyio
async def test_get_restaurant_movements_filters_by_movement_type(
    db_session,
):
    restaurant = Restaurant(
        name="Movement Type Restaurant",
        slug=f"movement-type-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    waste = InventoryMovement(
        ingredient_id=ingredient.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        unit_cost=Decimal("2.50"),
        reason="Spoilage",
    )

    purchase = InventoryMovement(
        ingredient_id=ingredient.id,
        movement_type="purchase",
        quantity=Decimal("10.000"),
        unit_cost=Decimal("2.50"),
        reason="Supplier delivery",
    )

    db_session.add_all([waste, purchase])
    await db_session.flush()

    repository = InventoryMovementRepository(db_session)

    movements = await repository.get_restaurant_movements(
        restaurant_id=restaurant.id,
        movement_type="waste",
    )

    assert len(movements) == 1
    assert movements[0].movement_type == "waste"


@pytest.mark.anyio
async def test_get_restaurant_movements_filters_by_created_after(
    db_session,
):
    restaurant = Restaurant(
        name="Date Filter Restaurant",
        slug=f"date-filter-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    now = datetime.now(timezone.utc)

    old_movement = InventoryMovement(
        ingredient_id=ingredient.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        unit_cost=Decimal("2.50"),
        reason="Old waste",
        created_at=now - timedelta(days=60),
    )

    recent_movement = InventoryMovement(
        ingredient_id=ingredient.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        unit_cost=Decimal("2.50"),
        reason="Recent waste",
        created_at=now - timedelta(days=5),
    )

    db_session.add_all([old_movement, recent_movement])
    await db_session.flush()

    repository = InventoryMovementRepository(db_session)

    movements = await repository.get_restaurant_movements(
        restaurant_id=restaurant.id,
        created_after=now - timedelta(days=30),
    )

    assert len(movements) == 1
    assert movements[0].reason == "Recent waste"


@pytest.mark.anyio
async def test_get_restaurant_movements_combines_all_filters(
    db_session,
):
    restaurant = Restaurant(
        name="Combined Filter Restaurant",
        slug=f"combined-filter-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    now = datetime.now(timezone.utc)

    old_waste = InventoryMovement(
        ingredient_id=ingredient.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        unit_cost=Decimal("2.50"),
        reason="Old waste",
        created_at=now - timedelta(days=60),
    )

    recent_waste = InventoryMovement(
        ingredient_id=ingredient.id,
        movement_type="waste",
        quantity=Decimal("1.000"),
        unit_cost=Decimal("2.50"),
        reason="Recent waste",
        created_at=now - timedelta(days=5),
    )

    recent_purchase = InventoryMovement(
        ingredient_id=ingredient.id,
        movement_type="purchase",
        quantity=Decimal("10.000"),
        unit_cost=Decimal("2.50"),
        reason="Recent purchase",
        created_at=now - timedelta(days=5),
    )

    db_session.add_all(
        [
            old_waste,
            recent_waste,
            recent_purchase,
        ]
    )

    await db_session.flush()

    repository = InventoryMovementRepository(db_session)

    movements = await repository.get_restaurant_movements(
        restaurant_id=restaurant.id,
        movement_type="waste",
        created_after=now - timedelta(days=30),
    )

    assert len(movements) == 1
    assert movements[0].reason == "Recent waste"
    assert movements[0].movement_type == "waste"