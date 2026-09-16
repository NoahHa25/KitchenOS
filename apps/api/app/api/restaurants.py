from uuid import UUID


from fastapi import APIRouter, Depends , HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantResponse,
    RestaurantUpdate,
)
from app.services.restaurant_service import RestaurantService


router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurants"],
)


@router.post("", response_model=RestaurantResponse)
async def create_restaurant(
    data: RestaurantCreate,
    db: AsyncSession = Depends(get_db),
):
    service = RestaurantService(
        RestaurantRepository(db),
    )

    return await service.create_restaurant(data)


@router.get("", response_model=list[RestaurantResponse])
async def list_restaurants(
    db: AsyncSession = Depends(get_db),
):
    service = RestaurantService(
        RestaurantRepository(db),
    )

    return await service.list_restaurants()

@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = RestaurantService(
        RestaurantRepository(db),
    )

    restaurant = await service.get_restaurant(restaurant_id)

    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    return restaurant

@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: UUID,
    data: RestaurantUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = RestaurantService(
        RestaurantRepository(db),
    )

    restaurant = await service.update_restaurant(
        restaurant_id,
        data,
    )

    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    return restaurant



@router.delete("/{restaurant_id}")
async def delete_restaurant(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = RestaurantService(
        RestaurantRepository(db),
    )

    deleted = await service.delete_restaurant(restaurant_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    return {
        "message": "Restaurant deleted successfully",
        "restaurant_id": restaurant_id,
    }