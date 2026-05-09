from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import SyncStatus, TipoContacto, TipoContribuyente


class ContactoCreate(BaseModel):
    id: UUID
    ruc: str
    razon_social: str
    nombre_fantasia: str | None = None
    tipo: TipoContacto
    tipo_contribuyente: TipoContribuyente | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    notas: str | None = None
    es_frecuente: bool = False
    sync_status: SyncStatus = SyncStatus.PENDING
    device_id: str | None = None


class ContactoUpdate(BaseModel):
    ruc: str | None = None
    razon_social: str | None = None
    nombre_fantasia: str | None = None
    tipo: TipoContacto | None = None
    tipo_contribuyente: TipoContribuyente | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    notas: str | None = None
    es_frecuente: bool | None = None
    sync_status: SyncStatus | None = None
    device_id: str | None = None


class ContactoOut(BaseModel):
    id: UUID
    ruc: str
    razon_social: str
    nombre_fantasia: str | None = None
    tipo: TipoContacto
    tipo_contribuyente: TipoContribuyente | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    notas: str | None = None
    es_frecuente: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    sync_status: SyncStatus
    device_id: str | None = None

    model_config = {"from_attributes": True}
