from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dashboard import Dashboard, RoleDashboard
from app.models.user import UserRole
from app.services import filter_service


async def expand_dashboard_filters(db: AsyncSession, dashboard: Dashboard) -> list:
    """Expand filter_ids into full FilterConfig objects for response."""
    if dashboard.filter_ids and isinstance(dashboard.filter_ids, list) and len(dashboard.filter_ids) > 0:
        filters = await filter_service.get_filters_by_ids(db, dashboard.filter_ids)
        return [
            {
                "key": f.key,
                "label": f.label,
                "type": f.type,
                "default_value": f.default_value,
                "options": f.options,
            }
            for f in filters
        ]
    elif dashboard.global_filters and isinstance(dashboard.global_filters, list) and len(dashboard.global_filters) > 0:
        return dashboard.global_filters
    return []


async def list_dashboards(db: AsyncSession, user_id: int) -> list[Dashboard]:
    """List dashboards the user can view based on their roles."""
    # Get user's role IDs
    ur_result = await db.execute(select(UserRole.role_id).where(UserRole.user_id == user_id))
    role_ids = [r for (r,) in ur_result.all()]

    if not role_ids:
        return []

    # Get dashboard IDs assigned to those roles
    rd_result = await db.execute(
        select(RoleDashboard.dashboard_id)
        .where(RoleDashboard.role_id.in_(role_ids), RoleDashboard.can_view == True)
        .distinct()
    )
    dashboard_ids = [d for (d,) in rd_result.all()]

    if not dashboard_ids:
        return []

    result = await db.execute(
        select(Dashboard).where(Dashboard.id.in_(dashboard_ids))
    )
    return result.scalars().all()


async def get_dashboard(db: AsyncSession, dashboard_id: int) -> Dashboard | None:
    result = await db.execute(
        select(Dashboard).where(Dashboard.id == dashboard_id)
    )
    return result.scalar_one_or_none()


async def create_dashboard(db: AsyncSession, **kwargs) -> Dashboard:
    dashboard = Dashboard(**kwargs)
    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)
    return dashboard


async def update_dashboard(db: AsyncSession, dashboard: Dashboard, **kwargs) -> Dashboard:
    for key, value in kwargs.items():
        if value is not None and hasattr(dashboard, key):
            setattr(dashboard, key, value)
    await db.commit()
    await db.refresh(dashboard)
    return dashboard


async def delete_dashboard(db: AsyncSession, dashboard: Dashboard) -> None:
    # Delete role-dashboard assignments first to avoid FK constraint
    rd_result = await db.execute(
        select(RoleDashboard).where(RoleDashboard.dashboard_id == dashboard.id)
    )
    for rd in rd_result.scalars().all():
        await db.delete(rd)
    await db.delete(dashboard)
    await db.commit()


async def update_layout(db: AsyncSession, dashboard: Dashboard, layout_config: list) -> Dashboard:
    dashboard.layout_config = layout_config
    await db.commit()
    await db.refresh(dashboard)
    return dashboard


async def update_filters(db: AsyncSession, dashboard: Dashboard, global_filters: list | None = None, filter_ids: list[int] | None = None) -> Dashboard:
    if filter_ids is not None:
        dashboard.filter_ids = filter_ids
        if global_filters is not None:
            dashboard.global_filters = global_filters
    elif global_filters is not None:
        dashboard.global_filters = global_filters
    await db.commit()
    await db.refresh(dashboard)
    return dashboard
