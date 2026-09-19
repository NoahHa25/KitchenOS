from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select

from app.core.database import AsyncSessionLocal
from app.models.ingredient import Ingredient
from app.models.inventory_movement import InventoryMovement
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.restaurant import Restaurant
from app.repositories.ingredient_repository import (
    IngredientRepository,
)
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.repositories.order_item_repository import (
    OrderItemRepository,
)
from app.repositories.order_repository import (
    OrderRepository,
)
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import (
    RecipeRepository,
)
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService


# ---------------------------------------------------------------------------
# Failing repository
# ---------------------------------------------------------------------------


class FailingInventoryMovementRepository:
    async def create(
        self,
        ingredient_id,
        movement_type,
        quantity,
        unit_cost=None,
        reason=None,
    ):
        raise RuntimeError(
            "Forced inventory movement failure"
        )


# ---------------------------------------------------------------------------
# Transaction rollback integration test
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_order_inventory_transaction_rolls_back_on_failure():
    restaurant_id = uuid4()
    ingredient_id = uuid4()
    recipe_id = uuid4()

    # ---------------------------------------------------------
    # Setup: create database records in FK dependency order.
    # Each stage is committed so the next stage has a valid
    # parent row in PostgreSQL.
    # ---------------------------------------------------------

    async with AsyncSessionLocal() as setup_db:
        restaurant = Restaurant(
            id=restaurant_id,
            name="Pantry Test Restaurant",
            slug=f"pantry-test-{uuid4().hex}",
        )

        setup_db.add(restaurant)

        await setup_db.commit()

    async with AsyncSessionLocal() as setup_db:
        ingredient = Ingredient(
            id=ingredient_id,
            restaurant_id=restaurant_id,
            name="Flour",
            unit="kg",
            current_stock=Decimal("10.00"),
            minimum_stock=Decimal("1.00"),
            cost_per_unit=Decimal("2.50"),
        )

        recipe = Recipe(
            id=recipe_id,
            restaurant_id=restaurant_id,
            name="Test Bread",
            description="Integration test recipe",
        )

        setup_db.add_all(
            [
                ingredient,
                recipe,
            ]
        )

        await setup_db.commit()

    async with AsyncSessionLocal() as setup_db:
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            quantity=Decimal("3.000"),
        )

        setup_db.add(recipe_ingredient)

        await setup_db.commit()

    try:
        # -----------------------------------------------------
        # Execute: force inventory movement creation to fail
        # after stock has been deducted.
        # -----------------------------------------------------

        async with AsyncSessionLocal() as db:
            service = OrderService(
                order_repository=OrderRepository(db),
                order_item_repository=OrderItemRepository(db),
                recipe_repository=RecipeRepository(db),
                recipe_ingredient_repository=(
                    RecipeIngredientRepository(db)
                ),
                ingredient_repository=IngredientRepository(db),
                inventory_movement_repository=(
                    FailingInventoryMovementRepository()
                ),
            )

            data = OrderCreate(
                restaurant_id=restaurant_id,
                items=[
                    OrderItemCreate(
                        recipe_id=recipe_id,
                        quantity=Decimal("1.000"),
                        unit_price=Decimal("15.00"),
                    ),
                ],
            )

            with pytest.raises(
                RuntimeError,
                match=(
                    "Forced inventory movement failure"
                ),
            ):
                await service.create_order(data)

        # -----------------------------------------------------
        # Verify: use a fresh session to prove the transaction
        # was rolled back in the actual PostgreSQL database.
        # -----------------------------------------------------

        async with AsyncSessionLocal() as verify_db:
            ingredient_result = await verify_db.execute(
                select(
                    Ingredient.current_stock
                ).where(
                    Ingredient.id == ingredient_id,
                    Ingredient.restaurant_id
                    == restaurant_id,
                )
            )

            stock = ingredient_result.scalar_one()

            order_count_result = (
                await verify_db.execute(
                    select(
                        func.count(Order.id)
                    ).where(
                        Order.restaurant_id
                        == restaurant_id,
                    )
                )
            )

            order_count = (
                order_count_result.scalar_one()
            )

            order_item_count_result = (
                await verify_db.execute(
                    select(
                        func.count(OrderItem.id)
                    )
                    .join(
                        Order,
                        Order.id
                        == OrderItem.order_id,
                    )
                    .where(
                        Order.restaurant_id
                        == restaurant_id,
                    )
                )
            )

            order_item_count = (
                order_item_count_result.scalar_one()
            )

            movement_count_result = (
                await verify_db.execute(
                    select(
                        func.count(
                            InventoryMovement.id
                        )
                    )
                    .join(
                        Ingredient,
                        Ingredient.id
                        == InventoryMovement.ingredient_id,
                    )
                    .where(
                        Ingredient.restaurant_id
                        == restaurant_id,
                    )
                )
            )

            movement_count = (
                movement_count_result.scalar_one()
            )

            assert stock == Decimal("10.00")
            assert order_count == 0
            assert order_item_count == 0
            assert movement_count == 0

    finally:
        # -----------------------------------------------------
        # Cleanup integration-test data.
        # -----------------------------------------------------

        async with AsyncSessionLocal() as cleanup_db:
            await cleanup_db.execute(
                delete(OrderItem).where(
                    OrderItem.order_id.in_(
                        select(Order.id).where(
                            Order.restaurant_id
                            == restaurant_id,
                        )
                    )
                )
            )

            await cleanup_db.execute(
                delete(Order).where(
                    Order.restaurant_id
                    == restaurant_id,
                )
            )

            await cleanup_db.execute(
                delete(InventoryMovement).where(
                    InventoryMovement.ingredient_id
                    == ingredient_id,
                )
            )

            await cleanup_db.execute(
                delete(RecipeIngredient).where(
                    RecipeIngredient.recipe_id
                    == recipe_id,
                )
            )

            await cleanup_db.execute(
                delete(Ingredient).where(
                    Ingredient.id == ingredient_id,
                )
            )

            await cleanup_db.execute(
                delete(Recipe).where(
                    Recipe.id == recipe_id,
                )
            )

            await cleanup_db.execute(
                delete(Restaurant).where(
                    Restaurant.id == restaurant_id,
                )
            )

            await cleanup_db.commit()

