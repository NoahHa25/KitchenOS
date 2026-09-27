from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.inventory_movement import InventoryMovement


class InventoryMovementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        ingredient_id: UUID,
        movement_type: str,
        quantity: Decimal,
        unit_cost: Decimal,
        reason: str | None = None,
    ) -> InventoryMovement:
        movement = InventoryMovement(
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost,
            reason=reason,
        )

        self.db.add(movement)
        await self.db.flush()

        return movement

    async def get_all(
        self,
        ingredient_id: UUID,
    ) -> list[InventoryMovement]:
        result = await self.db.execute(
            select(InventoryMovement)
            .where(
                InventoryMovement.ingredient_id == ingredient_id
            )
            .order_by(
                InventoryMovement.created_at.desc()
            )
        )

        return list(result.scalars().all())

    async def get_restaurant_movements(
        self,
        restaurant_id: UUID,
        movement_type: str | None = None,
        created_after: datetime | None = None,
    ) -> list[InventoryMovement]:
        query = (
            select(InventoryMovement)
            .join(
                Ingredient,
                Ingredient.id == InventoryMovement.ingredient_id,
            )
            .where(
                Ingredient.restaurant_id == restaurant_id,
            )
            .order_by(
                InventoryMovement.created_at.desc()
            )
        )

        if movement_type is not None:
            query = query.where(
                InventoryMovement.movement_type == movement_type,
            )

        if created_after is not None:
            query = query.where(
                InventoryMovement.created_at >= created_after,
            )

        result = await self.db.execute(query)

        return list(result.scalars().all())