from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.schemas import (
    UserCreate, UserUpdate, UserResponse, PaginatedResponse,
    RoleBrief, AssignRolesRequest,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_response(user) -> UserResponse:
    roles = []
    for link in user.role_links:
        roles.append(RoleBrief(id=link.role.id, name=link.role.name))
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        avatar=user.avatar,
        is_active=user.is_active,
        theme_preference=user.theme_preference,
        roles=roles,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    users, total = await user_service.list_users(db, page, size, search, is_active)
    return PaginatedResponse(
        items=[_to_user_response(u) for u in users],
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=UserResponse)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    user = await user_service.create_user(
        db, username=body.username, password=body.password,
        email=body.email, is_active=body.is_active,
        theme_preference=body.theme_preference,
    )
    await db.refresh(user, ["role_links"])
    return _to_user_response(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_user_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = body.model_dump(exclude_unset=True)
    user = await user_service.update_user(db, user, **update_data)
    await db.refresh(user, ["role_links"])
    return _to_user_response(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user_service.delete_user(db, user)
    return {"message": "User deactivated"}


@router.get("/{user_id}/roles")
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role_ids = await user_service.get_user_roles(db, user_id)
    roles = []
    for link in user.role_links:
        roles.append({"id": link.role.id, "name": link.role.name})
    return roles


@router.put("/{user_id}/roles")
async def assign_roles(
    user_id: int,
    body: AssignRolesRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user_service.assign_roles(db, user_id, body.role_ids)
    return {"message": "Roles updated"}
