from uuid import UUID

from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recipe import RecipeCreate, RecipeUpdate


class RecipeService:
    def __init__(self, repository: RecipeRepository):
        self.repository = repository

    async def create_recipe(
        self,
        data: RecipeCreate,
    ):
        recipe = await self.repository.create(
            restaurant_id=data.restaurant_id,
            name=data.name,
            description=data.description,
            selling_price=data.selling_price,
            portion_size=data.portion_size,
            portion_unit=data.portion_unit,
            is_active=data.is_active,
        )

        await self.repository.db.commit()
        await self.repository.db.refresh(recipe)

        return recipe

    async def list_recipes(
        self,
        restaurant_id: UUID,
    ):
        return await self.repository.get_all(
            restaurant_id=restaurant_id,
        )

    async def get_recipe(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
    ):
        return await self.repository.get_by_id(
            restaurant_id=restaurant_id,
            recipe_id=recipe_id,
        )

    async def update_recipe(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
        data: RecipeUpdate,
    ):
        recipe = await self.repository.get_by_id(
            restaurant_id=restaurant_id,
            recipe_id=recipe_id,
        )

        if recipe is None:
            return None

        recipe = await self.repository.update(
            recipe=recipe,
            name=data.name,
            description=data.description,
            selling_price=data.selling_price,
            portion_size=data.portion_size,
            portion_unit=data.portion_unit,
            is_active=data.is_active,
        )

        await self.repository.db.commit()
        await self.repository.db.refresh(recipe)

        return recipe

    async def delete_recipe(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
    ):
        recipe = await self.repository.get_by_id(
            restaurant_id=restaurant_id,
            recipe_id=recipe_id,
        )

        if recipe is None:
            return False

        await self.repository.delete(recipe)

        await self.repository.db.commit()

        return True