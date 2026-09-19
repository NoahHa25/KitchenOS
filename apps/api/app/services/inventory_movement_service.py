from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.schemas.inventory_movement import InventoryMovementCreate


class InventoryMovementService:
    def __init__(
        self,
        movement_repository: InventoryMovementRepository,
        ingredient_repository: IngredientRepository,
    ):
        self.movement_repository = movement_repository
        self.ingredient_repository = ingredient_repository

    async def create_movement(
        self,
        restaurant_id: UUID,
        data: InventoryMovementCreate,
    ):
        try:
            ingredient = await self.ingredient_repository.get_by_id(
                restaurant_id=restaurant_id,
                ingredient_id=data.ingredient_id,
            )

            if ingredient is None:
                raise HTTPException(
                    status_code=404,
                    detail="Ingredient not found",
                )

            movement_type = data.movement_type.lower().strip()
            quantity = Decimal(str(data.quantity))

            if movement_type not in {
                "purchase",
                "usage",
                "waste",
                "adjustment",
            }:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid movement type. "
                        "Use purchase, usage, waste, or adjustment."
                    ),
                )

            if quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Quantity must be greater than 0",
                )

            current_stock = Decimal(
                str(ingredient.current_stock)
            )

            current_unit_cost = Decimal(
                str(ingredient.cost_per_unit)
            )

            unit_cost = (
                Decimal(str(data.unit_cost))
                if data.unit_cost is not None
                else current_unit_cost
            )

            if unit_cost < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Unit cost cannot be negative",
                )

            if movement_type == "purchase":
                ingredient.current_stock = (
                    current_stock + quantity
                )

                # A purchase may establish a new cost basis.
                if data.unit_cost is not None:
                    ingredient.cost_per_unit = unit_cost

            elif movement_type in {"usage", "waste"}:
                if current_stock < quantity:
                    raise HTTPException(
                        status_code=400,
                        detail="Insufficient stock",
                    )

                ingredient.current_stock = (
                    current_stock - quantity
                )

            elif movement_type == "adjustment":
                ingredient.current_stock = quantity

            movement = await self.movement_repository.create(
                ingredient_id=data.ingredient_id,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=unit_cost,
                reason=data.reason,
            )

            await self.ingredient_repository.db.commit()

            await self.ingredient_repository.db.refresh(ingredient)
            await self.ingredient_repository.db.refresh(movement)

            return movement

        except Exception:
            await self.ingredient_repository.db.rollback()
            raise

    async def list_movements(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
    ):
        ingredient = await self.ingredient_repository.get_by_id(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
        )

        if ingredient is None:
            raise HTTPException(
                status_code=404,
                detail="Ingredient not found",
            )

        return await self.movement_repository.get_all(
            ingredient_id=ingredient_id,
        )

