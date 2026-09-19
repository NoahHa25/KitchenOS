from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.inventory_movement import (
    InventoryMovementCreate,
)
from app.services.inventory_movement_service import (
    InventoryMovementService,
)


# ---------------------------------------------------------------------------
# Fake database
# ---------------------------------------------------------------------------


class FakeDatabase:
    def __init__(self):
        self.commit_called = False
        self.rollback_called = False

    async def commit(self):
        self.commit_called = True

    async def rollback(self):
        self.rollback_called = True

    async def refresh(self, obj):
        return obj


# ---------------------------------------------------------------------------
# Fake repositories
# ---------------------------------------------------------------------------


class FakeIngredientRepository:
    def __init__(
        self,
        ingredient=None,
        db=None,
    ):
        self.ingredient = ingredient
        self.db = db or FakeDatabase()

    async def get_by_id(
        self,
        restaurant_id,
        ingredient_id,
    ):
        if self.ingredient is None:
            return None

        if self.ingredient.id != ingredient_id:
            return None

        if self.ingredient.restaurant_id != restaurant_id:
            return None

        return self.ingredient


class FakeMovementRepository:
    def __init__(
        self,
        movement_should_fail=False,
    ):
        self.movements = []
        self.movement_should_fail = movement_should_fail

    async def create(
        self,
        ingredient_id,
        movement_type,
        quantity,
        unit_cost,
        reason=None,
    ):
        if self.movement_should_fail:
            raise RuntimeError("Database error")

        movement = SimpleNamespace(
            id=uuid4(),
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost,
            reason=reason,
        )

        self.movements.append(movement)

        return movement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_ingredient(
    current_stock="10.00",
    cost_per_unit="2.50",
):
    return SimpleNamespace(
        id=uuid4(),
        restaurant_id=uuid4(),
        name="Flour",
        unit="kg",
        current_stock=Decimal(current_stock),
        minimum_stock=Decimal("1.00"),
        cost_per_unit=Decimal(cost_per_unit),
    )


def make_service(
    ingredient=None,
    ingredient_not_found=False,
    movement_should_fail=False,
):
    db = FakeDatabase()

    if ingredient_not_found:
        ingredient_repository = FakeIngredientRepository(
            ingredient=None,
            db=db,
        )
    else:
        ingredient_repository = FakeIngredientRepository(
            ingredient=ingredient,
            db=db,
        )

    movement_repository = FakeMovementRepository(
        movement_should_fail=movement_should_fail,
    )

    service = InventoryMovementService(
        ingredient_repository=ingredient_repository,
        movement_repository=movement_repository,
    )

    return (
        service,
        db,
        movement_repository,
    )


# ---------------------------------------------------------------------------
# Ingredient not found
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_ingredient_not_found():
    ingredient_id = uuid4()
    restaurant_id = uuid4()

    service, db, movement_repository = make_service(
        ingredient_not_found=True,
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient_id,
        movement_type="purchase",
        quantity=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_movement(
            restaurant_id=restaurant_id,
            data=data,
        )

    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "Ingredient not found"
    )

    assert movement_repository.movements == []
    assert db.rollback_called is True


# ---------------------------------------------------------------------------
# Purchase
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_purchase_increases_stock():
    ingredient = make_ingredient("10.00")

    service, db, movement_repository = make_service(
        ingredient
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="purchase",
        quantity=5,
    )

    await service.create_movement(
        restaurant_id=ingredient.restaurant_id,
        data=data,
    )

    assert ingredient.current_stock == Decimal("15.00")

    assert len(movement_repository.movements) == 1

    movement = movement_repository.movements[0]

    assert movement.ingredient_id == ingredient.id
    assert movement.movement_type == "purchase"
    assert movement.quantity == Decimal("5")
    assert movement.unit_cost == Decimal("2.50")
    assert movement.reason is None

    assert db.commit_called is True


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_usage_decreases_stock():
    ingredient = make_ingredient("10.00")

    service, db, movement_repository = make_service(
        ingredient
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="usage",
        quantity=3,
        reason="Kitchen usage",
    )

    await service.create_movement(
        restaurant_id=ingredient.restaurant_id,
        data=data,
    )

    assert ingredient.current_stock == Decimal("7.00")

    movement = movement_repository.movements[0]

    assert movement.movement_type == "usage"
    assert movement.quantity == Decimal("3")
    assert movement.unit_cost == Decimal("2.50")
    assert movement.reason == "Kitchen usage"

    assert db.commit_called is True


# ---------------------------------------------------------------------------
# Waste
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_waste_decreases_stock():
    ingredient = make_ingredient("10.00")

    service, db, movement_repository = make_service(
        ingredient
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="waste",
        quantity=2,
        reason="Spoiled ingredient",
    )

    await service.create_movement(
        restaurant_id=ingredient.restaurant_id,
        data=data,
    )

    assert ingredient.current_stock == Decimal("8.00")

    movement = movement_repository.movements[0]

    assert movement.movement_type == "waste"
    assert movement.quantity == Decimal("2")
    assert movement.unit_cost == Decimal("2.50")
    assert movement.reason == "Spoiled ingredient"

    assert db.commit_called is True


# ---------------------------------------------------------------------------
# Adjustment
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_adjustment_sets_stock():
    ingredient = make_ingredient("10.00")

    service, db, movement_repository = make_service(
        ingredient
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="adjustment",
        quantity=25,
        reason="Physical stock count",
    )

    await service.create_movement(
        restaurant_id=ingredient.restaurant_id,
        data=data,
    )

    assert ingredient.current_stock == Decimal("25.00")

    movement = movement_repository.movements[0]

    assert movement.movement_type == "adjustment"
    assert movement.quantity == Decimal("25")
    assert movement.unit_cost == Decimal("2.50")
    assert movement.reason == "Physical stock count"

    assert db.commit_called is True


# ---------------------------------------------------------------------------
# Invalid movement type
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_invalid_movement_type():
    ingredient = make_ingredient("10.00")

    service, db, movement_repository = make_service(
        ingredient
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="invalid",
        quantity=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_movement(
            restaurant_id=ingredient.restaurant_id,
            data=data,
        )

    assert exc_info.value.status_code == 400

    assert (
        exc_info.value.detail
        == (
            "Invalid movement type. "
            "Use purchase, usage, waste, or adjustment."
        )
    )

    assert ingredient.current_stock == Decimal("10.00")

    assert movement_repository.movements == []
    assert db.rollback_called is True


# ---------------------------------------------------------------------------
# Insufficient stock
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_usage_rejects_insufficient_stock():
    ingredient = make_ingredient("5.00")

    service, db, movement_repository = make_service(
        ingredient
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="usage",
        quantity=10,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_movement(
            restaurant_id=ingredient.restaurant_id,
            data=data,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Insufficient stock"

    assert ingredient.current_stock == Decimal("5.00")

    assert movement_repository.movements == []
    assert db.rollback_called is True


# ---------------------------------------------------------------------------
# Quantity validation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
@pytest.mark.parametrize(
    "quantity",
    [0, -1],
)
async def test_non_positive_quantity_is_rejected(
    quantity,
):
    ingredient_id = uuid4()

    with pytest.raises(ValidationError):
        InventoryMovementCreate(
            ingredient_id=ingredient_id,
            movement_type="purchase",
            quantity=quantity,
        )


# ---------------------------------------------------------------------------
# Database failure / rollback
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_movement_database_failure_rolls_back():
    ingredient = make_ingredient("10.00")

    service, db, movement_repository = make_service(
        ingredient,
        movement_should_fail=True,
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="purchase",
        quantity=5,
    )

    with pytest.raises(
        RuntimeError,
        match="Database error",
    ):
        await service.create_movement(
            restaurant_id=ingredient.restaurant_id,
            data=data,
        )

    # The fake database records the rollback request,
    # but does not restore the in-memory Python object.
    assert movement_repository.movements == []

    assert db.commit_called is False
    assert db.rollback_called is True