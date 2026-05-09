from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import DataResponse
from app.schemas.reportes import (
    DashboardOut,
    EgresosPorCategoriaOut,
    IRPProyeccionOut,
    IVAMensualOut,
    VencimientosOut,
)
from app.services import reporte_service

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/dashboard", response_model=DataResponse[DashboardOut])
async def dashboard(
    anio: int | None = Query(None, description="Año fiscal (por defecto: año actual)"),
    db: AsyncSession = Depends(get_db),
):
    result = await reporte_service.get_dashboard(db, anio)
    return DataResponse(data=result)


@router.get("/iva-mensual/{anio}", response_model=DataResponse[IVAMensualOut])
async def iva_mensual(anio: int, db: AsyncSession = Depends(get_db)):
    result = await reporte_service.get_iva_mensual(db, anio)
    return DataResponse(data=result)


@router.get("/irp-proyeccion/{anio}", response_model=DataResponse[IRPProyeccionOut])
async def irp_proyeccion(anio: int, db: AsyncSession = Depends(get_db)):
    result = await reporte_service.get_irp_proyeccion(db, anio)
    return DataResponse(data=result)


@router.get("/vencimientos", response_model=DataResponse[VencimientosOut])
async def vencimientos(db: AsyncSession = Depends(get_db)):
    result = await reporte_service.get_vencimientos(db)
    return DataResponse(data=result)


@router.get("/egresos-por-categoria/{anio}", response_model=DataResponse[EgresosPorCategoriaOut])
async def egresos_por_categoria(anio: int, db: AsyncSession = Depends(get_db)):
    result = await reporte_service.get_egresos_por_categoria(db, anio)
    return DataResponse(data=result)
