from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.schemas import (
    DashboardCreate, DashboardUpdate, DashboardResponse,
    LayoutUpdate, FiltersUpdate,
)
from app.services import dashboard_service

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


async def _dashboard_response(db, dashboard) -> DashboardResponse:
    resp = DashboardResponse.model_validate(dashboard)
    resp.global_filters = await dashboard_service.expand_dashboard_filters(db, dashboard)
    return resp


@router.get("", response_model=list[DashboardResponse])
async def list_dashboards(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboards = await dashboard_service.list_dashboards(db, current_user["user_id"])
    result = []
    for d in dashboards:
        result.append(await _dashboard_response(db, d))
    return result


@router.post("", response_model=DashboardResponse)
async def create_dashboard(
    body: DashboardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboard = await dashboard_service.create_dashboard(
        db, **body.model_dump(), created_by=current_user["user_id"],
    )
    return await _dashboard_response(db, dashboard)


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    dashboard = await dashboard_service.get_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return await _dashboard_response(db, dashboard)


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    body: DashboardUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    dashboard = await dashboard_service.get_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    dashboard = await dashboard_service.update_dashboard(
        db, dashboard, **body.model_dump(exclude_unset=True),
    )
    return await _dashboard_response(db, dashboard)


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    dashboard = await dashboard_service.get_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    await dashboard_service.delete_dashboard(db, dashboard)
    return {"message": "Dashboard deleted"}


@router.put("/{dashboard_id}/layout", response_model=DashboardResponse)
async def update_layout(
    dashboard_id: int,
    body: LayoutUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    dashboard = await dashboard_service.get_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    dashboard = await dashboard_service.update_layout(db, dashboard, body.layout_config)
    return await _dashboard_response(db, dashboard)


@router.put("/{dashboard_id}/filters", response_model=DashboardResponse)
async def update_filters(
    dashboard_id: int,
    body: FiltersUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    dashboard = await dashboard_service.get_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    dashboard = await dashboard_service.update_filters(
        db, dashboard, body.global_filters, body.filter_ids,
    )
    return await _dashboard_response(db, dashboard)
