from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole
from app.services.auth_service import hash_password


async def list_users(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[User], int]:
    query = select(User).options(selectinload(User.role_links).selectinload(UserRole.role))
    count_query = select(func.count(User.id))

    if search:
        filter_clause = User.username.contains(search) | User.email.contains(search)
        query = query.where(filter_clause)
        count_query = count_query.where(filter_clause)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    users = result.unique().scalars().all()
    return users, total


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role_links).selectinload(UserRole.role))
        .where(User.id == user_id)
    )
    return result.unique().scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, password: str, email: str | None = None,
                      is_active: bool = True, theme_preference: str = "light") -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        is_active=is_active,
        theme_preference=theme_preference,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        if value is not None and hasattr(user, key) and key != "password":
            setattr(user, key, value)
    if "password" in kwargs and kwargs["password"]:
        user.password_hash = hash_password(kwargs["password"])
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    user.is_active = False
    await db.commit()


async def get_user_roles(db: AsyncSession, user_id: int) -> list[int]:
    result = await db.execute(select(UserRole).where(UserRole.user_id == user_id))
    return [ur.role_id for ur in result.scalars().all()]


async def assign_roles(db: AsyncSession, user_id: int, role_ids: list[int]) -> None:
    await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
    for role_id in role_ids:
        db.add(UserRole(user_id=user_id, role_id=role_id))
    await db.commit()
