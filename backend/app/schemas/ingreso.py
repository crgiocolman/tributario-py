from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import SyncStatus, TipoIngreso


class IngresoCreate(BaseModel):
    id: UUID
    contacto_id: UUID
    comprobante_id: UUID | None = None
    tipo_ingreso: TipoIngreso
    periodo_devengado: str
    fecha_percepcion: date
    monto_bruto: int
    aporte_ips_trabajador: int
    otros_descuentos: int
    monto_exonerado: int
    monto_computable_irp: int
    es_gravado_irp: bool
    notas: str | None = None
    sync_status: SyncStatus = SyncStatus.PENDING
    device_id: str | None = None


class IngresoUpdate(BaseModel):
    contacto_id: UUID | None = None
    comprobante_id: UUID | None = None
    tipo_ingreso: TipoIngreso | None = None
    periodo_devengado: str | None = None
    fecha_percepcion: date | None = None
    monto_bruto: int | None = None
    aporte_ips_trabajador: int | None = None
    otros_descuentos: int | None = None
    monto_exonerado: int | None = None
    monto_computable_irp: int | None = None
    es_gravado_irp: bool | None = None
    notas: str | None = None
    sync_status: SyncStatus | None = None
    device_id: str | None = None


class IngresoOut(BaseModel):
    id: UUID
    contacto_id: UUID
    comprobante_id: UUID | None = None
    tipo_ingreso: TipoIngreso
    periodo_devengado: str
    fecha_percepcion: date
    monto_bruto: int
    aporte_ips_trabajador: int
    otros_descuentos: int
    monto_exonerado: int
    monto_computable_irp: int
    es_gravado_irp: bool
    acumulado_anual: int | None = None
    notas: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    sync_status: SyncStatus
    device_id: str | None = None

    model_config = {"from_attributes": True}


class DetalleMensual(BaseModel):
    mes: str
    computable: int
    acumulado: int


class AcumuladoAnualOut(BaseModel):
    anio_fiscal: int
    umbral_irp: int
    acumulado_bruto: int
    acumulado_computable_irp: int
    porcentaje_umbral: float
    superado_umbral: bool
    fecha_cruce_umbral: date | None = None
    detalle_mensual: list[DetalleMensual]
