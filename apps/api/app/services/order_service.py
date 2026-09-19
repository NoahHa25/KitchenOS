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
            recipe_ingredient_repository=(
                self.recipe_ingredient_repository
            ),
            inventory_movement_repository=(
                self.inventory_movement_repository
            ),
        )

        try:
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

                total_amount += (
                    item.quantity * item.unit_price
                )

                required = (
                    await inventory_service.calculate_required_ingredients(
                        restaurant_id=data.restaurant_id,
                        recipe_id=item.recipe_id,
                        recipe_quantity=item.quantity,
                    )
                )

                all_required.extend(required)

            # Phase 2: Aggregate requirements for duplicate ingredients
            all_required = (
                inventory_service.aggregate_required_ingredients(
                    all_required
                )
            )

            # Phase 3: Validate total required stock
            await inventory_service.validate_stock(
                all_required,
            )

            # Phase 4: Create the order
            order = await self.order_repository.create(
                restaurant_id=data.restaurant_id,
                status="pending",
                total_amount=total_amount,
            )

            # Phase 5: Create order items
            for item in data.items:
                await self.order_item_repository.create(
                    order_id=order.id,
                    recipe_id=item.recipe_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )

            # Phase 6: Consume inventory and record movements
            await inventory_service.consume_stock(
                required=all_required,
                order_id=order.id,
            )

            # Phase 7: Commit order + items + inventory atomically
            await self.order_repository.db.commit()

            # Reload order with items
            return await self.order_repository.get_by_id(
                restaurant_id=data.restaurant_id,
                order_id=order.id,
            )

        except Exception:
            await self.order_repository.db.rollback()
            raise

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

