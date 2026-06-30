import asyncio
import os
import sys

from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.chdir(os.path.dirname(os.path.dirname(__file__)))

from app.database import Base, async_session, engine
from app.models.chart import Chart
from app.models.dashboard import Dashboard, RoleDashboard
from app.models.role import Role
from app.models.user import User

DASHBOARD_NAME = "信贷审批驾驶舱（仿图）"
DASHBOARD_DESC = "按参考图搭建：指标总览 + 审批漏斗 + 渠道质量 + AI趋势"


def kpi_card_code(title: str, value: str, yoy: str, mom: str, trend: str, series: list[int]) -> str:
    color = "#19be6b" if trend == "up" else "#f56c6c"
    symbol = "▲" if trend == "up" else "▼"
    line_color = "#3a7afe" if trend == "up" else "#ff6b6b"
    area_color = "rgba(58, 122, 254, 0.12)" if trend == "up" else "rgba(255, 107, 107, 0.12)"
    data = ", ".join(str(v) for v in series)
    return f'''const {{ ref, onMounted, h }} = vue

const TITLE = "{title}"
const VALUE = "{value}"
const YOY = "{yoy}"
const MOM = "{mom}"
const DELTA_COLOR = "{color}"
const DELTA_SYMBOL = "{symbol}"

return {{
  setup() {{
    const $ = themeColors()
    const rootRef = ref(null)

    // useChartLifecycle with a getter for the .sparkline child element
    const {{ renderChart }} = useChartLifecycle(() => rootRef.value?.querySelector('.sparkline'))

    onMounted(() => {{
      renderChart({{
        animation: true,
        grid: {{ left: 0, right: 0, top: 4, bottom: 0 }},
        xAxis: {{ type: 'category', show: false, data: [{data}] }},
        yAxis: {{ type: 'value', show: false }},
        series: [{{
          type: 'line',
          smooth: true,
          symbol: 'none',
          data: [{data}],
          lineStyle: {{ color: '{line_color}', width: 2 }},
          areaStyle: {{ color: '{area_color}' }}
        }}]
      }})
    }})

    return () => h('div', {{
      ref: rootRef,
      style: cardStyle($, `background:${{$.gradientBg}};display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 1px 2px rgba(31,53,87,.05);`)
    }}, [
      h('div', {{ style: 'display:flex;justify-content:space-between;align-items:center;' }}, [
        h('div', {{ style: 'display:flex;align-items:center;gap:6px;' }}, [
          h('span', {{ style: 'display:inline-flex;width:14px;height:14px;border-radius:3px;background:#4f89ff;color:#fff;font-size:10px;align-items:center;justify-content:center;font-weight:700;' }}, 'i'),
          h('span', {{ style: `font-size:12px;color:${{$.titleColor}};font-weight:600;` }}, TITLE)
        ]),
        h('span', {{ style: `font-size:12px;color:${{$.mutedColor}};` }}, '近30天')
      ]),
      h('div', {{ style: 'display:flex;align-items:flex-end;gap:8px;' }}, [
        h('span', {{ style: `font-size:30px;line-height:1;color:${{$.valueColor}};font-weight:800;letter-spacing:0.5px;` }}, VALUE),
      ]),
      h('div', {{ class: 'sparkline', style: 'height:28px;width:100%;' }}),
      h('div', {{ style: `display:flex;justify-content:space-between;font-size:12px;color:${{$.subColor}};gap:8px;` }}, [
        h('span', null, '同比 ' + YOY),
        h('span', {{ style: 'color:' + DELTA_COLOR + ';font-weight:700;' }}, DELTA_SYMBOL + ' ' + MOM + ' (环比)')
      ])
    ])
  }}
}}'''


def flow_strip_code() -> str:
  return '''const { h } = vue

const NODES = [
  { name: '申请', value: '128,473', rate: '100%' },
  { name: 'KYC提交', value: '102,731', rate: '79.93%' },
  { name: 'KYC通过', value: '73,260', rate: '71.27%' },
  { name: '审批通过', value: '43,218', rate: '58.97%' },
  { name: '提现申请', value: '38,124', rate: '88.22%' },
  { name: '放款成功', value: '35,078', rate: '92.01%' }
]

return {
  setup() {
    const $ = themeColors()
    const palette = $.isDark
      ? ['#233450', '#244264', '#26506f', '#235965', '#206050', '#1f5a43']
      : ['#edf4ff', '#dceaff', '#d6f2ff', '#ddfbf2', '#ecfff2', '#f5fff7']

    function nodeStyle(i) {
      const clip = i < NODES.length - 1
        ? 'clip-path:polygon(0 0, calc(100% - 16px) 0, 100% 50%, calc(100% - 16px) 100%, 0 100%, 12px 50%);'
        : 'clip-path:polygon(0 0, 100% 0, 100% 100%, 0 100%, 12px 50%);'
      const pad = i === 0 ? 'padding:12px 14px;' : 'padding:12px 14px 12px 18px;'
      const border = $.isDark ? 'rgba(155,179,212,.35)' : '#dfe8f5'
      return 'flex:1;min-width:0;border-radius:8px;background:' + palette[i] + ';border:1px solid ' + border + ';position:relative;' + pad + clip
    }

    return () => h('div', {
      style: cardStyle($)
    }, [
      h('div', { style: 'display:flex;align-items:center;gap:8px;margin-bottom:10px;' }, [
        h('span', { style: 'display:inline-flex;width:18px;height:18px;border-radius:4px;background:#4f89ff;color:#fff;font-size:12px;align-items:center;justify-content:center;font-weight:700;' }, '2'),
        h('span', { style: `font-size:14px;font-weight:700;color:${$.titleColor};` }, '信贷漏斗（近30日）')
      ]),
      h('div', { style: 'display:flex;align-items:stretch;gap:8px;height:calc(100% - 30px);' },
        NODES.map((n, i) => h('div', { style: nodeStyle(i) }, [
          h('div', { style: `font-size:12px;color:${$.textColor};margin-bottom:8px;` }, n.name),
          h('div', { style: `font-size:24px;font-weight:800;color:${$.valueColor};line-height:1.1;margin-bottom:8px;` }, n.value),
          h('div', { style: `font-size:12px;color:${$.rateColor};font-weight:700;` }, n.rate),
          i < NODES.length - 1 ? h('div', { style: `position:absolute;right:-14px;top:50%;transform:translateY(-50%);font-size:18px;color:${$.arrowColor};font-weight:700;` }, '\u203a') : null
        ]))
      )
    ])
  }
}'''


def stage_table_code() -> str:
    return '''const { h } = vue

const ROWS = [
  ['申请', '128,473', '100%', '-'],
  ['KYC提交', '102,731', '79.93%', '-1.23pp'],
  ['KYC通过', '73,260', '71.27%', '+1.34pp'],
  ['审批通过', '43,218', '58.97%', '-2.11pp'],
  ['提现申请', '38,124', '88.22%', '-0.87pp'],
  ['放款成功', '35,078', '92.01%', '-0.69pp']
]

function trendColor(v) {
  if (v.startsWith('+')) return '#18b566'
  if (v.startsWith('-')) return '#ef5b66'
  return '#9aa7bd'
}

return {
  setup() {
    const $ = themeColors()

    return () => h('div', { style: `height:100%;width:100%;background:${$.cardBg};border:1px solid ${$.cardBorder};border-radius:8px;padding:10px 12px;box-sizing:border-box;display:flex;flex-direction:column;` }, [
      h('div', { style: `font-size:14px;font-weight:700;color:${$.titleColor};margin-bottom:8px;` }, '漏斗阶段汇总（近30日）'),
      h('div', { style: 'flex:1;min-height:0;overflow:auto;' }, [
        h('table', { style: `width:100%;border-collapse:collapse;font-size:12px;color:${$.tableColor};` }, [
        h('thead', { style: `position:sticky;top:0;z-index:1;background:${$.headBg};` }, [
          h('tr', null, ['步骤', '用户量', '较上一步转化', '环比变化'].map(t =>
            h('th', { style: `text-align:left;padding:6px;border-bottom:1px solid ${$.lineColor};color:${$.headColor};font-weight:600;` }, t)
          ))
        ]),
        h('tbody', null,
          ROWS.map(r => h('tr', null, [
            h('td', { style: `padding:7px 6px;border-bottom:1px solid ${$.rowColor};` }, r[0]),
            h('td', { style: `padding:7px 6px;border-bottom:1px solid ${$.rowColor};color:${$.strongColor};font-weight:700;` }, r[1]),
            h('td', { style: `padding:7px 6px;border-bottom:1px solid ${$.rowColor};` }, r[2]),
            h('td', { style: `padding:7px 6px;border-bottom:1px solid ${$.rowColor};color:${trendColor(r[3])};font-weight:700;` }, r[3])
          ]))
        )
      ])
      ])
    ])
  }
}'''


def channel_table_code() -> str:
    return '''const { h } = vue

const ROWS = [
  ['Facebook Ads', '22.41%', '-2.35', '-1,214'],
  ['Google Ads', '28.72%', '-0.84', '+542'],
  ['TikTok Ads', '19.38%', '-3.41', '-1,135'],
  ['Referral', '31.56%', '+1.28', '+518'],
  ['自然流量', '27.91%', '-0.31', '-204']
]

function c(v) {
  return v.startsWith('+') ? '#16b364' : '#ef5b66'
}

return {
  setup() {
    const $ = themeColors()

    return () => h('div', { style: `height:100%;width:100%;background:${$.cardBg};border:1px solid ${$.cardBorder};border-radius:8px;padding:10px 12px;box-sizing:border-box;display:flex;flex-direction:column;` }, [
      h('div', { style: 'display:flex;align-items:center;gap:8px;margin-bottom:8px;' }, [
        h('span', { style: 'display:inline-flex;width:18px;height:18px;border-radius:4px;background:#4f89ff;color:#fff;font-size:12px;align-items:center;justify-content:center;font-weight:700;' }, '3'),
        h('span', { style: `font-size:14px;font-weight:700;color:${$.titleColor};` }, '渠道审批表现（异常定位）')
      ]),
      h('div', { style: 'flex:1;min-height:0;overflow:auto;' }, [
        h('table', { style: `width:100%;border-collapse:collapse;font-size:12px;color:${$.tableColor};` }, [
        h('thead', { style: `position:sticky;top:0;z-index:1;background:${$.headBg};` }, [
          h('tr', null, ['渠道', '批准率', '环比(pp)', '影响量'].map(t =>
            h('th', { style: `text-align:left;padding:6px;border-bottom:1px solid ${$.lineColor};color:${$.headColor};font-weight:600;` }, t)
          ))
        ]),
        h('tbody', null,
          ROWS.map(r => h('tr', null, [
            h('td', { style: `padding:7px 6px;border-bottom:1px solid ${$.rowColor};font-weight:600;color:${$.strongColor};` }, r[0]),
            h('td', { style: `padding:7px 6px;border-bottom:1px solid ${$.rowColor};` }, r[1]),
            h('td', { style: `padding:7px 6px;border-bottom:1px solid ${$.rowColor};color:${c(r[2])};font-weight:700;` }, r[2]),
            h('td', { style: `padding:7px 6px;border-bottom:1px solid ${$.rowColor};color:${c(r[3])};font-weight:700;` }, r[3])
          ]))
        )
      ])
      ])
    ])
  }
}'''


def bar_code() -> str:
    return '''const { onMounted, h } = vue

const DATA = [
  { name: 'Facebook Ads', value: 22.41 },
  { name: 'Google Ads', value: 28.72 },
  { name: 'TikTok Ads', value: 19.38 },
  { name: 'Referral', value: 31.56 },
  { name: '自然流量', value: 27.91 }
]

return {
  setup() {
    const $ = themeColors()
    const { chartRef, renderChart } = useChartLifecycle()

    onMounted(() => {
      renderChart({
        animation: true,
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 40, right: 12, top: 30, bottom: 40 },
        xAxis: {
          type: 'category',
          data: DATA.map(d => d.name),
          axisLabel: { interval: 0, rotate: 10, fontSize: 11, color: $.axisColor },
          axisLine: { lineStyle: { color: $.splitColor } }
        },
        yAxis: {
          type: 'value',
          axisLabel: { formatter: '{value}%', color: $.axisColor },
          splitLine: { lineStyle: { color: $.splitColor, type: 'dashed' } }
        },
        series: [{
          type: 'bar',
          data: DATA.map(d => d.value),
          barWidth: 28,
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: (p) => p.dataIndex === 3 ? '#26c6a3' : '#3a7afe'
          },
          label: { show: true, position: 'top', formatter: '{c}%' }
        }]
      })
    })

    return () => h('div', { style: cardStyle($) }, [
      h('div', { style: `font-size:14px;font-weight:700;color:${$.titleColor};margin:2px 0 4px 4px;` }, '各渠道放款成功率（近30日）'),
      h('div', { ref: chartRef, style: chartAreaStyle() })
    ])
  }
}'''


def pie_code() -> str:
    return '''const { onMounted, h } = vue

const DATA = [
  { name: '证件问题', value: 31.9 },
  { name: '评分过低', value: 18.9 },
  { name: '人脸不匹配', value: 17.6 },
  { name: '逾期记录', value: 15.7 },
  { name: '征信不良', value: 9.8 },
  { name: '其他', value: 6.1 }
]

return {
  setup() {
    const $ = themeColors()
    const { chartRef, renderChart } = useChartLifecycle()

    onMounted(() => {
      renderChart({
        tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
        legend: { orient: 'vertical', right: 8, top: 20, textStyle: { fontSize: 11, color: $.legendColor } },
        series: [{
          type: 'pie',
          radius: ['38%', '68%'],
          center: ['36%', '53%'],
          avoidLabelOverlap: true,
          label: { formatter: '{d}%' },
          data: DATA,
          color: ['#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#E8684A', '#6DC8EC']
        }]
      })
    })

    return () => h('div', { style: cardStyle($) }, [
      h('div', { style: `font-size:14px;font-weight:700;color:${$.titleColor};margin:2px 0 4px 4px;` }, 'KYC失败原因分布（近30日）'),
      h('div', { ref: chartRef, style: chartAreaStyle() })
    ])
  }
}'''


def trend_code() -> str:
    return '''const { onMounted, h } = vue

const X = ['04-21', '04-26', '05-01', '05-06', '05-11', '05-16', '05-21', '05-26', '06-01', '06-06', '06-11', '06-16']
const APPROVAL = [28.6, 28.9, 28.3, 28.1, 27.9, 27.5, 27.8, 28.0, 27.7, 27.5, 27.3, 27.1]
const KPI = [3.4, 3.5, 3.3, 3.5, 3.2, 3.4, 3.3, 3.1, 3.2, 3.0, 3.1, 3.2]

return {
  setup() {
    const $ = themeColors()
    const { chartRef, renderChart } = useChartLifecycle()

    onMounted(() => {
      renderChart({
        tooltip: { trigger: 'axis' },
        legend: { top: 4, textStyle: { color: $.axisColor } },
        grid: { left: 40, right: 30, top: 40, bottom: 30 },
        xAxis: {
          type: 'category',
          data: X,
          axisLabel: { color: $.axisColor },
          axisLine: { lineStyle: { color: $.splitColor } }
        },
        yAxis: [
          {
            type: 'value',
            name: '通过率(%)',
            min: 24,
            max: 32,
            nameTextStyle: { color: $.axisColor },
            axisLabel: { color: $.axisColor },
            splitLine: { lineStyle: { color: $.splitColor, type: 'dashed' } }
          },
          {
            type: 'value',
            name: 'DPD7(%)',
            min: 2,
            max: 5,
            nameTextStyle: { color: $.axisColor },
            axisLabel: { color: $.axisColor },
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: '审批通过率',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            data: APPROVAL,
            lineStyle: { color: '#3a7afe', width: 2 },
            areaStyle: { color: 'rgba(58,122,254,0.08)' }
          },
          {
            name: 'DPD7',
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            data: KPI,
            lineStyle: { color: '#f59e0b', width: 2 }
          }
        ]
      })
    })

    return () => h('div', { style: cardStyle($) }, [
      h('div', { style: `display:flex;justify-content:space-between;align-items:center;margin:2px 0 4px 4px;` }, [
        h('span', { style: `font-size:14px;font-weight:700;color:${$.titleColor};` }, 'AI日级分析（审批与坏账趋势）'),
        h('span', { style: 'font-size:20px;font-weight:800;color:#ef5b66;padding-right:6px;' }, '3.21%')
      ]),
      h('div', { ref: chartRef, style: chartAreaStyle() })
    ])
  }
}'''


def ai_summary_code() -> str:
    return '''const { h } = vue

const FACTS = [
  '近30日审批通过率 27.35%，较上期下降 0.6pp。',
  'KYC阶段损失集中在证件问题与评分不足。',
  'TikTok 渠道质量波动最大，建议下调预算并复核投放包。',
  'Referral 渠道转化最佳，可作为短期增量抓手。'
]

const ACTIONS = [
  '优化证件识别模型阈值，减少误拒。',
  '将高风险客群分层至人工复审通道。',
  '对低质渠道设置日损失上限告警。'
]

return {
  setup() {
    const $ = themeColors()

    return () => h('div', { style: cardStyle($) }, [
      h('div', { style: 'display:flex;align-items:center;gap:8px;margin-bottom:10px;' }, [
        h('span', { style: 'display:inline-flex;width:18px;height:18px;border-radius:4px;background:#4f89ff;color:#fff;font-size:12px;align-items:center;justify-content:center;font-weight:700;' }, '4'),
        h('span', { style: `font-size:14px;font-weight:700;color:${$.titleColor};` }, 'AI日级分析区')
      ]),
      h('div', { style: `font-size:13px;font-weight:700;color:${$.strongColor};margin-bottom:6px;` }, '核心结论'),
      h('ul', { style: `margin:0 0 10px 16px;padding:0;color:${$.bodyColor};font-size:12px;line-height:1.6;` },
        FACTS.map(i => h('li', null, i))
      ),
      h('div', { style: `font-size:13px;font-weight:700;color:${$.strongColor};margin-bottom:6px;` }, '建议动作'),
      h('ul', { style: `margin:0 0 0 16px;padding:0;color:${$.bodyColor};font-size:12px;line-height:1.6;` },
        ACTIONS.map(i => h('li', null, i))
      )
    ])
  }
}'''


async def ensure_base_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_admin_user_id(db) -> int | None:
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    return admin.id if admin else None


async def upsert_chart(db, title: str, code: str, created_by: int | None) -> Chart:
    result = await db.execute(select(Chart).where(Chart.title == title))
    chart = result.scalar_one_or_none()
    if chart is None:
        chart = Chart(
            title=title,
            component_type="dynamic",
            component_code=code,
            created_by=created_by,
        )
        db.add(chart)
        await db.flush()
        print(f"  + 创建图表: {title}")
    else:
        chart.component_type = "dynamic"
        chart.component_code = code
        print(f"  * 更新图表: {title}")
    return chart


async def ensure_role_link(db, role_name: str, dashboard_id: int, can_edit: bool) -> None:
    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if role is None:
        return

    link_result = await db.execute(
        select(RoleDashboard).where(
            RoleDashboard.role_id == role.id,
            RoleDashboard.dashboard_id == dashboard_id,
        )
    )
    link = link_result.scalar_one_or_none()
    if link is None:
        db.add(
            RoleDashboard(
                role_id=role.id,
                dashboard_id=dashboard_id,
                can_view=True,
                can_edit=can_edit,
            )
        )
    else:
        link.can_view = True
        link.can_edit = can_edit


async def upsert_dashboard(db, created_by: int | None, chart_ids: dict[str, int]) -> Dashboard:
    layout = [
        {"chart_id": chart_ids["指标卡-申请人数"], "x": 0, "y": 0, "w": 3, "h": 2},
        {"chart_id": chart_ids["指标卡-KYC提交率"], "x": 3, "y": 0, "w": 3, "h": 2},
        {"chart_id": chart_ids["指标卡-KYC通过率"], "x": 6, "y": 0, "w": 3, "h": 2},
        {"chart_id": chart_ids["指标卡-审批通过率"], "x": 9, "y": 0, "w": 3, "h": 2},
        {"chart_id": chart_ids["指标卡-首逾率"], "x": 12, "y": 0, "w": 3, "h": 2},
        {"chart_id": chart_ids["指标卡-DPD7"], "x": 15, "y": 0, "w": 3, "h": 2},
        {"chart_id": chart_ids["指标卡-复借率"], "x": 18, "y": 0, "w": 3, "h": 2},
        {"chart_id": chart_ids["指标卡-放款总额"], "x": 21, "y": 0, "w": 3, "h": 2},
        {"chart_id": chart_ids["漏斗条带-近30日"], "x": 0, "y": 2, "w": 16, "h": 4},
        {"chart_id": chart_ids["漏斗阶段汇总表"], "x": 16, "y": 2, "w": 8, "h": 4},
        {"chart_id": chart_ids["渠道审批表现表"], "x": 0, "y": 6, "w": 8, "h": 4},
        {"chart_id": chart_ids["渠道放款成功率柱图"], "x": 8, "y": 6, "w": 8, "h": 4},
        {"chart_id": chart_ids["KYC失败原因饼图"], "x": 16, "y": 6, "w": 8, "h": 4},
        {"chart_id": chart_ids["AI策略建议面板"], "x": 0, "y": 10, "w": 10, "h": 4},
        {"chart_id": chart_ids["AI日级分析趋势图"], "x": 10, "y": 10, "w": 14, "h": 4},
    ]

    result = await db.execute(select(Dashboard).where(Dashboard.name == DASHBOARD_NAME))
    dashboard = result.scalar_one_or_none()

    if dashboard is None:
        dashboard = Dashboard(
            name=DASHBOARD_NAME,
            description=DASHBOARD_DESC,
            layout_config=layout,
            global_filters=[],
            filter_ids=None,
            is_published=True,
            created_by=created_by,
        )
        db.add(dashboard)
        await db.flush()
        print(f"  + 创建仪表板: {DASHBOARD_NAME}")
    else:
        dashboard.description = DASHBOARD_DESC
        dashboard.layout_config = layout
        dashboard.global_filters = []
        dashboard.filter_ids = None
        dashboard.is_published = True
        print(f"  * 更新仪表板: {DASHBOARD_NAME}")

    return dashboard


async def run() -> None:
    await ensure_base_tables()

    chart_specs = [
        ("指标卡-申请人数", kpi_card_code("申请人数", "128,473", "+6.7%", "+18.7%", "up", [62, 64, 63, 66, 65, 67, 69, 68, 66, 65, 68, 72])),
        ("指标卡-KYC提交率", kpi_card_code("KYC提交率", "71.42%", "+1.8pp", "+6.5pp", "up", [69, 70, 69, 71, 72, 73, 72, 74, 73, 72, 71, 72])),
        ("指标卡-KYC通过率", kpi_card_code("KYC通过率", "34.28%", "-1.2pp", "-3.6pp", "down", [40, 39, 38, 37, 36, 35, 35, 34, 34, 33, 34, 34])),
        ("指标卡-审批通过率", kpi_card_code("审批通过率", "27.35%", "-0.6pp", "-2.1pp", "down", [31, 30, 30, 29, 28, 28, 27, 28, 27, 27, 27, 27])),
        ("指标卡-首逾率", kpi_card_code("首逾率（Defaults 30+）", "3.21%", "+0.21pp", "+0.74pp", "down", [2.6, 2.7, 2.8, 2.8, 2.9, 3.0, 2.9, 3.0, 3.1, 3.0, 3.1, 3.2])),
        ("指标卡-DPD7", kpi_card_code("DPD7", "8.67%", "+0.45pp", "+1.23pp", "down", [8.1, 8.2, 8.0, 8.1, 8.3, 8.4, 8.5, 8.4, 8.6, 8.5, 8.6, 8.7])),
        ("指标卡-复借率", kpi_card_code("复借率", "23.14%", "+0.92pp", "+2.38pp", "up", [21.1, 21.5, 21.7, 22.0, 22.4, 22.6, 22.9, 23.0, 23.2, 23.0, 23.1, 23.1])),
        ("指标卡-放款总额", kpi_card_code("放款总额 (MXN)", "$86.42M", "+7.6%", "+22.3%", "down", [80, 81, 82, 83, 85, 86, 87, 89, 88, 87, 86, 86])),
        ("漏斗条带-近30日", flow_strip_code()),
        ("漏斗阶段汇总表", stage_table_code()),
        ("渠道审批表现表", channel_table_code()),
        ("渠道放款成功率柱图", bar_code()),
        ("KYC失败原因饼图", pie_code()),
        ("AI策略建议面板", ai_summary_code()),
        ("AI日级分析趋势图", trend_code()),
    ]

    async with async_session() as db:
        admin_id = await get_admin_user_id(db)
        chart_ids: dict[str, int] = {}

        print("开始写入图表组件...")
        for title, code in chart_specs:
            chart = await upsert_chart(db, title, code, admin_id)
            chart_ids[title] = chart.id

        print("开始写入仪表板与挂载布局...")
        dashboard = await upsert_dashboard(db, admin_id, chart_ids)
        await ensure_role_link(db, "管理员", dashboard.id, can_edit=True)
        await ensure_role_link(db, "访客", dashboard.id, can_edit=False)

        await db.commit()

        print("\n完成。")
        print(f"仪表板: {dashboard.name}")
        print(f"图表数量: {len(chart_specs)}")
        print("可在前端仪表板列表中查看。")


if __name__ == "__main__":
    asyncio.run(run())
