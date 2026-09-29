from datetime import datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from app.models.purchase_order import PurchaseOrderStatus
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from app.repositories.restaurant_insight_repository import (
    RestaurantInsightRepository,
)
from app.repositories.restaurant_memory import (
    RestaurantMemoryRepository,
)
from app.schemas.digital_twin import (
    DigitalTwinIntelligence,
    DigitalTwinInventory,
    DigitalTwinOperations,
    DigitalTwinPurchasing,
    DigitalTwinResponse,
    DigitalTwinSales,
)
from app.services.sales_service import SalesService


class DigitalTwinService:
    def __init__(
        self,
        order_repository: OrderRepository,
        ingredient_repository: IngredientRepository,
        purchase_order_repository: PurchaseOrderRepository,
        restaurant_memory_repository: RestaurantMemoryRepository,
        restaurant_insight_repository: RestaurantInsightRepository,
        sales_service: SalesService,
    ):
        self.order_repository = order_repository
        self.ingredient_repository = ingredient_repository
        self.purchase_order_repository = purchase_order_repository
        self.restaurant_memory_repository = (
            restaurant_memory_repository
        )
        self.restaurant_insight_repository = (
            restaurant_insight_repository
        )
        self.sales_service = sales_service

    async def get_restaurant_twin(
        self,
        restaurant_id: UUID,
    ) -> DigitalTwinResponse:
        now = datetime.now(timezone.utc)

        start_of_day = datetime.combine(
            now.date(),
            time.min,
            tzinfo=timezone.utc,
        )

        orders = await self.order_repository.get_all(
            restaurant_id=restaurant_id,
        )

        open_orders = sum(
            1
            for order in orders
            if (
                order.created_at >= start_of_day
                and order.status in {
                    "pending",
                    "preparing",
                    "ready",
                }
            )
        )

        orders_today = sum(
            1
            for order in orders
            if order.created_at >= start_of_day
        )

        sales = await self.sales_service.get_sales_summary_since(
            restaurant_id=restaurant_id,
            since=start_of_day,
        )

        ingredients = await self.ingredient_repository.get_all(
            restaurant_id=restaurant_id,
        )

        low_stock = await self.ingredient_repository.get_low_stock(
            restaurant_id=restaurant_id,
        )

        inventory_value = Decimal("0.00")

        for ingredient in ingredients:
            current_stock = Decimal(
                str(ingredient.current_stock)
            )
            cost_per_unit = Decimal(
                str(ingredient.cost_per_unit)
            )

            inventory_value += (
                current_stock * cost_per_unit
            )

        inventory_value = inventory_value.quantize(
            Decimal("0.01")
        )

        purchase_orders = (
            await self.purchase_order_repository.get_all(
                restaurant_id=restaurant_id,
            )
        )

        draft_orders = sum(
            1
            for purchase_order in purchase_orders
            if purchase_order.status
            == PurchaseOrderStatus.DRAFT
        )

        sent_orders = sum(
            1
            for purchase_order in purchase_orders
            if purchase_order.status
            == PurchaseOrderStatus.SENT
        )

        pending_orders = draft_orders + sent_orders

        memories = await self.restaurant_memory_repository.list(
            restaurant_id=restaurant_id,
        )

        insights = await self.restaurant_insight_repository.list(
            restaurant_id=restaurant_id,
            status="active",
        )

        return DigitalTwinResponse(
            restaurant_id=restaurant_id,
            generated_at=now,
            operations=DigitalTwinOperations(
                open_orders=open_orders,
                orders_today=orders_today,
            ),
            sales=DigitalTwinSales(
                revenue_today=sales["total_revenue"],
                completed_orders_today=sales["total_orders"],
            ),
            inventory=DigitalTwinInventory(
                ingredient_count=len(ingredients),
                low_stock_count=len(low_stock),
                inventory_value=inventory_value,
            ),
            purchasing=DigitalTwinPurchasing(
                draft_orders=draft_orders,
                sent_orders=sent_orders,
                pending_orders=pending_orders,
            ),
            intelligence=DigitalTwinIntelligence(
                active_memories=len(memories),
                active_insights=len(insights),
            ),
        )

