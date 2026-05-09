"""Tests de integración para el CRUD de comprobantes."""

from uuid import uuid4

import pytest

from tests.conftest import ALIMENTACION_ID, _comprobante_body, _contacto_body


async def test_crear_comprobante_estructura(client, contacto_id):
    body = _comprobante_body(contacto_id)
    resp = await client.post("/api/v1/comprobantes", json=body)

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["id"] == body["id"]
    assert data["contacto_id"] == contacto_id
    assert data["total"] == 165000
    assert data["imputacion_fiscal"] is not None
    assert data["imputacion_fiscal"]["categoria_irp_id"] == str(ALIMENTACION_ID)
    assert data["imputacion_fiscal"]["imputa_irp"] is True
    assert data["archivos_adjuntos"] == []


async def test_get_comprobante(client, comprobante_id):
    resp = await client.get(f"/api/v1/comprobantes/{comprobante_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == comprobante_id


async def test_get_comprobante_inexistente(client):
    resp = await client.get(f"/api/v1/comprobantes/{uuid4()}")
    assert resp.status_code == 404


async def test_listar_comprobantes_por_periodo(client, contacto_id):
    body1 = _comprobante_body(contacto_id, periodo_fiscal="2026-03",
                              numero_comprobante="001-001-0000001")
    body2 = _comprobante_body(contacto_id, id=str(uuid4()), periodo_fiscal="2026-04",
                              numero_comprobante="001-001-0000002")

    await client.post("/api/v1/comprobantes", json=body1)
    await client.post("/api/v1/comprobantes", json=body2)

    resp = await client.get("/api/v1/comprobantes", params={"periodo_fiscal": "2026-03"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["meta"]["total"] == 1
    assert payload["data"][0]["periodo_fiscal"] == "2026-03"


async def test_soft_delete_comprobante(client, comprobante_id):
    # Eliminar
    resp = await client.delete(f"/api/v1/comprobantes/{comprobante_id}")
    assert resp.status_code == 204

    # Ya no aparece en listado
    resp = await client.get("/api/v1/comprobantes")
    assert resp.json()["meta"]["total"] == 0

    # Tampoco en GET directo
    resp = await client.get(f"/api/v1/comprobantes/{comprobante_id}")
    assert resp.status_code == 404


async def test_timbrado_duplicado_falla(client, contacto_id):
    body1 = _comprobante_body(contacto_id, numero_comprobante="001-001-0000001")
    body2 = _comprobante_body(
        contacto_id,
        id=str(uuid4()),
        numero_comprobante="001-001-0000001",  # mismo timbrado + numero
    )
    r1 = await client.post("/api/v1/comprobantes", json=body1)
    assert r1.status_code == 201

    r2 = await client.post("/api/v1/comprobantes", json=body2)
    assert r2.status_code >= 400


async def test_crear_contacto_y_listar(client):
    body = _contacto_body(ruc="12345678-9", razon_social="Empresa Test SRL")
    resp = await client.post("/api/v1/contactos", json=body)
    assert resp.status_code == 201

    resp = await client.get("/api/v1/contactos")
    assert resp.json()["meta"]["total"] == 1
    assert resp.json()["data"][0]["ruc"] == "12345678-9"
