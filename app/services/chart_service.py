from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chart import Chart


async def list_charts(
    db: AsyncSession, page: int = 1, size: int = 20, search: str | None = None
) -> tuple[list[Chart], int]:
    query = select(Chart)
    count_query = select(func.count(Chart.id))
    if search:
        query = query.where(Chart.title.contains(search))
        count_query = count_query.where(Chart.title.contains(search))
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Chart.id).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_chart(db: AsyncSession, chart_id: int) -> Chart | None:
    result = await db.execute(select(Chart).where(Chart.id == chart_id))
    return result.scalar_one_or_none()


async def create_chart(db: AsyncSession, **kwargs) -> Chart:
    chart = Chart(**kwargs)
    db.add(chart)
    await db.commit()
    await db.refresh(chart)
    return chart


async def update_chart(db: AsyncSession, chart: Chart, **kwargs) -> Chart:
    for key, value in kwargs.items():
        if value is not None and hasattr(chart, key):
            setattr(chart, key, value)
    await db.commit()
    await db.refresh(chart)
    return chart


async def delete_chart(db: AsyncSession, chart: Chart) -> None:
    await db.delete(chart)
    await db.commit()
