from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from app.repositories.restaurant_insight_repository import (
    RestaurantInsightRepository,
)
from app.repositories.restaurant_memory import (
    RestaurantMemoryRepository,
)
from app.schemas.digital_twin import DigitalTwinResponse
from app.services.digital_twin_service import DigitalTwinService
from app.services.sales_service import SalesService


router = APIRouter(
    prefix="/restaurants",
    tags=["Digital Twin"],
)


def get_digital_twin_service(
    db: AsyncSession = Depends(get_db),
) -> DigitalTwinService:
    order_repository = OrderRepository(db)
    ingredient_repository = IngredientRepository(db)
    purchase_order_repository = PurchaseOrderRepository(db)
    restaurant_memory_repository = RestaurantMemoryRepository(db)
    restaurant_insight_repository = RestaurantInsightRepository(db)

    sales_service = SalesService(
        order_repository=order_repository,
    )

    return DigitalTwinService(
        order_repository=order_repository,
        ingredient_repository=ingredient_repository,
        purchase_order_repository=purchase_order_repository,
        restaurant_memory_repository=restaurant_memory_repository,
        restaurant_insight_repository=restaurant_insight_repository,
        sales_service=sales_service,
    )


@router.get(
    "/{restaurant_id}/digital-twin",
    response_model=DigitalTwinResponse,
)
async def get_digital_twin(
    restaurant_id: UUID,
    service: DigitalTwinService = Depends(
        get_digital_twin_service,
    ),
):
    return await service.get_restaurant_twin(
        restaurant_id=restaurant_id,
    )