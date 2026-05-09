import logging
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuracion_fiscal import ConfiguracionFiscal
from app.models.enums import TipoIngreso
from app.models.ingreso import Ingreso
from app.schemas.ingreso import AcumuladoAnualOut, DetalleMensual, IngresoCreate, IngresoUpdate

logger = logging.getLogger(__name__)

_UMBRAL_DEFAULT = 80_000_000


async def listar_ingresos(
    db: AsyncSession,
    *,
    anio_fiscal: int | None = None,
    tipo_ingreso: TipoIngreso | None = None,
    contacto_id: UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Ingreso], int]:
    stmt = select(Ingreso).where(Ingreso.deleted_at.is_(None))

    if anio_fiscal is not None:
        stmt = stmt.where(Ingreso.periodo_devengado.startswith(str(anio_fiscal)))
    if tipo_ingreso is not None:
        stmt = stmt.where(Ingreso.tipo_ingreso == tipo_ingreso)
    if contacto_id is not None:
        stmt = stmt.where(Ingreso.contacto_id == contacto_id)
    if fecha_desde is not None:
        stmt = stmt.where(Ingreso.fecha_percepcion >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(Ingreso.fecha_percepcion <= fecha_hasta)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.order_by(Ingreso.fecha_percepcion.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def get_ingreso(db: AsyncSession, id: UUID) -> Ingreso | None:
    return (
        await db.execute(
            select(Ingreso).where(Ingreso.id == id, Ingreso.deleted_at.is_(None))
        )
    ).scalar_one_or_none()


async def crear_ingreso(db: AsyncSession, data: IngresoCreate) -> Ingreso:
    now = datetime.now(timezone.utc)
    ingreso = Ingreso(**data.model_dump(), created_at=now, updated_at=now)
    db.add(ingreso)
    try:
        await db.commit()
        await db.refresh(ingreso)
    except Exception:
        await db.rollback()
        raise
    return ingreso


async def actualizar_ingreso(db: AsyncSession, ingreso: Ingreso, data: IngresoUpdate) -> Ingreso:
    now = datetime.now(timezone.utc)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ingreso, field, value)
    ingreso.updated_at = now
    try:
        await db.commit()
        await db.refresh(ingreso)
    except Exception:
        await db.rollback()
        raise
    return ingreso


async def eliminar_ingreso(db: AsyncSession, ingreso: Ingreso) -> None:
    ingreso.deleted_at = datetime.now(timezone.utc)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise


async def get_acumulado_anual(db: AsyncSession, anio: int) -> AcumuladoAnualOut:
    conf = (
        await db.execute(
            select(ConfiguracionFiscal).where(ConfiguracionFiscal.anio_fiscal == anio)
        )
    ).scalar_one_or_none()
    umbral = int(conf.umbral_irp) if conf else _UMBRAL_DEFAULT

    rows = (
        await db.execute(
            select(Ingreso)
            .where(
                Ingreso.periodo_devengado.startswith(str(anio)),
                Ingreso.deleted_at.is_(None),
            )
            .order_by(Ingreso.fecha_percepcion, Ingreso.created_at)
        )
    ).scalars().all()

    acum_bruto = 0
    acum_computable = 0
    fecha_cruce: date | None = None
    mensual: dict[str, dict] = {}

    for ing in rows:
        mes = ing.periodo_devengado[:7]
        if mes not in mensual:
            mensual[mes] = {"computable": 0, "acumulado": 0}

        acum_bruto += ing.monto_bruto
        if ing.es_gravado_irp:
            acum_computable += ing.monto_computable_irp
            if fecha_cruce is None and acum_computable >= umbral:
                fecha_cruce = ing.fecha_percepcion
            mensual[mes]["computable"] += ing.monto_computable_irp
        mensual[mes]["acumulado"] = acum_computable

    detalle = [
        DetalleMensual(mes=mes, computable=v["computable"], acumulado=v["acumulado"])
        for mes, v in sorted(mensual.items())
    ]

    porcentaje = round(acum_computable / umbral * 100, 2) if umbral > 0 else 0.0

    return AcumuladoAnualOut(
        anio_fiscal=anio,
        umbral_irp=umbral,
        acumulado_bruto=acum_bruto,
        acumulado_computable_irp=acum_computable,
        porcentaje_umbral=porcentaje,
        superado_umbral=acum_computable >= umbral,
        fecha_cruce_umbral=fecha_cruce,
        detalle_mensual=detalle,
    )
