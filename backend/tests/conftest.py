import os
from uuid import UUID, uuid4

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

# Sobreescribir DATABASE_URL ANTES de cualquier import de la app
_TEST_DB = "tributario_py_test"
_TEST_DB_URL = f"postgresql+asyncpg://admin:admin123@localhost:5432/{_TEST_DB}"
os.environ["DATABASE_URL"] = _TEST_DB_URL

from app.database import AsyncSessionLocal, Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed.categorias import seed_categorias_irp  # noqa: E402
from app.seed.configuracion import seed_configuracion_fiscal  # noqa: E402
from app.seed.reglas import seed_reglas_imputacion  # noqa: E402

# UUIDs fijos del seed — usados en tests para referenciar categorías
ALIMENTACION_ID = UUID("11111111-0001-0000-0000-000000000000")
ALIMENTACION_COD = "ALIMENTACION"

# Orden de borrado respetando FK constraints (dependientes primero)
_USER_TABLES = [
    "declaraciones_juradas",
    "archivos_adjuntos",
    "imputaciones_fiscales",
    "ingresos",
    "comprobantes",
    "periodos_fiscales",
    "contactos",
]


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Crea la BD de test si no existe, crea el schema y carga el seed."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="admin", password="admin123", database="postgres"
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", _TEST_DB
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{_TEST_DB}"')
    finally:
        await conn.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        insertado = await seed_categorias_irp(db)
        if insertado:
            await seed_reglas_imputacion(db)
        await seed_configuracion_fiscal(db)
        await db.commit()

    yield


@pytest.fixture(autouse=True)
async def clean_user_tables():
    """Limpia tablas de datos de usuario antes de cada test."""
    async with engine.begin() as conn:
        for name in _USER_TABLES:
            await conn.execute(Base.metadata.tables[name].delete())
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session


# --- Helpers de fixtures reutilizables ---

def _contacto_body(**overrides) -> dict:
    return {
        "id": str(uuid4()),
        "ruc": "80012345-6",
        "razon_social": "Test Empresa SA",
        "tipo": "proveedor",
        **overrides,
    }


def _comprobante_body(contacto_id: str, **overrides) -> dict:
    return {
        "id": str(uuid4()),
        "contacto_id": contacto_id,
        "tipo_operacion": "compra",
        "tipo_comprobante": "factura",
        "forma_emision": "electronica",
        "numero_timbrado": "12345678",
        "numero_comprobante": "001-001-0000001",
        "fecha_emision": "2026-04-15",
        "condicion": "contado",
        "moneda": "PYG",
        "monto_exento": 0,
        "monto_gravado_5": 0,
        "iva_5": 0,
        "monto_gravado_10": 150000,
        "iva_10": 15000,
        "total": 165000,
        "periodo_fiscal": "2026-04",
        "cargado_marangatu": "auto",
        "imputacion": {
            "id": str(uuid4()),
            "categoria_irp_id": str(ALIMENTACION_ID),
            "imputa_iva_credito": False,
            "iva_credito_porcentaje": "0.00",
            "iva_credito_monto": 0,
            "imputa_irp": True,
            "destino_reg_comprobante": "irp_rsp",
        },
        **overrides,
    }


@pytest.fixture
async def contacto_id(client) -> str:
    resp = await client.post("/api/v1/contactos", json=_contacto_body())
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


@pytest.fixture
async def comprobante_id(client, contacto_id) -> str:
    resp = await client.post("/api/v1/comprobantes", json=_comprobante_body(contacto_id))
    assert resp.status_code == 201
    return resp.json()["data"]["id"]
