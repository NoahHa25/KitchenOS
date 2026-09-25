from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import (
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)
from app.services.supplier_service import SupplierService


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


@router.post(
    "",
    response_model=SupplierResponse,
)
async def create_supplier(
    data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
):
    service = SupplierService(
        SupplierRepository(db),
    )

    return await service.create_supplier(data)


@router.get(
    "",
    response_model=list[SupplierResponse],
)
async def list_suppliers(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = SupplierService(
        SupplierRepository(db),
    )

    return await service.list_suppliers(
        restaurant_id=restaurant_id,
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
async def get_supplier(
    supplier_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = SupplierService(
        SupplierRepository(db),
    )

    supplier = await service.get_supplier(
        restaurant_id=restaurant_id,
        supplier_id=supplier_id,
    )

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return supplier


@router.patch(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
async def update_supplier(
    supplier_id: UUID,
    restaurant_id: UUID,
    data: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = SupplierService(
        SupplierRepository(db),
    )

    supplier = await service.update_supplier(
        restaurant_id=restaurant_id,
        supplier_id=supplier_id,
        data=data,
    )

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return supplier


@router.delete(
    "/{supplier_id}",
)
async def delete_supplier(
    supplier_id: UUID,
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = SupplierService(
        SupplierRepository(db),
    )

    deleted = await service.delete_supplier(
        restaurant_id=restaurant_id,
        supplier_id=supplier_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return {
        "message": "Supplier deleted successfully",
        "supplier_id": supplier_id,
    }
