"""Tests de integración para períodos fiscales y recálculo automático."""

from tests.conftest import _comprobante_body


async def test_crear_comprobante_crea_periodo(client, contacto_id):
    body = _comprobante_body(contacto_id, periodo_fiscal="2026-05")
    resp = await client.post("/api/v1/comprobantes", json=body)
    assert resp.status_code == 201

    resp = await client.get("/api/v1/periodos/2026-05")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["periodo"] == "2026-05"
    assert data["comprobantes"]["compras"] == 1
    assert data["comprobantes"]["ventas"] == 0


async def test_recalculo_acumula_comprobantes(client, contacto_id):
    periodo = "2026-06"

    body1 = _comprobante_body(contacto_id, periodo_fiscal=periodo,
                              numero_comprobante="001-001-0000001",
                              monto_gravado_10=100000, iva_10=10000, total=110000)
    body2 = _comprobante_body(contacto_id, periodo_fiscal=periodo,
                              numero_comprobante="001-001-0000002",
                              monto_gravado_10=200000, iva_10=20000, total=220000)

    await client.post("/api/v1/comprobantes", json=body1)
    await client.post("/api/v1/comprobantes", json=body2)

    resp = await client.get(f"/api/v1/periodos/{periodo}")
    data = resp.json()["data"]
    assert data["comprobantes"]["compras"] == 2
    assert data["resumen_iva"]["compras_gravadas_10"] == 300000


async def test_recalcular_manual(client, contacto_id):
    periodo = "2026-07"
    body = _comprobante_body(contacto_id, periodo_fiscal=periodo)
    await client.post("/api/v1/comprobantes", json=body)

    resp = await client.post(f"/api/v1/periodos/{periodo}/recalcular")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["comprobantes"]["compras"] == 1


async def test_listar_periodos_por_anio(client, contacto_id):
    for mes in ["03", "04", "05"]:
        body = _comprobante_body(
            contacto_id,
            periodo_fiscal=f"2026-{mes}",
            numero_comprobante=f"001-001-000000{mes}",
        )
        await client.post("/api/v1/comprobantes", json=body)

    resp = await client.get("/api/v1/periodos", params={"anio_fiscal": 2026})
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 3


async def test_iva_mensual_sin_datos(client):
    resp = await client.get("/api/v1/reportes/iva-mensual/2025")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["meses"] == []
    assert data["total_iva_debito"] == 0
    assert data["saldo_acumulado"] == 0


async def test_iva_mensual_con_comprobante(client, contacto_id):
    body = _comprobante_body(contacto_id, periodo_fiscal="2026-04")
    await client.post("/api/v1/comprobantes", json=body)

    resp = await client.get("/api/v1/reportes/iva-mensual/2026")
    data = resp.json()["data"]
    assert len(data["meses"]) == 1
    assert data["meses"][0]["periodo"] == "2026-04"
    assert data["meses"][0]["compras_gravadas_10"] == 150000
