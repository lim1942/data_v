from datetime import datetime

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User ──────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    email: str | None = None
    avatar: str | None = None
    is_active: bool = True
    theme_preference: str = "light"


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    avatar: str | None = None
    is_active: bool | None = None
    theme_preference: str | None = None
    password: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None
    avatar: str | None
    is_active: bool
    theme_preference: str
    roles: list["RoleBrief"] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Role ──────────────────────────────────────────────
class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = None
    permissions: dict = {}


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: dict | None = None


class RoleBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None
    permissions: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard ─────────────────────────────────────────
class DashboardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    layout_config: list = []
    global_filters: list = []
    filter_ids: list[int] | None = None
    is_published: bool = False


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    layout_config: list | None = None
    global_filters: list | None = None
    filter_ids: list[int] | None = None
    is_published: bool | None = None


class DashboardResponse(BaseModel):
    id: int
    name: str
    description: str | None
    layout_config: list
    global_filters: list
    filter_ids: list[int] | None = None
    is_published: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LayoutUpdate(BaseModel):
    layout_config: list


class FiltersUpdate(BaseModel):
    global_filters: list | None = None
    filter_ids: list[int] | None = None


# ── Filter ────────────────────────────────────────────
class FilterCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern=r"^(date_range|date|select|input)$")
    default_value: object | None = None
    options: list | None = None


class FilterUpdate(BaseModel):
    key: str | None = None
    label: str | None = None
    type: str | None = None
    default_value: object | None = None
    options: list | None = None


class FilterResponse(BaseModel):
    id: int
    key: str
    label: str
    type: str
    default_value: object | None
    options: list | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Chart ─────────────────────────────────────────────
class ChartCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    component_type: str = "dynamic"
    component_code: str | None = None


class ChartUpdate(BaseModel):
    title: str | None = None
    component_type: str | None = None
    component_code: str | None = None


class ChartResponse(BaseModel):
    id: int
    title: str
    component_type: str
    component_code: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Common ────────────────────────────────────────────
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int


class AssignRolesRequest(BaseModel):
    role_ids: list[int]


class RoleDashboardAssign(BaseModel):
    dashboard_id: int
    can_view: bool = True
    can_edit: bool = False


class BatchRoleDashboardAssign(BaseModel):
    dashboards: list[RoleDashboardAssign]


class AssignUsersRequest(BaseModel):
    user_ids: list[int]
