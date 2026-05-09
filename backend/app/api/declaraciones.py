from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import EstadoDJ, Formulario
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.declaracion import DeclaracionCreate, DeclaracionOut, DeclaracionUpdate
from app.services import declaracion_service

router = APIRouter(prefix="/declaraciones", tags=["declaraciones"])


@router.get("", response_model=ListResponse[DeclaracionOut])
async def listar_declaraciones(
    formulario: Formulario | None = None,
    anio_fiscal: int | None = None,
    estado: EstadoDJ | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items, total = await declaracion_service.listar_declaraciones(
        db,
        formulario=formulario,
        anio_fiscal=anio_fiscal,
        estado=estado,
        page=page,
        per_page=per_page,
    )
    return ListResponse(data=items, meta=PaginationMeta(total=total, page=page, per_page=per_page))


@router.post("", response_model=DataResponse[DeclaracionOut], status_code=201)
async def crear_declaracion(body: DeclaracionCreate, db: AsyncSession = Depends(get_db)):
    dj = await declaracion_service.crear_declaracion(db, body)
    return DataResponse(data=dj)


@router.put("/{id}", response_model=DataResponse[DeclaracionOut])
async def actualizar_declaracion(id: UUID, body: DeclaracionUpdate, db: AsyncSession = Depends(get_db)):
    dj = await declaracion_service.get_declaracion(db, id)
    if not dj:
        raise HTTPException(status_code=404, detail="Declaración no encontrada")
    dj = await declaracion_service.actualizar_declaracion(db, dj, body)
    return DataResponse(data=dj)
