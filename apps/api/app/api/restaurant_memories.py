from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.restaurant_memory import RestaurantMemoryRepository
from app.schemas.restaurant_memory import (
    RestaurantMemoryCreate,
    RestaurantMemoryResponse,
    RestaurantMemoryUpdate,
)

router = APIRouter(
    prefix="/memories",
    tags=["Restaurant Memory"],
)


@router.post(
    "",
    response_model=RestaurantMemoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_memory(
    restaurant_id: UUID,
    payload: RestaurantMemoryCreate,
    db: AsyncSession = Depends(get_db),
):
    repository = RestaurantMemoryRepository(db)

    memory = await repository.create(
        restaurant_id=restaurant_id,
        memory_type=payload.memory_type,
        title=payload.title,
        description=payload.description,
        importance=payload.importance,
        tags=payload.tags,
    )

    await db.commit()

    return memory


@router.get(
    "",
    response_model=list[RestaurantMemoryResponse],
)
async def list_memories(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repository = RestaurantMemoryRepository(db)

    return await repository.list(
        restaurant_id=restaurant_id,
    )


@router.get(
    "/{memory_id}",
    response_model=RestaurantMemoryResponse,
)
async def get_memory(
    memory_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repository = RestaurantMemoryRepository(db)

    memory = await repository.get_by_id(
        restaurant_id=restaurant_id,
        memory_id=memory_id,
    )

    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant memory not found",
        )

    return memory


@router.patch(
    "/{memory_id}",
    response_model=RestaurantMemoryResponse,
)
async def update_memory(
    memory_id: UUID,
    restaurant_id: UUID,
    payload: RestaurantMemoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    repository = RestaurantMemoryRepository(db)

    memory = await repository.get_by_id(
        restaurant_id=restaurant_id,
        memory_id=memory_id,
    )

    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant memory not found",
        )

    updated_memory = await repository.update(
        memory,
        title=payload.title,
        description=payload.description,
        importance=payload.importance,
        tags=payload.tags,
        resolved_at=payload.resolved_at,
    )

    await db.commit()

    return updated_memory


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_memory(
    memory_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repository = RestaurantMemoryRepository(db)

    memory = await repository.get_by_id(
        restaurant_id=restaurant_id,
        memory_id=memory_id,
    )

    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant memory not found",
        )

    await repository.delete(memory)
    await db.commit()