from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier


class SupplierRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        restaurant_id: UUID,
        name: str,
        contact_name: str | None,
        phone: str | None,
        email: str | None,
        notes: str | None,
    ) -> Supplier:
        supplier = Supplier(
            restaurant_id=restaurant_id,
            name=name,
            contact_name=contact_name,
            phone=phone,
            email=email,
            notes=notes,
        )

        self.db.add(supplier)
        await self.db.flush()

        return supplier

    async def get_all(
        self,
        restaurant_id: UUID,
    ) -> list[Supplier]:
        result = await self.db.execute(
            select(Supplier)
            .where(
                Supplier.restaurant_id == restaurant_id,
            )
            .order_by(
                Supplier.name.asc(),
            )
        )

        return list(result.scalars().all())

    async def get_by_id(
        self,
        restaurant_id: UUID,
        supplier_id: UUID,
    ) -> Supplier | None:
        result = await self.db.execute(
            select(Supplier)
            .where(
                Supplier.id == supplier_id,
                Supplier.restaurant_id == restaurant_id,
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        restaurant_id: UUID,
        supplier_id: UUID,
        **values,
    ) -> Supplier | None:
        supplier = await self.get_by_id(
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
        )

        if supplier is None:
            return None

        for field, value in values.items():
            if value is not None:
                setattr(supplier, field, value)

        await self.db.flush()

        return supplier

    async def delete(
        self,
        restaurant_id: UUID,
        supplier_id: UUID,
    ) -> bool:
        supplier = await self.get_by_id(
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
        )

        if supplier is None:
            return False

        await self.db.delete(supplier)
        await self.db.flush()

        return True
