from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import CargadoMarangatu, TipoOperacion
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.comprobante import ComprobanteCreate, ComprobanteOut, ComprobanteUpdate
from app.services import comprobante_service

router = APIRouter(prefix="/comprobantes", tags=["comprobantes"])


@router.get("", response_model=ListResponse[ComprobanteOut])
async def listar_comprobantes(
    periodo_fiscal: str | None = None,
    tipo_operacion: TipoOperacion | None = None,
    contacto_id: UUID | None = None,
    cargado_marangatu: CargadoMarangatu | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items, total = await comprobante_service.listar_comprobantes(
        db,
        periodo_fiscal=periodo_fiscal,
        tipo_operacion=tipo_operacion,
        contacto_id=contacto_id,
        cargado_marangatu=cargado_marangatu,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        per_page=per_page,
    )
    return ListResponse(data=items, meta=PaginationMeta(total=total, page=page, per_page=per_page))


@router.get("/{id}", response_model=DataResponse[ComprobanteOut])
async def get_comprobante(id: UUID, db: AsyncSession = Depends(get_db)):
    comp = await comprobante_service.get_comprobante(db, id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    return DataResponse(data=comp)


@router.post("", response_model=DataResponse[ComprobanteOut], status_code=201)
async def crear_comprobante(body: ComprobanteCreate, db: AsyncSession = Depends(get_db)):
    comp = await comprobante_service.crear_comprobante(db, body)
    return DataResponse(data=comp)


@router.put("/{id}", response_model=DataResponse[ComprobanteOut])
async def actualizar_comprobante(id: UUID, body: ComprobanteUpdate, db: AsyncSession = Depends(get_db)):
    comp = await comprobante_service.get_comprobante(db, id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    comp = await comprobante_service.actualizar_comprobante(db, comp, body)
    return DataResponse(data=comp)


@router.delete("/{id}", status_code=204)
async def eliminar_comprobante(id: UUID, db: AsyncSession = Depends(get_db)):
    comp = await comprobante_service.get_comprobante(db, id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    await comprobante_service.eliminar_comprobante(db, comp)
