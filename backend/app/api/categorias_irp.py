from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.categoria_irp import CategoriaIRP
from app.schemas.categoria_irp import CategoriaIRPOut
from app.schemas.common import DataResponse, ListResponse, PaginationMeta

router = APIRouter(prefix="/categorias-irp", tags=["categorias-irp"])


@router.get("", response_model=ListResponse[CategoriaIRPOut])
async def listar_categorias(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CategoriaIRP)
        .options(selectinload(CategoriaIRP.regla_imputacion))
        .where(CategoriaIRP.activo == True)  # noqa: E712
        .order_by(CategoriaIRP.orden)
    )
    items = result.scalars().all()
    return ListResponse(data=items, meta=PaginationMeta(total=len(items), page=1, per_page=len(items) or 1))


@router.get("/{categoria_id}", response_model=DataResponse[CategoriaIRPOut])
async def obtener_categoria(categoria_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CategoriaIRP)
        .options(selectinload(CategoriaIRP.regla_imputacion))
        .where(CategoriaIRP.id == categoria_id)
    )
    categoria = result.scalar_one_or_none()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return DataResponse(data=categoria)
