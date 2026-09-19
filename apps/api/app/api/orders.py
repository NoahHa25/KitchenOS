from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.repositories.order_item_repository import (
    OrderItemRepository,
)
from app.repositories.order_repository import OrderRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository

from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)
from app.schemas.sales import SalesSummaryResponse

from app.services.order_service import OrderService
from app.services.sales_service import SalesService


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


def get_order_service(
    db: AsyncSession,
) -> OrderService:
    return OrderService(
        order_repository=OrderRepository(db),
        order_item_repository=OrderItemRepository(db),
        recipe_repository=RecipeRepository(db),
        recipe_ingredient_repository=RecipeIngredientRepository(db),
        ingredient_repository=IngredientRepository(db),
        inventory_movement_repository=InventoryMovementRepository(db),
    )


@router.post(
    "",
    response_model=OrderResponse,
)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    service = get_order_service(db)

    order = await service.create_order(data)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found",
        )

    return order


@router.get(
    "",
    response_model=list[OrderResponse],
)
async def list_orders(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_order_service(db)

    return await service.order_repository.get_all(
        restaurant_id=restaurant_id,
    )


@router.get(
    "/sales/summary",
    response_model=SalesSummaryResponse,
)
async def get_sales_summary(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = SalesService(
        order_repository=OrderRepository(db),
    )

    return await service.get_sales_summary(
        restaurant_id=restaurant_id,
    )


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
async def update_order_status(
    order_id: UUID,
    data: OrderStatusUpdate,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_order_service(db)

    try:
        order = await service.update_status(
            restaurant_id=restaurant_id,
            order_id=order_id,
            new_status=data.status,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    await db.commit()

    return await service.order_repository.get_by_id(
        restaurant_id=restaurant_id,
        order_id=order_id,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    order_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_order_service(db)

    order = await service.order_repository.get_by_id(
        restaurant_id=restaurant_id,
        order_id=order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order