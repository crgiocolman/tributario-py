import logging
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.archivo_adjunto import ArchivoAdjunto
from app.models.categoria_irp import CategoriaIRP
from app.models.comprobante import Comprobante
from app.models.contacto import Contacto
from app.models.enums import (
    CargadoMarangatu,
    Condicion,
    DestinoRegComprobante,
    FormaEmision,
    FormaPago,
    SyncStatus,
    TipoComprobante,
    TipoContacto,
    TipoContribuyente,
    TipoIngreso,
    TipoOperacion,
)
from app.models.imputacion_fiscal import ImputacionFiscal
from app.models.ingreso import Ingreso
from app.schemas.categoria_irp import CategoriaIRPOut
from app.schemas.comprobante import ArchivoAdjuntoOut, ComprobanteOut
from app.schemas.contacto import ContactoOut
from app.schemas.imputacion import ImputacionOut
from app.schemas.ingreso import IngresoOut
from app.schemas.sync import CambioItem, ConflictoItem, PullResponse, PushRequest, PushResponse, SyncStatusResponse
from app.services.periodo_service import recalcular_periodo

logger = logging.getLogger(__name__)


# --- parsing helpers ---

def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _parse_enum(enum_cls, value: Any):
    if value is None:
        return None
    for candidate in (value, str(value).lower().replace("-", "_")):
        try:
            return enum_cls(candidate)
        except ValueError:
            continue
    return None


def _parse_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, AttributeError):
        return None


def _is_server_newer(server_dt: datetime | None, client_dt: datetime | None) -> bool:
    if server_dt is None or client_dt is None:
        return False
    return server_dt > client_dt


# --- table handlers ---

async def _apply_contacto(
    db: AsyncSession, item: CambioItem, now: datetime
) -> tuple[str, dict[str, Any] | None]:
    p = item.payload
    client_updated_at = _parse_dt(p.get("updated_at")) or now

    existing: Contacto | None = (
        await db.execute(select(Contacto).where(Contacto.id == item.registro_id))
    ).scalar_one_or_none()

    if existing is not None and _is_server_newer(existing.updated_at, client_updated_at):
        return "conflict", ContactoOut.model_validate(existing).model_dump(mode="json")

    if item.operacion == "delete":
        if existing is None:
            return "accepted", None
        existing.deleted_at = _parse_dt(p.get("deleted_at")) or now
        existing.updated_at = client_updated_at
        existing.sync_status = SyncStatus.SYNCED
        return "accepted", None

    fields: dict[str, Any] = {
        "ruc": p.get("ruc") or "",
        "razon_social": p.get("razon_social") or "",
        "nombre_fantasia": p.get("nombre_fantasia"),
        "tipo": _parse_enum(TipoContacto, p.get("tipo")) or TipoContacto.PROVEEDOR,
        "tipo_contribuyente": _parse_enum(TipoContribuyente, p.get("tipo_contribuyente")),
        "telefono": p.get("telefono"),
        "email": p.get("email"),
        "direccion": p.get("direccion"),
        "notas": p.get("notas"),
        "es_frecuente": bool(p.get("es_frecuente", False)),
        "device_id": p.get("device_id"),
        "sync_status": SyncStatus.SYNCED,
        "created_at": _parse_dt(p.get("created_at")) or now,
        "updated_at": client_updated_at,
        "deleted_at": _parse_dt(p.get("deleted_at")),
    }

    if existing is None:
        db.add(Contacto(id=item.registro_id, **fields))
    else:
        for k, v in fields.items():
            setattr(existing, k, v)

    return "accepted", None


async def _apply_comprobante(
    db: AsyncSession, item: CambioItem, now: datetime, periodos: set[str]
) -> tuple[str, dict[str, Any] | None]:
    p = item.payload
    client_updated_at = _parse_dt(p.get("updated_at")) or now

    existing: Comprobante | None = (
        await db.execute(
            select(Comprobante)
            .options(
                selectinload(Comprobante.imputacion_fiscal),
                selectinload(Comprobante.archivos_adjuntos),
            )
            .where(Comprobante.id == item.registro_id)
        )
    ).scalar_one_or_none()

    if existing is not None and _is_server_newer(existing.updated_at, client_updated_at):
        return "conflict", ComprobanteOut.model_validate(existing).model_dump(mode="json")

    if item.operacion == "delete":
        if existing is None:
            return "accepted", None
        periodos.add(existing.periodo_fiscal)
        existing.deleted_at = _parse_dt(p.get("deleted_at")) or now
        existing.updated_at = client_updated_at
        existing.sync_status = SyncStatus.SYNCED
        return "accepted", None

    contacto_id = _parse_uuid(p.get("contacto_id"))
    fecha_emision = _parse_date(p.get("fecha_emision"))
    tipo_operacion = _parse_enum(TipoOperacion, p.get("tipo_operacion"))
    tipo_comprobante = _parse_enum(TipoComprobante, p.get("tipo_comprobante"))
    forma_emision = _parse_enum(FormaEmision, p.get("forma_emision"))
    condicion = _parse_enum(Condicion, p.get("condicion"))

    if not all([contacto_id, fecha_emision, tipo_operacion, tipo_comprobante, forma_emision, condicion]):
        return "rejected", None

    tipo_cambio = None
    if p.get("tipo_cambio") is not None:
        try:
            tipo_cambio = Decimal(str(p["tipo_cambio"]))
        except InvalidOperation:
            pass

    periodo = p.get("periodo_fiscal") or ""

    fields: dict[str, Any] = {
        "contacto_id": contacto_id,
        "tipo_operacion": tipo_operacion,
        "tipo_comprobante": tipo_comprobante,
        "forma_emision": forma_emision,
        "numero_timbrado": p.get("numero_timbrado"),
        "numero_comprobante": p.get("numero_comprobante"),
        "fecha_emision": fecha_emision,
        "fecha_percepcion": _parse_date(p.get("fecha_percepcion")),
        "condicion": condicion,
        "moneda": p.get("moneda") or "PYG",
        "tipo_cambio": tipo_cambio,
        "monto_exento": int(p.get("monto_exento") or 0),
        "monto_gravado_5": int(p.get("monto_gravado_5") or 0),
        "iva_5": int(p.get("iva_5") or 0),
        "monto_gravado_10": int(p.get("monto_gravado_10") or 0),
        "iva_10": int(p.get("iva_10") or 0),
        "total": int(p.get("total") or 0),
        "forma_pago": _parse_enum(FormaPago, p.get("forma_pago")),
        "concepto": p.get("concepto"),
        "periodo_fiscal": periodo,
        "cargado_marangatu": _parse_enum(CargadoMarangatu, p.get("cargado_marangatu")) or CargadoMarangatu.AUTO,
        "notas": p.get("notas"),
        "device_id": p.get("device_id"),
        "sync_status": SyncStatus.SYNCED,
        "created_at": _parse_dt(p.get("created_at")) or now,
        "updated_at": client_updated_at,
        "deleted_at": _parse_dt(p.get("deleted_at")),
    }

    if existing is None:
        db.add(Comprobante(id=item.registro_id, **fields))
    else:
        if existing.periodo_fiscal != periodo:
            periodos.add(existing.periodo_fiscal)
        for k, v in fields.items():
            setattr(existing, k, v)

    if periodo:
        periodos.add(periodo)

    return "accepted", None


async def _apply_imputacion(
    db: AsyncSession, item: CambioItem, now: datetime
) -> tuple[str, dict[str, Any] | None]:
    p = item.payload
    client_updated_at = _parse_dt(p.get("updated_at")) or now

    existing: ImputacionFiscal | None = (
        await db.execute(select(ImputacionFiscal).where(ImputacionFiscal.id == item.registro_id))
    ).scalar_one_or_none()

    if existing is not None and _is_server_newer(existing.updated_at, client_updated_at):
        return "conflict", ImputacionOut.model_validate(existing).model_dump(mode="json")

    if item.operacion == "delete":
        return "rejected", None  # imputaciones no tienen soft delete

    comprobante_id = _parse_uuid(p.get("comprobante_id"))
    categoria_irp_id = _parse_uuid(p.get("categoria_irp_id"))
    destino = _parse_enum(DestinoRegComprobante, p.get("destino_reg_comprobante"))

    if not all([comprobante_id, categoria_irp_id, destino]):
        return "rejected", None

    porcentaje_raw = p.get("iva_credito_porcentaje", 0)
    try:
        iva_credito_porcentaje = Decimal(str(porcentaje_raw))
    except InvalidOperation:
        iva_credito_porcentaje = Decimal("0")

    fields: dict[str, Any] = {
        "comprobante_id": comprobante_id,
        "categoria_irp_id": categoria_irp_id,
        "imputa_iva_credito": bool(p.get("imputa_iva_credito", False)),
        "iva_credito_porcentaje": iva_credito_porcentaje,
        "iva_credito_monto": int(p.get("iva_credito_monto") or 0),
        "imputa_irp": bool(p.get("imputa_irp", False)),
        "destino_reg_comprobante": destino,
        "a_nombre_de": p.get("a_nombre_de"),
        "rectificado": bool(p.get("rectificado", False)),
        "fecha_rectificacion": _parse_dt(p.get("fecha_rectificacion")),
        "notas_rectificacion": p.get("notas_rectificacion"),
        "created_at": _parse_dt(p.get("created_at")) or now,
        "updated_at": client_updated_at,
    }

    if existing is None:
        db.add(ImputacionFiscal(id=item.registro_id, **fields))
    else:
        for k, v in fields.items():
            setattr(existing, k, v)

    return "accepted", None


async def _apply_ingreso(
    db: AsyncSession, item: CambioItem, now: datetime
) -> tuple[str, dict[str, Any] | None]:
    p = item.payload
    client_updated_at = _parse_dt(p.get("updated_at")) or now

    existing: Ingreso | None = (
        await db.execute(select(Ingreso).where(Ingreso.id == item.registro_id))
    ).scalar_one_or_none()

    if existing is not None and _is_server_newer(existing.updated_at, client_updated_at):
        return "conflict", IngresoOut.model_validate(existing).model_dump(mode="json")

    if item.operacion == "delete":
        if existing is None:
            return "accepted", None
        existing.deleted_at = _parse_dt(p.get("deleted_at")) or now
        existing.updated_at = client_updated_at
        existing.sync_status = SyncStatus.SYNCED
        return "accepted", None

    contacto_id = _parse_uuid(p.get("contacto_id"))
    tipo_ingreso = _parse_enum(TipoIngreso, p.get("tipo_ingreso"))
    fecha_percepcion = _parse_date(p.get("fecha_percepcion"))

    if not all([contacto_id, tipo_ingreso, fecha_percepcion]):
        return "rejected", None

    fields: dict[str, Any] = {
        "contacto_id": contacto_id,
        "comprobante_id": _parse_uuid(p.get("comprobante_id")),
        "tipo_ingreso": tipo_ingreso,
        "periodo_devengado": p.get("periodo_devengado") or "",
        "fecha_percepcion": fecha_percepcion,
        "monto_bruto": int(p.get("monto_bruto") or 0),
        "aporte_ips_trabajador": int(p.get("aporte_ips_trabajador") or 0),
        "otros_descuentos": int(p.get("otros_descuentos") or 0),
        "monto_exonerado": int(p.get("monto_exonerado") or 0),
        "monto_computable_irp": int(p.get("monto_computable_irp") or 0),
        "es_gravado_irp": bool(p.get("es_gravado_irp", False)),
        "acumulado_anual": int(p["acumulado_anual"]) if p.get("acumulado_anual") is not None else None,
        "notas": p.get("notas"),
        "device_id": p.get("device_id"),
        "sync_status": SyncStatus.SYNCED,
        "created_at": _parse_dt(p.get("created_at")) or now,
        "updated_at": client_updated_at,
        "deleted_at": _parse_dt(p.get("deleted_at")),
    }

    if existing is None:
        db.add(Ingreso(id=item.registro_id, **fields))
    else:
        for k, v in fields.items():
            setattr(existing, k, v)

    return "accepted", None


_TABLA_HANDLERS = {
    "contactos": _apply_contacto,
    "comprobantes": _apply_comprobante,
    "imputaciones_fiscales": _apply_imputacion,
    "ingresos": _apply_ingreso,
}


# --- public API ---

async def process_push(db: AsyncSession, request: PushRequest) -> PushResponse:
    now = datetime.now(timezone.utc)
    aceptados: list[UUID] = []
    rechazados: list[UUID] = []
    conflictos: list[ConflictoItem] = []
    periodos_a_recalcular: set[str] = set()

    for item in request.cambios:
        handler = _TABLA_HANDLERS.get(item.tabla)
        if handler is None:
            logger.warning("Tabla desconocida en push: %s", item.tabla)
            rechazados.append(item.registro_id)
            continue

        try:
            if item.tabla == "comprobantes":
                result, ganador = await handler(db, item, now, periodos_a_recalcular)  # type: ignore[call-arg]
            else:
                result, ganador = await handler(db, item, now)  # type: ignore[call-arg]
        except Exception:
            logger.exception("Error procesando cambio %s/%s", item.tabla, item.registro_id)
            rechazados.append(item.registro_id)
            continue

        if result == "accepted":
            aceptados.append(item.registro_id)
        elif result == "conflict":
            conflictos.append(ConflictoItem(registro_id=item.registro_id, tabla=item.tabla, ganador=ganador or {}))
        else:
            rechazados.append(item.registro_id)

    for periodo in periodos_a_recalcular:
        if periodo:
            await recalcular_periodo(db, periodo)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return PushResponse(
        aceptados=aceptados,
        rechazados=rechazados,
        conflictos=conflictos,
        server_timestamp=now,
    )


async def process_pull(db: AsyncSession, since: datetime | None) -> PullResponse:
    now = datetime.now(timezone.utc)

    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    def _since_filter(col):
        return col > since if since is not None else True

    contactos = (
        await db.execute(select(Contacto).where(_since_filter(Contacto.updated_at)))
    ).scalars().all()

    comprobantes = (
        await db.execute(
            select(Comprobante)
            .options(
                selectinload(Comprobante.imputacion_fiscal),
                selectinload(Comprobante.archivos_adjuntos),
            )
            .where(_since_filter(Comprobante.updated_at))
        )
    ).scalars().all()

    imputaciones = (
        await db.execute(select(ImputacionFiscal).where(_since_filter(ImputacionFiscal.updated_at)))
    ).scalars().all()

    ingresos = (
        await db.execute(select(Ingreso).where(_since_filter(Ingreso.updated_at)))
    ).scalars().all()

    # Adjuntos: immutables, se filtra por created_at. No incluye ruta_almacenamiento (solo metadata).
    adjuntos = (
        await db.execute(select(ArchivoAdjunto).where(_since_filter(ArchivoAdjunto.created_at)))
    ).scalars().all()

    # Categorías IRP: datos de referencia estáticos, siempre se devuelven todas (sin filtro since).
    categorias = (
        await db.execute(
            select(CategoriaIRP)
            .options(selectinload(CategoriaIRP.regla_imputacion))
            .where(CategoriaIRP.activo == True)
            .order_by(CategoriaIRP.orden)
        )
    ).scalars().all()

    cambios: dict[str, list[Any]] = {
        "contactos": [ContactoOut.model_validate(c).model_dump(mode="json") for c in contactos],
        "comprobantes": [ComprobanteOut.model_validate(c).model_dump(mode="json") for c in comprobantes],
        "imputaciones_fiscales": [ImputacionOut.model_validate(i).model_dump(mode="json") for i in imputaciones],
        "ingresos": [IngresoOut.model_validate(i).model_dump(mode="json") for i in ingresos],
        "adjuntos": [ArchivoAdjuntoOut.model_validate(a).model_dump(mode="json") for a in adjuntos],
        "categorias_irp": [CategoriaIRPOut.model_validate(c).model_dump(mode="json") for c in categorias],
    }

    return PullResponse(cambios=cambios, server_timestamp=now, hay_mas=False)


async def get_status() -> SyncStatusResponse:
    return SyncStatusResponse(server_timestamp=datetime.now(timezone.utc))
