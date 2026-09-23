import re
from decimal import Decimal
from uuid import UUID

from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.services.food_cost_service import FoodCostService


class AssistantService:
    """
    KitchenOS Intelligence Layer.

    The Assistant does not own restaurant business logic.

    It detects what the user is asking and delegates the actual
    data retrieval/calculation to KitchenOS repositories and services.
    """

    def __init__(
        self,
        recipe_repository: RecipeRepository,
        recipe_ingredient_repository: RecipeIngredientRepository,
        food_cost_service: FoodCostService,
    ):
        self.recipe_repository = recipe_repository
        self.recipe_ingredient_repository = (
            recipe_ingredient_repository
        )
        self.food_cost_service = food_cost_service

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def _detect_intent(self, message: str) -> str:
        text = message.lower().strip()

        if self._is_food_cost_question(text):
            return "food_cost"

        if self._is_ingredient_question(text):
            return "ingredient_lookup"

        if self._is_recipe_question(text):
            return "recipe_lookup"

        return "unknown"

    def _is_food_cost_question(self, text: str) -> bool:
        patterns = [
            r"\bfood cost\b",
            r"\bfoodcost\b",
            r"\bcost of\b",
            r"\bcost for\b",
            r"\bhow much does .+ cost\b",
            r"\bhow much is .+\b",
        ]

        return any(
            re.search(pattern, text)
            for pattern in patterns
        )

    def _is_ingredient_question(self, text: str) -> bool:
        patterns = [
            r"\bingredients?\s+(?:for|of)\b",
            r"\bwhat ingredients are in\b",
            r"\bwhat ingredients does\b",
            r"\bwhat is in\b",
        ]

        return any(
            re.search(pattern, text)
            for pattern in patterns
        )

    def _is_recipe_question(self, text: str) -> bool:
        patterns = [
            r"\brecipe\s+(?:for|of)\b",
            r"\bwhat(?:'s| is)\s+the\s+recipe\b",
            r"\bhow do i make\b",
            r"\bhow to make\b",
            r"\bhow can i make\b",
        ]

        return any(
            re.search(pattern, text)
            for pattern in patterns
        )

    # ------------------------------------------------------------------
    # Query extraction
    # ------------------------------------------------------------------

    def _extract_recipe_query(self, message: str) -> str:
        text = message.lower().strip()

        patterns = [
            r"what(?:'s| is)\s+the\s+recipe\s+for\s+(.+)",
            r"what(?:'s| is)\s+the\s+recipe\s+of\s+(.+)",
            r"recipe\s+for\s+(.+)",
            r"recipe\s+of\s+(.+)",
            r"how\s+do\s+i\s+make\s+(.+)",
            r"how\s+to\s+make\s+(.+)",
            r"how\s+can\s+i\s+make\s+(.+)",
            r"ingredients?\s+for\s+(.+)",
            r"ingredients?\s+of\s+(.+)",
            r"what\s+ingredients?\s+are\s+in\s+(.+)",
            r"what\s+ingredients?\s+does\s+(.+?)\s+have",
            r"what\s+is\s+in\s+(.+)",
            r"food\s+cost\s+(?:for|of)\s+(.+)",
            r"cost\s+(?:for|of)\s+(.+)",
            r"how\s+much\s+does\s+(.+?)\s+cost",
            r"how\s+much\s+is\s+(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return match.group(1).strip(
                    " ?!.,:;"
                )

        return text.strip(" ?!.,:;")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def answer(
        self,
        restaurant_id: UUID,
        message: str,
    ) -> dict:
        text = message.strip()

        if not text:
            return {
                "intent": "unknown",
                "answer": (
                    "Please tell me what you would like to know."
                ),
            }

        intent = self._detect_intent(text)

        if intent == "recipe_lookup":
            return await self._answer_recipe_lookup(
                restaurant_id=restaurant_id,
                message=text,
            )

        if intent == "ingredient_lookup":
            return await self._answer_ingredient_lookup(
                restaurant_id=restaurant_id,
                message=text,
            )

        if intent == "food_cost":
            return await self._answer_food_cost(
                restaurant_id=restaurant_id,
                message=text,
            )

        return {
            "intent": "unknown",
            "answer": (
                "I can currently help with recipes, "
                "ingredients, and food costs. "
                "Try asking about a recipe."
            ),
        }

    # ------------------------------------------------------------------
    # Recipe lookup
    # ------------------------------------------------------------------

    async def _answer_recipe_lookup(
        self,
        restaurant_id: UUID,
        message: str,
    ) -> dict:
        recipe_query = self._extract_recipe_query(message)

        recipe = await self.recipe_repository.find_by_name(
            restaurant_id=restaurant_id,
            query=recipe_query,
        )

        if recipe is None:
            return {
                "intent": "recipe_lookup",
                "answer": (
                    f"I couldn't find a recipe matching "
                    f'"{recipe_query}".'
                ),
            }

        ingredients = (
            await self.recipe_ingredient_repository.get_by_recipe(
                recipe.id
            )
        )

        lines = [
            f"**{recipe.name}**",
        ]

        if recipe.description:
            lines.extend(
                [
                    "",
                    recipe.description,
                ]
            )

        lines.extend(
            [
                "",
                "Ingredients:",
            ]
        )

        if not ingredients:
            lines.append(
                "No ingredients have been added yet."
            )
        else:
            for item in ingredients:
                if item.ingredient is None:
                    continue

                lines.append(
                    f"• {item.ingredient.name} — "
                    f"{item.quantity} "
                    f"{item.ingredient.unit}"
                )

        return {
            "intent": "recipe_lookup",
            "answer": "\n".join(lines),
        }

    # ------------------------------------------------------------------
    # Ingredient lookup
    # ------------------------------------------------------------------

    async def _answer_ingredient_lookup(
        self,
        restaurant_id: UUID,
        message: str,
    ) -> dict:
        recipe_query = self._extract_recipe_query(message)

        recipe = await self.recipe_repository.find_by_name(
            restaurant_id=restaurant_id,
            query=recipe_query,
        )

        if recipe is None:
            return {
                "intent": "ingredient_lookup",
                "answer": (
                    f"I couldn't find a recipe matching "
                    f'"{recipe_query}".'
                ),
            }

        ingredients = (
            await self.recipe_ingredient_repository.get_by_recipe(
                recipe.id
            )
        )

        lines = [
            f"**{recipe.name}** uses:",
        ]

        valid_ingredients = [
            item
            for item in ingredients
            if item.ingredient is not None
        ]

        if not valid_ingredients:
            lines.append(
                "No ingredients have been added yet."
            )
        else:
            for item in valid_ingredients:
                lines.append(
                    f"• {item.ingredient.name} — "
                    f"{item.quantity} "
                    f"{item.ingredient.unit}"
                )

        return {
            "intent": "ingredient_lookup",
            "answer": "\n".join(lines),
        }

    # ------------------------------------------------------------------
    # Food cost
    # ------------------------------------------------------------------

    async def _answer_food_cost(
        self,
        restaurant_id: UUID,
        message: str,
    ) -> dict:
        recipe_query = self._extract_recipe_query(message)

        recipe = await self.recipe_repository.find_by_name(
            restaurant_id=restaurant_id,
            query=recipe_query,
        )

        if recipe is None:
            return {
                "intent": "food_cost",
                "answer": (
                    f"I couldn't find a recipe matching "
                    f'"{recipe_query}".'
                ),
            }

        food_cost = (
            await self.food_cost_service.calculate_food_cost(
                restaurant_id=restaurant_id,
                recipe_id=recipe.id,
            )
        )

        if food_cost is None:
            return {
                "intent": "food_cost",
                "answer": (
                    f"I couldn't calculate the food cost "
                    f"for {recipe.name}."
                ),
            }

        selling_price = Decimal(str(recipe.selling_price))
        total_food_cost = Decimal(
            str(food_cost["food_cost"])
        )

        estimated_profit = (
            selling_price - total_food_cost
        ).quantize(
            Decimal("0.01")
        )

        if selling_price > 0:
            margin = (
                estimated_profit / selling_price * Decimal("100")
            ).quantize(
                Decimal("0.01")
            )
        else:
            margin = Decimal("0.00")

        lines = [
            f"**{recipe.name} — Food Cost**",
            "",
            f"Food cost: {total_food_cost:.2f}",
            f"Selling price: {selling_price:.2f}",
            f"Estimated profit: {estimated_profit:.2f}",
            f"Margin: {margin:.2f}%",
        ]

        if food_cost["breakdown"]:
            lines.extend(
                [
                    "",
                    "Cost breakdown:",
                ]
            )

            for item in food_cost["breakdown"]:
                lines.append(
                    f"• {item['ingredient']} — "
                    f"{item['quantity']} × "
                    f"{item['cost_per_unit']:.2f} = "
                    f"{item['total_cost']:.2f}"
                )

        return {
            "intent": "food_cost",
            "answer": "\n".join(lines),
        }