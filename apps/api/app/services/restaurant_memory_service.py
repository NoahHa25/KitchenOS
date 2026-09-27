from datetime import datetime
from uuid import UUID

from app.models.restaurant_memory import RestaurantMemory
from app.repositories.restaurant_memory import RestaurantMemoryRepository


class RestaurantMemoryService:
    def __init__(self, repository: RestaurantMemoryRepository):
        self.repository = repository

    async def create_memory(
        self,
        *,
        restaurant_id: UUID,
        memory_type: str,
        title: str,
        description: str,
        importance: str = "medium",
        tags: str | None = None,
    ) -> RestaurantMemory:
        return await self.repository.create(
            restaurant_id=restaurant_id,
            memory_type=memory_type,
            title=title,
            description=description,
            importance=importance,
            tags=tags,
        )

    async def get_memory(
        self,
        *,
        restaurant_id: UUID,
        memory_id: UUID,
    ) -> RestaurantMemory | None:
        return await self.repository.get_by_id(
            restaurant_id=restaurant_id,
            memory_id=memory_id,
        )

    async def list_memories(
        self,
        *,
        restaurant_id: UUID,
    ) -> list[RestaurantMemory]:
        return await self.repository.list(
            restaurant_id=restaurant_id,
        )

    async def update_memory(
        self,
        memory: RestaurantMemory,
        *,
        title: str | None = None,
        description: str | None = None,
        importance: str | None = None,
        tags: str | None = None,
        resolved_at: datetime | None = None,
    ) -> RestaurantMemory:
        return await self.repository.update(
            memory,
            title=title,
            description=description,
            importance=importance,
            tags=tags,
            resolved_at=resolved_at,
        )

    async def delete_memory(
        self,
        memory: RestaurantMemory,
    ) -> None:
        await self.repository.delete(memory)