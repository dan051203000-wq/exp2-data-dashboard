# -*- coding: utf-8 -*-
"""
实验2 · 校园一卡通消费数据看板
=================================================
技术栈：Streamlit + Pandas + Plotly
覆盖内容：
    基础任务 1-5   —— 需求分析/版面设计、数据预处理、基础图表、看板整合、结果验证
    进阶任务 1-3   —— 动态视觉效果、图表联动与筛选、排行榜/热力图/雷达图/仪表盘
    扩展任务 1-5   —— 实时数据源、阈值预警、大屏与移动端适配、报告导出、主题切换与钻取

启动：
    streamlit run app.py
"""

import io
import time
from contextlib import contextmanager
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils import charts
from utils.data_loader import load_clean_data, simulate_live_records
from utils.style import THEMES, card, get_theme, kpi_html, render_css, section_title

# ------------------------------------------------------------------ 页面配置
st.set_page_config(
    page_title="校园一卡通消费数据看板",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ 数据加载
df_all = load_clean_data()
MIN_DATE = df_all["日期"].min()
MAX_DATE = df_all["日期"].max()


# ================================================================== 侧边栏
with st.sidebar:
    st.markdown("### ⚙️ 看板控制台")

    # 支持通过 URL 参数预设主题/下钻学院（便于演示与截图复现，如 ?theme=亮色简约风）
    qp = st.query_params
    theme_default = qp.get("theme", "暗色科技风")
    if theme_default not in THEMES:
        theme_default = "暗色科技风"
    theme_name = st.radio("🎨 主题风格（扩展5）", list(THEMES.keys()),
                          index=list(THEMES).index(theme_default), horizontal=True)
    t = get_theme(theme_name)

    st.divider()
    st.markdown("**🗓️ 时间筛选（进阶2）**")
    date_range = st.date_input(
        "消费日期区间", value=(MIN_DATE, MAX_DATE),
        min_value=MIN_DATE, max_value=MAX_DATE, format="YYYY-MM-DD",
    )

    st.markdown("**🏷️ 维度筛选（进阶2）**")
    campus_sel = st.multiselect("校区", sorted(df_all["校区"].dropna().unique()),
                                default=sorted(df_all["校区"].dropna().unique()))
    college_sel = st.multiselect("学院", sorted(df_all["学院"].dropna().unique()),
                                 default=sorted(df_all["学院"].dropna().unique()))
    type_sel = st.multiselect("消费类型", sorted(df_all["消费类型"].dropna().unique()),
                              default=sorted(df_all["消费类型"].dropna().unique()))
    amt_lo, amt_hi = float(df_all["消费金额"].min()), float(df_all["消费金额"].max())
    amt_range = st.slider("单笔金额区间（元）", 0.0, float(int(amt_hi) + 1),
                          (0.0, float(int(amt_hi) + 1)), step=1.0)

    st.divider()
    st.markdown("**🚨 预警阈值（扩展2）**")
    # 支持通过 URL 参数预设阈值（便于演示与截图复现，如 ?thr_daily=300）
    thr_daily = st.slider("日均消费额预警上限（元）", 300, 1500,
                          int(qp.get("thr_daily", 800)), step=20)
    thr_big = st.slider("大额单笔（>50元）占比预警上限（%）", 0.5, 8.0,
                        float(qp.get("thr_big", 5.0)), step=0.5)
    target_per_capita = st.slider("人均消费目标（元）", 150, 400, 250, step=10)

    st.divider()
    st.markdown("**🔴 实时数据源（扩展1）**")
    live_mode = st.toggle("开启实时刷新", value=False)
    refresh_sec = st.slider("刷新间隔（秒）", 3, 30, 5, disabled=not live_mode)

    st.divider()
    if st.button("🔄 重置全部筛选与联动", use_container_width=True):
        st.session_state.pop("selected_college", None)
        st.session_state.pop("live_rows", None)
        st.rerun()

    st.caption("数据：校园一卡通 2025 秋季学期消费流水\n"
               "（原始数据 6040 条 → 清洗后 5905 条）")

render_css(t)


# ================================================================== 实时数据
@contextmanager
def live_scope():
    yield


if live_mode:
    st_autorefresh(interval=refresh_sec * 1000, key="auto_refresh")
    now = datetime.now()
    last = st.session_state.get("live_last")
    if last is None or (now - last).total_seconds() >= refresh_sec:
        new_rows = simulate_live_records(df_all, int(np.random.randint(1, 5)), now)
        buf = st.session_state.get("live_rows")
        buf = new_rows if buf is None else pd.concat([buf, new_rows], ignore_index=True)
        st.session_state["live_rows"] = buf.tail(300)      # 只保留最近 300 条，避免无限增长
        st.session_state["live_last"] = now
live_rows = st.session_state.get("live_rows")


# ================================================================== 数据筛选
def apply_filters(df: pd.DataFrame, with_date: bool = True) -> pd.DataFrame:
    d = df
    if with_date and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = date_range
        d = d[(d["日期"] >= start) & (d["日期"] <= end)]
    if campus_sel:
        d = d[d["校区"].isin(campus_sel)]
    if college_sel:
        d = d[d["学院"].isin(college_sel)]
    if type_sel:
        d = d[d["消费类型"].isin(type_sel)]
    d = d[(d["消费金额"] >= amt_range[0]) & (d["消费金额"] <= amt_range[1])]
    return d


hist = apply_filters(df_all, with_date=True)
live_part = apply_filters(live_rows, with_date=False) if live_rows is not None else None
df = pd.concat([hist, live_part], ignore_index=True) if live_part is not None and len(live_part) else hist

# 联动选择（点击柱状图 → 下钻到某个学院；也支持 ?college=xx 直接进入下钻态）
if "college" in st.query_params and not st.session_state.get("selected_college"):
    st.session_state["selected_college"] = st.query_params["college"]
selected_college = st.session_state.get("selected_college")
if selected_college and selected_college in set(df["学院"]):
    df_linked = df[df["学院"] == selected_college]
else:
    selected_college = None
    df_linked = df


# ================================================================== 指标计算
def compute_metrics(d: pd.DataFrame) -> dict:
    if d.empty:
        return dict(总额=0, 笔数=0, 人数=0, 人均=0, 日均=0, 环比=0, 大单占比=0, 天数=0)
    total = float(d["消费金额"].sum())
    days = max(d["日期"].nunique(), 1)
    people = max(d["学号"].nunique(), 1)
    dates = sorted(d["日期"].unique())
    half = max(len(dates) // 2, 1)
    first = float(d[d["日期"].isin(dates[:half])]["消费金额"].sum())
    second = float(d[d["日期"].isin(dates[half:])]["消费金额"].sum())
    growth = (second - first) / first * 100 if first else 0.0
    return dict(
        总额=total,
        笔数=int(len(d)),
        人数=int(d["学号"].nunique()),
        人均=total / people,
        日均=total / days,
        环比=growth,
        大单占比=float((d["消费金额"] > 50).mean() * 100),
        天数=days,
    )


m = compute_metrics(df)
warns = []
if m["日均"] > thr_daily:
    warns.append(f"日均消费额 {m['日均']:,.0f} 元 已超过预警线 {thr_daily:,} 元")
if m["大单占比"] > thr_big:
    warns.append(f"大额单笔（>50元）占比 {m['大单占比']:.2f}% 已超过预警线 {thr_big:.1f}%")
if m["环比"] < -10:
    warns.append(f"区间环比下滑 {m['环比']:.1f}%（低于 -10%），建议排查消费活跃度")

# ------------------------------------------------------------------ 标题栏
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
live_badge = ('<span class="live-dot"></span>实时数据流已接入'
              if live_mode else "静态数据集（可开启实时模式）")
st.markdown(
    f'<div class="dash-title">'
    f'<div><h1>🎓 校园一卡通消费数据看板</h1>'
    f'<div class="sub">统计周期 {MIN_DATE} ~ {MAX_DATE} ｜ '
    f'当前筛选 {m["天数"]} 天 / {m["笔数"]:,} 笔 ｜ 更新时间 {now_str}</div></div>'
    f'<div class="sub">{live_badge}</div>'
    f"</div>",
    unsafe_allow_html=True,
)

# 预警提示条（扩展2）
if warns:
    st.markdown(f'<div class="alert-bar">⚠️ 预警触发：{" ｜ ".join(warns)}</div>',
                unsafe_allow_html=True)
else:
    st.markdown(f'<div class="dash-card" style="padding:8px 14px;margin-bottom:10px;">'
                f'<span style="color:{t["ok"]};font-weight:600;">✅ 运行正常</span>'
                f'<span style="color:{t["subtext"]};font-size:12px;">　全部核心指标均在阈值范围内</span></div>',
                unsafe_allow_html=True)


# ================================================================== ① 数据概览区
st.markdown(section_title("① 数据概览区 · 核心指标"), unsafe_allow_html=True)

kpi_items = [
    ("消费总额", m["总额"], "{:,.0f}", "元", "", "flat", False),
    ("消费笔数", m["笔数"], "{:,.0f}", "笔", "", "flat", False),
    ("活跃消费人数", m["人数"], "{:,.0f}", "人", "", "flat", False),
    ("人均消费额", m["人均"], "{:,.1f}", "元", "", "flat", False),
    ("日均消费额", m["日均"], "{:,.0f}", "元",
     f"预警线 {thr_daily:,}", "flat", m["日均"] > thr_daily),
    ("区间环比增长率", m["环比"], "{:+.2f}", "%",
     "后半期 vs 前半期", "up" if m["环比"] > 0 else ("down" if m["环比"] < 0 else "flat"),
     m["环比"] < -10),
]
kpi_cols = st.columns(6)
kpi_slots = [c.empty() for c in kpi_cols]
animated = st.session_state.get("kpi_animated", False)
steps = 1 if animated else 26


def _paint_kpis(ratio: float) -> None:
    for slot, (label, value, fmt, unit, delta, ddir, warn) in zip(kpi_slots, kpi_items):
        slot.markdown(
            kpi_html(label, fmt.format(value * ratio), unit, delta, ddir, warn),
            unsafe_allow_html=True,
        )


_paint_kpis(1.0)
if not animated:
    # 进阶1：数值滚动动画（仅在首次加载时执行一次）
    for s in range(1, steps + 1):
        _paint_kpis(s / steps)
        time.sleep(0.012)
    _paint_kpis(1.0)
st.session_state["kpi_animated"] = True

# ================================================================== ② 维度统计区
st.markdown(section_title("② 维度统计区 · 学院 / 类型 / 场景 / 支付方式"), unsafe_allow_html=True)
c1, c2 = st.columns([1.25, 1])

with c1:
    with card(st, "各学院消费总额对比", "点击柱体可联动下钻到该学院（进阶2）"):
        order = (df.groupby("学院")["消费金额"].sum()
                   .sort_values(ascending=False).index.tolist())
        fig_college = charts.bar_college(df, t, highlight=selected_college, height=345)
        try:
            ev = st.plotly_chart(fig_college, use_container_width=True, key="college_bar",
                                 on_select="rerun", selection_mode="points")
            pts = (ev.selection.get("points") if ev and ev.selection else [])
            if pts:
                idx = pts[0].get("point_index", 0)
                if 0 <= idx < len(order):
                    picked = order[idx]
                    if picked != st.session_state.get("selected_college"):
                        st.session_state["selected_college"] = picked
                        st.rerun()
        except TypeError:                       # 低版本 Streamlit 无 on_select
            st.plotly_chart(fig_college, use_container_width=True)

with c2:
    with card(st, "消费类型金额占比", "环形图展示消费结构（基础图表）"):
        st.plotly_chart(charts.donut_category(df_linked, t, height=345),
                        use_container_width=True, key="donut_cat")

c3, c4, c5 = st.columns([1.15, 1.1, 1])
with c3:
    with card(st, "消费场景 TOP8 排行榜", "进阶3：数据排行榜"):
        st.plotly_chart(charts.bar_scene_top(df_linked, t, top=8, height=330),
                        use_container_width=True, key="bar_scene")
with c4:
    with card(st, "时段消费分布", "柱状图 + 笔数副轴"):
        st.plotly_chart(charts.bar_period(df_linked, t, height=330),
                        use_container_width=True, key="bar_period")
with c5:
    with card(st, "支付方式对比", "括号内为笔数占比"):
        st.plotly_chart(charts.bar_pay_method(df_linked, t, height=330),
                        use_container_width=True, key="bar_pay")

# ================================================================== ③ 趋势分析区
st.markdown(section_title("③ 趋势分析区 · 时间趋势 / 热力图 / 雷达图 / 仪表盘"), unsafe_allow_html=True)
d1, d2 = st.columns([1.6, 1])
with d1:
    with card(st, "每日消费趋势", "面积图 + 7 日移动平均线（hover 查看具体日期）"):
        st.plotly_chart(charts.line_daily(df_linked, t, height=350),
                        use_container_width=True, key="line_daily")
with d2:
    with card(st, "星期 × 小时 消费热力图", "进阶3：热力图定位消费高峰时段"):
        st.plotly_chart(charts.heatmap_week_hour(df_linked, t, height=350),
                        use_container_width=True, key="heatmap")

d3, d4, d5 = st.columns([1, 1, 1])
with d3:
    label = f"雷达图：{selected_college or '当前筛选'} vs 全校平均"
    with card(st, label, "进阶3：多维能力对比（各类型人均消费归一化）"):
        st.plotly_chart(charts.radar_college(df, t, selected_college or "", height=320),
                        use_container_width=True, key="radar")
with d4:
    with card(st, "人均消费目标达成率", "扩展3：进度仪表盘（阈值可视化）"):
        st.plotly_chart(charts.gauge_target(m["人均"], float(target_per_capita), t, height=320),
                        use_container_width=True, key="gauge")
with d5:
    with card(st, "月度消费额与环比", "柱状图 + 环比折线"):
        st.plotly_chart(charts.line_growth(df_linked, t, height=320),
                        use_container_width=True, key="growth")

d6, d7 = st.columns([1.6, 1])
with d6:
    with card(st, "月度 × 消费类型 堆叠分析", "多维度交叉分析"):
        st.plotly_chart(charts.stacked_month_type(df_linked, t, height=320),
                        use_container_width=True, key="stacked")
with d7:
    with card(st, "校区消费占比", "环形图展示校区结构"):
        st.plotly_chart(charts.donut_campus(df_linked, t, height=320),
                        use_container_width=True, key="donut_campus")

# ================================================================== ④ 明细数据区
st.markdown(section_title("④ 明细数据区 · 明细查询与数据导出"), unsafe_allow_html=True)

if selected_college:
    st.markdown(
        f'<div class="dash-card" style="padding:8px 14px;margin-bottom:8px;">'
        f'🔗 已联动下钻至 <b style="color:{t["accent"]}">{selected_college}</b>'
        f'　（明细表与部分图表已同步过滤）</div>', unsafe_allow_html=True,
    )
    if st.button("❌ 取消下钻"):
        st.session_state.pop("selected_college", None)
        st.rerun()

show_cols = ["订单号", "学号", "姓名", "学院", "年级", "校区",
             "消费时间", "消费类型", "消费场景", "消费金额", "支付方式",
             "星期名称", "时段"]
detail = df_linked[show_cols].sort_values("消费时间", ascending=False)

left, right = st.columns([3.4, 1])
with left:
    with card(st, f"消费流水明细（共 {len(detail):,} 条）", "支持列排序、滚动查看，扩展5：数据钻取"):
        top_n = st.slider("显示条数", 10, min(1000, max(len(detail), 10)),
                          min(200, max(len(detail), 10)), step=10, key="topn")
        st.dataframe(
            detail.head(top_n),
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={
                "消费金额": st.column_config.NumberColumn("消费金额", format="¥%.2f"),
                "消费时间": st.column_config.DatetimeColumn("消费时间", format="YYYY-MM-DD HH:mm:ss"),
            },
        )
with right:
    with card(st, "数据导出与分析报告", "扩展4：一键导出 CSV / Excel / 分析报告"):
        csv_bytes = detail.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ 导出 CSV", csv_bytes, "campus_card_detail.csv",
                           "text/csv", use_container_width=True)

        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
            detail.to_excel(writer, index=False, sheet_name="消费明细")
        st.download_button("⬇️ 导出 Excel", excel_buf.getvalue(),
                           "campus_card_detail.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

        report = f"""# 校园一卡通消费数据分析报告

生成时间：{now_str}
统计范围：{MIN_DATE} ~ {MAX_DATE}（当前筛选 {m['天数']} 天）

## 一、核心指标
- 消费总额：{m['总额']:,.2f} 元
- 消费笔数：{m['笔数']:,} 笔
- 活跃人数：{m['人数']:,} 人
- 人均消费：{m['人均']:,.2f} 元
- 日均消费：{m['日均']:,.2f} 元
- 区间环比：{m['环比']:+.2f}%
- 大额单笔（>50元）占比：{m['大单占比']:.2f}%

## 二、结构分析
{df_linked.groupby('消费类型')['消费金额'].agg(['count', 'sum']).rename(columns={'count': '笔数', 'sum': '金额'}).to_string()}

## 三、场景 TOP5
{df_linked.groupby('消费场景')['消费金额'].sum().sort_values(ascending=False).head(5).to_string()}

## 四、学院 TOP5
{df_linked.groupby('学院')['消费金额'].sum().sort_values(ascending=False).head(5).to_string()}

## 五、预警结论
{'；'.join(warns) if warns else '全部核心指标处于阈值范围内，运行正常。'}
"""
        st.download_button("⬇️ 导出分析报告 (Markdown)", report.encode("utf-8"),
                           "campus_card_report.md", "text/markdown",
                           use_container_width=True)

# ------------------------------------------------------------------ 页脚
st.markdown(
    f'<div style="text-align:center;color:{t["subtext"]};font-size:12px;margin-top:18px;">'
    f"实验2 数据看板的设计与实现 ｜ Streamlit + Pandas + Plotly ｜ 数据源：校园一卡通消费流水（模拟）</div>",
    unsafe_allow_html=True,
)
