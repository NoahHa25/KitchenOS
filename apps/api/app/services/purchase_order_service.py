from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.models.purchase_order import PurchaseOrderStatus
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.purchase_order import PurchaseOrderCreate


class PurchaseOrderService:
    def __init__(
        self,
        purchase_order_repository: PurchaseOrderRepository,
        supplier_repository: SupplierRepository,
        ingredient_repository: IngredientRepository,
        inventory_movement_repository: InventoryMovementRepository,
    ):
        self.purchase_order_repository = purchase_order_repository
        self.supplier_repository = supplier_repository
        self.ingredient_repository = ingredient_repository
        self.inventory_movement_repository = (
            inventory_movement_repository
        )

    async def create_purchase_order(
        self,
        data: PurchaseOrderCreate,
    ):
        supplier = await self.supplier_repository.get_by_id(
            restaurant_id=data.restaurant_id,
            supplier_id=data.supplier_id,
        )

        if supplier is None:
            raise HTTPException(
                status_code=404,
                detail="Supplier not found",
            )

        try:
            purchase_order = (
                await self.purchase_order_repository.create(
                    restaurant_id=data.restaurant_id,
                    supplier_id=data.supplier_id,
                    expected_delivery=data.expected_delivery,
                    notes=data.notes,
                )
            )

            ingredient_ids = set()

            for item in data.items:
                if item.ingredient_id in ingredient_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Duplicate ingredient in purchase order: "
                            f"{item.ingredient_id}"
                        ),
                    )

                ingredient_ids.add(item.ingredient_id)

                ingredient = (
                    await self.ingredient_repository.get_by_id(
                        restaurant_id=data.restaurant_id,
                        ingredient_id=item.ingredient_id,
                    )
                )

                if ingredient is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Ingredient not found: "
                            f"{item.ingredient_id}"
                        ),
                    )

                quantity = Decimal(str(item.quantity))
                unit_cost = Decimal(str(item.unit_cost))

                total_cost = quantity * unit_cost

                await self.purchase_order_repository.add_item(
                    purchase_order_id=purchase_order.id,
                    ingredient_id=item.ingredient_id,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    total_cost=total_cost,
                )

            await self.purchase_order_repository.db.commit()

            return await self.purchase_order_repository.get_by_id(
                restaurant_id=data.restaurant_id,
                purchase_order_id=purchase_order.id,
            )

        except Exception:
            await self.purchase_order_repository.db.rollback()
            raise

    async def list_purchase_orders(
        self,
        restaurant_id: UUID,
    ):
        return await self.purchase_order_repository.get_all(
            restaurant_id=restaurant_id,
        )

    async def get_purchase_order(
        self,
        restaurant_id: UUID,
        purchase_order_id: UUID,
    ):
        return await self.purchase_order_repository.get_by_id(
            restaurant_id=restaurant_id,
            purchase_order_id=purchase_order_id,
        )

    async def update_status(
        self,
        restaurant_id: UUID,
        purchase_order_id: UUID,
        new_status: PurchaseOrderStatus,
    ):
        purchase_order = (
            await self.purchase_order_repository.get_by_id(
                restaurant_id=restaurant_id,
                purchase_order_id=purchase_order_id,
            )
        )

        if purchase_order is None:
            return None

        allowed_transitions = {
            PurchaseOrderStatus.DRAFT: {
                PurchaseOrderStatus.SENT,
                PurchaseOrderStatus.CANCELLED,
            },
            PurchaseOrderStatus.SENT: {
                PurchaseOrderStatus.RECEIVED,
                PurchaseOrderStatus.CANCELLED,
            },
            PurchaseOrderStatus.RECEIVED: set(),
            PurchaseOrderStatus.CANCELLED: set(),
        }

        current_status = purchase_order.status

        if new_status not in allowed_transitions[current_status]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot change purchase order status "
                    f"from {current_status.value} "
                    f"to {new_status.value}"
                ),
            )

        try:
            purchase_order = (
                await self.purchase_order_repository.update_status(
                    purchase_order=purchase_order,
                    status=new_status,
                )
            )

            await self.purchase_order_repository.db.commit()

            return purchase_order

        except Exception:
            await self.purchase_order_repository.db.rollback()
            raise

    async def receive_purchase_order(
        self,
        restaurant_id: UUID,
        purchase_order_id: UUID,
    ):
        purchase_order = (
            await self.purchase_order_repository.get_by_id(
                restaurant_id=restaurant_id,
                purchase_order_id=purchase_order_id,
            )
        )

        if purchase_order is None:
            return None

        if purchase_order.status != PurchaseOrderStatus.SENT:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only sent purchase orders can be received"
                ),
            )

        try:
            for item in purchase_order.items:
                ingredient = (
                    await self.ingredient_repository.get_by_id(
                        restaurant_id=restaurant_id,
                        ingredient_id=item.ingredient_id,
                    )
                )

                if ingredient is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Ingredient not found: "
                            f"{item.ingredient_id}"
                        ),
                    )

                quantity = Decimal(str(item.quantity))
                unit_cost = Decimal(str(item.unit_cost))

                ingredient.current_stock = (
                    Decimal(str(ingredient.current_stock))
                    + quantity
                )

                ingredient.cost_per_unit = unit_cost

                await self.inventory_movement_repository.create(
                    ingredient_id=item.ingredient_id,
                    movement_type="purchase",
                    quantity=quantity,
                    unit_cost=unit_cost,
                    reason=(
                        f"Purchase order {purchase_order.id}"
                    ),
                )

            purchase_order.status = PurchaseOrderStatus.RECEIVED

            await self.purchase_order_repository.db.flush()
            await self.purchase_order_repository.db.commit()

            return await self.purchase_order_repository.get_by_id(
                restaurant_id=restaurant_id,
                purchase_order_id=purchase_order.id,
            )

        except Exception:
            await self.purchase_order_repository.db.rollback()
            raise
