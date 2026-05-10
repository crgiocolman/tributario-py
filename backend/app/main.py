from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import adjuntos, categorias_irp, comprobantes, contactos, declaraciones, exportacion, imputaciones, ingresos, periodos, reportes

app = FastAPI(title="TributarioPY API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_PREFIX = "/api/v1"

app.include_router(contactos.router, prefix=_PREFIX)
app.include_router(categorias_irp.router, prefix=_PREFIX)
app.include_router(comprobantes.router, prefix=_PREFIX)
app.include_router(adjuntos.router, prefix=_PREFIX)
app.include_router(ingresos.router, prefix=_PREFIX)
app.include_router(imputaciones.router, prefix=_PREFIX)
app.include_router(periodos.router, prefix=_PREFIX)
app.include_router(declaraciones.router, prefix=_PREFIX)
app.include_router(reportes.router, prefix=_PREFIX)
app.include_router(exportacion.router, prefix=_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}
