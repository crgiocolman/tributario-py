from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import TipoContacto
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.contacto import ContactoCreate, ContactoOut, ContactoUpdate
from app.services import contacto_service

router = APIRouter(prefix="/contactos", tags=["contactos"])


@router.get("", response_model=ListResponse[ContactoOut])
async def listar_contactos(
    tipo: TipoContacto | None = None,
    ruc: str | None = None,
    es_frecuente: bool | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items, total = await contacto_service.listar_contactos(
        db, tipo=tipo, ruc=ruc, es_frecuente=es_frecuente, q=q, page=page, per_page=per_page
    )
    return ListResponse(data=items, meta=PaginationMeta(total=total, page=page, per_page=per_page))


@router.get("/{id}", response_model=DataResponse[ContactoOut])
async def get_contacto(id: UUID, db: AsyncSession = Depends(get_db)):
    contacto = await contacto_service.get_contacto(db, id)
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return DataResponse(data=contacto)


@router.post("", response_model=DataResponse[ContactoOut], status_code=201)
async def crear_contacto(body: ContactoCreate, db: AsyncSession = Depends(get_db)):
    contacto = await contacto_service.crear_contacto(db, body)
    return DataResponse(data=contacto)


@router.put("/{id}", response_model=DataResponse[ContactoOut])
async def actualizar_contacto(id: UUID, body: ContactoUpdate, db: AsyncSession = Depends(get_db)):
    contacto = await contacto_service.get_contacto(db, id)
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    contacto = await contacto_service.actualizar_contacto(db, contacto, body)
    return DataResponse(data=contacto)


@router.delete("/{id}", status_code=204)
async def eliminar_contacto(id: UUID, db: AsyncSession = Depends(get_db)):
    contacto = await contacto_service.get_contacto(db, id)
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    await contacto_service.eliminar_contacto(db, contacto)
