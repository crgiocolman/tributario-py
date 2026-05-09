import asyncio
import logging

from app.database import AsyncSessionLocal
from app.seed.categorias import seed_categorias_irp
from app.seed.configuracion import seed_configuracion_fiscal
from app.seed.reglas import seed_reglas_imputacion

logger = logging.getLogger(__name__)


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        insertado = await seed_categorias_irp(db)
        if insertado:
            await seed_reglas_imputacion(db)
        await seed_configuracion_fiscal(db)
        await db.commit()
    logger.info("Seed completado.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
