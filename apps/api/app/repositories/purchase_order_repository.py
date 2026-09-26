from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem


class PurchaseOrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        restaurant_id: UUID,
        supplier_id: UUID,
        expected_delivery: datetime | None,
        notes: str | None,
    ) -> PurchaseOrder:
        purchase_order = PurchaseOrder(
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
            expected_delivery=expected_delivery,
            notes=notes,
        )

        self.db.add(purchase_order)
        await self.db.flush()

        return purchase_order

    async def add_item(
        self,
        purchase_order_id: UUID,
        ingredient_id: UUID,
        quantity,
        unit_cost,
        total_cost,
    ) -> PurchaseOrderItem:
        item = PurchaseOrderItem(
            purchase_order_id=purchase_order_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
        )

        self.db.add(item)
        await self.db.flush()

        return item

    async def get_by_id(
        self,
        restaurant_id: UUID,
        purchase_order_id: UUID,
    ) -> PurchaseOrder | None:
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.items),
            )
            .where(
                PurchaseOrder.id == purchase_order_id,
                PurchaseOrder.restaurant_id == restaurant_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
        restaurant_id: UUID,
    ) -> list[PurchaseOrder]:
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.items),
            )
            .where(
                PurchaseOrder.restaurant_id == restaurant_id,
            )
            .order_by(
                PurchaseOrder.created_at.desc(),
            )
        )

        return list(result.scalars().all())

    async def update_status(
        self,
        purchase_order: PurchaseOrder,
        status,
    ) -> PurchaseOrder:
        purchase_order.status = status

        await self.db.flush()

        return purchase_order