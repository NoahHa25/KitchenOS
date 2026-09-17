from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository

from app.schemas.food_cost import FoodCostResponse
from app.schemas.recipe import (
    RecipeCreate,
    RecipeResponse,
    RecipeUpdate,
)
from app.schemas.recipe_ingredient import (
    RecipeIngredientCreate,
    RecipeIngredientResponse,
    RecipeIngredientUpdate,
)

from app.services.food_cost_service import FoodCostService
from app.services.ingredient_service import IngredientService
from app.services.recipe_ingredient_service import (
    RecipeIngredientService,
)
from app.services.recipe_service import RecipeService

router = APIRouter(
    prefix="/recipes",
    tags=["Recipes"],
)


# ---------- Service Builders ----------

def get_recipe_service(db: AsyncSession) -> RecipeService:
    return RecipeService(
        RecipeRepository(db),
    )


def get_recipe_ingredient_service(
    db: AsyncSession,
) -> RecipeIngredientService:
    ingredient_repository = IngredientRepository(db)

    return RecipeIngredientService(
        repository=RecipeIngredientRepository(db),
        recipe_repository=RecipeRepository(db),
        ingredient_service=IngredientService(ingredient_repository),
    )


def get_food_cost_service(db: AsyncSession) -> FoodCostService:
    return FoodCostService(
        recipe_repository=RecipeRepository(db),
        recipe_ingredient_repository=RecipeIngredientRepository(db),
        ingredient_repository=IngredientRepository(db),
    )


# ---------- Recipe CRUD ----------

@router.post(
    "",
    response_model=RecipeResponse,
)
async def create_recipe(
    data: RecipeCreate,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_service(db)

    return await service.create_recipe(data)


@router.get(
    "",
    response_model=list[RecipeResponse],
)
async def list_recipes(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_service(db)

    return await service.list_recipes(
        restaurant_id=restaurant_id,
    )


@router.get(
    "/{recipe_id}",
    response_model=RecipeResponse,
)
async def get_recipe(
    recipe_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_service(db)

    recipe = await service.get_recipe(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
    )

    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found",
        )

    return recipe


@router.patch(
    "/{recipe_id}",
    response_model=RecipeResponse,
)
async def update_recipe(
    recipe_id: UUID,
    restaurant_id: UUID,
    data: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_service(db)

    recipe = await service.update_recipe(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
        data=data,
    )

    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found",
        )

    return recipe


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_service(db)

    deleted = await service.delete_recipe(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found",
        )

    return {
        "message": "Recipe deleted successfully",
        "recipe_id": recipe_id,
    }


# ---------- Recipe Ingredients ----------

@router.post(
    "/{recipe_id}/ingredients",
    response_model=RecipeIngredientResponse,
)
async def add_recipe_ingredient(
    recipe_id: UUID,
    restaurant_id: UUID,
    data: RecipeIngredientCreate,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_ingredient_service(db)

    recipe_ingredient = await service.add_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
        data=data,
    )

    if recipe_ingredient is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe or ingredient not found",
        )

    return recipe_ingredient


@router.get(
    "/{recipe_id}/ingredients",
    response_model=list[RecipeIngredientResponse],
)
async def list_recipe_ingredients(
    recipe_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_ingredient_service(db)

    recipe_ingredients = await service.list_ingredients(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
    )

    if recipe_ingredients is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found",
        )

    return recipe_ingredients


@router.patch(
    "/{recipe_id}/ingredients/{recipe_ingredient_id}",
    response_model=RecipeIngredientResponse,
)
async def update_recipe_ingredient(
    recipe_id: UUID,
    recipe_ingredient_id: UUID,
    restaurant_id: UUID,
    data: RecipeIngredientUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_ingredient_service(db)

    recipe_ingredient = await service.update_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
        recipe_ingredient_id=recipe_ingredient_id,
        data=data,
    )

    if recipe_ingredient is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe ingredient not found",
        )

    return recipe_ingredient


@router.delete(
    "/{recipe_id}/ingredients/{recipe_ingredient_id}",
)
async def delete_recipe_ingredient(
    recipe_id: UUID,
    recipe_ingredient_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_recipe_ingredient_service(db)

    deleted = await service.delete_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
        recipe_ingredient_id=recipe_ingredient_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Recipe ingredient not found",
        )

    return {
        "message": "Recipe ingredient deleted successfully",
        "recipe_ingredient_id": recipe_ingredient_id,
    }


# ---------- Food Cost ----------

@router.get(
    "/{recipe_id}/food-cost",
    response_model=FoodCostResponse,
)
async def get_food_cost(
    recipe_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = get_food_cost_service(db)

    result = await service.calculate_food_cost(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found",
        )

    return result