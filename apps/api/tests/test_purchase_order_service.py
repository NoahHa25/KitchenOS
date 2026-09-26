from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.purchase_order import PurchaseOrderStatus
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
)
from app.services.purchase_order_service import PurchaseOrderService


class FakeDB:
    def __init__(self):
        self.commit_count = 0
        self.rollback_count = 0
        self.flush_count = 0

    async def commit(self):
        self.commit_count += 1

    async def rollback(self):
        self.rollback_count += 1

    async def flush(self):
        self.flush_count += 1


class FakeSupplier:
    def __init__(
        self,
        supplier_id,
        restaurant_id,
        name="Fresh Foods",
    ):
        self.id = supplier_id
        self.restaurant_id = restaurant_id
        self.name = name


class FakeIngredient:
    def __init__(
        self,
        ingredient_id,
        restaurant_id,
        name="Tomatoes",
        current_stock=Decimal("10"),
        cost_per_unit=Decimal("2.00"),
    ):
        self.id = ingredient_id
        self.restaurant_id = restaurant_id
        self.name = name
        self.current_stock = Decimal(str(current_stock))
        self.cost_per_unit = Decimal(str(cost_per_unit))


class FakePurchaseOrderItem:
    def __init__(
        self,
        item_id,
        purchase_order_id,
        ingredient_id,
        quantity,
        unit_cost,
        total_cost,
    ):
        self.id = item_id
        self.purchase_order_id = purchase_order_id
        self.ingredient_id = ingredient_id
        self.quantity = Decimal(str(quantity))
        self.unit_cost = Decimal(str(unit_cost))
        self.total_cost = Decimal(str(total_cost))


class FakePurchaseOrder:
    def __init__(
        self,
        purchase_order_id,
        restaurant_id,
        supplier_id,
        status=PurchaseOrderStatus.DRAFT,
        expected_delivery=None,
        notes=None,
    ):
        self.id = purchase_order_id
        self.restaurant_id = restaurant_id
        self.supplier_id = supplier_id
        self.status = status
        self.expected_delivery = expected_delivery
        self.notes = notes
        self.items = []


class FakeSupplierRepository:
    def __init__(self):
        self.db = FakeDB()
        self.suppliers = {}

    async def get_by_id(
        self,
        restaurant_id,
        supplier_id,
    ):
        supplier = self.suppliers.get(supplier_id)

        if supplier is None:
            return None

        if supplier.restaurant_id != restaurant_id:
            return None

        return supplier


class FakeIngredientRepository:
    def __init__(self):
        self.ingredients = {}

    async def get_by_id(
        self,
        restaurant_id,
        ingredient_id,
    ):
        ingredient = self.ingredients.get(ingredient_id)

        if ingredient is None:
            return None

        if ingredient.restaurant_id != restaurant_id:
            return None

        return ingredient


class FakeInventoryMovementRepository:
    def __init__(self, db):
        self.db = db
        self.movements = []
        self.fail_on_create = False

    async def create(
        self,
        ingredient_id,
        movement_type,
        quantity,
        unit_cost,
        reason=None,
    ):
        if self.fail_on_create:
            raise RuntimeError("Inventory movement failed")

        movement = {
            "ingredient_id": ingredient_id,
            "movement_type": movement_type,
            "quantity": Decimal(str(quantity)),
            "unit_cost": Decimal(str(unit_cost)),
            "reason": reason,
        }

        self.movements.append(movement)

        return movement


class FakePurchaseOrderRepository:
    def __init__(self, db):
        self.db = db
        self.purchase_orders = {}

    async def create(
        self,
        restaurant_id,
        supplier_id,
        expected_delivery,
        notes,
    ):
        purchase_order = FakePurchaseOrder(
            purchase_order_id=uuid4(),
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
            expected_delivery=expected_delivery,
            notes=notes,
        )

        self.purchase_orders[purchase_order.id] = purchase_order

        return purchase_order

    async def add_item(
        self,
        purchase_order_id,
        ingredient_id,
        quantity,
        unit_cost,
        total_cost,
    ):
        purchase_order = self.purchase_orders[purchase_order_id]

        item = FakePurchaseOrderItem(
            item_id=uuid4(),
            purchase_order_id=purchase_order_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
        )

        purchase_order.items.append(item)

        return item

    async def get_by_id(
        self,
        restaurant_id,
        purchase_order_id,
    ):
        purchase_order = self.purchase_orders.get(
            purchase_order_id
        )

        if purchase_order is None:
            return None

        if purchase_order.restaurant_id != restaurant_id:
            return None

        return purchase_order

    async def get_all(
        self,
        restaurant_id,
    ):
        return [
            purchase_order
            for purchase_order in self.purchase_orders.values()
            if purchase_order.restaurant_id == restaurant_id
        ]

    async def update_status(
        self,
        purchase_order,
        status,
    ):
        purchase_order.status = status

        await self.db.flush()

        return purchase_order


def create_service():
    db = FakeDB()

    purchase_order_repository = FakePurchaseOrderRepository(db)
    supplier_repository = FakeSupplierRepository()
    ingredient_repository = FakeIngredientRepository()
    inventory_movement_repository = (
        FakeInventoryMovementRepository(db)
    )

    service = PurchaseOrderService(
        purchase_order_repository=purchase_order_repository,
        supplier_repository=supplier_repository,
        ingredient_repository=ingredient_repository,
        inventory_movement_repository=inventory_movement_repository,
    )

    return (
        service,
        db,
        purchase_order_repository,
        supplier_repository,
        ingredient_repository,
        inventory_movement_repository,
    )


def add_supplier(
    repository,
    restaurant_id,
):
    supplier = FakeSupplier(
        supplier_id=uuid4(),
        restaurant_id=restaurant_id,
    )

    repository.suppliers[supplier.id] = supplier

    return supplier


def add_ingredient(
    repository,
    restaurant_id,
    name="Tomatoes",
    current_stock=Decimal("10"),
    cost_per_unit=Decimal("2.00"),
):
    ingredient = FakeIngredient(
        ingredient_id=uuid4(),
        restaurant_id=restaurant_id,
        name=name,
        current_stock=current_stock,
        cost_per_unit=cost_per_unit,
    )

    repository.ingredients[ingredient.id] = ingredient

    return ingredient


def create_purchase_order_data(
    restaurant_id,
    supplier_id,
    ingredient_id,
    quantity="10",
    unit_cost="3.50",
):
    return PurchaseOrderCreate(
        restaurant_id=restaurant_id,
        supplier_id=supplier_id,
        items=[
            PurchaseOrderItemCreate(
                ingredient_id=ingredient_id,
                quantity=Decimal(quantity),
                unit_cost=Decimal(unit_cost),
            )
        ],
    )


@pytest.mark.asyncio
async def test_create_purchase_order():
    (
        service,
        db,
        purchase_order_repository,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    data = create_purchase_order_data(
        restaurant_id=restaurant_id,
        supplier_id=supplier.id,
        ingredient_id=ingredient.id,
        quantity="10",
        unit_cost="3.50",
    )

    purchase_order = await service.create_purchase_order(data)

    assert purchase_order is not None
    assert purchase_order.restaurant_id == restaurant_id
    assert purchase_order.supplier_id == supplier.id
    assert purchase_order.status == PurchaseOrderStatus.DRAFT

    assert len(purchase_order.items) == 1

    item = purchase_order.items[0]

    assert item.ingredient_id == ingredient.id
    assert item.quantity == Decimal("10")
    assert item.unit_cost == Decimal("3.50")
    assert item.total_cost == Decimal("35.00")

    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_create_purchase_order_rejects_missing_supplier():
    (
        service,
        db,
        _,
        _,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    data = create_purchase_order_data(
        restaurant_id=restaurant_id,
        supplier_id=uuid4(),
        ingredient_id=ingredient.id,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_purchase_order(data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Supplier not found"
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_create_purchase_order_rejects_supplier_from_wrong_restaurant():
    (
        service,
        db,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_a = uuid4()
    restaurant_b = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_a,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_b,
    )

    data = create_purchase_order_data(
        restaurant_id=restaurant_b,
        supplier_id=supplier.id,
        ingredient_id=ingredient.id,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_purchase_order(data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Supplier not found"
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_create_purchase_order_rejects_missing_ingredient():
    (
        service,
        db,
        _,
        supplier_repository,
        _,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    data = create_purchase_order_data(
        restaurant_id=restaurant_id,
        supplier_id=supplier.id,
        ingredient_id=uuid4(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_purchase_order(data)

    assert exc_info.value.status_code == 404
    assert "Ingredient not found" in exc_info.value.detail

    assert db.commit_count == 0
    assert db.rollback_count == 1


@pytest.mark.asyncio
async def test_create_purchase_order_rejects_ingredient_from_wrong_restaurant():
    (
        service,
        db,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_a = uuid4()
    restaurant_b = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_a,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_a,
    )

    data = create_purchase_order_data(
        restaurant_id=restaurant_b,
        supplier_id=supplier.id,
        ingredient_id=ingredient.id,
    )

    with pytest.raises(HTTPException):
        await service.create_purchase_order(data)

    assert db.commit_count == 0
    assert db.rollback_count == 0


@pytest.mark.asyncio
async def test_create_purchase_order_rejects_duplicate_ingredients():
    (
        service,
        db,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    data = PurchaseOrderCreate(
        restaurant_id=restaurant_id,
        supplier_id=supplier.id,
        items=[
            PurchaseOrderItemCreate(
                ingredient_id=ingredient.id,
                quantity=Decimal("10"),
                unit_cost=Decimal("3.50"),
            ),
            PurchaseOrderItemCreate(
                ingredient_id=ingredient.id,
                quantity=Decimal("5"),
                unit_cost=Decimal("3.50"),
            ),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_purchase_order(data)

    assert exc_info.value.status_code == 400
    assert "Duplicate ingredient" in exc_info.value.detail

    assert db.commit_count == 0
    assert db.rollback_count == 1


@pytest.mark.asyncio
async def test_list_purchase_orders_is_scoped_to_restaurant():
    (
        service,
        _,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_a = uuid4()
    restaurant_b = uuid4()

    supplier_a = add_supplier(
        supplier_repository,
        restaurant_a,
    )

    supplier_b = add_supplier(
        supplier_repository,
        restaurant_b,
    )

    ingredient_a = add_ingredient(
        ingredient_repository,
        restaurant_a,
    )

    ingredient_b = add_ingredient(
        ingredient_repository,
        restaurant_b,
    )

    await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_a,
            supplier_id=supplier_a.id,
            ingredient_id=ingredient_a.id,
        )
    )

    await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_b,
            supplier_id=supplier_b.id,
            ingredient_id=ingredient_b.id,
        )
    )

    purchase_orders = await service.list_purchase_orders(
        restaurant_id=restaurant_a,
    )

    assert len(purchase_orders) == 1
    assert purchase_orders[0].restaurant_id == restaurant_a


@pytest.mark.asyncio
async def test_get_purchase_order_returns_none_for_wrong_restaurant():
    (
        service,
        _,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_a = uuid4()
    restaurant_b = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_a,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_a,
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_a,
            supplier_id=supplier.id,
            ingredient_id=ingredient.id,
        )
    )

    result = await service.get_purchase_order(
        restaurant_id=restaurant_b,
        purchase_order_id=purchase_order.id,
    )

    assert result is None


@pytest.mark.asyncio
async def test_update_status_draft_to_sent():
    (
        service,
        db,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id,
            supplier.id,
            ingredient.id,
        )
    )

    updated = await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.SENT,
    )

    assert updated.status == PurchaseOrderStatus.SENT
    assert db.commit_count == 2


@pytest.mark.asyncio
async def test_update_status_sent_to_received():
    (
        service,
        _,
        purchase_order_repository,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id,
            supplier.id,
            ingredient.id,
        )
    )

    await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.SENT,
    )

    updated = await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.RECEIVED,
    )

    assert updated.status == PurchaseOrderStatus.RECEIVED


@pytest.mark.asyncio
async def test_update_status_draft_to_cancelled():
    (
        service,
        _,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id,
            supplier.id,
            ingredient.id,
        )
    )

    updated = await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.CANCELLED,
    )

    assert updated.status == PurchaseOrderStatus.CANCELLED


@pytest.mark.asyncio
async def test_update_status_sent_to_cancelled():
    (
        service,
        _,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id,
            supplier.id,
            ingredient.id,
        )
    )

    await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.SENT,
    )

    updated = await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.CANCELLED,
    )

    assert updated.status == PurchaseOrderStatus.CANCELLED


@pytest.mark.asyncio
async def test_invalid_status_transition_is_rejected():
    (
        service,
        db,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id,
            supplier.id,
            ingredient.id,
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_status(
            restaurant_id=restaurant_id,
            purchase_order_id=purchase_order.id,
            new_status=PurchaseOrderStatus.RECEIVED,
        )

    assert exc_info.value.status_code == 400
    assert "Cannot change purchase order status" in (
        exc_info.value.detail
    )

    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_update_status_returns_none_for_nonexistent_purchase_order():
    (
        service,
        _,
        _,
        _,
        _,
        _,
    ) = create_service()

    result = await service.update_status(
        restaurant_id=uuid4(),
        purchase_order_id=uuid4(),
        new_status=PurchaseOrderStatus.SENT,
    )

    assert result is None


@pytest.mark.asyncio
async def test_receive_purchase_order_increases_stock():
    (
        service,
        db,
        _,
        supplier_repository,
        ingredient_repository,
        inventory_movement_repository,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
        current_stock=Decimal("10"),
        cost_per_unit=Decimal("2.00"),
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_id,
            supplier_id=supplier.id,
            ingredient_id=ingredient.id,
            quantity="15",
            unit_cost="3.50",
        )
    )

    await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.SENT,
    )

    received = await service.receive_purchase_order(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
    )

    assert received.status == PurchaseOrderStatus.RECEIVED
    assert ingredient.current_stock == Decimal("25")

    assert db.commit_count == 3
    assert len(inventory_movement_repository.movements) == 1


@pytest.mark.asyncio
async def test_receive_purchase_order_updates_ingredient_cost():
    (
        service,
        _,
        _,
        supplier_repository,
        ingredient_repository,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
        cost_per_unit=Decimal("2.00"),
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_id,
            supplier_id=supplier.id,
            ingredient_id=ingredient.id,
            quantity="10",
            unit_cost="4.25",
        )
    )

    await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.SENT,
    )

    await service.receive_purchase_order(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
    )

    assert ingredient.cost_per_unit == Decimal("4.25")


@pytest.mark.asyncio
async def test_receive_purchase_order_creates_purchase_movement():
    (
        service,
        _,
        _,
        supplier_repository,
        ingredient_repository,
        inventory_movement_repository,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_id,
            supplier_id=supplier.id,
            ingredient_id=ingredient.id,
            quantity="12",
            unit_cost="3.75",
        )
    )

    await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.SENT,
    )

    await service.receive_purchase_order(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
    )

    assert len(inventory_movement_repository.movements) == 1

    movement = inventory_movement_repository.movements[0]

    assert movement["ingredient_id"] == ingredient.id
    assert movement["movement_type"] == "purchase"
    assert movement["quantity"] == Decimal("12")
    assert movement["unit_cost"] == Decimal("3.75")
    assert str(purchase_order.id) in movement["reason"]


@pytest.mark.asyncio
async def test_receive_purchase_order_cannot_be_received_twice():
    (
        service,
        db,
        _,
        supplier_repository,
        ingredient_repository,
        inventory_movement_repository,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
        current_stock=Decimal("10"),
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_id,
            supplier_id=supplier.id,
            ingredient_id=ingredient.id,
            quantity="10",
            unit_cost="3.00",
        )
    )

    await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.SENT,
    )

    await service.receive_purchase_order(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
    )

    stock_after_first_receive = ingredient.current_stock
    movement_count_after_first_receive = len(
        inventory_movement_repository.movements
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.receive_purchase_order(
            restaurant_id=restaurant_id,
            purchase_order_id=purchase_order.id,
        )

    assert exc_info.value.status_code == 400
    assert "Only sent purchase orders can be received" in (
        exc_info.value.detail
    )

    assert ingredient.current_stock == stock_after_first_receive
    assert len(inventory_movement_repository.movements) == (
        movement_count_after_first_receive
    )

    assert db.rollback_count == 0


@pytest.mark.asyncio
async def test_cancelled_purchase_order_cannot_be_received():
    (
        service,
        _,
        _,
        supplier_repository,
        ingredient_repository,
        inventory_movement_repository,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_id,
            supplier_id=supplier.id,
            ingredient_id=ingredient.id,
        )
    )

    await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.CANCELLED,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.receive_purchase_order(
            restaurant_id=restaurant_id,
            purchase_order_id=purchase_order.id,
        )

    assert exc_info.value.status_code == 400
    assert "Only sent purchase orders can be received" in (
        exc_info.value.detail
    )

    assert len(inventory_movement_repository.movements) == 0


@pytest.mark.asyncio
async def test_receive_purchase_order_returns_none_when_not_found():
    (
        service,
        _,
        _,
        _,
        _,
        _,
    ) = create_service()

    result = await service.receive_purchase_order(
        restaurant_id=uuid4(),
        purchase_order_id=uuid4(),
    )

    assert result is None


@pytest.mark.asyncio
async def test_receive_purchase_order_rolls_back_on_inventory_failure():
    (
        service,
        db,
        _,
        supplier_repository,
        ingredient_repository,
        inventory_movement_repository,
    ) = create_service()

    restaurant_id = uuid4()

    supplier = add_supplier(
        supplier_repository,
        restaurant_id,
    )

    ingredient = add_ingredient(
        ingredient_repository,
        restaurant_id,
        current_stock=Decimal("10"),
        cost_per_unit=Decimal("2.00"),
    )

    purchase_order = await service.create_purchase_order(
        create_purchase_order_data(
            restaurant_id=restaurant_id,
            supplier_id=supplier.id,
            ingredient_id=ingredient.id,
            quantity="10",
            unit_cost="5.00",
        )
    )

    await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order.id,
        new_status=PurchaseOrderStatus.SENT,
    )

    inventory_movement_repository.fail_on_create = True

    with pytest.raises(RuntimeError) as exc_info:
        await service.receive_purchase_order(
            restaurant_id=restaurant_id,
            purchase_order_id=purchase_order.id,
        )

    assert str(exc_info.value) == "Inventory movement failed"

    assert db.rollback_count == 1

    assert ingredient.current_stock == Decimal("20")
    assert ingredient.cost_per_unit == Decimal("5.00")

    assert purchase_order.status == PurchaseOrderStatus.SENT

