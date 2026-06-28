from datetime import datetime, timedelta, timezone

import bcrypt

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.user import User, UserRole
from app.models.role import Role


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": str(user_id), "username": username, "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise ValueError("Invalid token")


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    result = await db.execute(
        select(User).where(User.username == username, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def get_user_with_roles(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role_links).selectinload(UserRole.role))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return None

    roles = []
    all_permissions = {}
    for link in user.role_links:
        role = link.role
        roles.append({"id": role.id, "name": role.name})
        permissions = role.permissions or {}
        # Merge permissions: later roles overwrite earlier ones for same resource
        for resource, actions in permissions.items():
            if resource in all_permissions:
                if isinstance(actions, dict) and isinstance(all_permissions[resource], dict):
                    all_permissions[resource] = {**all_permissions[resource], **actions}
                else:
                    all_permissions[resource] = actions
            else:
                all_permissions[resource] = actions

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "is_active": user.is_active,
        "theme_preference": user.theme_preference,
        "roles": roles,
        "permissions": all_permissions,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }
