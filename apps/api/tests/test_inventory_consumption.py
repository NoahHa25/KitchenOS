from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.inventory_consumption_service import (
    InventoryConsumptionService,
)
from app.services.order_service import OrderService


# ---------------------------------------------------------------------------
# Fake database
# ---------------------------------------------------------------------------


class FakeDB:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def refresh(self, obj):
        return obj


# ---------------------------------------------------------------------------
# Fake repositories
# ---------------------------------------------------------------------------


class FakeIngredientRepository:
    def __init__(self, ingredients=None, db=None):
        self.ingredients = ingredients or {}
        self.db = db or FakeDB()

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


class FakeRecipeIngredientRepository:
    def __init__(self, recipe_ingredients=None):
        self.recipe_ingredients = recipe_ingredients or {}

    async def get_by_recipe(self, recipe_id):
        return self.recipe_ingredients.get(recipe_id, [])


class FakeInventoryMovementRepository:
    def __init__(self, should_fail=False):
        self.movements = []
        self.should_fail = should_fail

    async def create(
        self,
        ingredient_id,
        movement_type,
        quantity,
        unit_cost,
        reason=None,
    ):
        if self.should_fail:
            raise RuntimeError("Inventory movement failed")

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


class FakeRecipeRepository:
    def __init__(self, recipes=None):
        self.recipes = recipes or {}

    async def get_by_id(
        self,
        restaurant_id,
        recipe_id,
    ):
        recipe = self.recipes.get(recipe_id)

        if recipe is None:
            return None

        if recipe.restaurant_id != restaurant_id:
            return None

        return recipe


class FakeOrderRepository:
    def __init__(self, db):
        self.db = db
        self.orders = []

    async def create(
        self,
        restaurant_id,
        status,
        total_amount,
    ):
        order = SimpleNamespace(
            id=uuid4(),
            restaurant_id=restaurant_id,
            status=status,
            total_amount=total_amount,
        )

        self.orders.append(order)

        return order

    async def get_by_id(
        self,
        restaurant_id,
        order_id,
    ):
        for order in self.orders:
            if (
                order.restaurant_id == restaurant_id
                and order.id == order_id
            ):
                return order

        return None


class FakeOrderItemRepository:
    def __init__(self):
        self.items = []

    async def create(
        self,
        order_id,
        recipe_id,
        quantity,
        unit_price,
    ):
        item = SimpleNamespace(
            id=uuid4(),
            order_id=order_id,
            recipe_id=recipe_id,
            quantity=quantity,
            unit_price=unit_price,
        )

        self.items.append(item)

        return item


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_ingredient(
    name="Flour",
    current_stock=Decimal("10"),
    ingredient_id=None,
    restaurant_id=None,
):
    return SimpleNamespace(
        id=ingredient_id or uuid4(),
        restaurant_id=restaurant_id or uuid4(),
        name=name,
        unit="kg",
        current_stock=Decimal(str(current_stock)),
        minimum_stock=Decimal("1"),
        cost_per_unit=Decimal("2.50"),
    )


def make_recipe_ingredient(
    recipe_id,
    ingredient_id,
    quantity,
):
    return SimpleNamespace(
        id=uuid4(),
        recipe_id=recipe_id,
        ingredient_id=ingredient_id,
        quantity=Decimal(str(quantity)),
    )


def make_recipe(
    recipe_id=None,
    restaurant_id=None,
):
    return SimpleNamespace(
        id=recipe_id or uuid4(),
        restaurant_id=restaurant_id or uuid4(),
        name="Test Recipe",
        description="Test recipe",
    )


def make_consumption_service(
    ingredients,
    recipe_ingredients,
    movement_repo=None,
):
    ingredient_repo = FakeIngredientRepository(
        ingredients
    )

    recipe_ingredient_repo = (
        FakeRecipeIngredientRepository(
            recipe_ingredients
        )
    )

    movement_repo = (
        movement_repo
        or FakeInventoryMovementRepository()
    )

    service = InventoryConsumptionService(
        ingredient_repository=ingredient_repo,
        recipe_ingredient_repository=(
            recipe_ingredient_repo
        ),
        inventory_movement_repository=movement_repo,
    )

    return (
        service,
        ingredient_repo,
        movement_repo,
    )


# ---------------------------------------------------------------------------
# Ingredient calculation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_calculate_required_ingredients():
    restaurant_id = uuid4()
    recipe_id = uuid4()
    ingredient_id = uuid4()

    ingredient = make_ingredient(
        ingredient_id=ingredient_id,
        restaurant_id=restaurant_id,
        current_stock=Decimal("10"),
    )

    recipe_ingredient = make_recipe_ingredient(
        recipe_id=recipe_id,
        ingredient_id=ingredient_id,
        quantity=Decimal("2"),
    )

    service, _, _ = make_consumption_service(
        ingredients={
            ingredient_id: ingredient,
        },
        recipe_ingredients={
            recipe_id: [recipe_ingredient],
        },
    )

    result = await service.calculate_required_ingredients(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
        recipe_quantity=Decimal("2"),
    )

    assert len(result) == 1
    assert result[0]["ingredient"] == ingredient
    assert result[0]["required_quantity"] == Decimal("4")


# ---------------------------------------------------------------------------
# Duplicate ingredient aggregation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_aggregate_duplicate_ingredients():
    restaurant_id = uuid4()
    ingredient_id = uuid4()

    ingredient = make_ingredient(
        ingredient_id=ingredient_id,
        restaurant_id=restaurant_id,
        current_stock=Decimal("20"),
    )

    required = [
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("2"),
        },
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("3"),
        },
    ]

    result = (
        InventoryConsumptionService.aggregate_required_ingredients(
            required
        )
    )

    assert len(result) == 1
    assert result[0]["ingredient"] == ingredient
    assert result[0]["required_quantity"] == Decimal("5")


# ---------------------------------------------------------------------------
# Stock validation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_validate_stock_rejects_insufficient_total_stock():
    restaurant_id = uuid4()
    ingredient_id = uuid4()

    ingredient = make_ingredient(
        name="Flour",
        ingredient_id=ingredient_id,
        restaurant_id=restaurant_id,
        current_stock=Decimal("3"),
    )

    service, _, _ = make_consumption_service(
        ingredients={
            ingredient_id: ingredient,
        },
        recipe_ingredients={},
    )

    required = [
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("4"),
        }
    ]

    with pytest.raises(HTTPException) as exc_info:
        await service.validate_stock(required)

    assert exc_info.value.status_code == 400
    assert (
        "Insufficient stock for Flour"
        in str(exc_info.value.detail)
    )


# ---------------------------------------------------------------------------
# Stock consumption
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_consume_stock_decreases_stock_and_records_usage():
    restaurant_id = uuid4()
    ingredient_id = uuid4()
    order_id = uuid4()

    ingredient = make_ingredient(
        name="Flour",
        ingredient_id=ingredient_id,
        restaurant_id=restaurant_id,
        current_stock=Decimal("10"),
    )

    service, ingredient_repo, movement_repo = (
        make_consumption_service(
            ingredients={
                ingredient_id: ingredient,
            },
            recipe_ingredients={},
        )
    )

    required = [
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("3"),
        }
    ]

    await service.consume_stock(
        required=required,
        order_id=order_id,
    )

    updated_ingredient = await ingredient_repo.get_by_id(
        restaurant_id=restaurant_id,
        ingredient_id=ingredient_id,
    )

    assert updated_ingredient.current_stock == Decimal("7")

    assert len(movement_repo.movements) == 1

    movement = movement_repo.movements[0]

    assert movement.ingredient_id == ingredient_id
    assert movement.quantity == Decimal("3")
    assert movement.movement_type == "usage"
    assert movement.unit_cost == Decimal("2.50")
    assert movement.reason == f"Order {order_id}"


# ---------------------------------------------------------------------------
# Duplicate ingredient stock validation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_order_rejects_combined_duplicate_ingredient_requirement():
    ingredient_id = uuid4()
    restaurant_id = uuid4()

    ingredient = make_ingredient(
        name="Flour",
        ingredient_id=ingredient_id,
        restaurant_id=restaurant_id,
        current_stock=Decimal("4"),
    )

    required = [
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("3"),
        },
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("3"),
        },
    ]

    aggregated = (
        InventoryConsumptionService.aggregate_required_ingredients(
            required
        )
    )

    assert len(aggregated) == 1
    assert (
        aggregated[0]["required_quantity"]
        == Decimal("6")
    )

    service, _, _ = make_consumption_service(
        ingredients={
            ingredient_id: ingredient,
        },
        recipe_ingredients={},
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.validate_stock(aggregated)

    assert exc_info.value.status_code == 400
    assert (
        "Insufficient stock for Flour"
        in str(exc_info.value.detail)
    )


# ---------------------------------------------------------------------------
# Order consumption
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_order_consumes_aggregated_inventory():
    restaurant_id = uuid4()
    recipe_id = uuid4()
    ingredient_id = uuid4()

    ingredient = make_ingredient(
        name="Flour",
        ingredient_id=ingredient_id,
        restaurant_id=restaurant_id,
        current_stock=Decimal("10"),
    )

    recipe = make_recipe(
        recipe_id=recipe_id,
        restaurant_id=restaurant_id,
    )

    recipe_ingredient = make_recipe_ingredient(
        recipe_id=recipe_id,
        ingredient_id=ingredient_id,
        quantity=Decimal("2"),
    )

    db = FakeDB()

    ingredient_repo = FakeIngredientRepository(
        {
            ingredient_id: ingredient,
        },
        db=db,
    )

    recipe_ingredient_repo = (
        FakeRecipeIngredientRepository(
            {
                recipe_id: [recipe_ingredient],
            }
        )
    )

    movement_repo = FakeInventoryMovementRepository()

    recipe_repo = FakeRecipeRepository(
        {
            recipe_id: recipe,
        }
    )

    order_repo = FakeOrderRepository(db)
    order_item_repo = FakeOrderItemRepository()

    order_service = OrderService(
        order_repository=order_repo,
        order_item_repository=order_item_repo,
        recipe_repository=recipe_repo,
        recipe_ingredient_repository=(
            recipe_ingredient_repo
        ),
        ingredient_repository=ingredient_repo,
        inventory_movement_repository=movement_repo,
    )

    order_data = OrderCreate(
        restaurant_id=restaurant_id,
        items=[
            OrderItemCreate(
                recipe_id=recipe_id,
                quantity=Decimal("2"),
                unit_price=Decimal("20.00"),
            )
        ],
    )

    result = await order_service.create_order(
        order_data
    )

    assert result is not None

    assert ingredient.current_stock == Decimal("6")

    assert len(movement_repo.movements) == 1

    movement = movement_repo.movements[0]

    assert movement.movement_type == "usage"
    assert movement.quantity == Decimal("4")
    assert movement.unit_cost == Decimal("2.50")

    assert len(order_repo.orders) == 1
    assert len(order_item_repo.items) == 1

    assert db.committed is True
    assert db.rolled_back is False


# ---------------------------------------------------------------------------
# Transaction rollback
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_order_rolls_back_when_inventory_movement_fails():
    restaurant_id = uuid4()
    recipe_id = uuid4()
    ingredient_id = uuid4()

    ingredient = make_ingredient(
        name="Flour",
        ingredient_id=ingredient_id,
        restaurant_id=restaurant_id,
        current_stock=Decimal("10"),
    )

    recipe = make_recipe(
        recipe_id=recipe_id,
        restaurant_id=restaurant_id,
    )

    recipe_ingredient = make_recipe_ingredient(
        recipe_id=recipe_id,
        ingredient_id=ingredient_id,
        quantity=Decimal("2"),
    )

    db = FakeDB()

    ingredient_repo = FakeIngredientRepository(
        {
            ingredient_id: ingredient,
        },
        db=db,
    )

    recipe_ingredient_repo = (
        FakeRecipeIngredientRepository(
            {
                recipe_id: [recipe_ingredient],
            }
        )
    )

    movement_repo = FakeInventoryMovementRepository(
        should_fail=True
    )

    recipe_repo = FakeRecipeRepository(
        {
            recipe_id: recipe,
        }
    )

    order_repo = FakeOrderRepository(db)
    order_item_repo = FakeOrderItemRepository()

    order_service = OrderService(
        order_repository=order_repo,
        order_item_repository=order_item_repo,
        recipe_repository=recipe_repo,
        recipe_ingredient_repository=(
            recipe_ingredient_repo
        ),
        ingredient_repository=ingredient_repo,
        inventory_movement_repository=movement_repo,
    )

    order_data = OrderCreate(
        restaurant_id=restaurant_id,
        items=[
            OrderItemCreate(
                recipe_id=recipe_id,
                quantity=Decimal("1"),
                unit_price=Decimal("20.00"),
            )
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="Inventory movement failed",
    ):
        await order_service.create_order(
            order_data
        )

    assert db.rolled_back is True
    assert db.committed is False

