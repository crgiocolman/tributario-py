from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class CambioItem(BaseModel):
    tabla: str
    registro_id: UUID
    operacion: Literal["create", "update", "delete"]
    payload: dict[str, Any]
    timestamp: datetime


class PushRequest(BaseModel):
    device_id: str
    cambios: list[CambioItem]


class ConflictoItem(BaseModel):
    registro_id: UUID
    tabla: str
    ganador: dict[str, Any]


class PushResponse(BaseModel):
    aceptados: list[UUID]
    rechazados: list[UUID]
    conflictos: list[ConflictoItem]
    server_timestamp: datetime


class PullResponse(BaseModel):
    cambios: dict[str, list[Any]]
    server_timestamp: datetime
    hay_mas: bool


class SyncStatusResponse(BaseModel):
    server_timestamp: datetime
