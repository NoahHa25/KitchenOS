from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class SupplierCreate(BaseModel):
    restaurant_id: UUID
    name: str
    contact_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    contact_name: str | None
    phone: str | None
    email: EmailStr | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
