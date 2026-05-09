import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings


async def guardar_archivo(file: UploadFile, anio: int, mes: int) -> tuple[str, str, int]:
    ext = Path(file.filename or "").suffix.lower() or ".bin"
    filename = f"{uuid4()}{ext}"
    ruta_relativa = f"{anio}/{mes:02d}/{filename}"
    ruta_completa = Path(settings.storage_path) / ruta_relativa
    ruta_completa.parent.mkdir(parents=True, exist_ok=True)

    contenido = await file.read()
    sha256 = hashlib.sha256(contenido).hexdigest()
    tamano = len(contenido)

    ruta_completa.write_bytes(contenido)
    return str(ruta_relativa), sha256, tamano


def ruta_absoluta(ruta_almacenamiento: str) -> Path:
    return Path(settings.storage_path) / ruta_almacenamiento


def eliminar_archivo(ruta_almacenamiento: str) -> None:
    ruta = ruta_absoluta(ruta_almacenamiento)
    if ruta.exists():
        ruta.unlink()
