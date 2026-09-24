import re
from decimal import Decimal
from uuid import UUID

from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.services.food_cost_service import FoodCostService
from app.services.ingredient_service import IngredientService
from app.services.recipe_impact_service import RecipeImpactService
from app.services.sales_service import SalesService
from app.services.sales_intelligence_service import (
    SalesIntelligenceService,
)
from app.services.purchase_recommendation_service import (
    PurchaseRecommendationService,
)


class AssistantService:
    def __init__(
        self,
        recipe_repository,
        recipe_ingredient_repository,
        food_cost_service,
        ingredient_service,
        sales_service,
        sales_intelligence_service,
        recipe_impact_service,
        purchase_recommendation_service,
        purchase_intelligence_service,
    ):
        self.recipe_repository = recipe_repository
        self.recipe_ingredient_repository = recipe_ingredient_repository
        self.food_cost_service = food_cost_service
        self.ingredient_service = ingredient_service
        self.sales_service = sales_service
        self.sales_intelligence_service = sales_intelligence_service
        self.recipe_impact_service = recipe_impact_service
        self.purchase_recommendation_service = (
            purchase_recommendation_service
        )
        self.purchase_intelligence_service = (
            purchase_intelligence_service
        )

    async def answer(
        self,
        restaurant_id: UUID,
        query: str,
    ) -> dict:
        normalized_query = query.strip()

        if not normalized_query:
            return {
                "intent": "unknown",
                "answer": "Please tell me what you would like to know.",
            }

        intent = self.detect_intent(normalized_query)

        if intent == "recipe_lookup":
            return {
                "intent": intent,
                "answer": await self._answer_recipe_lookup(
                    restaurant_id=restaurant_id,
                    query=normalized_query,
                ),
            }

        if intent == "ingredient_lookup":
            return {
                "intent": intent,
                "answer": await self._answer_ingredient_lookup(
                    restaurant_id=restaurant_id,
                    query=normalized_query,
                ),
            }

        if intent == "food_cost":
            return {
                "intent": intent,
                "answer": await self._answer_food_cost(
                    restaurant_id=restaurant_id,
                    query=normalized_query,
                ),
            }

        if intent == "inventory_status":
            return {
                "intent": intent,
                "answer": await self._answer_inventory_status(
                    restaurant_id=restaurant_id,
                    query=normalized_query,
                ),
            }

        if intent == "recipe_impact":
            return {
                "intent": intent,
                "answer": await self._answer_recipe_impact(
                    restaurant_id=restaurant_id,
                ),
            }

        if intent == "purchase_intelligence":
            return {
                "intent": intent,
                "answer": await self._answer_purchase_intelligence(
                    restaurant_id=restaurant_id,
                    query=normalized_query,
                ),
            }

        if intent == "purchase_recommendations":
            return await self._handle_purchase_recommendations(
                restaurant_id=restaurant_id,
            )

        if intent == "low_stock":
            return {
                "intent": intent,
                "answer": await self._answer_low_stock(
                    restaurant_id=restaurant_id,
                ),
            }

        if intent == "sales_summary":
            return {
                "intent": intent,
                "answer": await self._answer_sales_summary(
                    restaurant_id=restaurant_id,
                ),
            }

        if intent == "top_selling_recipes":
            return {
                "intent": intent,
                "answer": await self._answer_top_selling_recipes(
                    restaurant_id=restaurant_id,
                ),
            }

        return {
            "intent": "unknown",
            "answer": (
                "I can currently help with recipes, ingredients, "
                "food costs, inventory status, low-stock items, "
                "purchase recommendations, purchase intelligence, "
                "recipes affected by low stock, sales summaries, "
                "and top-selling recipes."
            ),
        }

    def detect_intent(
        self,
        query: str,
    ) -> str:
        normalized = query.strip().lower()

        if not normalized:
            return "unknown"

        if self._is_recipe_impact_question(normalized):
            return "recipe_impact"

        if self._is_purchase_intelligence_question(normalized):
            return "purchase_intelligence"

        # Purchase recommendations must be checked before low stock.
        if self._is_purchase_question(normalized):
            return "purchase_recommendations"

        if self._is_low_stock_question(normalized):
            return "low_stock"

        if self._is_top_selling_question(normalized):
            return "top_selling_recipes"

        if self._is_sales_question(normalized):
            return "sales_summary"

        if self._is_food_cost_question(normalized):
            return "food_cost"

        if self._is_inventory_status_question(normalized):
            return "inventory_status"

        if self._is_ingredient_question(normalized):
            return "ingredient_lookup"

        if self._is_recipe_question(normalized):
            return "recipe_lookup"

        return "unknown"

    def _is_purchase_intelligence_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\bwhy\s+should\s+we\s+buy\b",
            r"\bwhy\s+do\s+we\s+need\s+to\s+buy\b",
            r"\bwhy\s+should\s+we\s+purchase\b",
            r"\bwhy\s+do\s+we\s+need\s+to\s+purchase\b",
            r"\bwhy\s+buy\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _is_purchase_question(
        self,
        query: str,
    ) -> bool:
        purchase_keywords = (
            "what should we buy",
            "what do we need to buy",
            "purchase recommendations",
            "buy today",
            "shopping list",
            "restock",
        )

        return any(
            keyword in query
            for keyword in purchase_keywords
        )

    def _is_recipe_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\brecipe\b",
            r"\bhow\s+(?:do\s+i|can\s+i)\s+(?:make|cook|prepare)\b",
            r"\bhow\s+to\s+(?:make|cook|prepare)\b",
            r"\bmake\s+(?:a|the)?\s*recipe\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _is_ingredient_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\bingredients?\b",
            r"\bwhat\s+is\s+in\b",
            r"\bwhat\s+are\s+in\b",
            r"\bwhat\s+goes\s+into\b",
            r"\bwhat\s+do\s+i\s+need\s+for\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _is_food_cost_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\bfood\s+cost\b",
            r"\bcost\s+of\b",
            r"\bhow\s+much\s+does\b.*\bcost\b",
            r"\bhow\s+much\s+does\s+it\s+cost\b",
            r"\bcosting\b",
            r"\bmargin\b",
            r"\bprofit\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _is_inventory_status_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\bdo\s+we\s+have\b",
            r"\bhow\s+much\b.*\bdo\s+we\s+have\b",
            r"\bhow\s+much\b.*\bis\s+in\s+stock\b",
            r"\bhow\s+much\b.*\bare\s+in\s+stock\b",
            r"\bwhat(?:'s|\s+is)\s+(?:the\s+)?stock\b",
            r"\bcurrent\s+stock\b",
            r"\bstock\s+of\b",
            r"\benough\s+stock\b",
            r"\binventory\s+of\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _is_recipe_impact_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\bwhich\s+recipes?\s+are\s+affected\b",
            r"\bwhat\s+recipes?\s+are\s+affected\b",
            r"\bwhich\s+recipes?\s+use\s+.*\b(low|running\s+low)\b",
            r"\bwhat\s+recipes?\s+use\s+.*\b(low|running\s+low)\b",
            r"\bwhich\s+menu\s+items?\s+are\s+affected\b",
            r"\bwhat\s+menu\s+items?\s+are\s+affected\b",
            r"\bwhich\s+recipes?\s+are\s+affected\s+by\s+low\s+(?:stock|inventory)\b",
            r"\bwhat\s+recipes?\s+are\s+affected\s+by\s+low\s+(?:stock|inventory)\b",
            r"\bwhich\s+recipes?\s+use\s+ingredients?\s+that\s+are\s+running\s+low\b",
            r"\bwhat\s+recipes?\s+use\s+ingredients?\s+that\s+are\s+running\s+low\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _is_low_stock_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\blow\s+stock\b",
            r"\blow\s+stocks\b",
            r"\brunning\s+low\b",
            r"\brun\s+low\b",
            r"\bwhich\s+ingredients?\s+are\s+low\b",
            r"\bwhat\s+ingredients?\s+are\s+low\b",
            r"\bwhat(?:'s|\s+is)\s+running\s+low\b",
            r"\bwhat(?:'s|\s+is)\s+low\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _is_top_selling_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\bwhat\s+sold\s+the\s+most\b",
            r"\bwhat\s+sold\s+best\b",
            r"\bwhat\s+are\s+our\s+top\s+(?:selling\s+)?(?:dishes|recipes|items)\b",
            r"\bwhat\s+are\s+our\s+best\s+selling\s+(?:dishes|recipes|items)\b",
            r"\btop\s+selling\s+(?:dishes|recipes|items)\b",
            r"\bbest\s+selling\s+(?:dishes|recipes|items)\b",
            r"\bmost\s+popular\s+(?:dishes|recipes|items)\b",
            r"\btop\s+(?:dishes|recipes|menu\s+items)\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _is_sales_question(
        self,
        query: str,
    ) -> bool:
        patterns = [
            r"\bsales\b",
            r"\bsold\b",
            r"\brevenue\b",
            r"\btotal\s+sales\b",
            r"\bsales\s+summary\b",
            r"\bhow\s+much\s+have\s+we\s+sold\b",
            r"\bhow\s+much\s+did\s+we\s+sell\b",
            r"\bhow\s+many\s+orders\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _extract_recipe_query(
        self,
        query: str,
    ) -> str:
        patterns = [
            r"what(?:'s|\s+is)\s+the\s+recipe\s+for\s+(.+)",
            r"recipe\s+for\s+(.+)",
            r"how\s+(?:do\s+i|can\s+i)\s+(?:make|cook|prepare)\s+(.+)",
            r"how\s+to\s+(?:make|cook|prepare)\s+(.+)",
            r"make\s+(?:a|the)?\s*recipe\s+(?:for\s+)?(.+)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                query,
                re.IGNORECASE,
            )

            if match:
                return self._clean_query_value(
                    match.group(1),
                )

        return self._clean_query_value(query)

    def _extract_inventory_query(
        self,
        query: str,
    ) -> str:
        patterns = [
            r"do\s+we\s+have\s+(.+)",
            r"how\s+much\s+(.+?)\s+do\s+we\s+have",
            r"how\s+much\s+(.+?)\s+is\s+in\s+stock",
            r"how\s+much\s+(.+?)\s+are\s+in\s+stock",
            r"what(?:'s|\s+is)\s+(?:the\s+)?stock\s+(?:of\s+)?(.+)",
            r"current\s+stock\s+(?:of\s+)?(.+)",
            r"stock\s+(?:of\s+)?(.+)",
            r"enough\s+stock\s+(?:of\s+)?(.+)",
            r"inventory\s+(?:of\s+)?(.+)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                query,
                re.IGNORECASE,
            )

            if match:
                return self._clean_query_value(
                    match.group(1),
                )

        return self._clean_query_value(query)

    def _extract_purchase_intelligence_query(
        self,
        query: str,
    ) -> str:
        patterns = [
            r"why\s+should\s+we\s+buy\s+(.+)",
            r"why\s+do\s+we\s+need\s+to\s+buy\s+(.+)",
            r"why\s+should\s+we\s+purchase\s+(.+)",
            r"why\s+do\s+we\s+need\s+to\s+purchase\s+(.+)",
            r"why\s+buy\s+(.+)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                query,
                re.IGNORECASE,
            )

            if match:
                return self._clean_query_value(
                    match.group(1),
                )

        return self._clean_query_value(query)

    def _clean_query_value(
        self,
        value: str,
    ) -> str:
        cleaned = value.strip()

        cleaned = re.sub(
            r"[?.!,]+$",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"^(?:the|a|an)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        return cleaned.strip()

    async def _answer_recipe_lookup(
        self,
        restaurant_id: UUID,
        query: str,
    ) -> str:
        recipe_query = self._extract_recipe_query(
            query,
        )

        recipe = await self.recipe_repository.find_by_name(
            restaurant_id=restaurant_id,
            query=recipe_query,
        )

        if recipe is None:
            return (
                f'I couldn\'t find a recipe matching "{recipe_query}".'
            )

        recipe_ingredients = (
            await self.recipe_ingredient_repository.get_by_recipe(
                recipe_id=recipe.id,
            )
        )

        lines = [
            f"**{recipe.name}**",
        ]

        if getattr(recipe, "description", None):
            lines.append(
                f"\nDescription: {recipe.description}"
            )

        if not recipe_ingredients:
            lines.append(
                "\nNo ingredients have been added yet."
            )

            return "\n".join(lines)

        lines.append("\nIngredients:")

        for item in recipe_ingredients:
            ingredient = item.ingredient

            quantity = self._format_number(
                item.quantity,
            )

            lines.append(
                f"• {ingredient.name} — "
                f"{quantity} {ingredient.unit}"
            )

        return "\n".join(lines)

    async def _answer_ingredient_lookup(
        self,
        restaurant_id: UUID,
        query: str,
    ) -> str:
        recipe_query = self._extract_ingredient_recipe_query(
            query,
        )

        recipe = await self.recipe_repository.find_by_name(
            restaurant_id=restaurant_id,
            query=recipe_query,
        )

        if recipe is None:
            return (
                f'I couldn\'t find a recipe matching "{recipe_query}".'
            )

        recipe_ingredients = (
            await self.recipe_ingredient_repository.get_by_recipe(
                recipe_id=recipe.id,
            )
        )

        if not recipe_ingredients:
            return (
                f"**{recipe.name}** does not have any ingredients "
                "listed yet."
            )

        lines = [
            f"**{recipe.name}** uses:",
            "",
        ]

        for item in recipe_ingredients:
            ingredient = item.ingredient

            quantity = self._format_number(
                item.quantity,
            )

            lines.append(
                f"• {ingredient.name} — "
                f"{quantity} {ingredient.unit}"
            )

        return "\n".join(lines)

    def _extract_ingredient_recipe_query(
        self,
        query: str,
    ) -> str:
        patterns = [
            r"what\s+ingredients?\s+(?:are\s+)?in\s+(.+)",
            r"what\s+are\s+the\s+ingredients?\s+for\s+(.+)",
            r"ingredients?\s+for\s+(.+)",
            r"what\s+is\s+in\s+(.+)",
            r"what\s+are\s+in\s+(.+)",
            r"what\s+goes\s+into\s+(.+)",
            r"what\s+do\s+i\s+need\s+for\s+(.+)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                query,
                re.IGNORECASE,
            )

            if match:
                return self._clean_query_value(
                    match.group(1),
                )

        return self._clean_query_value(query)

    async def _answer_food_cost(
        self,
        restaurant_id: UUID,
        query: str,
    ) -> str:
        recipe_query = self._extract_food_cost_recipe_query(
            query,
        )

        result = await self.food_cost_service.calculate_food_cost(
            restaurant_id=restaurant_id,
            recipe_name=recipe_query,
        )

        if result is None:
            return (
                f'I couldn\'t find a recipe matching "{recipe_query}".'
            )

        lines = [
            f"**{result['recipe_name']} — Food Cost**",
            "",
            (
                f"Food cost: "
                f"{self._format_decimal(result['food_cost'])}"
            ),
        ]

        selling_price = result.get("selling_price")

        if selling_price is not None:
            lines.append(
                f"Selling price: "
                f"{self._format_decimal(selling_price)}"
            )

            profit = result.get("profit")

            if profit is not None:
                lines.append(
                    f"Estimated profit: "
                    f"{self._format_decimal(profit)}"
                )

            margin = result.get("margin")

            if margin is not None:
                lines.append(
                    f"Margin: {self._format_decimal(margin)}%"
                )

        breakdown = result.get("breakdown", [])

        if breakdown:
            lines.append("")
            lines.append("Cost breakdown:")

            for item in breakdown:
                quantity = self._format_number(
                    item["quantity"],
                )

                cost_per_unit = self._format_decimal(
                    item["cost_per_unit"],
                )

                total_cost = self._format_decimal(
                    item["total_cost"],
                )

                lines.append(
                    f"• {item['ingredient_name']} — "
                    f"{quantity} × {cost_per_unit} = {total_cost}"
                )

        return "\n".join(lines)

    def _extract_food_cost_recipe_query(
        self,
        query: str,
    ) -> str:
        patterns = [
            r"food\s+cost\s+(?:of|for)\s+(.+)",
            r"cost\s+(?:of|for)\s+(.+)",
            r"how\s+much\s+does\s+(.+?)\s+cost",
            r"what\s+is\s+the\s+margin\s+(?:of|for)\s+(.+)",
            r"margin\s+(?:of|for)\s+(.+)",
            r"profit\s+(?:of|for)\s+(.+)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                query,
                re.IGNORECASE,
            )

            if match:
                return self._clean_query_value(
                    match.group(1),
                )

        return self._clean_query_value(query)

    async def _answer_inventory_status(
        self,
        restaurant_id: UUID,
        query: str,
    ) -> str:
        ingredient_query = self._extract_inventory_query(
            query,
        )

        normalized_ingredient_query = (
            self._normalize_ingredient_query(
                ingredient_query,
            )
        )

        ingredient = (
            await self.ingredient_service.find_ingredient_by_name(
                restaurant_id=restaurant_id,
                query=normalized_ingredient_query,
            )
        )

        if ingredient is None:
            return (
                f'I couldn\'t find an ingredient matching '
                f'"{ingredient_query}".'
            )

        current_stock = self._format_number(
            ingredient.current_stock,
        )

        minimum_stock = self._format_number(
            ingredient.minimum_stock,
        )

        if ingredient.current_stock <= ingredient.minimum_stock:
            status = "Low stock"
        else:
            status = "In stock"

        return (
            f"**{ingredient.name}**\n\n"
            f"Stock: {current_stock} {ingredient.unit}\n"
            f"Minimum stock: {minimum_stock} {ingredient.unit}\n"
            f"Status: {status}"
        )

    async def _answer_recipe_impact(
        self,
        restaurant_id: UUID,
    ) -> str:
        affected_recipes = (
            await self.recipe_impact_service.get_low_stock_recipe_impact(
                restaurant_id=restaurant_id,
            )
        )

        if not affected_recipes:
            return (
                "No recipes are currently affected by low-stock "
                "ingredients."
            )

        lines = [
            "**Recipes Affected by Low Stock**",
            "",
        ]

        for recipe in affected_recipes:
            lines.append(
                f"**{recipe['recipe_name']}**"
            )

            for ingredient in recipe["affected_ingredients"]:
                current_stock = self._format_number(
                    ingredient["current_stock"],
                )

                minimum_stock = self._format_number(
                    ingredient["minimum_stock"],
                )

                lines.append(
                    f"• {ingredient['ingredient_name']} — "
                    f"{current_stock} {ingredient['unit']} "
                    f"(minimum: {minimum_stock} {ingredient['unit']})"
                )

            lines.append("")

        recipe_count = len(affected_recipes)

        recipe_word = (
            "recipe"
            if recipe_count == 1
            else "recipes"
        )

        lines.append(
            f"{recipe_count} {recipe_word} are currently "
            "affected by low stock."
        )

        return "\n".join(lines)

    async def _answer_low_stock(
        self,
        restaurant_id: UUID,
    ) -> str:
        ingredients = await self.ingredient_service.get_low_stock(
            restaurant_id=restaurant_id,
        )

        if not ingredients:
            return (
                "No ingredients are currently below their "
                "minimum stock level."
            )

        lines = [
            "**Low Stock**",
            "",
        ]

        for ingredient in ingredients:
            current_stock = self._format_number(
                ingredient.current_stock,
            )

            minimum_stock = self._format_number(
                ingredient.minimum_stock,
            )

            lines.append(
                f"• {ingredient.name} — "
                f"{current_stock} {ingredient.unit} "
                f"(minimum: {minimum_stock} {ingredient.unit})"
            )

        return "\n".join(lines)

    async def _answer_sales_summary(
        self,
        restaurant_id: UUID,
    ) -> str:
        summary = await self.sales_service.get_sales_summary(
            restaurant_id=restaurant_id,
        )

        total_orders = summary["total_orders"]

        total_revenue = self._format_decimal(
            summary["total_revenue"],
        )

        return (
            "**Sales Summary**\n\n"
            f"Completed orders: {total_orders}\n"
            f"Total revenue: {total_revenue}"
        )

    async def _answer_top_selling_recipes(
        self,
        restaurant_id: UUID,
    ) -> str:
        recipes = (
            await self.sales_intelligence_service.get_top_selling_recipes(
                restaurant_id=restaurant_id,
            )
        )

        if not recipes:
            return "No completed sales have been recorded yet."

        lines = [
            "**Top Selling Recipes**",
            "",
        ]

        for recipe in recipes:
            quantity_sold = self._format_number(
                recipe["quantity_sold"],
            )

            lines.append(
                f"• {recipe['recipe_name']} — "
                f"{quantity_sold} sold"
            )

        return "\n".join(lines)

    async def _answer_purchase_intelligence(
        self,
        restaurant_id: UUID,
        query: str,
    ) -> str:
        ingredient_query = (
            self._extract_purchase_intelligence_query(
                query,
            )
        )

        result = (
            await self.purchase_intelligence_service.get_purchase_reason(
                restaurant_id=restaurant_id,
                ingredient_name=ingredient_query,
            )
        )

        if result is None:
            return (
                f'I couldn\'t find an ingredient matching '
                f'"{ingredient_query}".'
            )

        ingredient_name = result["ingredient_name"]

        current_stock = self._format_number(
            result["current_stock"],
        )

        minimum_stock = self._format_number(
            result["minimum_stock"],
        )

        recommended_purchase = self._format_number(
            result["recommended_purchase"],
        )

        unit = result["unit"]

        if result["recommended_purchase"] <= 0:
            return (
                f"**{ingredient_name}** does not currently need "
                "to be purchased.\n\n"
                f"Current stock: {current_stock} {unit}\n"
                f"Minimum stock: {minimum_stock} {unit}\n\n"
                "This ingredient is not currently on the "
                "purchase recommendation list."
            )

        lines = [
            f"**{ingredient_name} — Purchase Reason**",
            "",
            f"Current stock: {current_stock} {unit}",
            f"Minimum stock: {minimum_stock} {unit}",
            (
                f"Recommended purchase: "
                f"{recommended_purchase} {unit}"
            ),
            "",
            (
                f"{ingredient_name} is below the minimum "
                "stock level."
            ),
        ]

        affected_recipes = result.get(
            "affected_recipes",
            [],
        )

        if affected_recipes:
            recipe_count = len(affected_recipes)

            if recipe_count == 1:
                lines.extend(
                    [
                        "",
                        "It is used in 1 low-stock affected recipe.",
                    ]
                )
            else:
                lines.extend(
                    [
                        "",
                        (
                            f"It is used in {recipe_count} "
                            "low-stock affected recipes."
                        ),
                    ]
                )

            lines.extend(
                [
                    "",
                    "**Affected recipes:**",
                ]
            )

            for recipe in affected_recipes:
                quantity_sold = self._format_number(
                    recipe["quantity_sold"],
                )

                lines.append(
                    f"• {recipe['recipe_name']} — "
                    f"{quantity_sold} sold."
                )

        return "\n".join(lines)

    async def _handle_purchase_recommendations(
        self,
        restaurant_id: UUID,
    ) -> dict:
        recommendations = (
            await self.purchase_recommendation_service
            .get_purchase_recommendations(
                restaurant_id
            )
        )

        if not recommendations:
            return {
                "intent": "purchase_recommendations",
                "answer": "No purchases are needed today.",
            }

        lines = [
            "**Purchase Recommendations**",
            "",
        ]

        for item in recommendations:
            ingredient_name = item["ingredient_name"]
            purchase_quantity = item["recommended_purchase"]
            unit = item["unit"]

            current_stock = item.get("current_stock")
            minimum_stock = item.get("minimum_stock")

            line = (
                f"• {ingredient_name} — "
                f"Buy {self._format_number(purchase_quantity)} {unit}"
            )

            if current_stock is not None and minimum_stock is not None:
                line += (
                    f" (Current: "
                    f"{self._format_number(current_stock)} {unit}, "
                    f"Target: "
                    f"{self._format_number(minimum_stock)} {unit})"
                )

            lines.append(line)

        return {
            "intent": "purchase_recommendations",
            "answer": "\n".join(lines),
        }

    def _format_number(
        self,
        value,
    ) -> str:
        if isinstance(value, Decimal):
            value = value.normalize()

            if value == value.to_integral():
                return str(int(value))

            return (
                format(value, "f")
                .rstrip("0")
                .rstrip(".")
            )

        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))

            return f"{value:g}"

        return str(value)

    def _format_decimal(
        self,
        value,
    ) -> str:
        if value is None:
            return "0.00"

        decimal_value = Decimal(str(value))

        return f"{decimal_value:.2f}"

    def _normalize_ingredient_query(
        self,
        query: str,
    ) -> str:
        normalized = query.strip().lower()

        if normalized.endswith("ies"):
            return f"{normalized[:-3]}y"

        if normalized.endswith("oes"):
            return normalized[:-2]

        if normalized.endswith("es"):
            return normalized[:-2]

        if normalized.endswith("s"):
            return normalized[:-1]

        return normalized