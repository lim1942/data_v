from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.dashboard import RoleDashboard


async def list_roles(db: AsyncSession) -> list[Role]:
    result = await db.execute(select(Role).order_by(Role.id))
    return result.scalars().all()


async def get_role(db: AsyncSession, role_id: int) -> Role | None:
    result = await db.execute(select(Role).where(Role.id == role_id))
    return result.scalar_one_or_none()


async def create_role(db: AsyncSession, name: str, description: str | None = None,
                      permissions: dict | None = None) -> Role:
    role = Role(name=name, description=description, permissions=permissions or {})
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def update_role(db: AsyncSession, role: Role, **kwargs) -> Role:
    for key, value in kwargs.items():
        if value is not None and hasattr(role, key):
            setattr(role, key, value)
    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(db: AsyncSession, role: Role) -> None:
    # Check if role has users
    result = await db.execute(select(func.count()).where(Role.id == role.id))
    await db.delete(role)
    await db.commit()


async def get_role_dashboards(db: AsyncSession, role_id: int) -> list[dict]:
    result = await db.execute(
        select(RoleDashboard).where(RoleDashboard.role_id == role_id)
    )
    return [
        {"dashboard_id": rd.dashboard_id, "can_view": rd.can_view, "can_edit": rd.can_edit}
        for rd in result.scalars().all()
    ]


async def assign_dashboards(db: AsyncSession, role_id: int, dashboards: list[dict]) -> None:
    await db.execute(delete(RoleDashboard).where(RoleDashboard.role_id == role_id))
    for item in dashboards:
        db.add(RoleDashboard(
            role_id=role_id,
            dashboard_id=item["dashboard_id"],
            can_view=item.get("can_view", True),
            can_edit=item.get("can_edit", False),
        ))
    await db.commit()


async def update_dashboard_permission(db: AsyncSession, role_id: int, dashboard_id: int,
                                      can_view: bool | None = None, can_edit: bool | None = None) -> RoleDashboard | None:
    result = await db.execute(
        select(RoleDashboard).where(
            RoleDashboard.role_id == role_id,
            RoleDashboard.dashboard_id == dashboard_id,
        )
    )
    rd = result.scalar_one_or_none()
    if rd:
        if can_view is not None:
            rd.can_view = can_view
        if can_edit is not None:
            rd.can_edit = can_edit
        await db.commit()
    return rd
