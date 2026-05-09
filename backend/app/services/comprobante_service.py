import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comprobante import Comprobante
from app.models.enums import CargadoMarangatu, TipoOperacion
from app.models.imputacion_fiscal import ImputacionFiscal
from app.schemas.comprobante import ComprobanteCreate, ComprobanteUpdate
from app.services.periodo_service import recalcular_periodo

logger = logging.getLogger(__name__)


def _with_relations(stmt):
    return stmt.options(
        selectinload(Comprobante.imputacion_fiscal),
        selectinload(Comprobante.archivos_adjuntos),
    )


async def listar_comprobantes(
    db: AsyncSession,
    *,
    periodo_fiscal: str | None = None,
    tipo_operacion: TipoOperacion | None = None,
    contacto_id: UUID | None = None,
    cargado_marangatu: CargadoMarangatu | None = None,
    fecha_desde=None,
    fecha_hasta=None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Comprobante], int]:
    stmt = _with_relations(select(Comprobante)).where(Comprobante.deleted_at.is_(None))

    if periodo_fiscal is not None:
        stmt = stmt.where(Comprobante.periodo_fiscal == periodo_fiscal)
    if tipo_operacion is not None:
        stmt = stmt.where(Comprobante.tipo_operacion == tipo_operacion)
    if contacto_id is not None:
        stmt = stmt.where(Comprobante.contacto_id == contacto_id)
    if cargado_marangatu is not None:
        stmt = stmt.where(Comprobante.cargado_marangatu == cargado_marangatu)
    if fecha_desde is not None:
        stmt = stmt.where(Comprobante.fecha_emision >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(Comprobante.fecha_emision <= fecha_hasta)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.order_by(Comprobante.fecha_emision.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def get_comprobante(db: AsyncSession, id: UUID) -> Comprobante | None:
    return (
        await db.execute(
            _with_relations(select(Comprobante)).where(
                Comprobante.id == id,
                Comprobante.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()


async def crear_comprobante(db: AsyncSession, data: ComprobanteCreate) -> Comprobante:
    now = datetime.now(timezone.utc)
    comp_data = data.model_dump(exclude={"imputacion"})
    comprobante = Comprobante(**comp_data, created_at=now, updated_at=now)
    db.add(comprobante)

    imp_data = data.imputacion.model_dump()
    imputacion = ImputacionFiscal(
        **imp_data,
        comprobante_id=comprobante.id,
        rectificado=False,
        created_at=now,
        updated_at=now,
    )
    db.add(imputacion)

    await db.flush()
    await recalcular_periodo(db, comprobante.periodo_fiscal)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return await get_comprobante(db, comprobante.id)


async def actualizar_comprobante(db: AsyncSession, comprobante: Comprobante, data: ComprobanteUpdate) -> Comprobante:
    now = datetime.now(timezone.utc)
    periodo_anterior = comprobante.periodo_fiscal

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(comprobante, field, value)
    comprobante.updated_at = now

    await db.flush()
    await recalcular_periodo(db, comprobante.periodo_fiscal)
    if periodo_anterior != comprobante.periodo_fiscal:
        await recalcular_periodo(db, periodo_anterior)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return await get_comprobante(db, comprobante.id)


async def eliminar_comprobante(db: AsyncSession, comprobante: Comprobante) -> None:
    periodo = comprobante.periodo_fiscal
    comprobante.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await recalcular_periodo(db, periodo)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
