from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.purchase_order import PurchaseOrderStatus
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderStatusUpdate,
)
from app.services.purchase_order_service import PurchaseOrderService


router = APIRouter(
    prefix="/purchase-orders",
    tags=["Purchase Orders"],
)


def get_purchase_order_service(
    db: AsyncSession,
) -> PurchaseOrderService:
    return PurchaseOrderService(
        purchase_order_repository=PurchaseOrderRepository(db),
        supplier_repository=SupplierRepository(db),
        ingredient_repository=IngredientRepository(db),
        inventory_movement_repository=InventoryMovementRepository(db),
    )


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=201,
)
async def create_purchase_order(
    data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
):
    service = get_purchase_order_service(db)

    return await service.create_purchase_order(data)


@router.get(
    "",
    response_model=list[PurchaseOrderResponse],
)
async def list_purchase_orders(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_purchase_order_service(db)

    return await service.list_purchase_orders(
        restaurant_id=restaurant_id,
    )


@router.get(
    "/{purchase_order_id}",
    response_model=PurchaseOrderResponse,
)
async def get_purchase_order(
    purchase_order_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_purchase_order_service(db)

    purchase_order = await service.get_purchase_order(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order_id,
    )

    if purchase_order is None:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found",
        )

    return purchase_order


@router.patch(
    "/{purchase_order_id}/status",
    response_model=PurchaseOrderResponse,
)
async def update_purchase_order_status(
    purchase_order_id: UUID,
    restaurant_id: UUID,
    data: PurchaseOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = get_purchase_order_service(db)

    purchase_order = await service.update_status(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order_id,
        new_status=data.status,
    )

    if purchase_order is None:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found",
        )

    return purchase_order


@router.post(
    "/{purchase_order_id}/receive",
    response_model=PurchaseOrderResponse,
)
async def receive_purchase_order(
    purchase_order_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_purchase_order_service(db)

    purchase_order = await service.receive_purchase_order(
        restaurant_id=restaurant_id,
        purchase_order_id=purchase_order_id,
    )

    if purchase_order is None:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found",
        )

    return purchase_order