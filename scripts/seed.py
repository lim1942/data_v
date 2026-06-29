import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.chdir(os.path.dirname(os.path.dirname(__file__)))

from app.database import async_session, engine, Base
from app.models.user import User, UserRole
from app.models.role import Role
from app.models.dashboard import Dashboard, RoleDashboard
from app.models.chart import Chart
from app.models.filter import Filter
from sqlalchemy import select, text, func
import bcrypt

SAMPLE_TABLES = ["sample_sales", "sample_growth", "sample_traffic", "sample_regions", "sample_funnel"]


async def _count(conn, table: str) -> int:
    r = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
    return (r.scalar() or 0)


async def seed_sample_tables(conn):
    """Create sample data tables if not exist; skip inserts if already populated."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sample_sales (month TEXT PRIMARY KEY, sales REAL)
    """))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sample_growth (date TEXT PRIMARY KEY, users INTEGER)
    """))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sample_traffic (source TEXT PRIMARY KEY, count INTEGER)
    """))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sample_regions (region TEXT PRIMARY KEY, region_code TEXT, revenue REAL)
    """))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sample_funnel (stage TEXT PRIMARY KEY, count INTEGER)
    """))

    if await _count(conn, "sample_sales") == 0:
        for month, sales in [("2026-01", 120), ("2026-02", 185), ("2026-03", 160),
                              ("2026-04", 210), ("2026-05", 195), ("2026-06", 245)]:
            await conn.execute(
                text("INSERT INTO sample_sales (month, sales) VALUES (:m, :s)"),
                {"m": month, "s": sales})

    if await _count(conn, "sample_growth") == 0:
        for date, users in [("2026-01-01", 1200), ("2026-02-01", 1850), ("2026-03-01", 2300),
                            ("2026-04-01", 3100), ("2026-05-01", 4200), ("2026-06-01", 5600)]:
            await conn.execute(
                text("INSERT INTO sample_growth (date, users) VALUES (:d, :u)"),
                {"d": date, "u": users})

    if await _count(conn, "sample_traffic") == 0:
        for source, count in [("搜索引擎", 4520), ("直接访问", 3210), ("社交媒体", 2180),
                               ("邮件营销", 980), ("外部链接", 650)]:
            await conn.execute(
                text("INSERT INTO sample_traffic (source, count) VALUES (:s, :c)"),
                {"s": source, "c": count})

    if await _count(conn, "sample_regions") == 0:
        for region, code, revenue in [
            ("华北", "north", 380), ("华南", "south", 420), ("华东", "east", 510),
            ("西部", "west", 230), ("东北", "north", 180), ("华中", "east", 290),
        ]:
            await conn.execute(
                text("INSERT INTO sample_regions (region, region_code, revenue) VALUES (:r, :c, :v)"),
                {"r": region, "c": code, "v": revenue})

    if await _count(conn, "sample_funnel") == 0:
        for stage, count in [("访问", 10000), ("注册", 6500), ("浏览商品", 4200),
                              ("加入购物车", 2100), ("下单", 1200), ("支付", 850)]:
            await conn.execute(
                text("INSERT INTO sample_funnel (stage, count) VALUES (:s, :c)"),
                {"s": stage, "c": count})


async def _get_or_create(db, model, lookup: dict, defaults: dict):
    """Return existing record or create a new one."""
    result = await db.execute(
        select(model).where(*(getattr(model, k) == v for k, v in lookup.items()))
    )
    obj = result.scalar_one_or_none()
    if obj is not None:
        return obj, False
    obj = model(**lookup, **defaults)
    db.add(obj)
    await db.flush()
    return obj, True


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add component_type/component_code columns to existing charts tables
        for col, spec in [("component_type", "VARCHAR(20) NOT NULL DEFAULT 'legacy'"),
                          ("component_code", "TEXT")]:
            try:
                await conn.execute(
                    text(f"ALTER TABLE charts ADD COLUMN {col} {spec}")
                )
            except Exception:
                pass  # column already exists
        await seed_sample_tables(conn)

    created_any = False

    async with async_session() as db:
        # ── Filters ────────────────────────────────────────────
        filter_defs = [
            ("date_range", "日期范围", "date_range", None, None),
            ("region", "地区", "select", "all",
             [{"label": "全部", "value": "all"}, {"label": "华东", "value": "east"},
              {"label": "华北", "value": "north"}, {"label": "华南", "value": "south"},
              {"label": "西部", "value": "west"}]),
            ("keyword", "关键字", "input", "", None),
        ]
        filters = {}
        for key, label, ftype, default, opts in filter_defs:
            f, created = await _get_or_create(db, Filter, {"key": key}, {
                "label": label, "type": ftype, "default_value": default, "options": opts,
            })
            filters[key] = f
            if created:
                print(f"  + 筛选器: {label} ({key})")

        # ── Roles ──────────────────────────────────────────────
        admin_role, c = await _get_or_create(db, Role, {"name": "管理员"}, {
            "description": "系统完全访问权限",
            "permissions": {"system": {"users": "rw", "roles": "rw", "dashboards": "rw", "charts": "rw"}},
        })
        if c: print(f"  + 角色: 管理员")
        created_any |= c

        viewer_role, c = await _get_or_create(db, Role, {"name": "访客"}, {
            "description": "只读权限",
            "permissions": {"system": {"users": "r", "roles": "r", "dashboards": "r", "charts": "r"}},
        })
        if c: print(f"  + 角色: 访客")
        created_any |= c

        # ── Users ──────────────────────────────────────────────
        admin_user, c = await _get_or_create(db, User, {"username": "admin"}, {
            "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
            "email": "admin@example.com", "is_active": True, "theme_preference": "dark",
        })
        if c:
            print(f"  + 用户: admin")
            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
        created_any |= c

        viewer_user, c = await _get_or_create(db, User, {"username": "viewer"}, {
            "password_hash": bcrypt.hashpw("viewer123".encode(), bcrypt.gensalt()).decode(),
            "email": "viewer@example.com", "is_active": True,
        })
        if c:
            print(f"  + 用户: viewer")
            db.add(UserRole(user_id=viewer_user.id, role_id=viewer_role.id))
        created_any |= c

        await db.flush()

        # ── Charts ─────────────────────────────────────────────
        chart_defs = [
            {
                "title": "月度销售额",
                "component_code": (
                    'const { ref, onMounted, onUnmounted, inject, watch, h } = vue\n'
                    '\n'
                    'const ALL = [\n'
                    '  { month: "2026-01", sales: 120 }, { month: "2026-02", sales: 185 },\n'
                    '  { month: "2026-03", sales: 160 }, { month: "2026-04", sales: 210 },\n'
                    '  { month: "2026-05", sales: 195 }, { month: "2026-06", sales: 245 },\n'
                    ']\n'
                    '\n'
                    'return {\n'
                    '  setup() {\n'
                    '    const filters = inject("filters", {})\n'
                    '    const chartRef = ref(null)\n'
                    '    let chartInstance = null\n'
                    '\n'
                    '    function filterData() {\n'
                    '      const dr = filters.date_range\n'
                    '      if (dr && Array.isArray(dr) && dr.length === 2) {\n'
                    '        return ALL.filter(d => d.month >= dr[0] && d.month <= dr[1])\n'
                    '      }\n'
                    '      return ALL\n'
                    '    }\n'
                    '\n'
                    '    function render() {\n'
                    '      if (!chartRef.value) return\n'
                    '      if (!chartInstance) chartInstance = echarts.init(chartRef.value, getEChartsTheme())\n'
                    '      const d = filterData()\n'
                    '      chartInstance.setOption({\n'
                    '        backgroundColor: "transparent",\n'
                    '        tooltip: { trigger: "axis" },\n'
                    '        legend: { bottom: 0, textStyle: { fontSize: 12 } },\n'
                    '        grid: { top: 30, bottom: 50, left: 65, right: 20 },\n'
                    '        xAxis: { type: "category", data: d.map(r => r.month) },\n'
                    '        yAxis: { name: "金额 (万元)" },\n'
                    '        series: [{ type: "bar", data: d.map(r => r.sales), barMaxWidth: 40,\n'
                    '          itemStyle: { borderRadius: [4, 4, 0, 0], color: "#6c8cff" } }],\n'
                    '      })\n'
                    '    }\n'
                    '\n'
                    '    onMounted(() => render())\n'
                    '    onUnmounted(() => chartInstance?.dispose())\n'
                    '    watch(() => filters.date_range, () => render())\n'
                    '\n'
                    '    return () => h("div", { ref: chartRef, style: "width:100%;height:100%" })\n'
                    '  },\n'
                    '}'
                ),
            },
            {
                "title": "用户增长趋势",
                "component_code": (
                    'const { ref, onMounted, onUnmounted, inject, watch, h } = vue\n'
                    '\n'
                    'const ALL = [\n'
                    '  { date: "2026-01-01", users: 1200 }, { date: "2026-02-01", users: 1850 },\n'
                    '  { date: "2026-03-01", users: 2300 }, { date: "2026-04-01", users: 3100 },\n'
                    '  { date: "2026-05-01", users: 4200 }, { date: "2026-06-01", users: 5600 },\n'
                    ']\n'
                    '\n'
                    'return {\n'
                    '  setup() {\n'
                    '    const filters = inject("filters", {})\n'
                    '    const chartRef = ref(null)\n'
                    '    let chartInstance = null\n'
                    '\n'
                    '    function filterData() {\n'
                    '      const dr = filters.date_range\n'
                    '      if (dr && Array.isArray(dr) && dr.length === 2) {\n'
                    '        return ALL.filter(d => d.date >= dr[0] && d.date <= dr[1])\n'
                    '      }\n'
                    '      return ALL\n'
                    '    }\n'
                    '\n'
                    '    function render() {\n'
                    '      if (!chartRef.value) return\n'
                    '      if (!chartInstance) chartInstance = echarts.init(chartRef.value, getEChartsTheme())\n'
                    '      const d = filterData()\n'
                    '      chartInstance.setOption({\n'
                    '        backgroundColor: "transparent",\n'
                    '        tooltip: { trigger: "axis" },\n'
                    '        legend: { bottom: 0 },\n'
                    '        grid: { top: 30, bottom: 50, left: 60, right: 20 },\n'
                    '        xAxis: { type: "category", data: d.map(r => r.date) },\n'
                    '        yAxis: { name: "用户数" },\n'
                    '        series: [{ type: "line", data: d.map(r => r.users), smooth: true,\n'
                    '          lineStyle: { width: 2, color: "#00d4aa" },\n'
                    '          areaStyle: { color: "rgba(0,212,170,0.08)" } }],\n'
                    '      })\n'
                    '    }\n'
                    '\n'
                    '    onMounted(() => render())\n'
                    '    onUnmounted(() => chartInstance?.dispose())\n'
                    '    watch(() => filters.date_range, () => render())\n'
                    '\n'
                    '    return () => h("div", { ref: chartRef, style: "width:100%;height:100%" })\n'
                    '  },\n'
                    '}'
                ),
            },
            {
                "title": "流量来源分布",
                "component_code": (
                    'const { ref, onMounted, onUnmounted, inject, watch, h } = vue\n'
                    '\n'
                    'const ALL = [\n'
                    '  { name: "搜索引擎", value: 4520 }, { name: "直接访问", value: 3210 },\n'
                    '  { name: "社交媒体", value: 2180 }, { name: "邮件营销", value: 980 },\n'
                    '  { name: "外部链接", value: 650 },\n'
                    ']\n'
                    '\n'
                    'return {\n'
                    '  setup() {\n'
                    '    const filters = inject("filters", {})\n'
                    '    const chartRef = ref(null)\n'
                    '    let chartInstance = null\n'
                    '\n'
                    '    function filterData() {\n'
                    '      const kw = filters.keyword\n'
                    '      if (kw && String(kw).trim()) {\n'
                    '        return ALL.filter(d => d.name.includes(String(kw).trim()))\n'
                    '      }\n'
                    '      return ALL\n'
                    '    }\n'
                    '\n'
                    '    function render() {\n'
                    '      if (!chartRef.value) return\n'
                    '      if (!chartInstance) chartInstance = echarts.init(chartRef.value, getEChartsTheme())\n'
                    '      const d = filterData()\n'
                    '      chartInstance.setOption({\n'
                    '        backgroundColor: "transparent",\n'
                    '        tooltip: { trigger: "item" },\n'
                    '        legend: { orient: "vertical", left: "left", bottom: 0 },\n'
                    '        series: [{ type: "pie", radius: ["45%", "72%"], center: ["50%", "45%"],\n'
                    '          label: { show: false }, data: d,\n'
                    '          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0,\n'
                    '            shadowColor: "rgba(0,0,0,0.3)" } } }],\n'
                    '        color: utils.colors,\n'
                    '      })\n'
                    '    }\n'
                    '\n'
                    '    onMounted(() => render())\n'
                    '    onUnmounted(() => chartInstance?.dispose())\n'
                    '    watch(() => filters.keyword, () => render())\n'
                    '\n'
                    '    return () => h("div", { ref: chartRef, style: "width:100%;height:100%" })\n'
                    '  },\n'
                    '}'
                ),
            },
            {
                "title": "各区域收入",
                "component_code": (
                    'const { ref, onMounted, onUnmounted, inject, watch, h } = vue\n'
                    '\n'
                    'const ALL = [\n'
                    '  { region: "华北", code: "north", revenue: 380 },\n'
                    '  { region: "华南", code: "south", revenue: 420 },\n'
                    '  { region: "华东", code: "east", revenue: 510 },\n'
                    '  { region: "西部", code: "west", revenue: 230 },\n'
                    '  { region: "东北", code: "north", revenue: 180 },\n'
                    '  { region: "华中", code: "east", revenue: 290 },\n'
                    ']\n'
                    '\n'
                    'return {\n'
                    '  setup() {\n'
                    '    const filters = inject("filters", {})\n'
                    '    const chartRef = ref(null)\n'
                    '    let chartInstance = null\n'
                    '\n'
                    '    function filterData() {\n'
                    '      const region = filters.region\n'
                    '      if (region && region !== "all") {\n'
                    '        return ALL.filter(r => r.code === region)\n'
                    '      }\n'
                    '      return ALL\n'
                    '    }\n'
                    '\n'
                    '    function render() {\n'
                    '      if (!chartRef.value) return\n'
                    '      if (!chartInstance) chartInstance = echarts.init(chartRef.value, getEChartsTheme())\n'
                    '      const d = filterData()\n'
                    '      chartInstance.setOption({\n'
                    '        backgroundColor: "transparent",\n'
                    '        tooltip: { trigger: "axis" },\n'
                    '        legend: { bottom: 0 },\n'
                    '        grid: { top: 20, bottom: 50, left: 65, right: 20 },\n'
                    '        xAxis: { type: "category", data: d.map(r => r.region) },\n'
                    '        yAxis: { name: "金额 (万元)" },\n'
                    '        series: [{ type: "bar", data: d.map(r => r.revenue),\n'
                    '          barMaxWidth: 40, itemStyle: { borderRadius: [4, 4, 0, 0] } }],\n'
                    '      })\n'
                    '    }\n'
                    '\n'
                    '    onMounted(() => render())\n'
                    '    onUnmounted(() => chartInstance?.dispose())\n'
                    '    watch(() => filters.region, () => render())\n'
                    '\n'
                    '    return () => h("div", { ref: chartRef, style: "width:100%;height:100%" })\n'
                    '  },\n'
                    '}'
                ),
            },
            {
                "title": "系统性能监控",
                "component_code": (
                    'const { ref, onMounted, onUnmounted, h } = vue\n'
                    '\n'
                    'return {\n'
                    '  setup() {\n'
                    '    const chartRef = ref(null)\n'
                    '    let chartInstance = null\n'
                    '\n'
                    '    onMounted(() => {\n'
                    '      if (!chartRef.value) return\n'
                    '      chartInstance = echarts.init(chartRef.value, getEChartsTheme())\n'
                    '      chartInstance.setOption({\n'
                    '        backgroundColor: "transparent",\n'
                    '        series: [{ type: "gauge", startAngle: 210, endAngle: -30,\n'
                    '          center: ["50%", "55%"], radius: "85%", min: 0, max: 100,\n'
                    '          detail: { fontSize: 24, offsetCenter: [0, "60%"], valueAnimation: true },\n'
                    '          data: [{ value: 78, name: "CPU" }] }],\n'
                    '      })\n'
                    '    })\n'
                    '\n'
                    '    onUnmounted(() => chartInstance?.dispose())\n'
                    '\n'
                    '    return () => h("div", { ref: chartRef, style: "width:100%;height:100%" })\n'
                    '  },\n'
                    '}'
                ),
            },
            {
                "title": "转化漏斗",
                "component_code": (
                    'const { ref, onMounted, onUnmounted, h } = vue\n'
                    '\n'
                    'return {\n'
                    '  setup() {\n'
                    '    const chartRef = ref(null)\n'
                    '    let chartInstance = null\n'
                    '\n'
                    '    onMounted(() => {\n'
                    '      if (!chartRef.value) return\n'
                    '      chartInstance = echarts.init(chartRef.value, getEChartsTheme())\n'
                    '      chartInstance.setOption({\n'
                    '        backgroundColor: "transparent",\n'
                    '        tooltip: { trigger: "item" },\n'
                    '        series: [{ type: "funnel", left: "10%", right: "10%", top: 20, bottom: 20,\n'
                    '          gap: 2, label: { show: true, position: "inside" },\n'
                    '          data: [\n'
                    '            { name: "访问", value: 10000 }, { name: "注册", value: 6500 },\n'
                    '            { name: "浏览商品", value: 4200 }, { name: "加入购物车", value: 2100 },\n'
                    '            { name: "下单", value: 1200 }, { name: "支付", value: 850 },\n'
                    '          ] }],\n'
                    '      })\n'
                    '    })\n'
                    '\n'
                    '    onUnmounted(() => chartInstance?.dispose())\n'
                    '\n'
                    '    return () => h("div", { ref: chartRef, style: "width:100%;height:100%" })\n'
                    '  },\n'
                    '}'
                ),
            },
            {
                "title": "动态示例 - 流量占比环形图",
                "component_code": (
                    'const { ref, onMounted, onUnmounted, h } = vue\n'
                    '\n'
                    'return {\n'
                    '  setup() {\n'
                    '    const chartRef = ref(null)\n'
                    '    let chartInstance = null\n'
                    '\n'
                    '    onMounted(() => {\n'
                    '      if (!chartRef.value) return\n'
                    '      chartInstance = echarts.init(chartRef.value, getEChartsTheme())\n'
                    '      chartInstance.setOption({\n'
                    '        backgroundColor: "transparent",\n'
                    '        tooltip: { trigger: "item" },\n'
                    '        legend: { orient: "vertical", left: "left", bottom: 0 },\n'
                    '        series: [{ type: "pie", radius: ["45%", "72%"], center: ["50%", "45%"],\n'
                    '          label: { show: false },\n'
                    '          data: [\n'
                    '            { name: "搜索引擎", value: 4520 }, { name: "直接访问", value: 3210 },\n'
                    '            { name: "社交媒体", value: 2180 }, { name: "邮件营销", value: 980 },\n'
                    '            { name: "外部链接", value: 650 },\n'
                    '          ] }],\n'
                    '        color: utils.colors,\n'
                    '      })\n'
                    '    })\n'
                    '\n'
                    '    onUnmounted(() => chartInstance?.dispose())\n'
                    '\n'
                    '    return () => h("div", { ref: chartRef, style: "width:100%;height:100%" })\n'
                    '  },\n'
                    '}'
                ),
            },
        ]
        charts = {}
        for cd in chart_defs:
            c, created = await _get_or_create(db, Chart, {"title": cd["title"]}, {
                "data_source": None,
                "options_config": {},
                "component_type": "dynamic",
                "component_code": cd.get("component_code"),
                "created_by": admin_user.id,
            })
            charts[c.title] = c
            if created:
                print(f"  + 图表: {c.title}")
                created_any = True

        await db.flush()

        # ── Dashboard ──────────────────────────────────────────
        dash, c = await _get_or_create(db, Dashboard, {"name": "销售概览"}, {
            "description": "主要销售业绩数据大屏 — 图表通过依赖注入接收过滤值",
            "layout_config": [
                {"chart_id": charts["月度销售额"].id, "x": 0, "y": 0, "w": 6, "h": 1},
                {"chart_id": charts["用户增长趋势"].id, "x": 6, "y": 0, "w": 6, "h": 1},
                {"chart_id": charts["流量来源分布"].id, "x": 0, "y": 1, "w": 4, "h": 1},
                {"chart_id": charts["各区域收入"].id, "x": 4, "y": 1, "w": 8, "h": 1},
                {"chart_id": charts["系统性能监控"].id, "x": 0, "y": 2, "w": 4, "h": 1},
                {"chart_id": charts["转化漏斗"].id, "x": 4, "y": 2, "w": 4, "h": 1},
            ],
            "global_filters": [
                {"key": "date_range", "label": "日期范围", "type": "date_range",
                 "default_value": ["2026-01-01", "2026-06-30"]},
                {"key": "region", "label": "区域", "type": "select",
                 "default_value": "all", "options": [
                     {"label": "全部区域", "value": "all"}, {"label": "华东", "value": "east"},
                     {"label": "华北", "value": "north"}, {"label": "华南", "value": "south"},
                     {"label": "西部", "value": "west"},
                 ]},
                {"key": "keyword", "label": "关键字", "type": "input", "default_value": ""},
            ],
            "filter_ids": [filters["date_range"].id, filters["region"].id, filters["keyword"].id],
            "is_published": True,
            "created_by": admin_user.id,
        })
        if c:
            print(f"  + 仪表板: {dash.name}")
            created_any = True

        # ── Role-Dashboard assignments ─────────────────────────
        existing_rd = await db.execute(
            select(RoleDashboard).where(
                RoleDashboard.role_id == admin_role.id,
                RoleDashboard.dashboard_id == dash.id))
        if not existing_rd.scalar_one_or_none():
            db.add(RoleDashboard(role_id=admin_role.id, dashboard_id=dash.id, can_view=True, can_edit=True))
        existing_rd = await db.execute(
            select(RoleDashboard).where(
                RoleDashboard.role_id == viewer_role.id,
                RoleDashboard.dashboard_id == dash.id))
        if not existing_rd.scalar_one_or_none():
            db.add(RoleDashboard(role_id=viewer_role.id, dashboard_id=dash.id, can_view=True, can_edit=False))

        await db.commit()

    if created_any:
        print("\n种子数据已就绪!")
    else:
        print("\n数据已存在，跳过。")
    print("  admin   / admin123   (管理员)")
    print("  viewer  / viewer123  (访客)")
    print("\n测试筛选器注入: 打开仪表板 → 切换「区域」下拉 → 「各区域收入」图表按区域过滤")


if __name__ == "__main__":
    asyncio.run(seed())
