from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.ingredient_repository import IngredientRepository
from app.schemas.ingredient import (
    IngredientCreate,
    IngredientResponse,
    IngredientUpdate,
)
from app.services.ingredient_service import IngredientService

router = APIRouter(
    prefix="/ingredients",
    tags=["Ingredients"],
)


@router.post("", response_model=IngredientResponse)
async def create_ingredient(
    data: IngredientCreate,
    db: AsyncSession = Depends(get_db),
):
    service = IngredientService(
        IngredientRepository(db),
    )

    return await service.create_ingredient(data)


@router.get(
    "",
    response_model=list[IngredientResponse],
)
async def list_ingredients(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = IngredientService(
        IngredientRepository(db),
    )

    return await service.list_ingredients(
        restaurant_id=restaurant_id,
    )


@router.get(
    "/{ingredient_id}",
    response_model=IngredientResponse,
)
async def get_ingredient(
    ingredient_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = IngredientService(
        IngredientRepository(db),
    )

    ingredient = await service.get_ingredient(
        restaurant_id=restaurant_id,
        ingredient_id=ingredient_id,
    )

    if ingredient is None:
        raise HTTPException(
            status_code=404,
            detail="Ingredient not found",
        )

    return ingredient


@router.patch(
    "/{ingredient_id}",
    response_model=IngredientResponse,
)
async def update_ingredient(
    ingredient_id: UUID,
    restaurant_id: UUID,
    data: IngredientUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = IngredientService(
        IngredientRepository(db),
    )

    ingredient = await service.update_ingredient(
        restaurant_id=restaurant_id,
        ingredient_id=ingredient_id,
        data=data,
    )

    if ingredient is None:
        raise HTTPException(
            status_code=404,
            detail="Ingredient not found",
        )

    return ingredient


@router.delete("/{ingredient_id}")
async def delete_ingredient(
    ingredient_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = IngredientService(
        IngredientRepository(db),
    )

    deleted = await service.delete_ingredient(
        restaurant_id=restaurant_id,
        ingredient_id=ingredient_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Ingredient not found",
        )

    return {
        "message": "Ingredient deleted successfully",
        "ingredient_id": ingredient_id,
    }