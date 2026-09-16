from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.schemas.inventory_movement import (
    InventoryMovementCreate,
    InventoryMovementResponse,
)
from app.services.inventory_movement_service import (
    InventoryMovementService,
)

router = APIRouter(
    prefix="/inventory-movements",
    tags=["Inventory Movements"],
)


def get_service(
    db: AsyncSession,
) -> InventoryMovementService:
    return InventoryMovementService(
        movement_repository=InventoryMovementRepository(db),
        ingredient_repository=IngredientRepository(db),
    )


@router.post(
    "",
    response_model=InventoryMovementResponse,
)
async def create_inventory_movement(
    restaurant_id: UUID,
    data: InventoryMovementCreate,
    db: AsyncSession = Depends(get_db),
):
    service = get_service(db)

    return await service.create_movement(
        restaurant_id=restaurant_id,
        data=data,
    )


@router.get(
    "",
    response_model=list[InventoryMovementResponse],
)
async def list_inventory_movements(
    restaurant_id: UUID,
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_service(db)

    return await service.list_movements(
        restaurant_id=restaurant_id,
        ingredient_id=ingredient_id,
    )