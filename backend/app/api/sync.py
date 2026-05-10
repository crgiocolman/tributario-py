from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.sync import PullResponse, PushRequest, PushResponse, SyncStatusResponse
from app.services import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/push", response_model=PushResponse)
async def push(body: PushRequest, db: AsyncSession = Depends(get_db)):
    return await sync_service.process_push(db, body)


@router.get("/pull", response_model=PullResponse)
async def pull(since: datetime | None = None, db: AsyncSession = Depends(get_db)):
    return await sync_service.process_pull(db, since)


@router.get("/status", response_model=SyncStatusResponse)
async def status():
    return await sync_service.get_status()
