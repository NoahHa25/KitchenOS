from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.assistant import (
    AssistantRequest,
    AssistantResponse,
)
from app.services.assistant_service import AssistantService
from app.services.food_cost_service import FoodCostService


router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"],
)


def get_assistant_service(
    db: AsyncSession,
) -> AssistantService:
    recipe_repository = RecipeRepository(db)
    recipe_ingredient_repository = RecipeIngredientRepository(db)

    food_cost_service = FoodCostService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        ingredient_repository=IngredientRepository(db),
    )

    return AssistantService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        food_cost_service=food_cost_service,
    )


@router.post(
    "",
    response_model=AssistantResponse,
)
async def ask_assistant(
    data: AssistantRequest,
    db: AsyncSession = Depends(get_db),
):
    service = get_assistant_service(db)

    result = await service.answer(
        restaurant_id=data.restaurant_id,
        message=data.query,
    )

    return AssistantResponse(**result)