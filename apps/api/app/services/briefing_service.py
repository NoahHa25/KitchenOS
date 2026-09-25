from uuid import UUID

from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)


class BriefingService:
    def __init__(
        self,
        sales_service,
        ingredient_service,
        recipe_impact_service,
        purchase_recommendation_service,
        sales_intelligence_service,
        demand_forecast_service,
        recipe_ingredient_repository: RecipeIngredientRepository,
    ):
        self.sales_service = sales_service
        self.ingredient_service = ingredient_service
        self.recipe_impact_service = recipe_impact_service
        self.purchase_recommendation_service = (
            purchase_recommendation_service
        )
        self.sales_intelligence_service = (
            sales_intelligence_service
        )
        self.demand_forecast_service = (
            demand_forecast_service
        )
        self.recipe_ingredient_repository = (
            recipe_ingredient_repository
        )

    async def get_morning_brief(
        self,
        restaurant_id: UUID,
    ) -> dict:
        sales = await self.sales_service.get_sales_summary(
            restaurant_id=restaurant_id,
        )

        low_stock = await self.ingredient_service.get_low_stock(
            restaurant_id=restaurant_id,
        )

        recipe_impact = (
            await self.recipe_impact_service.get_low_stock_recipe_impact(
                restaurant_id=restaurant_id,
            )
        )

        purchase_recommendations = (
            await self.purchase_recommendation_service
            .get_purchase_recommendations(
                restaurant_id=restaurant_id,
            )
        )

        top_selling = (
            await self.sales_intelligence_service
            .get_top_selling_recipes(
                restaurant_id=restaurant_id,
            )
        )

        top_recipe = (
            top_selling[0]
            if top_selling
            else None
        )

        demand_forecast = []

        if top_recipe is not None:
            recipe_ingredients = (
                await self.recipe_ingredient_repository
                .get_by_recipe(
                    recipe_id=top_recipe["recipe_id"],
                )
            )

            for recipe_ingredient in recipe_ingredients:
                ingredient = recipe_ingredient.ingredient

                if ingredient is None:
                    continue

                forecast = (
                    await self.demand_forecast_service
                    .get_forecast(
                        restaurant_id=restaurant_id,
                        ingredient_name=ingredient.name,
                    )
                )

                if forecast is None:
                    continue

                demand_forecast.append(forecast)

        return {
            "sales": sales,
            "low_stock": low_stock,
            "recipe_impact": recipe_impact,
            "purchase_recommendations": (
                purchase_recommendations
            ),
            "top_recipe": top_recipe,
            "demand_forecast": demand_forecast,
        }

