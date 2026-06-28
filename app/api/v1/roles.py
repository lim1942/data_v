from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.schemas import (
    RoleCreate, RoleUpdate, RoleResponse,
    BatchRoleDashboardAssign, RoleDashboardAssign,
)
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    roles = await role_service.list_roles(db)
    return [RoleResponse.model_validate(r) for r in roles]


@router.post("", response_model=RoleResponse)
async def create_role(
    body: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    role = await role_service.create_role(db, name=body.name, description=body.description,
                                          permissions=body.permissions)
    return RoleResponse.model_validate(role)


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleResponse.model_validate(role)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    body: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    update_data = body.model_dump(exclude_unset=True)
    role = await role_service.update_role(db, role, **update_data)
    return RoleResponse.model_validate(role)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    await role_service.delete_role(db, role)
    return {"message": "Role deleted"}


@router.get("/{role_id}/dashboards")
async def get_role_dashboards(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return await role_service.get_role_dashboards(db, role_id)


@router.put("/{role_id}/dashboards")
async def assign_dashboards(
    role_id: int,
    body: BatchRoleDashboardAssign,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    items = [d.model_dump() for d in body.dashboards]
    await role_service.assign_dashboards(db, role_id, items)
    return {"message": "Dashboard permissions updated"}


@router.put("/{role_id}/dashboards/{dashboard_id}")
async def update_dashboard_permission(
    role_id: int,
    dashboard_id: int,
    body: RoleDashboardAssign,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    rd = await role_service.update_dashboard_permission(
        db, role_id, dashboard_id, body.can_view, body.can_edit,
    )
    if not rd:
        raise HTTPException(status_code=404, detail="Role-dashboard assignment not found")
    return {"message": "Permission updated"}
