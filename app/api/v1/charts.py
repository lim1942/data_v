from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.schemas import (
    ChartCreate, ChartUpdate, ChartResponse, PaginatedResponse,
)
from app.services import chart_service

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("", response_model=PaginatedResponse)
async def list_charts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    charts, total = await chart_service.list_charts(db, page, size, search)
    return PaginatedResponse(
        items=[ChartResponse.model_validate(c) for c in charts],
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=ChartResponse)
async def create_chart(
    body: ChartCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    chart = await chart_service.create_chart(db, **body.model_dump(), created_by=current_user["user_id"])
    return ChartResponse.model_validate(chart)


@router.get("/{chart_id}", response_model=ChartResponse)
async def get_chart(
    chart_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    chart = await chart_service.get_chart(db, chart_id)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    return ChartResponse.model_validate(chart)


@router.put("/{chart_id}", response_model=ChartResponse)
async def update_chart(
    chart_id: int,
    body: ChartUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    chart = await chart_service.get_chart(db, chart_id)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    chart = await chart_service.update_chart(db, chart, **body.model_dump(exclude_unset=True))
    return ChartResponse.model_validate(chart)


@router.delete("/{chart_id}")
async def delete_chart(
    chart_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    chart = await chart_service.get_chart(db, chart_id)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    await chart_service.delete_chart(db, chart)
    return {"message": "Chart deleted"}
