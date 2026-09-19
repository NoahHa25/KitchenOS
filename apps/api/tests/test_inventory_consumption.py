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
    def __init__(self, ingredients):
        self.ingredients = ingredients
        self.db = FakeDB()

    async def get_by_id(self, restaurant_id, ingredient_id):
        return self.ingredients.get(ingredient_id)


class FakeRecipeIngredientRepository:
    def __init__(self, recipe_ingredients):
        self.recipe_ingredients = recipe_ingredients

    async def get_by_recipe(self, recipe_id):
        return self.recipe_ingredients.get(recipe_id, [])


class FakeInventoryMovementRepository:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.created = []

    async def create(
        self,
        ingredient_id,
        movement_type,
        quantity,
        reason=None,
    ):
        if self.should_fail:
            raise RuntimeError("Movement creation failed")

        movement = SimpleNamespace(
            id=uuid4(),
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
        )

        self.created.append(movement)
        return movement


class FakeRecipeRepository:
    def __init__(self, recipes):
        self.recipes = recipes

    async def get_by_id(self, restaurant_id, recipe_id):
        return self.recipes.get(recipe_id)


class FakeOrderRepository:
    def __init__(self):
        self.db = FakeDB()
        self.created_order = None

    async def create(
        self,
        restaurant_id,
        status="pending",
        total_amount=0,
    ):
        self.created_order = SimpleNamespace(
            id=uuid4(),
            restaurant_id=restaurant_id,
            status=status,
            total_amount=total_amount,
            items=[],
        )

        return self.created_order

    async def get_by_id(self, restaurant_id, order_id):
        if self.created_order is None:
            return None

        if self.created_order.id != order_id:
            return None

        if self.created_order.restaurant_id != restaurant_id:
            return None

        return self.created_order


class FakeOrderItemRepository:
    def __init__(self):
        self.created_items = []

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

        self.created_items.append(item)

        return item


def make_ingredient(stock="10.00", name="Flour"):
    ingredient = SimpleNamespace(
        id=uuid4(),
        name=name,
        current_stock=Decimal(stock),
    )

    return ingredient


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


def make_recipe():
    return SimpleNamespace(
        id=uuid4(),
    )


def make_consumption_service(
    ingredients,
    recipe_ingredients,
    movement_should_fail=False,
):
    ingredient_repository = FakeIngredientRepository(
        ingredients
    )

    recipe_ingredient_repository = (
        FakeRecipeIngredientRepository(
            recipe_ingredients
        )
    )

    movement_repository = FakeInventoryMovementRepository(
        should_fail=movement_should_fail,
    )

    service = InventoryConsumptionService(
        ingredient_repository=ingredient_repository,
        recipe_ingredient_repository=(
            recipe_ingredient_repository
        ),
        inventory_movement_repository=movement_repository,
    )

    return (
        service,
        ingredient_repository,
        movement_repository,
    )


@pytest.mark.anyio
async def test_calculate_required_ingredients():
    restaurant_id = uuid4()
    recipe_id = uuid4()

    ingredient = make_ingredient("20.00")

    recipe_ingredient = make_recipe_ingredient(
        recipe_id=recipe_id,
        ingredient_id=ingredient.id,
        quantity="2.500",
    )

    service, _, _ = make_consumption_service(
        ingredients={
            ingredient.id: ingredient,
        },
        recipe_ingredients={
            recipe_id: [recipe_ingredient],
        },
    )

    result = await service.calculate_required_ingredients(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
        recipe_quantity=Decimal("4"),
    )

    assert len(result) == 1
    assert result[0]["ingredient"] is ingredient
    assert result[0]["required_quantity"] == Decimal("10.000")


def test_aggregate_duplicate_ingredients():
    ingredient = make_ingredient("20.00")

    required = [
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("3.000"),
        },
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("2.000"),
        },
    ]

    result = (
        InventoryConsumptionService.aggregate_required_ingredients(
            required
        )
    )

    assert len(result) == 1
    assert result[0]["ingredient"] is ingredient
    assert result[0]["required_quantity"] == Decimal("5.000")


@pytest.mark.anyio
async def test_validate_stock_rejects_insufficient_total_stock():
    ingredient = make_ingredient("5.00")

    required = [
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("6.000"),
        },
    ]

    service, _, _ = make_consumption_service(
        ingredients={ingredient.id: ingredient},
        recipe_ingredients={},
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.validate_stock(required)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Insufficient stock for Flour"


@pytest.mark.anyio
async def test_consume_stock_decreases_stock_and_records_usage():
    ingredient = make_ingredient("10.00")

    service, _, movement_repository = (
        make_consumption_service(
            ingredients={ingredient.id: ingredient},
            recipe_ingredients={},
        )
    )

    order_id = uuid4()

    required = [
        {
            "ingredient": ingredient,
            "required_quantity": Decimal("3.500"),
        },
    ]

    await service.consume_stock(
        required=required,
        order_id=order_id,
    )

    assert ingredient.current_stock == Decimal("6.500")

    assert len(movement_repository.created) == 1

    movement = movement_repository.created[0]

    assert movement.ingredient_id == ingredient.id
    assert movement.movement_type == "usage"
    assert movement.quantity == 3.5
    assert str(order_id) in movement.reason


@pytest.mark.anyio
async def test_order_rejects_combined_duplicate_ingredient_requirement():
    restaurant_id = uuid4()

    ingredient = make_ingredient("5.00")

    recipe_one = make_recipe()
    recipe_two = make_recipe()

    recipe_ingredient_one = make_recipe_ingredient(
        recipe_id=recipe_one.id,
        ingredient_id=ingredient.id,
        quantity="3.000",
    )

    recipe_ingredient_two = make_recipe_ingredient(
        recipe_id=recipe_two.id,
        ingredient_id=ingredient.id,
        quantity="3.000",
    )

    order_repository = FakeOrderRepository()

    order_item_repository = FakeOrderItemRepository()

    ingredient_repository = FakeIngredientRepository(
        ingredients={
            ingredient.id: ingredient,
        }
    )

    recipe_repository = FakeRecipeRepository(
        recipes={
            recipe_one.id: recipe_one,
            recipe_two.id: recipe_two,
        }
    )

    recipe_ingredient_repository = (
        FakeRecipeIngredientRepository(
            recipe_ingredients={
                recipe_one.id: [recipe_ingredient_one],
                recipe_two.id: [recipe_ingredient_two],
            }
        )
    )

    movement_repository = FakeInventoryMovementRepository()

    service = OrderService(
        order_repository=order_repository,
        order_item_repository=order_item_repository,
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=(
            recipe_ingredient_repository
        ),
        ingredient_repository=ingredient_repository,
        inventory_movement_repository=movement_repository,
    )

    data = OrderCreate(
        restaurant_id=restaurant_id,
        items=[
            OrderItemCreate(
                recipe_id=recipe_one.id,
                quantity=Decimal("1"),
                unit_price=Decimal("10.00"),
            ),
            OrderItemCreate(
                recipe_id=recipe_two.id,
                quantity=Decimal("1"),
                unit_price=Decimal("12.00"),
            ),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_order(data)

    assert exc_info.value.status_code == 400
    assert "Insufficient stock for Flour" in exc_info.value.detail

    assert order_repository.created_order is None
    assert order_item_repository.created_items == []
    assert movement_repository.created == []

    assert ingredient.current_stock == Decimal("5.00")
    assert order_repository.db.committed is False
    assert order_repository.db.rolled_back is True


@pytest.mark.anyio
async def test_order_consumes_aggregated_inventory():
    restaurant_id = uuid4()

    ingredient = make_ingredient("10.00")

    recipe_one = make_recipe()
    recipe_two = make_recipe()

    recipe_ingredient_one = make_recipe_ingredient(
        recipe_id=recipe_one.id,
        ingredient_id=ingredient.id,
        quantity="3.000",
    )

    recipe_ingredient_two = make_recipe_ingredient(
        recipe_id=recipe_two.id,
        ingredient_id=ingredient.id,
        quantity="2.000",
    )

    order_repository = FakeOrderRepository()

    order_item_repository = FakeOrderItemRepository()

    ingredient_repository = FakeIngredientRepository(
        ingredients={
            ingredient.id: ingredient,
        }
    )

    recipe_repository = FakeRecipeRepository(
        recipes={
            recipe_one.id: recipe_one,
            recipe_two.id: recipe_two,
        }
    )

    recipe_ingredient_repository = (
        FakeRecipeIngredientRepository(
            recipe_ingredients={
                recipe_one.id: [recipe_ingredient_one],
                recipe_two.id: [recipe_ingredient_two],
            }
        )
    )

    movement_repository = FakeInventoryMovementRepository()

    service = OrderService(
        order_repository=order_repository,
        order_item_repository=order_item_repository,
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=(
            recipe_ingredient_repository
        ),
        ingredient_repository=ingredient_repository,
        inventory_movement_repository=movement_repository,
    )

    data = OrderCreate(
        restaurant_id=restaurant_id,
        items=[
            OrderItemCreate(
                recipe_id=recipe_one.id,
                quantity=Decimal("1"),
                unit_price=Decimal("10.00"),
            ),
            OrderItemCreate(
                recipe_id=recipe_two.id,
                quantity=Decimal("1"),
                unit_price=Decimal("12.00"),
            ),
        ],
    )

    result = await service.create_order(data)

    assert result is order_repository.created_order

    assert result.status == "pending"
    assert result.total_amount == Decimal("22.00")

    assert len(order_item_repository.created_items) == 2

    assert ingredient.current_stock == Decimal("5.00")

    assert len(movement_repository.created) == 1

    movement = movement_repository.created[0]

    assert movement.ingredient_id == ingredient.id
    assert movement.movement_type == "usage"
    assert movement.quantity == 5.0

    assert order_repository.db.committed is True
    assert order_repository.db.rolled_back is False


@pytest.mark.anyio
async def test_order_rolls_back_when_inventory_movement_fails():
    restaurant_id = uuid4()

    ingredient = make_ingredient("10.00")
    recipe = make_recipe()

    recipe_ingredient = make_recipe_ingredient(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        quantity="3.000",
    )

    order_repository = FakeOrderRepository()

    order_item_repository = FakeOrderItemRepository()

    ingredient_repository = FakeIngredientRepository(
        ingredients={
            ingredient.id: ingredient,
        }
    )

    recipe_repository = FakeRecipeRepository(
        recipes={
            recipe.id: recipe,
        }
    )

    recipe_ingredient_repository = (
        FakeRecipeIngredientRepository(
            recipe_ingredients={
                recipe.id: [recipe_ingredient],
            }
        )
    )

    movement_repository = FakeInventoryMovementRepository(
        should_fail=True,
    )

    service = OrderService(
        order_repository=order_repository,
        order_item_repository=order_item_repository,
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=(
            recipe_ingredient_repository
        ),
        ingredient_repository=ingredient_repository,
        inventory_movement_repository=movement_repository,
    )

    data = OrderCreate(
        restaurant_id=restaurant_id,
        items=[
            OrderItemCreate(
                recipe_id=recipe.id,
                quantity=Decimal("1"),
                unit_price=Decimal("15.00"),
            ),
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="Movement creation failed",
    ):
        await service.create_order(data)

    assert order_repository.db.committed is False
    assert order_repository.db.rolled_back is True

    assert order_repository.created_order is not None
    assert len(order_item_repository.created_items) == 1

    # The fake repository does not emulate database rollback.
    # In PostgreSQL, the surrounding transaction rollback
    # restores these database changes.
    assert ingredient.current_stock == Decimal("7.000")

