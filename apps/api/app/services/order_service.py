from decimal import Decimal
from uuid import UUID

from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.repositories.order_item_repository import (
    OrderItemRepository,
)
from app.repositories.order_repository import OrderRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.order import OrderCreate
from app.services.inventory_consumption_service import (
    InventoryConsumptionService,
)


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
        recipe_repository: RecipeRepository,
        recipe_ingredient_repository: RecipeIngredientRepository,
        ingredient_repository: IngredientRepository,
        inventory_movement_repository: InventoryMovementRepository,
    ):
        self.order_repository = order_repository
        self.order_item_repository = order_item_repository
        self.recipe_repository = recipe_repository
        self.recipe_ingredient_repository = (
            recipe_ingredient_repository
        )
        self.ingredient_repository = ingredient_repository
        self.inventory_movement_repository = (
            inventory_movement_repository
        )

    async def create_order(
        self,
        data: OrderCreate,
    ):
        inventory_service = InventoryConsumptionService(
            ingredient_repository=self.ingredient_repository,
            recipe_ingredient_repository=self.recipe_ingredient_repository,
        )

        total_amount = Decimal("0.00")
        all_required: list[dict] = []

        # Phase 1: Validate recipes and calculate requirements
        for item in data.items:
            recipe = await self.recipe_repository.get_by_id(
                restaurant_id=data.restaurant_id,
                recipe_id=item.recipe_id,
            )

            if recipe is None:
                return None

            total_amount += item.quantity * item.unit_price

            required = (
                await inventory_service.calculate_required_ingredients(
                    restaurant_id=data.restaurant_id,
                    recipe_id=item.recipe_id,
                    recipe_quantity=item.quantity,
                )
            )

            all_required.extend(required)

        # Phase 2: Validate stock
        await inventory_service.validate_stock(
            all_required,
        )

        # Phase 3: Create order
        order = await self.order_repository.create(
            restaurant_id=data.restaurant_id,
            status="pending",
            total_amount=total_amount,
        )

        # Phase 4: Create order items
        for item in data.items:
            await self.order_item_repository.create(
                order_id=order.id,
                recipe_id=item.recipe_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )

        # Phase 5: Consume inventory
        for item in all_required:
            ingredient = item["ingredient"]
            required_quantity = item["required_quantity"]

            await self.ingredient_repository.update(
                restaurant_id=data.restaurant_id,
                ingredient_id=ingredient.id,
                current_stock=(
                    ingredient.current_stock
                    - required_quantity
                ),
            )

            await self.inventory_movement_repository.create(
                ingredient_id=ingredient.id,
                movement_type="out",
                quantity=required_quantity,
                reason=f"Order {order.id}",
            )

        # Phase 6: Commit everything
        await self.order_repository.db.commit()

        # Reload order with items
        return await self.order_repository.get_by_id(
            restaurant_id=data.restaurant_id,
            order_id=order.id,
        )

    async def update_status(
        self,
        restaurant_id: UUID,
        order_id: UUID,
        new_status: str,
    ):
        order = await self.order_repository.get_by_id(
            restaurant_id=restaurant_id,
            order_id=order_id,
        )

        if order is None:
            return None

        allowed_transitions = {
            "pending": {
                "preparing",
                "cancelled",
            },
            "preparing": {
                "completed",
                "cancelled",
            },
            "completed": set(),
            "cancelled": set(),
        }

        current_status = order.status

        if new_status not in allowed_transitions:
            raise ValueError(
                f"Invalid order status: {new_status}"
            )

        if new_status not in allowed_transitions[current_status]:
            raise ValueError(
                f"Cannot change order status "
                f"from {current_status} to {new_status}"
            )

        return await self.order_repository.update(
            order=order,
            status=new_status,
        )
