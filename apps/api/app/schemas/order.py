from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    recipe_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class OrderCreate(BaseModel):
    restaurant_id: UUID
    items: list[OrderItemCreate] = Field(min_length=1)
    
    
class OrderStatusUpdate(BaseModel):
    status: str


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    recipe_id: UUID
    quantity: Decimal
    unit_price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    status: str
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse]