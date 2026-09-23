from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.recipe_ingredient import RecipeIngredient


class RecipeIngredientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        recipe_id: UUID,
        ingredient_id: UUID,
        quantity: float,
    ) -> RecipeIngredient:
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
        )

        self.db.add(recipe_ingredient)
        await self.db.flush()

        return recipe_ingredient

    async def get_by_id(
        self,
        recipe_ingredient_id: UUID,
    ) -> RecipeIngredient | None:
        result = await self.db.execute(
            select(RecipeIngredient)
            .where(
                RecipeIngredient.id == recipe_ingredient_id
            )
            .options(
                selectinload(RecipeIngredient.ingredient)
            )
        )

        return result.scalar_one_or_none()

    async def get_by_recipe(
        self,
        recipe_id: UUID,
    ) -> list[RecipeIngredient]:
        result = await self.db.execute(
            select(RecipeIngredient)
            .where(
                RecipeIngredient.recipe_id == recipe_id
            )
            .options(
                selectinload(RecipeIngredient.ingredient)
            )
            .order_by(RecipeIngredient.id)
        )

        return list(result.scalars().all())

    async def get_by_recipe_and_ingredient(
        self,
        recipe_id: UUID,
        ingredient_id: UUID,
    ) -> RecipeIngredient | None:
        result = await self.db.execute(
            select(RecipeIngredient)
            .where(
                RecipeIngredient.recipe_id == recipe_id,
                RecipeIngredient.ingredient_id == ingredient_id,
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        recipe_ingredient: RecipeIngredient,
        quantity: float,
    ) -> RecipeIngredient:
        recipe_ingredient.quantity = quantity

        await self.db.flush()

        return recipe_ingredient

    async def delete(
        self,
        recipe_ingredient: RecipeIngredient,
    ) -> None:
        await self.db.delete(recipe_ingredient)
        await self.db.flush()