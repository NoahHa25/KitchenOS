from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository

from app.schemas.assistant import (
    AssistantRequest,
    AssistantResponse,
)
from app.schemas.briefing import MorningBriefResponse

from app.services.assistant_service import AssistantService
from app.services.briefing_service import BriefingService
from app.services.demand_forecast_service import DemandForecastService
from app.services.ingredient_service import IngredientService
from app.services.purchase_intelligence_service import (
    PurchaseIntelligenceService,
)
from app.services.purchase_recommendation_service import (
    PurchaseRecommendationService,
)
from app.services.recipe_impact_service import RecipeImpactService
from app.services.sales_intelligence_service import SalesIntelligenceService
from app.services.sales_service import SalesService


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

    purchase_recommendation_service = PurchaseRecommendationService(
        ingredient_service=ingredient_service,
    )

    sales_service = SalesService(
        order_repository=order_repository,
    )

    sales_intelligence_service = SalesIntelligenceService(
        order_repository=order_repository,
        recipe_repository=recipe_repository,
    )

    recipe_impact_service = RecipeImpactService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        ingredient_service=ingredient_service,
    )

    purchase_intelligence_service = PurchaseIntelligenceService(
        ingredient_service=ingredient_service,
        purchase_recommendation_service=(
            purchase_recommendation_service
        ),
        recipe_impact_service=recipe_impact_service,
        sales_intelligence_service=sales_intelligence_service,
    )

    return AssistantService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        ingredient_service=ingredient_service,
        sales_service=sales_service,
        sales_intelligence_service=sales_intelligence_service,
        recipe_impact_service=recipe_impact_service,
        purchase_recommendation_service=(
            purchase_recommendation_service
        ),
        purchase_intelligence_service=(
            purchase_intelligence_service
        ),
    )


def get_briefing_service(
    db: AsyncSession = Depends(get_db),
) -> BriefingService:
    ingredient_repository = IngredientRepository(db)
    recipe_repository = RecipeRepository(db)
    recipe_ingredient_repository = RecipeIngredientRepository(db)
    order_repository = OrderRepository(db)

    ingredient_service = IngredientService(
        repository=ingredient_repository,
    )

    recipe_impact_service = RecipeImpactService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        ingredient_service=ingredient_service,
    )

    purchase_recommendation_service = (
        PurchaseRecommendationService(
            ingredient_service=ingredient_service,
        )
    )

    sales_intelligence_service = SalesIntelligenceService(
        order_repository=order_repository,
        recipe_repository=recipe_repository,
    )

    purchase_intelligence_service = (
        PurchaseIntelligenceService(
            ingredient_service=ingredient_service,
            purchase_recommendation_service=(
                purchase_recommendation_service
            ),
            recipe_impact_service=recipe_impact_service,
            sales_intelligence_service=sales_intelligence_service,
        )
    )

    sales_service = SalesService(
        order_repository=order_repository,
    )

    demand_forecast_service = DemandForecastService(
        order_repository=order_repository,
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        ingredient_service=ingredient_service,
    )

    return BriefingService(
        sales_service=sales_service,
        ingredient_service=ingredient_service,
        recipe_impact_service=recipe_impact_service,
        purchase_recommendation_service=(
            purchase_recommendation_service
        ),
        sales_intelligence_service=sales_intelligence_service,
        demand_forecast_service=demand_forecast_service,
        recipe_ingredient_repository=recipe_ingredient_repository,
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


@router.get(
    "/briefing/morning/{restaurant_id}",
    response_model=MorningBriefResponse,
)
async def morning_brief(
    restaurant_id: UUID,
    service: BriefingService = Depends(
        get_briefing_service,
    ),
):
    return await service.get_morning_brief(
        restaurant_id=restaurant_id,
    )