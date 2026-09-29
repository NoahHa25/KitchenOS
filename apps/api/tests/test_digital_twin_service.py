from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.purchase_order import PurchaseOrderStatus
from app.services.digital_twin_service import DigitalTwinService


class FakeOrder:
    def __init__(
        self,
        restaurant_id,
        status,
        total_amount="0.00",
        created_at=None,
    ):
        self.id = uuid4()
        self.restaurant_id = restaurant_id
        self.status = status
        self.total_amount = Decimal(str(total_amount))
        self.created_at = created_at or datetime.now(timezone.utc)


class FakeIngredient:
    def __init__(
        self,
        restaurant_id,
        name,
        current_stock,
        minimum_stock,
        cost_per_unit,
    ):
        self.id = uuid4()
        self.restaurant_id = restaurant_id
        self.name = name
        self.current_stock = Decimal(str(current_stock))
        self.minimum_stock = Decimal(str(minimum_stock))
        self.cost_per_unit = Decimal(str(cost_per_unit))


class FakePurchaseOrder:
    def __init__(
        self,
        restaurant_id,
        status,
    ):
        self.id = uuid4()
        self.restaurant_id = restaurant_id
        self.status = status


class FakeMemory:
    def __init__(self, restaurant_id):
        self.id = uuid4()
        self.restaurant_id = restaurant_id


class FakeInsight:
    def __init__(
        self,
        restaurant_id,
        status="active",
    ):
        self.id = uuid4()
        self.restaurant_id = restaurant_id
        self.status = status


class FakeOrderRepository:
    def __init__(self):
        self.orders = []

    async def get_all(self, restaurant_id):
        return [
            order
            for order in self.orders
            if order.restaurant_id == restaurant_id
        ]

    async def get_completed_orders_since(
        self,
        restaurant_id,
        since,
    ):
        return [
            order
            for order in self.orders
            if (
                order.restaurant_id == restaurant_id
                and order.status == "completed"
                and order.created_at >= since
            )
        ]


class FakeIngredientRepository:
    def __init__(self):
        self.ingredients = []

    async def get_all(self, restaurant_id):
        return [
            ingredient
            for ingredient in self.ingredients
            if ingredient.restaurant_id == restaurant_id
        ]

    async def get_low_stock(self, restaurant_id):
        return [
            ingredient
            for ingredient in self.ingredients
            if (
                ingredient.restaurant_id == restaurant_id
                and ingredient.current_stock <= ingredient.minimum_stock
            )
        ]


class FakePurchaseOrderRepository:
    def __init__(self):
        self.purchase_orders = []

    async def get_all(self, restaurant_id):
        return [
            purchase_order
            for purchase_order in self.purchase_orders
            if purchase_order.restaurant_id == restaurant_id
        ]


class FakeRestaurantMemoryRepository:
    def __init__(self):
        self.memories = []

    async def list(self, restaurant_id):
        return [
            memory
            for memory in self.memories
            if memory.restaurant_id == restaurant_id
        ]


class FakeRestaurantInsightRepository:
    def __init__(self):
        self.insights = []

    async def list(
        self,
        restaurant_id,
        status=None,
    ):
        insights = [
            insight
            for insight in self.insights
            if insight.restaurant_id == restaurant_id
        ]

        if status is not None:
            insights = [
                insight
                for insight in insights
                if insight.status == status
            ]

        return insights


class FakeSalesService:
    def __init__(self, order_repository):
        self.order_repository = order_repository

    async def get_sales_summary_since(
        self,
        restaurant_id,
        since,
    ):
        orders = await self.order_repository.get_completed_orders_since(
            restaurant_id=restaurant_id,
            since=since,
        )

        total_revenue = Decimal("0.00")

        for order in orders:
            total_revenue += order.total_amount

        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
        }


def create_service():
    order_repository = FakeOrderRepository()
    ingredient_repository = FakeIngredientRepository()
    purchase_order_repository = FakePurchaseOrderRepository()
    restaurant_memory_repository = FakeRestaurantMemoryRepository()
    restaurant_insight_repository = FakeRestaurantInsightRepository()

    sales_service = FakeSalesService(
        order_repository=order_repository,
    )

    service = DigitalTwinService(
        order_repository=order_repository,
        ingredient_repository=ingredient_repository,
        purchase_order_repository=purchase_order_repository,
        restaurant_memory_repository=restaurant_memory_repository,
        restaurant_insight_repository=restaurant_insight_repository,
        sales_service=sales_service,
    )

    return (
        service,
        order_repository,
        ingredient_repository,
        purchase_order_repository,
        restaurant_memory_repository,
        restaurant_insight_repository,
    )


@pytest.mark.asyncio
async def test_digital_twin_returns_zero_state_for_empty_restaurant():
    (
        service,
        _,
        _,
        _,
        _,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    result = await service.get_restaurant_twin(
        restaurant_id=restaurant_id,
    )

    assert result.restaurant_id == restaurant_id

    assert result.operations.open_orders == 0
    assert result.operations.orders_today == 0

    assert result.sales.revenue_today == Decimal("0.00")
    assert result.sales.completed_orders_today == 0

    assert result.inventory.ingredient_count == 0
    assert result.inventory.low_stock_count == 0
    assert result.inventory.inventory_value == Decimal("0.00")

    assert result.purchasing.draft_orders == 0
    assert result.purchasing.sent_orders == 0
    assert result.purchasing.pending_orders == 0

    assert result.intelligence.active_memories == 0
    assert result.intelligence.active_insights == 0


@pytest.mark.asyncio
async def test_digital_twin_counts_open_orders_and_orders_today():
    (
        service,
        order_repository,
        _,
        _,
        _,
        _,
    ) = create_service()

    restaurant_id = uuid4()
    now = datetime.now(timezone.utc)

    order_repository.orders.extend(
        [
            FakeOrder(
                restaurant_id=restaurant_id,
                status="pending",
                total_amount="10.00",
                created_at=now,
            ),
            FakeOrder(
                restaurant_id=restaurant_id,
                status="preparing",
                total_amount="20.00",
                created_at=now,
            ),
            FakeOrder(
                restaurant_id=restaurant_id,
                status="ready",
                total_amount="30.00",
                created_at=now,
            ),
            FakeOrder(
                restaurant_id=restaurant_id,
                status="completed",
                total_amount="40.00",
                created_at=now,
            ),
            FakeOrder(
                restaurant_id=restaurant_id,
                status="cancelled",
                total_amount="50.00",
                created_at=now,
            ),
            FakeOrder(
                restaurant_id=restaurant_id,
                status="pending",
                total_amount="60.00",
                created_at=now - timedelta(days=1),
            ),
        ]
    )

    result = await service.get_restaurant_twin(
        restaurant_id=restaurant_id,
    )

    assert result.operations.open_orders == 3
    assert result.operations.orders_today == 5


@pytest.mark.asyncio
async def test_digital_twin_calculates_today_sales():
    (
        service,
        order_repository,
        _,
        _,
        _,
        _,
    ) = create_service()

    restaurant_id = uuid4()
    now = datetime.now(timezone.utc)

    order_repository.orders.extend(
        [
            FakeOrder(
                restaurant_id=restaurant_id,
                status="completed",
                total_amount="100.00",
                created_at=now,
            ),
            FakeOrder(
                restaurant_id=restaurant_id,
                status="completed",
                total_amount="75.50",
                created_at=now,
            ),
            FakeOrder(
                restaurant_id=restaurant_id,
                status="completed",
                total_amount="999.99",
                created_at=now - timedelta(days=1),
            ),
            FakeOrder(
                restaurant_id=restaurant_id,
                status="pending",
                total_amount="500.00",
                created_at=now,
            ),
        ]
    )

    result = await service.get_restaurant_twin(
        restaurant_id=restaurant_id,
    )

    assert result.sales.completed_orders_today == 2
    assert result.sales.revenue_today == Decimal("175.50")


@pytest.mark.asyncio
async def test_digital_twin_calculates_inventory_state():
    (
        service,
        _,
        ingredient_repository,
        _,
        _,
        _,
    ) = create_service()

    restaurant_id = uuid4()

    ingredient_repository.ingredients.extend(
        [
            FakeIngredient(
                restaurant_id=restaurant_id,
                name="Tomato",
                current_stock="10",
                minimum_stock="5",
                cost_per_unit="3.50",
            ),
            FakeIngredient(
                restaurant_id=restaurant_id,
                name="Cheese",
                current_stock="2",
                minimum_stock="5",
                cost_per_unit="8.00",
            ),
            FakeIngredient(
                restaurant_id=restaurant_id,
                name="Salt",
                current_stock="1",
                minimum_stock="1",
                cost_per_unit="2.00",
            ),
        ]
    )

    result = await service.get_restaurant_twin(
        restaurant_id=restaurant_id,
    )

    assert result.inventory.ingredient_count == 3
    assert result.inventory.low_stock_count == 2

    # Tomato: 10 * 3.50 = 35.00
    # Cheese: 2 * 8.00 = 16.00
    # Salt: 1 * 2.00 = 2.00
    # Total = 53.00
    assert result.inventory.inventory_value == Decimal("53.00")


@pytest.mark.asyncio
async def test_digital_twin_counts_purchase_orders_and_intelligence():
    (
        service,
        _,
        _,
        purchase_order_repository,
        memory_repository,
        insight_repository,
    ) = create_service()

    restaurant_id = uuid4()

    purchase_order_repository.purchase_orders.extend(
        [
            FakePurchaseOrder(
                restaurant_id=restaurant_id,
                status=PurchaseOrderStatus.DRAFT,
            ),
            FakePurchaseOrder(
                restaurant_id=restaurant_id,
                status=PurchaseOrderStatus.SENT,
            ),
            FakePurchaseOrder(
                restaurant_id=restaurant_id,
                status=PurchaseOrderStatus.RECEIVED,
            ),
            FakePurchaseOrder(
                restaurant_id=restaurant_id,
                status=PurchaseOrderStatus.CANCELLED,
            ),
        ]
    )

    memory_repository.memories.extend(
        [
            FakeMemory(restaurant_id=restaurant_id),
            FakeMemory(restaurant_id=restaurant_id),
        ]
    )

    insight_repository.insights.extend(
        [
            FakeInsight(
                restaurant_id=restaurant_id,
                status="active",
            ),
            FakeInsight(
                restaurant_id=restaurant_id,
                status="resolved",
            ),
        ]
    )

    result = await service.get_restaurant_twin(
        restaurant_id=restaurant_id,
    )

    assert result.purchasing.draft_orders == 1
    assert result.purchasing.sent_orders == 1
    assert result.purchasing.pending_orders == 2

    assert result.intelligence.active_memories == 2
    assert result.intelligence.active_insights == 1


@pytest.mark.asyncio
async def test_digital_twin_is_scoped_to_restaurant():
    (
        service,
        order_repository,
        ingredient_repository,
        _,
        _,
        _,
    ) = create_service()

    restaurant_a = uuid4()
    restaurant_b = uuid4()

    order_repository.orders.extend(
        [
            FakeOrder(
                restaurant_id=restaurant_a,
                status="pending",
                total_amount="100.00",
            ),
            FakeOrder(
                restaurant_id=restaurant_b,
                status="pending",
                total_amount="200.00",
            ),
        ]
    )

    ingredient_repository.ingredients.extend(
        [
            FakeIngredient(
                restaurant_id=restaurant_a,
                name="Tomato",
                current_stock="10",
                minimum_stock="5",
                cost_per_unit="3.00",
            ),
            FakeIngredient(
                restaurant_id=restaurant_b,
                name="Cheese",
                current_stock="20",
                minimum_stock="5",
                cost_per_unit="8.00",
            ),
        ]
    )

    result = await service.get_restaurant_twin(
        restaurant_id=restaurant_a,
    )

    assert result.restaurant_id == restaurant_a

    assert result.operations.open_orders == 1
    assert result.operations.orders_today == 1

    assert result.inventory.ingredient_count == 1
    assert result.inventory.inventory_value == Decimal("30.00")

