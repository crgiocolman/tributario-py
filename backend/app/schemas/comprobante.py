from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import (
    CargadoMarangatu,
    Condicion,
    FormaEmision,
    FormaPago,
    SyncStatus,
    TipoComprobante,
    TipoOperacion,
)
from app.schemas.imputacion import ImputacionCreate, ImputacionOut


class ArchivoAdjuntoOut(BaseModel):
    id: UUID
    comprobante_id: UUID
    nombre_archivo: str
    tipo_mime: str
    tamano_bytes: int
    hash_sha256: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ComprobanteCreate(BaseModel):
    id: UUID
    contacto_id: UUID
    tipo_operacion: TipoOperacion
    tipo_comprobante: TipoComprobante
    forma_emision: FormaEmision
    numero_timbrado: str | None = None
    numero_comprobante: str | None = None
    fecha_emision: date
    fecha_percepcion: date | None = None
    condicion: Condicion
    moneda: str
    tipo_cambio: Decimal | None = None
    monto_exento: int
    monto_gravado_5: int
    iva_5: int
    monto_gravado_10: int
    iva_10: int
    total: int
    forma_pago: FormaPago | None = None
    concepto: str | None = None
    periodo_fiscal: str
    cargado_marangatu: CargadoMarangatu
    notas: str | None = None
    sync_status: SyncStatus = SyncStatus.PENDING
    device_id: str | None = None
    imputacion: ImputacionCreate


class ComprobanteUpdate(BaseModel):
    contacto_id: UUID | None = None
    tipo_operacion: TipoOperacion | None = None
    tipo_comprobante: TipoComprobante | None = None
    forma_emision: FormaEmision | None = None
    numero_timbrado: str | None = None
    numero_comprobante: str | None = None
    fecha_emision: date | None = None
    fecha_percepcion: date | None = None
    condicion: Condicion | None = None
    moneda: str | None = None
    tipo_cambio: Decimal | None = None
    monto_exento: int | None = None
    monto_gravado_5: int | None = None
    iva_5: int | None = None
    monto_gravado_10: int | None = None
    iva_10: int | None = None
    total: int | None = None
    forma_pago: FormaPago | None = None
    concepto: str | None = None
    periodo_fiscal: str | None = None
    cargado_marangatu: CargadoMarangatu | None = None
    notas: str | None = None
    sync_status: SyncStatus | None = None
    device_id: str | None = None


class ComprobanteOut(BaseModel):
    id: UUID
    contacto_id: UUID
    tipo_operacion: TipoOperacion
    tipo_comprobante: TipoComprobante
    forma_emision: FormaEmision
    numero_timbrado: str | None = None
    numero_comprobante: str | None = None
    fecha_emision: date
    fecha_percepcion: date | None = None
    condicion: Condicion
    moneda: str
    tipo_cambio: Decimal | None = None
    monto_exento: int
    monto_gravado_5: int
    iva_5: int
    monto_gravado_10: int
    iva_10: int
    total: int
    forma_pago: FormaPago | None = None
    concepto: str | None = None
    periodo_fiscal: str
    cargado_marangatu: CargadoMarangatu
    notas: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    sync_status: SyncStatus
    device_id: str | None = None
    imputacion_fiscal: ImputacionOut | None = None
    archivos_adjuntos: list[ArchivoAdjuntoOut] = []

    model_config = {"from_attributes": True}
