from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe


class RecipeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        restaurant_id: UUID,
        name: str,
        description: str | None = None,
    ) -> Recipe:
        recipe = Recipe(
            restaurant_id=restaurant_id,
            name=name,
            description=description,
        )

        self.db.add(recipe)
        await self.db.flush()

        return recipe

    async def get_by_id(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
    ) -> Recipe | None:
        result = await self.db.execute(
            select(Recipe).where(
                Recipe.id == recipe_id,
                Recipe.restaurant_id == restaurant_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
        restaurant_id: UUID,
    ) -> list[Recipe]:
        result = await self.db.execute(
            select(Recipe)
            .where(
                Recipe.restaurant_id == restaurant_id
            )
            .order_by(Recipe.created_at.desc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        recipe: Recipe,
        name: str | None = None,
        description: str | None = None,
    ) -> Recipe:
        if name is not None:
            recipe.name = name

        if description is not None:
            recipe.description = description

        await self.db.flush()

        return recipe

    async def delete(
        self,
        recipe: Recipe,
    ) -> None:
        await self.db.delete(recipe)
        await self.db.flush()