import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contacto import Contacto
from app.models.enums import TipoContacto
from app.schemas.contacto import ContactoCreate, ContactoUpdate

logger = logging.getLogger(__name__)


async def listar_contactos(
    db: AsyncSession,
    *,
    tipo: TipoContacto | None = None,
    ruc: str | None = None,
    es_frecuente: bool | None = None,
    q: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Contacto], int]:
    stmt = select(Contacto).where(Contacto.deleted_at.is_(None))

    if tipo is not None:
        stmt = stmt.where(Contacto.tipo == tipo)
    if ruc is not None:
        stmt = stmt.where(Contacto.ruc == ruc)
    if es_frecuente is not None:
        stmt = stmt.where(Contacto.es_frecuente == es_frecuente)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Contacto.razon_social.ilike(like),
                Contacto.nombre_fantasia.ilike(like),
                Contacto.ruc.ilike(like),
            )
        )

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.order_by(Contacto.razon_social).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def get_contacto(db: AsyncSession, id: UUID) -> Contacto | None:
    return (
        await db.execute(
            select(Contacto).where(Contacto.id == id, Contacto.deleted_at.is_(None))
        )
    ).scalar_one_or_none()


async def crear_contacto(db: AsyncSession, data: ContactoCreate) -> Contacto:
    now = datetime.now(timezone.utc)
    contacto = Contacto(**data.model_dump(), created_at=now, updated_at=now)
    db.add(contacto)
    try:
        await db.commit()
        await db.refresh(contacto)
    except Exception:
        await db.rollback()
        raise
    return contacto


async def actualizar_contacto(db: AsyncSession, contacto: Contacto, data: ContactoUpdate) -> Contacto:
    now = datetime.now(timezone.utc)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contacto, field, value)
    contacto.updated_at = now
    try:
        await db.commit()
        await db.refresh(contacto)
    except Exception:
        await db.rollback()
        raise
    return contacto


async def eliminar_contacto(db: AsyncSession, contacto: Contacto) -> None:
    contacto.deleted_at = datetime.now(timezone.utc)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
