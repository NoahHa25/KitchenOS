from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.repositories.order_repository import OrderRepository


class SalesService:
    def __init__(
        self,
        order_repository: OrderRepository,
    ):
        self.order_repository = order_repository

    async def get_sales_summary(
        self,
        restaurant_id: UUID,
    ) -> dict:
        orders = await self.order_repository.get_completed_orders(
            restaurant_id=restaurant_id,
        )

        total_revenue = Decimal("0.00")

        for order in orders:
            total_revenue += order.total_amount

        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
        }

    async def get_sales_summary_since(
        self,
        restaurant_id: UUID,
        since: datetime,
    ) -> dict:
        orders = (
            await self.order_repository.get_completed_orders_since(
                restaurant_id=restaurant_id,
                since=since,
            )
        )

        total_revenue = Decimal("0.00")

        for order in orders:
            total_revenue += order.total_amount

        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
        }