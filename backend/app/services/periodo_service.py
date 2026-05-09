import calendar
import logging
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria_irp import CategoriaIRP
from app.models.comprobante import Comprobante
from app.models.configuracion_fiscal import ConfiguracionFiscal
from app.models.enums import TipoOperacion
from app.models.imputacion_fiscal import ImputacionFiscal
from app.models.ingreso import Ingreso
from app.models.periodo_fiscal import PeriodoFiscal
from app.schemas.periodo import (
    ComprobantesResumen,
    EstadoPresentacion,
    PeriodoFiscalOut,
    ResumenIRP,
    ResumenIVA,
)

logger = logging.getLogger(__name__)

# Días de vencimiento por dígito RUC (dígito 0 → día 25 F120, 26 Reg. Comprob.)
_DIA_F120 = {0: 25, 1: 26, 2: 27, 3: 28, 4: 22, 5: 23, 6: 24, 7: 25, 8: 26, 9: 27}
_DIA_REG = {d: v + 1 for d, v in _DIA_F120.items()}


def _vencimiento(periodo: str, dia: int) -> date:
    year, month = int(periodo[:4]), int(periodo[5:7])
    if month == 12:
        year, month = year + 1, 1
    else:
        month += 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(dia, last))


async def recalcular_periodo(db: AsyncSession, periodo: str) -> PeriodoFiscal:
    anio_fiscal = int(periodo[:4])
    now = datetime.now(timezone.utc)

    rows = (
        await db.execute(
            select(Comprobante, ImputacionFiscal)
            .join(ImputacionFiscal, ImputacionFiscal.comprobante_id == Comprobante.id, isouter=True)
            .where(Comprobante.periodo_fiscal == periodo, Comprobante.deleted_at.is_(None))
        )
    ).all()

    tv10 = tv5 = tve = tvd = tc10 = tc5 = tce = tci = cvc = cvv = eirp = 0

    for comp, imp in rows:
        if comp.tipo_operacion == TipoOperacion.VENTA:
            tv10 += comp.monto_gravado_10
            tv5 += comp.monto_gravado_5
            tve += comp.monto_exento
            tvd += comp.iva_10 + comp.iva_5
            cvv += 1
        else:
            tc10 += comp.monto_gravado_10
            tc5 += comp.monto_gravado_5
            tce += comp.monto_exento
            cvc += 1
            if imp and imp.imputa_iva_credito:
                tci += imp.iva_credito_monto
            if imp and imp.imputa_irp:
                eirp += comp.total

    ingresos_irp = (
        await db.execute(
            select(func.coalesce(func.sum(Ingreso.monto_computable_irp), 0))
            .where(Ingreso.periodo_devengado == periodo)
        )
    ).scalar() or 0

    pf = (
        await db.execute(select(PeriodoFiscal).where(PeriodoFiscal.periodo == periodo))
    ).scalar_one_or_none()

    if pf is None:
        pf = PeriodoFiscal(
            id=uuid4(),
            periodo=periodo,
            anio_fiscal=anio_fiscal,
            created_at=now,
            updated_at=now,
        )
        db.add(pf)
    else:
        pf.updated_at = now

    pf.total_ventas_gravadas_10 = tv10
    pf.total_ventas_gravadas_5 = tv5
    pf.total_ventas_exentas = tve
    pf.total_iva_debito = tvd
    pf.total_compras_gravadas_10 = tc10
    pf.total_compras_gravadas_5 = tc5
    pf.total_compras_exentas = tce
    pf.total_iva_credito_utilizado = tci
    pf.saldo_iva = tvd - tci
    pf.total_ingresos_irp = int(ingresos_irp)
    pf.total_egresos_irp = eirp
    pf.cantidad_comprobantes_compras = cvc
    pf.cantidad_comprobantes_ventas = cvv

    await db.flush()
    return pf


async def listar_periodos(
    db: AsyncSession,
    *,
    anio_fiscal: int | None = None,
    f120_presentado: bool | None = None,
    reg_comprobantes_presentado: bool | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[PeriodoFiscal], int]:
    stmt = select(PeriodoFiscal)

    if anio_fiscal is not None:
        stmt = stmt.where(PeriodoFiscal.anio_fiscal == anio_fiscal)
    if f120_presentado is not None:
        stmt = stmt.where(PeriodoFiscal.f120_presentado == f120_presentado)
    if reg_comprobantes_presentado is not None:
        stmt = stmt.where(PeriodoFiscal.reg_comprobantes_presentado == reg_comprobantes_presentado)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.order_by(PeriodoFiscal.periodo.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def get_periodo_detalle(db: AsyncSession, periodo: str) -> PeriodoFiscalOut | None:
    pf = (
        await db.execute(select(PeriodoFiscal).where(PeriodoFiscal.periodo == periodo))
    ).scalar_one_or_none()
    if pf is None:
        return None

    cat_rows = (
        await db.execute(
            select(CategoriaIRP.codigo, func.sum(Comprobante.total))
            .join(ImputacionFiscal, ImputacionFiscal.categoria_irp_id == CategoriaIRP.id)
            .join(Comprobante, Comprobante.id == ImputacionFiscal.comprobante_id)
            .where(
                Comprobante.periodo_fiscal == periodo,
                Comprobante.deleted_at.is_(None),
                Comprobante.tipo_operacion == TipoOperacion.COMPRA,
                ImputacionFiscal.imputa_irp.is_(True),
            )
            .group_by(CategoriaIRP.codigo)
        )
    ).all()
    egresos_por_cat = {codigo: int(total) for codigo, total in cat_rows}

    conf = (
        await db.execute(
            select(ConfiguracionFiscal).where(ConfiguracionFiscal.anio_fiscal == pf.anio_fiscal)
        )
    ).scalar_one_or_none()

    estado = EstadoPresentacion(
        f120_presentado=pf.f120_presentado,
        f120_fecha_presentacion=pf.f120_fecha_presentacion,
        reg_comprobantes_presentado=pf.reg_comprobantes_presentado,
        reg_comprobantes_fecha=pf.reg_comprobantes_fecha,
    )
    if conf:
        digito = conf.ultimo_digito_ruc
        today = date.today()
        f120_venc = _vencimiento(periodo, _DIA_F120.get(digito, 25))
        reg_venc = _vencimiento(periodo, _DIA_REG.get(digito, 26))
        estado.f120_vencimiento = f120_venc
        estado.f120_dias_restantes = (f120_venc - today).days
        estado.reg_comprobantes_vencimiento = reg_venc
        estado.reg_comprobantes_dias_restantes = (reg_venc - today).days

    return PeriodoFiscalOut(
        id=pf.id,
        periodo=pf.periodo,
        anio_fiscal=pf.anio_fiscal,
        resumen_iva=ResumenIVA(
            ventas_gravadas_10=pf.total_ventas_gravadas_10,
            ventas_gravadas_5=pf.total_ventas_gravadas_5,
            ventas_exentas=pf.total_ventas_exentas,
            iva_debito=pf.total_iva_debito,
            compras_gravadas_10=pf.total_compras_gravadas_10,
            compras_gravadas_5=pf.total_compras_gravadas_5,
            compras_exentas=pf.total_compras_exentas,
            iva_credito_utilizado=pf.total_iva_credito_utilizado,
            saldo_iva=pf.saldo_iva,
        ),
        resumen_irp=ResumenIRP(
            ingresos_computables=pf.total_ingresos_irp,
            egresos_por_categoria=egresos_por_cat,
            total_egresos=pf.total_egresos_irp,
        ),
        estado_presentacion=estado,
        comprobantes=ComprobantesResumen(
            compras=pf.cantidad_comprobantes_compras,
            ventas=pf.cantidad_comprobantes_ventas,
        ),
        created_at=pf.created_at,
        updated_at=pf.updated_at,
    )
