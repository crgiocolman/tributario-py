import calendar
import logging
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria_irp import CategoriaIRP
from app.models.comprobante import Comprobante
from app.models.configuracion_fiscal import ConfiguracionFiscal
from app.models.imputacion_fiscal import ImputacionFiscal
from app.models.ingreso import Ingreso
from app.models.periodo_fiscal import PeriodoFiscal
from app.schemas.reportes import (
    DashboardOut,
    DashboardResumenIRP,
    DashboardResumenIVA,
    EgresoCategoria,
    EgresosPorCategoriaOut,
    IRPProyeccionOut,
    IVAMensualOut,
    IVAMes,
    VencimientoItem,
    VencimientosOut,
)
from app.services.irp_service import calcular_impuesto_irp

logger = logging.getLogger(__name__)

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


async def get_dashboard(db: AsyncSession, anio: int | None = None) -> DashboardOut:
    if anio is None:
        anio = date.today().year

    periodos = (
        await db.execute(select(PeriodoFiscal).where(PeriodoFiscal.anio_fiscal == anio))
    ).scalars().all()

    iva_debito_ytd = sum(p.total_iva_debito for p in periodos)
    iva_credito_ytd = sum(p.total_iva_credito_utilizado for p in periodos)
    pendientes_f120 = sum(1 for p in periodos if not p.f120_presentado)

    conf = (
        await db.execute(
            select(ConfiguracionFiscal).where(ConfiguracionFiscal.anio_fiscal == anio)
        )
    ).scalar_one_or_none()
    umbral = int(conf.umbral_irp) if conf else 80_000_000

    acum_computable = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(Ingreso.monto_computable_irp), 0)).where(
                    Ingreso.periodo_devengado.startswith(str(anio)),
                    Ingreso.deleted_at.is_(None),
                    Ingreso.es_gravado_irp.is_(True),
                )
            )
        ).scalar()
        or 0
    )

    egresos_irp = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(Comprobante.total), 0))
                .join(ImputacionFiscal, ImputacionFiscal.comprobante_id == Comprobante.id)
                .where(
                    Comprobante.periodo_fiscal.startswith(str(anio)),
                    Comprobante.deleted_at.is_(None),
                    ImputacionFiscal.imputa_irp.is_(True),
                )
            )
        ).scalar()
        or 0
    )

    renta_neta = max(0, acum_computable - egresos_irp)
    impuesto = calcular_impuesto_irp(renta_neta, conf)
    porcentaje = round(acum_computable / umbral * 100, 2) if umbral > 0 else 0.0

    mes_actual = date.today().strftime("%Y-%m")
    count_mes = (
        await db.execute(
            select(func.count(Comprobante.id)).where(
                Comprobante.periodo_fiscal == mes_actual,
                Comprobante.deleted_at.is_(None),
            )
        )
    ).scalar() or 0

    vencimientos = await get_vencimientos(db)

    return DashboardOut(
        anio_fiscal=anio,
        fecha_generacion=datetime.now(timezone.utc),
        resumen_iva=DashboardResumenIVA(
            periodos_con_datos=len(periodos),
            iva_debito_ytd=iva_debito_ytd,
            iva_credito_ytd=iva_credito_ytd,
            saldo_ytd=iva_debito_ytd - iva_credito_ytd,
            periodos_pendientes_f120=pendientes_f120,
        ),
        resumen_irp=DashboardResumenIRP(
            acumulado_computable=acum_computable,
            umbral_irp=umbral,
            porcentaje_umbral=porcentaje,
            superado_umbral=acum_computable >= umbral,
            impuesto_estimado=impuesto.total,
        ),
        proximos_vencimientos=vencimientos.items[:5],
        comprobantes_mes_actual=int(count_mes),
    )


async def get_iva_mensual(db: AsyncSession, anio: int) -> IVAMensualOut:
    periodos = (
        await db.execute(
            select(PeriodoFiscal)
            .where(PeriodoFiscal.anio_fiscal == anio)
            .order_by(PeriodoFiscal.periodo)
        )
    ).scalars().all()

    meses = [
        IVAMes(
            periodo=pf.periodo,
            iva_debito=pf.total_iva_debito,
            iva_credito_utilizado=pf.total_iva_credito_utilizado,
            saldo_iva=pf.saldo_iva,
            ventas_gravadas_10=pf.total_ventas_gravadas_10,
            ventas_gravadas_5=pf.total_ventas_gravadas_5,
            ventas_exentas=pf.total_ventas_exentas,
            compras_gravadas_10=pf.total_compras_gravadas_10,
            compras_gravadas_5=pf.total_compras_gravadas_5,
            compras_exentas=pf.total_compras_exentas,
            cantidad_compras=pf.cantidad_comprobantes_compras,
            cantidad_ventas=pf.cantidad_comprobantes_ventas,
            f120_presentado=pf.f120_presentado,
        )
        for pf in periodos
    ]

    total_debito = sum(m.iva_debito for m in meses)
    total_credito = sum(m.iva_credito_utilizado for m in meses)

    return IVAMensualOut(
        anio_fiscal=anio,
        meses=meses,
        total_iva_debito=total_debito,
        total_iva_credito=total_credito,
        saldo_acumulado=total_debito - total_credito,
    )


async def get_irp_proyeccion(db: AsyncSession, anio: int) -> IRPProyeccionOut:
    conf = (
        await db.execute(
            select(ConfiguracionFiscal).where(ConfiguracionFiscal.anio_fiscal == anio)
        )
    ).scalar_one_or_none()

    ingresos_rows = (
        await db.execute(
            select(Ingreso).where(
                Ingreso.periodo_devengado.startswith(str(anio)),
                Ingreso.deleted_at.is_(None),
            )
        )
    ).scalars().all()

    bruto_acum = sum(i.monto_bruto for i in ingresos_rows)
    computable_acum = sum(i.monto_computable_irp for i in ingresos_rows if i.es_gravado_irp)

    cat_rows = (
        await db.execute(
            select(
                CategoriaIRP.codigo,
                func.coalesce(func.sum(Comprobante.total), 0),
                func.count(Comprobante.id),
            )
            .join(ImputacionFiscal, ImputacionFiscal.categoria_irp_id == CategoriaIRP.id)
            .join(Comprobante, Comprobante.id == ImputacionFiscal.comprobante_id)
            .where(
                Comprobante.periodo_fiscal.startswith(str(anio)),
                Comprobante.deleted_at.is_(None),
                ImputacionFiscal.imputa_irp.is_(True),
            )
            .group_by(CategoriaIRP.codigo)
        )
    ).all()

    egresos_por_cat = {codigo: int(total) for codigo, total, _ in cat_rows}
    total_egresos = sum(egresos_por_cat.values())
    renta_neta_actual = max(0, computable_acum - total_egresos)

    today = date.today()
    meses_transcurridos = today.month if today.year == anio else 12
    meses_restantes = max(0, 12 - meses_transcurridos)
    renta_neta_proyectada = (
        int(renta_neta_actual * 12 / meses_transcurridos) if meses_transcurridos > 0 else renta_neta_actual
    )

    impuesto = calcular_impuesto_irp(renta_neta_proyectada, conf)
    reserva_mensual = int(impuesto.total / 12) if impuesto.total > 0 else 0

    ejercicio_inicio = conf.fecha_inicio_ejercicio if conf else date(anio, 1, 1)
    ejercicio_fin = conf.fecha_fin_ejercicio if conf else date(anio, 12, 31)

    return IRPProyeccionOut(
        anio_fiscal=anio,
        ejercicio_inicio=ejercicio_inicio,
        ejercicio_fin=ejercicio_fin,
        ingresos_brutos_acumulados=bruto_acum,
        ingresos_computables_irp=computable_acum,
        egresos_deducibles_acumulados=total_egresos,
        egresos_por_categoria=egresos_por_cat,
        renta_neta_actual=renta_neta_actual,
        renta_neta_proyectada_anual=renta_neta_proyectada,
        impuesto_proyectado=impuesto,
        reserva_mensual_sugerida=reserva_mensual,
        meses_transcurridos=meses_transcurridos,
        meses_restantes=meses_restantes,
    )


async def get_vencimientos(db: AsyncSession) -> VencimientosOut:
    conf = (
        await db.execute(
            select(ConfiguracionFiscal).order_by(ConfiguracionFiscal.anio_fiscal.desc())
        )
    ).scalar_one_or_none()

    if not conf:
        return VencimientosOut(items=[])

    digito = conf.ultimo_digito_ruc
    today = date.today()

    periodos = (
        await db.execute(
            select(PeriodoFiscal).order_by(PeriodoFiscal.periodo.desc()).limit(24)
        )
    ).scalars().all()

    items: list[VencimientoItem] = []
    for pf in periodos:
        f120_venc = _vencimiento(pf.periodo, _DIA_F120.get(digito, 25))
        reg_venc = _vencimiento(pf.periodo, _DIA_REG.get(digito, 26))
        f120_dias = (f120_venc - today).days
        reg_dias = (reg_venc - today).days

        if not pf.f120_presentado and f120_dias > -30:
            items.append(
                VencimientoItem(
                    periodo=pf.periodo,
                    formulario="F120",
                    vencimiento=f120_venc,
                    dias_restantes=f120_dias,
                    presentado=False,
                    fecha_presentacion=pf.f120_fecha_presentacion,
                )
            )
        if not pf.reg_comprobantes_presentado and reg_dias > -30:
            items.append(
                VencimientoItem(
                    periodo=pf.periodo,
                    formulario="REG_COMPROBANTES",
                    vencimiento=reg_venc,
                    dias_restantes=reg_dias,
                    presentado=False,
                    fecha_presentacion=pf.reg_comprobantes_fecha,
                )
            )

    items.sort(key=lambda x: x.vencimiento)
    return VencimientosOut(items=items)


async def get_egresos_por_categoria(db: AsyncSession, anio: int) -> EgresosPorCategoriaOut:
    rows = (
        await db.execute(
            select(
                CategoriaIRP.codigo,
                CategoriaIRP.nombre,
                func.coalesce(func.sum(Comprobante.total), 0),
                func.count(Comprobante.id),
            )
            .join(ImputacionFiscal, ImputacionFiscal.categoria_irp_id == CategoriaIRP.id)
            .join(Comprobante, Comprobante.id == ImputacionFiscal.comprobante_id)
            .where(
                Comprobante.periodo_fiscal.startswith(str(anio)),
                Comprobante.deleted_at.is_(None),
                ImputacionFiscal.imputa_irp.is_(True),
            )
            .group_by(CategoriaIRP.codigo, CategoriaIRP.nombre)
            .order_by(func.sum(Comprobante.total).desc())
        )
    ).all()

    egresos = [
        EgresoCategoria(
            codigo=codigo,
            nombre=nombre,
            total=int(total),
            cantidad_comprobantes=int(count),
        )
        for codigo, nombre, total, count in rows
    ]

    return EgresosPorCategoriaOut(
        anio_fiscal=anio,
        egresos=egresos,
        total_general=sum(e.total for e in egresos),
    )
