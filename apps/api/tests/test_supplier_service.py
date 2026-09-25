from uuid import uuid4

import pytest

from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.services.supplier_service import SupplierService


class FakeSupplier:
    def __init__(
        self,
        supplier_id,
        restaurant_id,
        name,
        contact_name=None,
        phone=None,
        email=None,
        notes=None,
    ):
        self.id = supplier_id
        self.restaurant_id = restaurant_id
        self.name = name
        self.contact_name = contact_name
        self.phone = phone
        self.email = email
        self.notes = notes


class FakeDB:
    def __init__(self):
        self.commit_count = 0
        self.refresh_count = 0

    async def commit(self):
        self.commit_count += 1

    async def refresh(self, instance):
        self.refresh_count += 1


class FakeSupplierRepository:
    def __init__(self):
        self.db = FakeDB()
        self.suppliers = {}

    async def create(
        self,
        restaurant_id,
        name,
        contact_name,
        phone,
        email,
        notes,
    ):
        supplier = FakeSupplier(
            supplier_id=uuid4(),
            restaurant_id=restaurant_id,
            name=name,
            contact_name=contact_name,
            phone=phone,
            email=email,
            notes=notes,
        )

        self.suppliers[supplier.id] = supplier

        return supplier

    async def get_all(self, restaurant_id):
        return [
            supplier
            for supplier in self.suppliers.values()
            if supplier.restaurant_id == restaurant_id
        ]

    async def get_by_id(
        self,
        restaurant_id,
        supplier_id,
    ):
        supplier = self.suppliers.get(supplier_id)

        if supplier is None:
            return None

        if supplier.restaurant_id != restaurant_id:
            return None

        return supplier

    async def update(
        self,
        restaurant_id,
        supplier_id,
        **values,
    ):
        supplier = await self.get_by_id(
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
        )

        if supplier is None:
            return None

        for field, value in values.items():
            if value is not None:
                setattr(supplier, field, value)

        return supplier

    async def delete(
        self,
        restaurant_id,
        supplier_id,
    ):
        supplier = await self.get_by_id(
            restaurant_id=restaurant_id,
            supplier_id=supplier_id,
        )

        if supplier is None:
            return False

        del self.suppliers[supplier_id]

        return True


@pytest.mark.asyncio
async def test_create_supplier():
    repository = FakeSupplierRepository()
    service = SupplierService(repository)

    restaurant_id = uuid4()

    data = SupplierCreate(
        restaurant_id=restaurant_id,
        name="Fresh Foods",
        contact_name="John Smith",
        phone="+123456789",
        email="john@freshfoods.com",
        notes="Main produce supplier",
    )

    supplier = await service.create_supplier(data)

    assert supplier.restaurant_id == restaurant_id
    assert supplier.name == "Fresh Foods"
    assert supplier.contact_name == "John Smith"
    assert supplier.phone == "+123456789"
    assert supplier.email == "john@freshfoods.com"
    assert supplier.notes == "Main produce supplier"

    assert repository.db.commit_count == 1
    assert repository.db.refresh_count == 1


@pytest.mark.asyncio
async def test_list_suppliers_is_scoped_to_restaurant():
    repository = FakeSupplierRepository()
    service = SupplierService(repository)

    restaurant_a = uuid4()
    restaurant_b = uuid4()

    await service.create_supplier(
        SupplierCreate(
            restaurant_id=restaurant_a,
            name="Supplier A",
        )
    )

    await service.create_supplier(
        SupplierCreate(
            restaurant_id=restaurant_b,
            name="Supplier B",
        )
    )

    suppliers = await service.list_suppliers(
        restaurant_id=restaurant_a,
    )

    assert len(suppliers) == 1
    assert suppliers[0].name == "Supplier A"


@pytest.mark.asyncio
async def test_get_supplier_returns_supplier_for_correct_restaurant():
    repository = FakeSupplierRepository()
    service = SupplierService(repository)

    restaurant_id = uuid4()

    supplier = await service.create_supplier(
        SupplierCreate(
            restaurant_id=restaurant_id,
            name="Fresh Foods",
        )
    )

    result = await service.get_supplier(
        restaurant_id=restaurant_id,
        supplier_id=supplier.id,
    )

    assert result is supplier


@pytest.mark.asyncio
async def test_get_supplier_returns_none_for_wrong_restaurant():
    repository = FakeSupplierRepository()
    service = SupplierService(repository)

    restaurant_a = uuid4()
    restaurant_b = uuid4()

    supplier = await service.create_supplier(
        SupplierCreate(
            restaurant_id=restaurant_a,
            name="Fresh Foods",
        )
    )

    result = await service.get_supplier(
        restaurant_id=restaurant_b,
        supplier_id=supplier.id,
    )

    assert result is None


@pytest.mark.asyncio
async def test_update_supplier():
    repository = FakeSupplierRepository()
    service = SupplierService(repository)

    restaurant_id = uuid4()

    supplier = await service.create_supplier(
        SupplierCreate(
            restaurant_id=restaurant_id,
            name="Old Supplier Name",
            phone="+111111111",
        )
    )

    updated = await service.update_supplier(
        restaurant_id=restaurant_id,
        supplier_id=supplier.id,
        data=SupplierUpdate(
            name="New Supplier Name",
            phone="+222222222",
        ),
    )

    assert updated is not None
    assert updated.name == "New Supplier Name"
    assert updated.phone == "+222222222"

    assert repository.db.commit_count == 2
    assert repository.db.refresh_count == 2


@pytest.mark.asyncio
async def test_update_supplier_returns_none_when_not_found():
    repository = FakeSupplierRepository()
    service = SupplierService(repository)

    result = await service.update_supplier(
        restaurant_id=uuid4(),
        supplier_id=uuid4(),
        data=SupplierUpdate(
            name="Updated Supplier",
        ),
    )

    assert result is None


@pytest.mark.asyncio
async def test_delete_supplier():
    repository = FakeSupplierRepository()
    service = SupplierService(repository)

    restaurant_id = uuid4()

    supplier = await service.create_supplier(
        SupplierCreate(
            restaurant_id=restaurant_id,
            name="Fresh Foods",
        )
    )

    deleted = await service.delete_supplier(
        restaurant_id=restaurant_id,
        supplier_id=supplier.id,
    )

    assert deleted is True

    result = await service.get_supplier(
        restaurant_id=restaurant_id,
        supplier_id=supplier.id,
    )

    assert result is None


@pytest.mark.asyncio
async def test_delete_supplier_returns_false_when_not_found():
    repository = FakeSupplierRepository()
    service = SupplierService(repository)

    deleted = await service.delete_supplier(
        restaurant_id=uuid4(),
        supplier_id=uuid4(),
    )

    assert deleted is False


def test_supplier_rejects_invalid_email():
    with pytest.raises(ValueError):
        SupplierCreate(
            restaurant_id=uuid4(),
            name="Fresh Foods",
            email="not-an-email",
        )


def test_supplier_allows_optional_contact_fields():
    supplier = SupplierCreate(
        restaurant_id=uuid4(),
        name="Fresh Foods",
    )

    assert supplier.contact_name is None
    assert supplier.phone is None
    assert supplier.email is None
    assert supplier.notes is None
