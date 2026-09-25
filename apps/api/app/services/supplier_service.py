from uuid import UUID

from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierUpdate


class SupplierService:
    def __init__(self, repository: SupplierRepository):
        self.repository = repository

    async def create_supplier(
        self,
        data: SupplierCreate,
    ):
        supplier = await self.repository.create(
            restaurant_id=data.restaurant_id,
            name=data.name,
            contact_name=data.contact_name,
            phone=data.phone,
            email=data.email,
            notes=data.notes,
        )

        await self.repository.db.commit()
        await self.repository.db.refresh(supplier)

        return supplier

    async def list_suppliers(
        self,
        restaurant_id: UUID,
    ):
        return await self.repository.get_all(
            restaurant_id=restaurant_id,
        )

    async def get_supplier(
        self,
        restaurant_id: UUID,
        supplier_id: UUID,
    ):
        return await self.repository.get_by_id(
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
        )

    async def update_supplier(
        self,
        restaurant_id: UUID,
        supplier_id: UUID,
        data: SupplierUpdate,
    ):
        supplier = await self.repository.update(
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
            **data.model_dump(exclude_unset=True),
        )

        if supplier is None:
            return None

        await self.repository.db.commit()
        await self.repository.db.refresh(supplier)

        return supplier

    async def delete_supplier(
        self,
        restaurant_id: UUID,
        supplier_id: UUID,
    ):
        deleted = await self.repository.delete(
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
        )

        if not deleted:
            return False

        await self.repository.db.commit()

        return True
