from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order_item import OrderItem


class OrderItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        order_id: UUID,
        recipe_id: UUID,
        quantity,
        unit_price,
    ) -> OrderItem:
        order_item = OrderItem(
            order_id=order_id,
            recipe_id=recipe_id,
            quantity=quantity,
            unit_price=unit_price,
        )

        self.db.add(order_item)
        await self.db.flush()

        return order_item

    async def get_by_id(
        self,
        order_item_id: UUID,
    ) -> OrderItem | None:
        result = await self.db.execute(
            select(OrderItem).where(
                OrderItem.id == order_item_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_order(
        self,
        order_id: UUID,
    ) -> list[OrderItem]:
        result = await self.db.execute(
            select(OrderItem)
            .where(
                OrderItem.order_id == order_id,
            )
            .order_by(OrderItem.id)
        )

        return list(result.scalars().all())

    async def delete(
        self,
        order_item: OrderItem,
    ) -> None:
        await self.db.delete(order_item)
        await self.db.flush()