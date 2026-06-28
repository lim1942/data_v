from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.schemas import FilterCreate, FilterUpdate, FilterResponse, PaginatedResponse
from app.services import filter_service

router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("", response_model=PaginatedResponse)
async def list_filters(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    items, total = await filter_service.list_filters(db, page, size, search)
    return PaginatedResponse(
        items=[FilterResponse.model_validate(f) for f in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/options/all", response_model=list[FilterResponse])
async def get_all_filters(
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    filters = await filter_service.get_all_filters(db)
    return [FilterResponse.model_validate(f) for f in filters]


@router.post("", response_model=FilterResponse)
async def create_filter(
    body: FilterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await filter_service.create_filter(
        db, **body.model_dump(), created_by=current_user["user_id"],
    )


@router.get("/{filter_id}", response_model=FilterResponse)
async def get_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    f = await filter_service.get_filter(db, filter_id)
    if not f:
        raise HTTPException(status_code=404, detail="Filter not found")
    return f


@router.put("/{filter_id}", response_model=FilterResponse)
async def update_filter(
    filter_id: int,
    body: FilterUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    f = await filter_service.get_filter(db, filter_id)
    if not f:
        raise HTTPException(status_code=404, detail="Filter not found")
    return await filter_service.update_filter(db, f, **body.model_dump(exclude_unset=True))


@router.delete("/{filter_id}")
async def delete_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    f = await filter_service.get_filter(db, filter_id)
    if not f:
        raise HTTPException(status_code=404, detail="Filter not found")
    await filter_service.delete_filter(db, f)
    return {"message": "Filter deleted"}
