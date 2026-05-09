import io
import logging
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria_irp import CategoriaIRP
from app.models.comprobante import Comprobante
from app.models.configuracion_fiscal import ConfiguracionFiscal
from app.models.contacto import Contacto
from app.models.enums import TipoIngreso, TipoOperacion
from app.models.imputacion_fiscal import ImputacionFiscal
from app.models.ingreso import Ingreso
from app.schemas.reportes import (
    F120Compras,
    F120Liquidacion,
    F120ResumenOut,
    F120Ventas,
    F515EgresoCategoria,
    F515IngresoDetalle,
    F515Liquidacion,
    F515ResumenOut,
)
from app.services.irp_service import calcular_impuesto_irp

logger = logging.getLogger(__name__)

_TIPO_COMPROBANTE_COD = {
    "factura": "1",
    "nota_credito": "2",
    "nota_debito": "3",
    "autofactura": "4",
    "ticket": "6",
    "boleta_resimple": "7",
    "liquidacion_salario": "1",
}
_CONDICION_COD = {"contado": "1", "credito": "2"}
_DESTINO_IMP = {"iva": "211", "irp_rsp": "715", "no_imputar": "0"}
_TIPO_OP_COD = {"compra": "C", "venta": "V"}

_CSV_HEADER = (
    "tipo_registro;tipo_comprobante;fecha_emision;ruc_contraparte;nombre_contraparte;"
    "numero_timbrado;numero_comprobante;monto_gravado_10;iva_10;monto_gravado_5;iva_5;"
    "monto_exento;total;condicion;tipo_operacion;imputacion"
)


async def export_reg_comprobantes_csv(db: AsyncSession, periodo: str) -> str:
    rows = (
        await db.execute(
            select(Comprobante, Contacto, ImputacionFiscal)
            .join(Contacto, Contacto.id == Comprobante.contacto_id)
            .outerjoin(ImputacionFiscal, ImputacionFiscal.comprobante_id == Comprobante.id)
            .where(
                Comprobante.periodo_fiscal == periodo,
                Comprobante.deleted_at.is_(None),
            )
            .order_by(Comprobante.fecha_emision, Comprobante.tipo_operacion)
        )
    ).all()

    out = io.StringIO()
    out.write(_CSV_HEADER + "\r\n")

    for comp, contacto, imp in rows:
        tipo_reg = _TIPO_OP_COD.get(comp.tipo_operacion.value, "C")
        tipo_comp = _TIPO_COMPROBANTE_COD.get(comp.tipo_comprobante.value, "1")
        fecha = comp.fecha_emision.strftime("%d/%m/%Y")
        condicion = _CONDICION_COD.get(comp.condicion.value, "1")
        destino = imp.destino_reg_comprobante.value if imp else "no_imputar"
        imputacion = _DESTINO_IMP.get(destino, "0")

        linea = ";".join([
            tipo_reg,
            tipo_comp,
            fecha,
            contacto.ruc,
            contacto.razon_social,
            comp.numero_timbrado or "",
            comp.numero_comprobante or "",
            str(comp.monto_gravado_10),
            str(comp.iva_10),
            str(comp.monto_gravado_5),
            str(comp.iva_5),
            str(comp.monto_exento),
            str(comp.total),
            condicion,
            tipo_reg,
            imputacion,
        ])
        out.write(linea + "\r\n")

    return out.getvalue()


async def export_f120_resumen(db: AsyncSession, periodo: str) -> F120ResumenOut:
    anio = int(periodo[:4])
    conf = (
        await db.execute(
            select(ConfiguracionFiscal).where(ConfiguracionFiscal.anio_fiscal == anio)
        )
    ).scalar_one_or_none()
    ruc = conf.ruc if conf else "COMPLETAR"

    rows = (
        await db.execute(
            select(Comprobante, ImputacionFiscal)
            .outerjoin(ImputacionFiscal, ImputacionFiscal.comprobante_id == Comprobante.id)
            .where(
                Comprobante.periodo_fiscal == periodo,
                Comprobante.deleted_at.is_(None),
            )
        )
    ).all()

    vg10 = vg5 = vexe = vid10 = vid5 = 0
    cg10 = cg5 = cexe = cic10 = cic5 = 0

    for comp, imp in rows:
        if comp.tipo_operacion == TipoOperacion.VENTA:
            vg10 += comp.monto_gravado_10
            vg5 += comp.monto_gravado_5
            vexe += comp.monto_exento
            vid10 += comp.iva_10
            vid5 += comp.iva_5
        else:
            cg10 += comp.monto_gravado_10
            cg5 += comp.monto_gravado_5
            cexe += comp.monto_exento
            if imp and imp.imputa_iva_credito and imp.iva_credito_monto > 0:
                total_iva = comp.iva_10 + comp.iva_5
                if total_iva > 0:
                    c10 = int(imp.iva_credito_monto * comp.iva_10 / total_iva)
                    cic10 += c10
                    cic5 += imp.iva_credito_monto - c10
                elif comp.iva_10 > 0:
                    cic10 += imp.iva_credito_monto
                else:
                    cic5 += imp.iva_credito_monto

    total_debito = vid10 + vid5
    total_credito = cic10 + cic5
    saldo = total_debito - total_credito

    return F120ResumenOut(
        periodo=periodo,
        ruc=ruc,
        ventas=F120Ventas(
            gravadas_10=vg10,
            iva_debito_10=vid10,
            gravadas_5=vg5,
            iva_debito_5=vid5,
            exentas=vexe,
            total_iva_debito=total_debito,
        ),
        compras=F120Compras(
            gravadas_10=cg10,
            iva_credito_10_utilizado=cic10,
            gravadas_5=cg5,
            iva_credito_5_utilizado=cic5,
            exentas=cexe,
            total_iva_credito_utilizado=total_credito,
        ),
        liquidacion=F120Liquidacion(
            iva_debito=total_debito,
            iva_credito=total_credito,
            saldo=saldo,
            a_pagar=max(0, saldo),
            saldo_a_favor=max(0, -saldo),
        ),
    )


async def export_f515_resumen(db: AsyncSession, anio: int) -> F515ResumenOut:
    conf = (
        await db.execute(
            select(ConfiguracionFiscal).where(ConfiguracionFiscal.anio_fiscal == anio)
        )
    ).scalar_one_or_none()
    ruc = conf.ruc if conf else "COMPLETAR"

    ingresos_rows = (
        await db.execute(
            select(Ingreso).where(
                Ingreso.periodo_devengado.startswith(str(anio)),
                Ingreso.deleted_at.is_(None),
            )
        )
    ).scalars().all()

    _tipos_especiales = (TipoIngreso.SALARIO, TipoIngreso.AGUINALDO, TipoIngreso.HONORARIOS)
    salarios_brutos = sum(i.monto_bruto for i in ingresos_rows if i.tipo_ingreso == TipoIngreso.SALARIO)
    aguinaldo_exo = sum(i.monto_bruto for i in ingresos_rows if i.tipo_ingreso == TipoIngreso.AGUINALDO)
    honorarios = sum(i.monto_bruto for i in ingresos_rows if i.tipo_ingreso == TipoIngreso.HONORARIOS)
    otros = sum(i.monto_bruto for i in ingresos_rows if i.tipo_ingreso not in _tipos_especiales)
    aporte_ips = sum(i.aporte_ips_trabajador for i in ingresos_rows)
    total_computable = sum(i.monto_computable_irp for i in ingresos_rows if i.es_gravado_irp)

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
            .order_by(CategoriaIRP.codigo)
        )
    ).all()

    egresos_deducibles = {
        codigo: F515EgresoCategoria(total=int(total), cantidad_comprobantes=int(count))
        for codigo, total, count in cat_rows
    }
    total_egresos = sum(e.total for e in egresos_deducibles.values())
    renta_neta = max(0, total_computable - total_egresos)

    impuesto = calcular_impuesto_irp(renta_neta, conf)

    ejercicio_inicio = conf.fecha_inicio_ejercicio if conf else date(anio, 1, 1)
    ejercicio_fin = conf.fecha_fin_ejercicio if conf else date(anio, 12, 31)

    return F515ResumenOut(
        anio_fiscal=anio,
        ruc=ruc,
        ejercicio_inicio=ejercicio_inicio,
        ejercicio_fin=ejercicio_fin,
        ingresos=F515IngresoDetalle(
            salarios_brutos=salarios_brutos,
            aporte_ips=aporte_ips,
            aguinaldo_exonerado=aguinaldo_exo,
            honorarios_profesionales=honorarios,
            otros_ingresos=otros,
            total_computable_irp=total_computable,
        ),
        egresos_deducibles=egresos_deducibles,
        total_egresos_deducibles=total_egresos,
        renta_neta=renta_neta,
        liquidacion_irp=F515Liquidacion(
            tramo_8=impuesto.tramo_8_porciento,
            tramo_9=impuesto.tramo_9_porciento,
            tramo_10=impuesto.tramo_10_porciento,
            total_impuesto=impuesto.total,
            retenciones_sufridas=0,
            saldo_a_pagar=impuesto.total,
        ),
    )
