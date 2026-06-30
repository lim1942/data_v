from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, text

from app.database import engine, Base, async_session
from app.api.v1.router import router as v1_router
from app.models.filter import Filter


async def seed_filters():
    """Insert default filters if none exist."""
    async with async_session() as db:
        result = await db.execute(select(func.count(Filter.id)))
        count = result.scalar() or 0
        if count > 0:
            return

        defaults = [
            Filter(key="date_range", label="日期范围", type="date_range", default_value=None, options=None),
            Filter(key="region", label="地区", type="select", default_value="all", options=[
                {"label": "全部", "value": "all"},
                {"label": "华东", "value": "east"},
                {"label": "华北", "value": "north"},
                {"label": "华南", "value": "south"},
            ]),
            Filter(key="keyword", label="关键字", type="input", default_value="", options=None),
        ]
        db.add_all(defaults)
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add component_type/component_code columns if upgrading from older schema
        for col, spec in [("component_type", "VARCHAR(20) NOT NULL DEFAULT 'dynamic'"),
                          ("component_code", "TEXT")]:
            try:
                await conn.execute(
                    text(f"ALTER TABLE charts ADD COLUMN {col} {spec}")
                )
            except Exception:
                pass
    await seed_filters()
    yield
    await engine.dispose()


app = FastAPI(title="Data Dashboard API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
