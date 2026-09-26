from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.purchase_order import PurchaseOrderStatus


class PurchaseOrderItemCreate(BaseModel):
    ingredient_id: UUID

    quantity: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=3,
    )

    unit_cost: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
    )


class PurchaseOrderCreate(BaseModel):
    restaurant_id: UUID

    supplier_id: UUID

    expected_delivery: datetime | None = None

    notes: str | None = None

    items: list[PurchaseOrderItemCreate] = Field(
        min_length=1,
    )


class PurchaseOrderItemResponse(BaseModel):
    id: UUID
    ingredient_id: UUID
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal

    model_config = {
        "from_attributes": True,
    }


class PurchaseOrderResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    supplier_id: UUID
    status: PurchaseOrderStatus
    expected_delivery: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItemResponse]

    model_config = {
        "from_attributes": True,
    }


class PurchaseOrderStatusUpdate(BaseModel):
    status: PurchaseOrderStatus