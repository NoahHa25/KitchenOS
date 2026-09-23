from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.assistant_service import AssistantService
from app.services.food_cost_service import FoodCostService
from app.services.ingredient_service import IngredientService
from app.services.sales_service import SalesService
from app.services.recipe_impact_service import RecipeImpactService


router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"],
)


def get_assistant_service(
    db: AsyncSession = Depends(get_db),
) -> AssistantService:
    ingredient_repository = IngredientRepository(db)
    recipe_repository = RecipeRepository(db)
    recipe_ingredient_repository = RecipeIngredientRepository(db)
    order_repository = OrderRepository(db)

    ingredient_service = IngredientService(
        repository=ingredient_repository,
    )

    food_cost_service = FoodCostService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        ingredient_repository=ingredient_repository,
    )

    sales_service = SalesService(
        order_repository=order_repository,
    )

    return AssistantService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        food_cost_service=food_cost_service,
        ingredient_service=ingredient_service,
        sales_service=sales_service,
        recipe_impact_service=RecipeImpactService(
            recipe_repository=recipe_repository,
            recipe_ingredient_repository=recipe_ingredient_repository,
            ingredient_repository=ingredient_repository,
        ),
    )


@router.post(
    "",
    response_model=AssistantResponse,
)
async def assistant(
    data: AssistantRequest,
    service: AssistantService = Depends(
        get_assistant_service,
    ),
):
    result = await service.answer(
        restaurant_id=data.restaurant_id,
        query=data.query,
    )

    return AssistantResponse(**result)
