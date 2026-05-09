import logging
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria_irp import CategoriaIRP
from app.models.enums import DestinoRegComprobante
from app.models.regla_imputacion import ReglaImputacion

logger = logging.getLogger(__name__)

# Mapeo: codigo_categoria → (imputa_iva_credito, iva_porcentaje, imputa_irp, destino)
_REGLAS: list[tuple[str, bool, Decimal | None, bool, DestinoRegComprobante]] = [
    ("ACTIVIDAD_GRAVADA",     True,  Decimal("100.00"), True,  DestinoRegComprobante.IRP_RSP),
    ("SERVICIOS_BASICOS",     True,  Decimal("50.00"),  True,  DestinoRegComprobante.IRP_RSP),
    ("ALIMENTACION",          False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("VESTIMENTA",            False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("ALQUILER_VIVIENDA",     False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("VEHICULO",              False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("SALUD",                 False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("ESPARCIMIENTO",         False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("EDUCACION",             False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("SERVICIOS_FINANCIEROS", False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("DONACIONES",            False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("MANTENIMIENTO_VIVIENDA",False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("MOBILIARIO_HOGAR",      False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("APORTE_IPS",            False, None,              True,  DestinoRegComprobante.IRP_RSP),
    ("NO_DEDUCIBLE",          False, None,              False, DestinoRegComprobante.NO_IMPUTAR),
    ("NO_IMPUTAR",            False, None,              False, DestinoRegComprobante.NO_IMPUTAR),
]


async def seed_reglas_imputacion(db: AsyncSession) -> None:
    """Inserta una ReglaImputacion por categoría IRP."""
    result = await db.execute(select(CategoriaIRP.codigo, CategoriaIRP.id))
    cat_map: dict[str, uuid.UUID] = {row.codigo: row.id for row in result}

    rows = []
    for i, (codigo, iva_cred, iva_pct, irp, destino) in enumerate(_REGLAS):
        cat_id = cat_map.get(codigo)
        if cat_id is None:
            logger.warning("reglas_imputacion: categoría '%s' no encontrada, skip.", codigo)
            continue
        rows.append({
            "id": uuid.UUID(f"22222222-{i+1:04d}-0000-0000-000000000000"),
            "categoria_irp_id": cat_id,
            "imputa_iva_credito": iva_cred,
            "imputa_iva_credito_porcentaje": iva_pct,
            "imputa_irp": irp,
            "destino_reg_comprobante": destino.value,
            "notas": None,
        })

    await db.execute(ReglaImputacion.__table__.insert(), rows)
    logger.info("reglas_imputacion: insertadas %d filas.", len(rows))
