from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DigitalTwinOperations(BaseModel):
    open_orders: int
    orders_today: int


class DigitalTwinSales(BaseModel):
    revenue_today: Decimal
    completed_orders_today: int


class DigitalTwinInventory(BaseModel):
    ingredient_count: int
    low_stock_count: int
    inventory_value: Decimal


class DigitalTwinPurchasing(BaseModel):
    draft_orders: int
    sent_orders: int
    pending_orders: int


class DigitalTwinIntelligence(BaseModel):
    active_memories: int
    active_insights: int


class DigitalTwinResponse(BaseModel):
    restaurant_id: UUID
    generated_at: datetime

    operations: DigitalTwinOperations
    sales: DigitalTwinSales
    inventory: DigitalTwinInventory
    purchasing: DigitalTwinPurchasing
    intelligence: DigitalTwinIntelligence