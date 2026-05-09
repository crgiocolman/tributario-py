from app.models.configuracion_fiscal import ConfiguracionFiscal
from app.schemas.reportes import ImpuestoProyectado, TramoIRP

_TRAMO_1_HASTA = 50_000_000
_TRAMO_2_HASTA = 150_000_000


def calcular_impuesto_irp(
    renta_neta: int,
    conf: ConfiguracionFiscal | None = None,
) -> ImpuestoProyectado:
    if conf is not None:
        t1_hasta = int(conf.tramo_irp_1_hasta)
        t2_hasta = int(conf.tramo_irp_2_hasta)
        t1_tasa = float(conf.tramo_irp_1_tasa) / 100
        t2_tasa = float(conf.tramo_irp_2_tasa) / 100
        t3_tasa = float(conf.tramo_irp_3_tasa) / 100
    else:
        t1_hasta = _TRAMO_1_HASTA
        t2_hasta = _TRAMO_2_HASTA
        t1_tasa = 0.08
        t2_tasa = 0.09
        t3_tasa = 0.10

    if renta_neta <= 0:
        z = TramoIRP(base=0, impuesto=0)
        return ImpuestoProyectado(
            tramo_8_porciento=z,
            tramo_9_porciento=z,
            tramo_10_porciento=z,
            total=0,
        )

    base1 = min(renta_neta, t1_hasta)
    imp1 = int(base1 * t1_tasa)

    base2 = max(0, min(renta_neta, t2_hasta) - t1_hasta)
    imp2 = int(base2 * t2_tasa)

    base3 = max(0, renta_neta - t2_hasta)
    imp3 = int(base3 * t3_tasa)

    return ImpuestoProyectado(
        tramo_8_porciento=TramoIRP(base=base1, impuesto=imp1),
        tramo_9_porciento=TramoIRP(base=base2, impuesto=imp2),
        tramo_10_porciento=TramoIRP(base=base3, impuesto=imp3),
        total=imp1 + imp2 + imp3,
    )
