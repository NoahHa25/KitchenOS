from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.repositories.restaurant_insight_repository import (
    RestaurantInsightRepository,
)
from app.schemas.restaurant_insight import RestaurantInsightResponse
from app.services.restaurant_brain_analysis_service import (
    RestaurantBrainAnalysisService,
)
from app.services.restaurant_brain_service import RestaurantBrainService


router = APIRouter(
    prefix="/restaurants/{restaurant_id}/brain",
    tags=["Restaurant Brain"],
)


def get_brain_analysis_service(
    db: AsyncSession = Depends(get_db),
) -> RestaurantBrainAnalysisService:
    inventory_repository = InventoryMovementRepository(db)
    insight_repository = RestaurantInsightRepository(db)
    brain_service = RestaurantBrainService(insight_repository)

    return RestaurantBrainAnalysisService(
        inventory_repository=inventory_repository,
        brain_service=brain_service,
    )


@router.post(
    "/analyze",
    response_model=list[RestaurantInsightResponse],
    status_code=status.HTTP_200_OK,
)
async def analyze_restaurant(
    restaurant_id: UUID,
    service: RestaurantBrainAnalysisService = Depends(
        get_brain_analysis_service,
    ),
):
    return await service.detect_repeated_waste(
        restaurant_id=restaurant_id,
        lookback_days=30,
        threshold=3,
    )