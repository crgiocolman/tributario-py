"""Tests para los endpoints de exportación CSV y resúmenes F120/F515."""

from tests.conftest import ALIMENTACION_COD, _comprobante_body, _contacto_body

_PERIODO = "2026-04"
_CSV_COLS = [
    "tipo_registro", "tipo_comprobante", "fecha_emision", "ruc_contraparte",
    "nombre_contraparte", "numero_timbrado", "numero_comprobante",
    "monto_gravado_10", "iva_10", "monto_gravado_5", "iva_5",
    "monto_exento", "total", "condicion", "tipo_operacion", "imputacion",
]


async def test_csv_header_correcto(client):
    resp = await client.get(f"/api/v1/exportar/reg-comprobantes/{_PERIODO}")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    header = resp.text.splitlines()[0]
    assert header == ";".join(_CSV_COLS)


async def test_csv_periodo_vacio(client):
    resp = await client.get(f"/api/v1/exportar/reg-comprobantes/{_PERIODO}")
    assert resp.status_code == 200
    lines = [l for l in resp.text.splitlines() if l.strip()]
    assert len(lines) == 1  # solo el header


async def test_csv_linea_compra(client, contacto_id):
    body = _comprobante_body(contacto_id)
    await client.post("/api/v1/comprobantes", json=body)

    resp = await client.get(f"/api/v1/exportar/reg-comprobantes/{_PERIODO}")
    lines = resp.text.splitlines()
    assert len(lines) == 2  # header + 1 línea

    cols = lines[1].split(";")
    assert cols[0] == "C"                   # tipo_registro: compra
    assert cols[1] == "1"                   # tipo_comprobante: factura
    assert "/" in cols[2]                   # fecha en DD/MM/YYYY
    assert cols[7] == "150000"              # monto_gravado_10
    assert cols[8] == "15000"              # iva_10
    assert cols[12] == "165000"            # total
    assert cols[13] == "1"                 # condicion: contado
    assert cols[15] == "715"               # imputacion: IRP-RSP


async def test_f120_estructura(client):
    resp = await client.get(f"/api/v1/exportar/f120-resumen/{_PERIODO}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["formulario"] == "F120"
    assert data["periodo"] == _PERIODO
    assert "ventas" in data
    assert "compras" in data
    assert "liquidacion" in data
    assert "iva_debito_10" in data["ventas"]
    assert "iva_credito_10_utilizado" in data["compras"]
    assert "a_pagar" in data["liquidacion"]


async def test_f120_totales_compra(client, contacto_id):
    body = _comprobante_body(contacto_id)
    await client.post("/api/v1/comprobantes", json=body)

    resp = await client.get(f"/api/v1/exportar/f120-resumen/{_PERIODO}")
    data = resp.json()["data"]
    assert data["compras"]["gravadas_10"] == 150000
    assert data["compras"]["exentas"] == 0
    assert data["liquidacion"]["iva_debito"] == 0   # no hay ventas
    assert data["liquidacion"]["saldo"] <= 0         # sin ventas, saldo a favor o cero


async def test_f515_estructura(client):
    resp = await client.get("/api/v1/exportar/f515-resumen/2026")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["formulario"] == "F515"
    assert data["anio_fiscal"] == 2026
    assert "ingresos" in data
    assert "egresos_deducibles" in data
    assert "liquidacion_irp" in data
    assert "renta_neta" in data
    assert data["liquidacion_irp"]["tramo_8"]["base"] >= 0
    assert data["liquidacion_irp"]["saldo_a_pagar"] >= 0


async def test_f515_con_egresos(client, contacto_id):
    body = _comprobante_body(contacto_id)
    await client.post("/api/v1/comprobantes", json=body)

    resp = await client.get("/api/v1/exportar/f515-resumen/2026")
    data = resp.json()["data"]
    assert ALIMENTACION_COD in data["egresos_deducibles"]
    assert data["egresos_deducibles"][ALIMENTACION_COD]["total"] == 165000
    assert data["egresos_deducibles"][ALIMENTACION_COD]["cantidad_comprobantes"] == 1
    assert data["total_egresos_deducibles"] == 165000
