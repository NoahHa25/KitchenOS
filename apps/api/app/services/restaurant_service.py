from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate
from app.models.restaurant import Restaurant
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.recipe_ingredient_repository import RecipeIngredientRepository
from app.services.ingredient_service import IngredientService

class RestaurantService:
    def __init__(self, repository: RestaurantRepository):
        self.repository = repository

    async def create_restaurant(self, data: RestaurantCreate):
        return await self.repository.create(
            name=data.name,
            slug=data.slug,
        )

    async def list_restaurants(self):
        return await self.repository.get_all()

    async def get_restaurant(self, restaurant_id):
        return await self.repository.get_by_id(restaurant_id)

    async def update_restaurant(
        self,
        restaurant_id,
        data: RestaurantUpdate,
    ):
        return await self.repository.update(
            restaurant_id=restaurant_id,
            name=data.name,
            slug=data.slug,
        )

    async def delete_restaurant(self, restaurant_id):
        return await self.repository.delete(restaurant_id)