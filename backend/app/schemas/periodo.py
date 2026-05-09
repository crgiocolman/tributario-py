from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class ResumenIVA(BaseModel):
    ventas_gravadas_10: int
    ventas_gravadas_5: int
    ventas_exentas: int
    iva_debito: int
    compras_gravadas_10: int
    compras_gravadas_5: int
    compras_exentas: int
    iva_credito_utilizado: int
    saldo_iva: int


class ResumenIRP(BaseModel):
    ingresos_computables: int
    egresos_por_categoria: dict[str, int]
    total_egresos: int


class EstadoPresentacion(BaseModel):
    f120_presentado: bool
    f120_fecha_presentacion: datetime | None = None
    f120_vencimiento: date | None = None
    f120_dias_restantes: int | None = None
    reg_comprobantes_presentado: bool
    reg_comprobantes_fecha: datetime | None = None
    reg_comprobantes_vencimiento: date | None = None
    reg_comprobantes_dias_restantes: int | None = None


class ComprobantesResumen(BaseModel):
    compras: int
    ventas: int


class PeriodoFiscalOut(BaseModel):
    id: UUID
    periodo: str
    anio_fiscal: int
    resumen_iva: ResumenIVA
    resumen_irp: ResumenIRP
    estado_presentacion: EstadoPresentacion
    comprobantes: ComprobantesResumen
    created_at: datetime
    updated_at: datetime


class PeriodoFiscalListItem(BaseModel):
    id: UUID
    periodo: str
    anio_fiscal: int
    saldo_iva: int
    total_ingresos_irp: int
    total_egresos_irp: int
    cantidad_comprobantes_compras: int
    cantidad_comprobantes_ventas: int
    f120_presentado: bool
    reg_comprobantes_presentado: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
