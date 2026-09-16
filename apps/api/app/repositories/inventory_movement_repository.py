from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_movement import InventoryMovement


class InventoryMovementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        ingredient_id: UUID,
        movement_type: str,
        quantity: float,
        reason: str | None = None,
    ) -> InventoryMovement:
        movement = InventoryMovement(
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
        )

        self.db.add(movement)
        await self.db.commit()
        await self.db.refresh(movement)

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