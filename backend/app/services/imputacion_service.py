import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria_irp import CategoriaIRP
from app.models.comprobante import Comprobante
from app.models.imputacion_fiscal import ImputacionFiscal
from app.schemas.imputacion import BatchRectificarBody, ImputacionUpdate

logger = logging.getLogger(__name__)


async def get_imputacion(db: AsyncSession, id: UUID) -> ImputacionFiscal | None:
    return (
        await db.execute(select(ImputacionFiscal).where(ImputacionFiscal.id == id))
    ).scalar_one_or_none()


async def rectificar_imputacion(
    db: AsyncSession, imputacion: ImputacionFiscal, data: ImputacionUpdate
) -> ImputacionFiscal:
    now = datetime.now(timezone.utc)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(imputacion, field, value)
    imputacion.rectificado = True
    imputacion.fecha_rectificacion = now
    imputacion.updated_at = now
    try:
        await db.commit()
        await db.refresh(imputacion)
    except Exception:
        await db.rollback()
        raise
    return imputacion


async def batch_rectificar(db: AsyncSession, body: BatchRectificarBody) -> int:
    now = datetime.now(timezone.utc)
    cambios = body.cambios

    stmt = (
        select(ImputacionFiscal)
        .join(Comprobante, Comprobante.id == ImputacionFiscal.comprobante_id)
        .where(
            Comprobante.periodo_fiscal == body.periodo_fiscal,
            Comprobante.deleted_at.is_(None),
            ImputacionFiscal.destino_reg_comprobante == cambios.destino_anterior,
        )
    )

    if cambios.solo_categorias:
        stmt = stmt.join(CategoriaIRP, CategoriaIRP.id == ImputacionFiscal.categoria_irp_id).where(
            CategoriaIRP.codigo.in_(cambios.solo_categorias)
        )

    imputaciones = (await db.execute(stmt)).scalars().all()

    for imp in imputaciones:
        imp.destino_reg_comprobante = cambios.destino_nuevo
        imp.rectificado = True
        imp.fecha_rectificacion = now
        imp.updated_at = now
        if cambios.notas_rectificacion:
            imp.notas_rectificacion = cambios.notas_rectificacion

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return len(imputaciones)
