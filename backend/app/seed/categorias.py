import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria_irp import CategoriaIRP

logger = logging.getLogger(__name__)

_CATEGORIAS = [
    {
        "id": uuid.UUID("11111111-0001-0000-0000-000000000000"),
        "codigo": "ALIMENTACION",
        "nombre": "Alimentación",
        "descripcion": "Gastos en alimentos y bebidas para consumo personal y familiar.",
        "articulo_ley": "Art. 64 num. 1",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 1,
    },
    {
        "id": uuid.UUID("11111111-0002-0000-0000-000000000000"),
        "codigo": "VESTIMENTA",
        "nombre": "Vestimenta",
        "descripcion": "Ropa, calzado y accesorios personales.",
        "articulo_ley": "Art. 64 num. 2",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 2,
    },
    {
        "id": uuid.UUID("11111111-0003-0000-0000-000000000000"),
        "codigo": "ALQUILER_VIVIENDA",
        "nombre": "Alquiler vivienda",
        "descripcion": "Alquiler de la vivienda principal.",
        "articulo_ley": "Art. 64 num. 3",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 3,
    },
    {
        "id": uuid.UUID("11111111-0004-0000-0000-000000000000"),
        "codigo": "MANTENIMIENTO_VIVIENDA",
        "nombre": "Mantenimiento vivienda",
        "descripcion": "Reparaciones y mantenimiento del hogar.",
        "articulo_ley": "Art. 64 num. 4",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 4,
    },
    {
        "id": uuid.UUID("11111111-0005-0000-0000-000000000000"),
        "codigo": "MOBILIARIO_HOGAR",
        "nombre": "Mobiliario / electrodomésticos / enseres hogar",
        "descripcion": "Muebles, electrodomésticos y artículos para el hogar.",
        "articulo_ley": "Art. 64 num. 5",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 5,
    },
    {
        "id": uuid.UUID("11111111-0006-0000-0000-000000000000"),
        "codigo": "ESPARCIMIENTO",
        "nombre": "Esparcimiento",
        "descripcion": "Cine, gimnasio, barbería, mascotas y entretenimiento.",
        "articulo_ley": "Art. 64 num. 6",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 6,
    },
    {
        "id": uuid.UUID("11111111-0007-0000-0000-000000000000"),
        "codigo": "SALUD",
        "nombre": "Salud",
        "descripcion": "Consultas médicas, medicamentos, seguros médicos y gastos de salud.",
        "articulo_ley": "Art. 64 num. 7",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 7,
    },
    {
        "id": uuid.UUID("11111111-0008-0000-0000-000000000000"),
        "codigo": "EDUCACION",
        "nombre": "Educación",
        "descripcion": "Cursos, libros, capacitaciones y gastos educativos.",
        "articulo_ley": "Art. 64 num. 8",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 8,
    },
    {
        "id": uuid.UUID("11111111-0009-0000-0000-000000000000"),
        "codigo": "VEHICULO",
        "nombre": "Vehículo",
        "descripcion": "Combustible, mantenimiento y compra de vehículo (una vez cada 3 años).",
        "articulo_ley": "Art. 64 num. 9",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 9,
    },
    {
        "id": uuid.UUID("11111111-0010-0000-0000-000000000000"),
        "codigo": "SERVICIOS_BASICOS",
        "nombre": "Servicios básicos",
        "descripcion": "Electricidad, agua, internet y telefonía.",
        "articulo_ley": "Art. 64 num. 10",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 10,
    },
    {
        "id": uuid.UUID("11111111-0011-0000-0000-000000000000"),
        "codigo": "APORTE_IPS",
        "nombre": "Aporte IPS trabajador",
        "descripcion": "Aporte del trabajador al Instituto de Previsión Social (9% del salario bruto).",
        "articulo_ley": "Art. 64 num. 11",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 11,
    },
    {
        "id": uuid.UUID("11111111-0012-0000-0000-000000000000"),
        "codigo": "DONACIONES",
        "nombre": "Donaciones",
        "descripcion": "Donaciones a entidades sin fines de lucro reconocidas.",
        "articulo_ley": "Art. 64 num. 12",
        "limite_porcentaje": 1.00,
        "activo": True,
        "orden": 12,
    },
    {
        "id": uuid.UUID("11111111-0013-0000-0000-000000000000"),
        "codigo": "ACTIVIDAD_GRAVADA",
        "nombre": "Gastos actividad profesional",
        "descripcion": "Gastos directamente vinculados a la actividad gravada por IRP.",
        "articulo_ley": "Art. 64 num. 13",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 13,
    },
    {
        "id": uuid.UUID("11111111-0014-0000-0000-000000000000"),
        "codigo": "SERVICIOS_FINANCIEROS",
        "nombre": "Intereses de préstamos, seguros",
        "descripcion": "Intereses de préstamos personales y primas de seguros de vida.",
        "articulo_ley": "Art. 64 num. 14",
        "limite_porcentaje": None,
        "activo": True,
        "orden": 14,
    },
    {
        "id": uuid.UUID("11111111-0015-0000-0000-000000000000"),
        "codigo": "NO_DEDUCIBLE",
        "nombre": "No deducible",
        "descripcion": "Gasto no deducible del IRP-RSP. No se imputa a ningún impuesto.",
        "articulo_ley": None,
        "limite_porcentaje": None,
        "activo": True,
        "orden": 15,
    },
    {
        "id": uuid.UUID("11111111-0016-0000-0000-000000000000"),
        "codigo": "NO_IMPUTAR",
        "nombre": "No imputar",
        "descripcion": "Comprobante que no debe imputarse a ningún impuesto.",
        "articulo_ley": None,
        "limite_porcentaje": None,
        "activo": True,
        "orden": 16,
    },
]


async def seed_categorias_irp(db: AsyncSession) -> bool:
    """Inserta las 16 categorías IRP. Devuelve True si insertó, False si ya existían."""
    count = await db.scalar(select(func.count()).select_from(CategoriaIRP))
    if count > 0:
        logger.info("categorias_irp: ya existen %d filas, skip.", count)
        return False

    await db.execute(
        CategoriaIRP.__table__.insert(),
        _CATEGORIAS,
    )
    logger.info("categorias_irp: insertadas 16 filas.")
    return True
