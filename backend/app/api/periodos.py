from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.periodo import PeriodoFiscalListItem, PeriodoFiscalOut
from app.services import periodo_service

router = APIRouter(prefix="/periodos", tags=["periodos"])


@router.get("", response_model=ListResponse[PeriodoFiscalListItem])
async def listar_periodos(
    anio_fiscal: int | None = None,
    f120_presentado: bool | None = None,
    reg_comprobantes_presentado: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items, total = await periodo_service.listar_periodos(
        db,
        anio_fiscal=anio_fiscal,
        f120_presentado=f120_presentado,
        reg_comprobantes_presentado=reg_comprobantes_presentado,
        page=page,
        per_page=per_page,
    )
    return ListResponse(data=items, meta=PaginationMeta(total=total, page=page, per_page=per_page))


@router.post("/{periodo}/recalcular", response_model=DataResponse[PeriodoFiscalOut])
async def recalcular_periodo(periodo: str, db: AsyncSession = Depends(get_db)):
    await periodo_service.recalcular_periodo(db, periodo)
    await db.commit()
    result = await periodo_service.get_periodo_detalle(db, periodo)
    return DataResponse(data=result)


@router.get("/{periodo}", response_model=DataResponse[PeriodoFiscalOut])
async def get_periodo(periodo: str, db: AsyncSession = Depends(get_db)):
    result = await periodo_service.get_periodo_detalle(db, periodo)
    if not result:
        raise HTTPException(status_code=404, detail="Período fiscal no encontrado")
    return DataResponse(data=result)
