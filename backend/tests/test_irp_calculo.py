"""Tests unitarios para irp_service.calcular_impuesto_irp — sin BD."""

from app.services.irp_service import calcular_impuesto_irp


def test_renta_neta_cero():
    r = calcular_impuesto_irp(0)
    assert r.total == 0
    assert r.tramo_8_porciento.base == 0
    assert r.tramo_9_porciento.base == 0
    assert r.tramo_10_porciento.base == 0


def test_renta_neta_negativa():
    r = calcular_impuesto_irp(-5_000_000)
    assert r.total == 0


def test_tramo_1_solo():
    # 30M → todo en tramo 1 (8%)
    r = calcular_impuesto_irp(30_000_000)
    assert r.tramo_8_porciento.base == 30_000_000
    assert r.tramo_8_porciento.impuesto == 2_400_000
    assert r.tramo_9_porciento.base == 0
    assert r.tramo_10_porciento.base == 0
    assert r.total == 2_400_000


def test_tramo_1_limite_exacto():
    # Exactamente 50M → todo en tramo 1
    r = calcular_impuesto_irp(50_000_000)
    assert r.tramo_8_porciento.base == 50_000_000
    assert r.tramo_8_porciento.impuesto == 4_000_000
    assert r.tramo_9_porciento.base == 0
    assert r.total == 4_000_000


def test_tramos_1_y_2():
    # 80M → 50M@8% + 30M@9%
    r = calcular_impuesto_irp(80_000_000)
    assert r.tramo_8_porciento.base == 50_000_000
    assert r.tramo_8_porciento.impuesto == 4_000_000
    assert r.tramo_9_porciento.base == 30_000_000
    assert r.tramo_9_porciento.impuesto == 2_700_000
    assert r.tramo_10_porciento.base == 0
    assert r.total == 6_700_000


def test_tramo_2_limite_exacto():
    # Exactamente 150M → 50M@8% + 100M@9%
    r = calcular_impuesto_irp(150_000_000)
    assert r.tramo_8_porciento.base == 50_000_000
    assert r.tramo_8_porciento.impuesto == 4_000_000
    assert r.tramo_9_porciento.base == 100_000_000
    assert r.tramo_9_porciento.impuesto == 9_000_000
    assert r.tramo_10_porciento.base == 0
    assert r.total == 13_000_000


def test_todos_los_tramos():
    # 200M → 50M@8% + 100M@9% + 50M@10%
    r = calcular_impuesto_irp(200_000_000)
    assert r.tramo_8_porciento.base == 50_000_000
    assert r.tramo_8_porciento.impuesto == 4_000_000
    assert r.tramo_9_porciento.base == 100_000_000
    assert r.tramo_9_porciento.impuesto == 9_000_000
    assert r.tramo_10_porciento.base == 50_000_000
    assert r.tramo_10_porciento.impuesto == 5_000_000
    assert r.total == 18_000_000


def test_total_es_suma_de_tramos():
    """Invariante: total siempre == suma de los tres tramos."""
    for renta in [1, 40_000_000, 50_000_000, 75_000_000, 150_000_000, 300_000_000]:
        r = calcular_impuesto_irp(renta)
        assert r.total == (
            r.tramo_8_porciento.impuesto
            + r.tramo_9_porciento.impuesto
            + r.tramo_10_porciento.impuesto
        )


def test_con_configuracion_fiscal_custom():
    """Respeta tasas y tramos de ConfiguracionFiscal cuando se provee."""

    class FakeConf:
        tramo_irp_1_hasta = 40_000_000
        tramo_irp_2_hasta = 100_000_000
        tramo_irp_1_tasa = 7   # 7%
        tramo_irp_2_tasa = 8   # 8%
        tramo_irp_3_tasa = 9   # 9%

    r = calcular_impuesto_irp(120_000_000, FakeConf())
    assert r.tramo_8_porciento.base == 40_000_000
    assert r.tramo_9_porciento.base == 60_000_000
    assert r.tramo_10_porciento.base == 20_000_000
    assert r.tramo_8_porciento.impuesto == int(40_000_000 * 0.07)
    assert r.tramo_9_porciento.impuesto == int(60_000_000 * 0.08)
    assert r.tramo_10_porciento.impuesto == int(20_000_000 * 0.09)
    assert r.total == (
        r.tramo_8_porciento.impuesto
        + r.tramo_9_porciento.impuesto
        + r.tramo_10_porciento.impuesto
    )
