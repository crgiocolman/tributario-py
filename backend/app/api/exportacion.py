from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import DataResponse
from app.schemas.reportes import F120ResumenOut, F515ResumenOut
from app.services import exportacion_service

router = APIRouter(prefix="/exportar", tags=["exportacion"])


@router.get("/reg-comprobantes/{periodo}")
async def reg_comprobantes(periodo: str, db: AsyncSession = Depends(get_db)):
    csv_content = await exportacion_service.export_reg_comprobantes_csv(db, periodo)
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="reg_comprobantes_{periodo}.csv"'},
    )


@router.get("/f120-resumen/{periodo}", response_model=DataResponse[F120ResumenOut])
async def f120_resumen(periodo: str, db: AsyncSession = Depends(get_db)):
    result = await exportacion_service.export_f120_resumen(db, periodo)
    return DataResponse(data=result)


@router.get("/f515-resumen/{anio}", response_model=DataResponse[F515ResumenOut])
async def f515_resumen(anio: int, db: AsyncSession = Depends(get_db)):
    result = await exportacion_service.export_f515_resumen(db, anio)
    return DataResponse(data=result)
