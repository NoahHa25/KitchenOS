from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant_memory import RestaurantMemory


class RestaurantMemoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        restaurant_id: UUID,
        memory_type: str,
        title: str,
        description: str,
        importance: str = "medium",
        tags: str | None = None,
    ) -> RestaurantMemory:
        memory = RestaurantMemory(
            restaurant_id=restaurant_id,
            memory_type=memory_type,
            title=title,
            description=description,
            importance=importance,
            tags=tags,
        )

        self.db.add(memory)
        await self.db.flush()
        await self.db.refresh(memory)

        return memory

    async def get_by_id(
        self,
        *,
        restaurant_id: UUID,
        memory_id: UUID,
    ) -> RestaurantMemory | None:
        result = await self.db.execute(
            select(RestaurantMemory).where(
                RestaurantMemory.id == memory_id,
                RestaurantMemory.restaurant_id == restaurant_id,
            )
        )

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        restaurant_id: UUID,
    ) -> list[RestaurantMemory]:
        result = await self.db.execute(
            select(RestaurantMemory)
            .where(RestaurantMemory.restaurant_id == restaurant_id)
            .order_by(RestaurantMemory.created_at.desc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        memory: RestaurantMemory,
        *,
        title: str | None = None,
        description: str | None = None,
        importance: str | None = None,
        tags: str | None = None,
        resolved_at=None,
    ) -> RestaurantMemory:
        if title is not None:
            memory.title = title

        if description is not None:
            memory.description = description

        if importance is not None:
            memory.importance = importance

        if tags is not None:
            memory.tags = tags

        if resolved_at is not None:
            memory.resolved_at = resolved_at

        await self.db.flush()
        await self.db.refresh(memory)

        return memory

    async def delete(self, memory: RestaurantMemory) -> None:
        await self.db.delete(memory)
        await self.db.flush()