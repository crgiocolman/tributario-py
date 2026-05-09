from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import TipoIngreso
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.ingreso import AcumuladoAnualOut, IngresoCreate, IngresoOut, IngresoUpdate
from app.services import ingreso_service

router = APIRouter(prefix="/ingresos", tags=["ingresos"])


@router.get("/acumulado/{anio}", response_model=DataResponse[AcumuladoAnualOut])
async def get_acumulado(anio: int, db: AsyncSession = Depends(get_db)):
    result = await ingreso_service.get_acumulado_anual(db, anio)
    return DataResponse(data=result)


@router.get("", response_model=ListResponse[IngresoOut])
async def listar_ingresos(
    anio_fiscal: int | None = None,
    tipo_ingreso: TipoIngreso | None = None,
    contacto_id: UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items, total = await ingreso_service.listar_ingresos(
        db,
        anio_fiscal=anio_fiscal,
        tipo_ingreso=tipo_ingreso,
        contacto_id=contacto_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        per_page=per_page,
    )
    return ListResponse(data=items, meta=PaginationMeta(total=total, page=page, per_page=per_page))


@router.get("/{id}", response_model=DataResponse[IngresoOut])
async def get_ingreso(id: UUID, db: AsyncSession = Depends(get_db)):
    ingreso = await ingreso_service.get_ingreso(db, id)
    if not ingreso:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    return DataResponse(data=ingreso)


@router.post("", response_model=DataResponse[IngresoOut], status_code=201)
async def crear_ingreso(body: IngresoCreate, db: AsyncSession = Depends(get_db)):
    ingreso = await ingreso_service.crear_ingreso(db, body)
    return DataResponse(data=ingreso)


@router.put("/{id}", response_model=DataResponse[IngresoOut])
async def actualizar_ingreso(id: UUID, body: IngresoUpdate, db: AsyncSession = Depends(get_db)):
    ingreso = await ingreso_service.get_ingreso(db, id)
    if not ingreso:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    ingreso = await ingreso_service.actualizar_ingreso(db, ingreso, body)
    return DataResponse(data=ingreso)


@router.delete("/{id}", status_code=204)
async def eliminar_ingreso(id: UUID, db: AsyncSession = Depends(get_db)):
    ingreso = await ingreso_service.get_ingreso(db, id)
    if not ingreso:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    await ingreso_service.eliminar_ingreso(db, ingreso)
