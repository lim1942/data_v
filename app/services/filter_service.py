from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.filter import Filter


async def list_filters(db: AsyncSession, page: int = 1, size: int = 20, search: str | None = None):
    query = select(Filter)
    count_query = select(func.count(Filter.id))

    if search:
        query = query.where(Filter.label.contains(search) | Filter.key.contains(search))
        count_query = count_query.where(Filter.label.contains(search) | Filter.key.contains(search))

    total = (await db.execute(count_query)).scalar() or 0
    items = (await db.execute(query.offset((page - 1) * size).limit(size).order_by(Filter.id))).scalars().all()

    return items, total


async def get_filter(db: AsyncSession, filter_id: int) -> Filter | None:
    result = await db.execute(select(Filter).where(Filter.id == filter_id))
    return result.scalar_one_or_none()


async def get_filters_by_ids(db: AsyncSession, filter_ids: list[int]) -> list[Filter]:
    if not filter_ids:
        return []
    result = await db.execute(select(Filter).where(Filter.id.in_(filter_ids)))
    return list(result.scalars().all())


async def get_all_filters(db: AsyncSession) -> list[Filter]:
    result = await db.execute(select(Filter).order_by(Filter.id))
    return list(result.scalars().all())


async def create_filter(db: AsyncSession, **kwargs) -> Filter:
    filter_obj = Filter(**kwargs)
    db.add(filter_obj)
    await db.commit()
    await db.refresh(filter_obj)
    return filter_obj


async def update_filter(db: AsyncSession, filter_obj: Filter, **kwargs) -> Filter:
    for key, value in kwargs.items():
        if value is not None and hasattr(filter_obj, key):
            setattr(filter_obj, key, value)
    await db.commit()
    await db.refresh(filter_obj)
    return filter_obj


async def delete_filter(db: AsyncSession, filter_obj: Filter) -> None:
    await db.delete(filter_obj)
    await db.commit()
