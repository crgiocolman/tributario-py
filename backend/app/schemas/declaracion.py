from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import EstadoDJ, Formulario


class DeclaracionCreate(BaseModel):
    id: UUID
    periodo_fiscal_id: UUID | None = None
    formulario: Formulario
    periodo: str
    numero_orden: str | None = None
    fecha_presentacion: datetime
    es_rectificativa: bool = False
    rectifica_a: UUID | None = None
    monto_impuesto: int
    monto_multa: int = 0
    monto_intereses: int = 0
    monto_mora: int = 0
    monto_total_pagado: int
    fecha_pago: datetime | None = None
    estado: EstadoDJ
    notas: str | None = None


class DeclaracionUpdate(BaseModel):
    numero_orden: str | None = None
    fecha_presentacion: datetime | None = None
    monto_impuesto: int | None = None
    monto_multa: int | None = None
    monto_intereses: int | None = None
    monto_mora: int | None = None
    monto_total_pagado: int | None = None
    fecha_pago: datetime | None = None
    estado: EstadoDJ | None = None
    notas: str | None = None


class DeclaracionOut(BaseModel):
    id: UUID
    periodo_fiscal_id: UUID | None = None
    formulario: Formulario
    periodo: str
    numero_orden: str | None = None
    fecha_presentacion: datetime
    es_rectificativa: bool
    rectifica_a: UUID | None = None
    monto_impuesto: int
    monto_multa: int
    monto_intereses: int
    monto_mora: int
    monto_total_pagado: int
    fecha_pago: datetime | None = None
    estado: EstadoDJ
    notas: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
