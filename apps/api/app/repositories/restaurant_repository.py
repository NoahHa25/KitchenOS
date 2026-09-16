from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Restaurant


class RestaurantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, slug: str) -> Restaurant:
        restaurant = Restaurant(
            name=name,
            slug=slug,
        )

        self.db.add(restaurant)
        await self.db.commit()
        await self.db.refresh(restaurant)

        return restaurant

    async def get_all(self) -> list[Restaurant]:
        result = await self.db.execute(select(Restaurant))
        return list(result.scalars().all())

    async def get_by_id(self, restaurant_id) -> Restaurant | None:
        return await self.db.get(Restaurant, restaurant_id)

    async def update(
        self,
        restaurant_id,
        name: str | None = None,
        slug: str | None = None,
    ) -> Restaurant | None:
        restaurant = await self.db.get(Restaurant, restaurant_id)

        if restaurant is None:
            return None

        if name is not None:
            restaurant.name = name

        if slug is not None:
            restaurant.slug = slug

        await self.db.commit()
        await self.db.refresh(restaurant)

        return restaurant

    async def delete(self, restaurant_id) -> bool:
        restaurant = await self.db.get(Restaurant, restaurant_id)

        if restaurant is None:
            return False

        await self.db.delete(restaurant)
        await self.db.commit()

        return True