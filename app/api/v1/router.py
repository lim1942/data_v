from fastapi import APIRouter

from app.api.v1 import auth, users, roles, charts, dashboards, filters

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(roles.router)
router.include_router(charts.router)
router.include_router(dashboards.router)
router.include_router(filters.router)
