from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ReglaImputacionEmbedded(BaseModel):
    imputa_iva_credito: bool
    imputa_iva_credito_porcentaje: Decimal | None
    imputa_irp: bool
    destino_reg_comprobante: str

    model_config = {"from_attributes": True}


class CategoriaIRPOut(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None
    articulo_ley: str | None
    limite_porcentaje: Decimal | None
    activo: bool
    orden: int
    regla_imputacion: ReglaImputacionEmbedded | None

    model_config = {"from_attributes": True}
