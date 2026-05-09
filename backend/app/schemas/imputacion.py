from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import DestinoRegComprobante


class ImputacionCreate(BaseModel):
    id: UUID
    categoria_irp_id: UUID
    imputa_iva_credito: bool
    iva_credito_porcentaje: Decimal
    iva_credito_monto: int
    imputa_irp: bool
    destino_reg_comprobante: DestinoRegComprobante
    a_nombre_de: str | None = None


class ImputacionOut(BaseModel):
    id: UUID
    comprobante_id: UUID
    categoria_irp_id: UUID
    imputa_iva_credito: bool
    iva_credito_porcentaje: Decimal
    iva_credito_monto: int
    imputa_irp: bool
    destino_reg_comprobante: DestinoRegComprobante
    a_nombre_de: str | None = None
    rectificado: bool
    fecha_rectificacion: datetime | None = None
    notas_rectificacion: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ImputacionUpdate(BaseModel):
    categoria_irp_id: UUID | None = None
    imputa_iva_credito: bool | None = None
    iva_credito_porcentaje: Decimal | None = None
    iva_credito_monto: int | None = None
    imputa_irp: bool | None = None
    destino_reg_comprobante: DestinoRegComprobante | None = None
    a_nombre_de: str | None = None
    notas_rectificacion: str | None = None


class BatchRectificarCambios(BaseModel):
    destino_anterior: DestinoRegComprobante
    destino_nuevo: DestinoRegComprobante
    solo_categorias: list[str] | None = None
    notas_rectificacion: str | None = None


class BatchRectificarBody(BaseModel):
    periodo_fiscal: str
    cambios: BatchRectificarCambios
