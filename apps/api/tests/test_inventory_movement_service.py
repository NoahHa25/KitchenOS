from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.inventory_movement import InventoryMovementCreate
from app.services.inventory_movement_service import (
    InventoryMovementService,
)


class FakeDB:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def refresh(self, obj):
        return None


class FakeIngredientRepository:
    def __init__(self, ingredient=None, db=None):
        self.ingredient = ingredient
        self.db = db or FakeDB()

    async def get_by_id(self, restaurant_id, ingredient_id):
        return self.ingredient


class FakeMovementRepository:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.created = None

    async def create(
        self,
        ingredient_id,
        movement_type,
        quantity,
        reason=None,
    ):
        if self.should_fail:
            raise RuntimeError("Database error")

        self.created = SimpleNamespace(
            id=uuid4(),
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
        )

        return self.created


def make_ingredient(stock="10.00"):
    return SimpleNamespace(
        id=uuid4(),
        current_stock=Decimal(stock),
    )


def make_service(
    ingredient,
    movement_should_fail=False,
):
    db = FakeDB()

    ingredient_repository = FakeIngredientRepository(
        ingredient=ingredient,
        db=db,
    )

    movement_repository = FakeMovementRepository(
        should_fail=movement_should_fail,
    )

    service = InventoryMovementService(
        movement_repository=movement_repository,
        ingredient_repository=ingredient_repository,
    )

    return service, db, movement_repository


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
        reason="Supplier delivery",
    )

    await service.create_movement(
        restaurant_id=uuid4(),
        data=data,
    )

    assert ingredient.current_stock == Decimal("15.00")
    assert movement_repository.created.movement_type == "purchase"
    assert movement_repository.created.quantity == 5.0
    assert db.committed is True


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
        restaurant_id=uuid4(),
        data=data,
    )

    assert ingredient.current_stock == Decimal("7.00")
    assert movement_repository.created.movement_type == "usage"
    assert db.committed is True


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
        restaurant_id=uuid4(),
        data=data,
    )

    assert ingredient.current_stock == Decimal("8.00")
    assert movement_repository.created.movement_type == "waste"
    assert db.committed is True


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
        restaurant_id=uuid4(),
        data=data,
    )

    assert ingredient.current_stock == Decimal("25.00")
    assert movement_repository.created.movement_type == "adjustment"
    assert db.committed is True


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
            restaurant_id=uuid4(),
            data=data,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Insufficient stock"
    assert ingredient.current_stock == Decimal("5.00")
    assert movement_repository.created is None
    assert db.rolled_back is True
    assert db.committed is False


@pytest.mark.anyio
async def test_invalid_movement_type_is_rejected():
    ingredient = make_ingredient("10.00")

    service, db, movement_repository = make_service(
        ingredient
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="something_invalid",
        quantity=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_movement(
            restaurant_id=uuid4(),
            data=data,
        )

    assert exc_info.value.status_code == 400
    assert ingredient.current_stock == Decimal("10.00")
    assert movement_repository.created is None
    assert db.rolled_back is True
    assert db.committed is False


@pytest.mark.anyio
@pytest.mark.parametrize("quantity", [0, -1])
async def test_non_positive_quantity_is_rejected(quantity):
    ingredient = make_ingredient("10.00")

    service, db, movement_repository = make_service(
        ingredient
    )

    data = InventoryMovementCreate(
        ingredient_id=ingredient.id,
        movement_type="purchase",
        quantity=quantity,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_movement(
            restaurant_id=uuid4(),
            data=data,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Quantity must be greater than 0"
    assert ingredient.current_stock == Decimal("10.00")
    assert movement_repository.created is None
    assert db.rolled_back is True
    assert db.committed is False


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

    with pytest.raises(RuntimeError, match="Database error"):
        await service.create_movement(
            restaurant_id=uuid4(),
            data=data,
        )

    assert ingredient.current_stock == Decimal("15.00")
    assert db.rolled_back is True
    assert db.committed is False

