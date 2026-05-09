import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.declaracion_jurada import DeclaracionJurada
from app.models.enums import EstadoDJ, Formulario
from app.schemas.declaracion import DeclaracionCreate, DeclaracionUpdate

logger = logging.getLogger(__name__)


async def listar_declaraciones(
    db: AsyncSession,
    *,
    formulario: Formulario | None = None,
    anio_fiscal: int | None = None,
    estado: EstadoDJ | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[DeclaracionJurada], int]:
    stmt = select(DeclaracionJurada)

    if formulario is not None:
        stmt = stmt.where(DeclaracionJurada.formulario == formulario)
    if anio_fiscal is not None:
        stmt = stmt.where(DeclaracionJurada.periodo.startswith(str(anio_fiscal)))
    if estado is not None:
        stmt = stmt.where(DeclaracionJurada.estado == estado)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.order_by(DeclaracionJurada.fecha_presentacion.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def get_declaracion(db: AsyncSession, id: UUID) -> DeclaracionJurada | None:
    return (
        await db.execute(select(DeclaracionJurada).where(DeclaracionJurada.id == id))
    ).scalar_one_or_none()


async def crear_declaracion(db: AsyncSession, data: DeclaracionCreate) -> DeclaracionJurada:
    now = datetime.now(timezone.utc)
    dj = DeclaracionJurada(**data.model_dump(), created_at=now, updated_at=now)
    db.add(dj)
    try:
        await db.commit()
        await db.refresh(dj)
    except Exception:
        await db.rollback()
        raise
    return dj


async def actualizar_declaracion(db: AsyncSession, dj: DeclaracionJurada, data: DeclaracionUpdate) -> DeclaracionJurada:
    now = datetime.now(timezone.utc)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dj, field, value)
    dj.updated_at = now
    try:
        await db.commit()
        await db.refresh(dj)
    except Exception:
        await db.rollback()
        raise
    return dj
