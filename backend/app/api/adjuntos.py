from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.archivo_adjunto import ArchivoAdjunto
from app.models.comprobante import Comprobante
from app.models.enums import SyncStatus
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.comprobante import ArchivoAdjuntoOut
from app.services import storage_service

router = APIRouter(tags=["adjuntos"])


@router.post(
    "/comprobantes/{comprobante_id}/adjuntos",
    response_model=DataResponse[ArchivoAdjuntoOut],
    status_code=201,
)
async def subir_adjunto(
    comprobante_id: UUID,
    archivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    comp = (
        await db.execute(
            select(Comprobante).where(
                Comprobante.id == comprobante_id,
                Comprobante.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")

    anio = comp.fecha_emision.year
    mes = comp.fecha_emision.month
    ruta, sha256, tamano = await storage_service.guardar_archivo(archivo, anio, mes)

    now = datetime.now(timezone.utc)
    adjunto = ArchivoAdjunto(
        id=uuid4(),
        comprobante_id=comprobante_id,
        nombre_archivo=archivo.filename or "archivo",
        tipo_mime=archivo.content_type or "application/octet-stream",
        tamano_bytes=tamano,
        ruta_almacenamiento=ruta,
        hash_sha256=sha256,
        sync_status=SyncStatus.SYNCED,
        created_at=now,
    )
    db.add(adjunto)
    await db.commit()
    await db.refresh(adjunto)
    return DataResponse(data=adjunto)


@router.get(
    "/comprobantes/{comprobante_id}/adjuntos",
    response_model=ListResponse[ArchivoAdjuntoOut],
)
async def listar_adjuntos(comprobante_id: UUID, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(ArchivoAdjunto).where(ArchivoAdjunto.comprobante_id == comprobante_id)
        )
    ).scalars().all()
    items = list(rows)
    return ListResponse(
        data=items,
        meta=PaginationMeta(total=len(items), page=1, per_page=max(len(items), 1)),
    )


@router.get("/adjuntos/{id}/download")
async def descargar_adjunto(id: UUID, db: AsyncSession = Depends(get_db)):
    adj = (
        await db.execute(select(ArchivoAdjunto).where(ArchivoAdjunto.id == id))
    ).scalar_one_or_none()
    if not adj:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")
    ruta = storage_service.ruta_absoluta(adj.ruta_almacenamiento)
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")
    return FileResponse(str(ruta), filename=adj.nombre_archivo, media_type=adj.tipo_mime)


@router.delete("/adjuntos/{id}", status_code=204)
async def eliminar_adjunto(id: UUID, db: AsyncSession = Depends(get_db)):
    adj = (
        await db.execute(select(ArchivoAdjunto).where(ArchivoAdjunto.id == id))
    ).scalar_one_or_none()
    if not adj:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")
    storage_service.eliminar_archivo(adj.ruta_almacenamiento)
    await db.delete(adj)
    await db.commit()
