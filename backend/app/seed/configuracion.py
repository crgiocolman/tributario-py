import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuracion_fiscal import ConfiguracionFiscal

logger = logging.getLogger(__name__)

_AHORA = datetime(2026, 5, 9, 0, 0, 0, tzinfo=timezone.utc)

_CONFIGS = [
    {
        "id": uuid.UUID("33333333-2025-0000-0000-000000000000"),
        "anio_fiscal": 2025,
        "ruc": "COMPLETAR",
        "razon_social": "COMPLETAR",
        "ultimo_digito_ruc": 0,
        "umbral_irp": 80_000_000,
        "tramo_irp_1_hasta": 50_000_000,
        "tramo_irp_1_tasa": "8.00",
        "tramo_irp_2_hasta": 150_000_000,
        "tramo_irp_2_tasa": "9.00",
        "tramo_irp_3_tasa": "10.00",
        "tasa_iva_general": "10.00",
        "tasa_iva_reducida": "5.00",
        "multa_dj_determinativa": 50_000,
        "multa_dj_informativa": 100_000,
        "tasa_interes_diario": "0.0500",
        "fecha_inicio_ejercicio": date(2025, 1, 1),
        "fecha_fin_ejercicio": date(2025, 12, 31),
        "created_at": _AHORA,
        "updated_at": _AHORA,
    },
    {
        "id": uuid.UUID("33333333-2026-0000-0000-000000000000"),
        "anio_fiscal": 2026,
        "ruc": "COMPLETAR",
        "razon_social": "COMPLETAR",
        "ultimo_digito_ruc": 0,
        "umbral_irp": 80_000_000,
        "tramo_irp_1_hasta": 50_000_000,
        "tramo_irp_1_tasa": "8.00",
        "tramo_irp_2_hasta": 150_000_000,
        "tramo_irp_2_tasa": "9.00",
        "tramo_irp_3_tasa": "10.00",
        "tasa_iva_general": "10.00",
        "tasa_iva_reducida": "5.00",
        "multa_dj_determinativa": 50_000,
        "multa_dj_informativa": 100_000,
        "tasa_interes_diario": "0.0500",
        "fecha_inicio_ejercicio": date(2026, 1, 1),
        "fecha_fin_ejercicio": date(2026, 12, 31),
        "created_at": _AHORA,
        "updated_at": _AHORA,
    },
]


async def seed_configuracion_fiscal(db: AsyncSession) -> None:
    """Inserta ConfiguracionFiscal para 2025 y 2026 si no existen."""
    for cfg in _CONFIGS:
        existe = await db.scalar(
            select(ConfiguracionFiscal.id).where(
                ConfiguracionFiscal.anio_fiscal == cfg["anio_fiscal"]
            )
        )
        if existe:
            logger.info("configuracion_fiscal: anio %d ya existe, skip.", cfg["anio_fiscal"])
            continue
        await db.execute(ConfiguracionFiscal.__table__.insert().values(cfg))
        logger.info("configuracion_fiscal: insertado anio %d.", cfg["anio_fiscal"])
