from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        restaurant_id: UUID,
        status: str = "pending",
        total_amount=0,
    ) -> Order:
        order = Order(
            restaurant_id=restaurant_id,
            status=status,
            total_amount=total_amount,
        )

        self.db.add(order)
        await self.db.flush()

        return order

    async def get_by_id(
      self,
      restaurant_id: UUID,
      order_id: UUID,
    ) -> Order | None:
      result = await self.db.execute(
        select(Order)
        .options(
            selectinload(Order.items),
        )
        .where(
            Order.id == order_id,
            Order.restaurant_id == restaurant_id,
        )
    )

      return result.scalar_one_or_none()

    async def get_all(
      self,
      restaurant_id: UUID,
    ) -> list[Order]:
      result = await self.db.execute(
        select(Order)
        .options(
            selectinload(Order.items),
        )
        .where(
            Order.restaurant_id == restaurant_id,
        )
        .order_by(
            Order.created_at.desc(),
        )
    )

      return list(result.scalars().all())
  
  
    async def get_completed_orders(
           self,
           restaurant_id: UUID,
        ) -> list[Order]:
           result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.items),
            )
            .where(
                Order.restaurant_id == restaurant_id,
                Order.status == "completed",
            )
            .order_by(
                Order.created_at.desc(),
            )
        )
           return list(result.scalars().all())

    async def update(
        self,
        order: Order,
        status: str | None = None,
        total_amount=None,
    ) -> Order:
        if status is not None:
            order.status = status

        if total_amount is not None:
            order.total_amount = total_amount

        await self.db.flush()

        return order

    async def delete(
        self,
        order: Order,
    ) -> None:
        await self.db.delete(order)
        await self.db.flush()
        
        
        
    async def get_by_id_with_items(
       self,
       restaurant_id: UUID,
       order_id: UUID,
    ) -> Order | None:
       result = await self.db.execute(
        select(Order)
        .options(
            selectinload(Order.items),
        )
        .where(
            Order.id == order_id,
            Order.restaurant_id == restaurant_id,
        )
    )

       return result.scalar_one_or_none()