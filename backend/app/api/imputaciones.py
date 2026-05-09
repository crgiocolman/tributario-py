from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import DataResponse
from app.schemas.imputacion import BatchRectificarBody, ImputacionOut, ImputacionUpdate
from app.services import imputacion_service

router = APIRouter(prefix="/imputaciones", tags=["imputaciones"])


@router.put("/batch-rectificar", response_model=DataResponse[dict])
async def batch_rectificar(body: BatchRectificarBody, db: AsyncSession = Depends(get_db)):
    count = await imputacion_service.batch_rectificar(db, body)
    return DataResponse(data={"rectificadas": count, "periodo_fiscal": body.periodo_fiscal})


@router.put("/{id}", response_model=DataResponse[ImputacionOut])
async def rectificar_imputacion(id: UUID, body: ImputacionUpdate, db: AsyncSession = Depends(get_db)):
    imp = await imputacion_service.get_imputacion(db, id)
    if not imp:
        raise HTTPException(status_code=404, detail="Imputación no encontrada")
    imp = await imputacion_service.rectificar_imputacion(db, imp, body)
    return DataResponse(data=imp)
