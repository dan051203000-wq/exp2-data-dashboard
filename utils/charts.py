# -*- coding: utf-8 -*-
"""看板图表组件：封装全部 Plotly 图形，统一配色、字体与交互行为。"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

FONT = "Microsoft YaHei, SimHei, PingFang SC, sans-serif"


def apply_theme(fig, t: dict, height: int = 320, legend_top: bool = True):
    """统一图表外观。"""
    fig.update_layout(
        template=t["plot_template"],
        height=height,
        font=dict(family=FONT, size=12, color=t["text"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=12, t=30, b=10),
        hoverlabel=dict(
            bgcolor=t["panel_solid"], bordercolor=t["border"],
            font=dict(family=FONT, size=12, color=t["text"]),
        ),
        legend=dict(
            orientation="h",
            y=1.14 if legend_top else -0.18,
            x=0,
            font=dict(size=11, color=t["subtext"]),
        ),
        xaxis=dict(gridcolor="rgba(128,128,128,.22)", zeroline=False,
                   linecolor="rgba(128,128,128,.35)"),
        yaxis=dict(gridcolor="rgba(128,128,128,.22)", zeroline=False,
                   linecolor="rgba(128,128,128,.35)"),
    )
    return fig


# ------------------------------------------------------------------ 分类对比
def bar_college(df: pd.DataFrame, t: dict, highlight: str | None = None, height: int = 330):
    """各学院消费总额对比（柱状图，支持点击联动高亮）。"""
    g = (df.groupby("学院")
           .agg(消费总额=("消费金额", "sum"), 消费笔数=("订单号", "count"),
                人均消费=("消费金额", "mean"))
           .reset_index())
    g["人均消费"] = (df.groupby("学院").apply(
        lambda x: x["消费金额"].sum() / x["学号"].nunique(), include_groups=False
    ).values.round(2))
    g = g.sort_values("消费总额", ascending=False)

    colors = []
    palette = t["palette"]
    for c in g["学院"]:
        if highlight and c == highlight:
            colors.append(t["warn"])
        else:
            colors.append(palette[len(colors) % len(palette)])

    fig = go.Figure(
        go.Bar(
            x=g["学院"], y=g["消费总额"], name="消费总额",
            marker=dict(color=colors, line=dict(width=0, color=t["accent"]),
                        cornerradius=4),
            customdata=g[["消费笔数", "人均消费"]].values,
            hovertemplate=("<b>%{x}</b><br>消费总额：%{y:,.0f} 元"
                           "<br>消费笔数：%{customdata[0]:,.0f} 笔"
                           "<br>人均消费：%{customdata[1]:,.2f} 元<extra></extra>"),
        )
    )
    fig = apply_theme(fig, t, height)
    fig.update_layout(showlegend=False,
                      yaxis_title="消费总额（元）", xaxis_title=None,
                      clickmode="event+select")
    return fig


def bar_scene_top(df: pd.DataFrame, t: dict, top: int = 8, height: int = 330):
    """消费场景排行榜（横向条形图，从高到低）。"""
    g = (df.groupby("消费场景")["消费金额"].sum()
           .sort_values(ascending=False).head(top).reset_index())
    g = g.sort_values("消费金额", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=g["消费金额"], y=g["消费场景"], orientation="h",
            marker=dict(color=g["消费金额"], colorscale=[
                [0, t["accent"]], [1, t["accent2"]]],
                line=dict(width=0), cornerradius=4),
            text=[f"{v:,.0f}" for v in g["消费金额"]],
            textposition="outside",
            textfont=dict(size=11, color=t["subtext"]),
            hovertemplate="<b>%{y}</b><br>消费总额：%{x:,.0f} 元<extra></extra>",
        )
    )
    fig = apply_theme(fig, t, height)
    fig.update_layout(showlegend=False, xaxis_title="消费总额（元）", yaxis_title=None)
    return fig


def bar_period(df: pd.DataFrame, t: dict, height: int = 300):
    """时段消费分布（柱状图 + 笔数副轴）。"""
    order = ["早餐", "午餐", "下午茶", "晚餐", "夜宵"]
    g = (df.groupby("时段")
           .agg(消费总额=("消费金额", "sum"), 消费笔数=("订单号", "count"))
           .reindex(order).fillna(0).reset_index())
    fig = go.Figure()
    fig.add_bar(x=g["时段"], y=g["消费总额"], name="消费总额",
                marker=dict(color=t["palette"][0], cornerradius=4),
                hovertemplate="%{x}<br>消费总额：%{y:,.0f} 元<extra></extra>")
    fig.add_scatter(x=g["时段"], y=g["消费笔数"], name="消费笔数",
                    yaxis="y2", mode="lines+markers",
                    line=dict(color=t["palette"][3], width=2.5),
                    marker=dict(size=7, color=t["palette"][3]),
                    hovertemplate="%{x}<br>消费笔数：%{y:,.0f} 笔<extra></extra>")
    fig = apply_theme(fig, t, height)
    fig.update_layout(
        yaxis=dict(title="消费总额（元）", gridcolor="rgba(128,128,128,.22)"),
        yaxis2=dict(title=dict(text="笔数", font=dict(size=11, color=t["subtext"])),
                    overlaying="y", side="right", showgrid=False),
        margin=dict(l=10, r=30, t=30, b=10),
    )
    return fig


def bar_pay_method(df: pd.DataFrame, t: dict, height: int = 300):
    """支付方式对比（条形图）。"""
    g = (df.groupby("支付方式")
           .agg(消费总额=("消费金额", "sum"), 占比=("订单号", "count"))
           .reset_index())
    g["占比"] = (g["占比"] / g["占比"].sum() * 100).round(1)
    fig = go.Figure(
        go.Bar(x=g["支付方式"], y=g["消费总额"],
               marker=dict(color=[t["palette"][0], t["palette"][1]], cornerradius=5),
               text=[f"{v:.1f}%" for v in g["占比"]], textposition="outside",
               textfont=dict(size=11, color=t["subtext"]),
               customdata=g["占比"].values,
               hovertemplate="<b>%{x}</b><br>消费总额：%{y:,.0f} 元<br>笔数占比：%{customdata:.1f}%<extra></extra>")
    )
    fig = apply_theme(fig, t, height)
    fig.update_layout(showlegend=False, yaxis_title="消费总额（元）", xaxis_title=None)
    return fig


# ------------------------------------------------------------------ 趋势分析
def line_daily(df: pd.DataFrame, t: dict, height: int = 330):
    """每日消费趋势（面积图 + 7 日移动平均线）。"""
    g = (df.groupby("日期")
           .agg(消费总额=("消费金额", "sum"), 消费笔数=("订单号", "count"))
           .reset_index())
    g["日期"] = pd.to_datetime(g["日期"])
    g["7日均线"] = g["消费总额"].rolling(7, min_periods=1).mean().round(2)

    fig = go.Figure()
    fig.add_scatter(x=g["日期"], y=g["消费总额"], name="当日消费额",
                    mode="lines", fill="tozeroy",
                    line=dict(color=t["accent"], width=1.6),
                    fillcolor="rgba(0,229,255,.16)" if t["accent"] == "#00e5ff" else "rgba(46,124,246,.16)",
                    hovertemplate="%{x|%Y-%m-%d}<br>当日消费额：%{y:,.0f} 元<extra></extra>")
    fig.add_scatter(x=g["日期"], y=g["7日均线"], name="7日移动平均",
                    mode="lines", line=dict(color=t["palette"][3], width=2.4, dash="dot"),
                    hovertemplate="%{x|%Y-%m-%d}<br>7日均线：%{y:,.0f} 元<extra></extra>")
    fig = apply_theme(fig, t, height)
    fig.update_layout(yaxis_title="消费总额（元）", xaxis_title=None,
                      hovermode="x unified")
    return fig


def stacked_month_type(df: pd.DataFrame, t: dict, height: int = 300):
    """月度 × 消费类型堆叠柱状图。"""
    g = df.groupby(["月份", "消费类型"])["消费金额"].sum().reset_index()
    fig = px.bar(g, x="月份", y="消费金额", color="消费类型",
                 color_discrete_sequence=t["palette"], barmode="stack")
    fig = apply_theme(fig, t, height)
    fig.update_traces(marker_line_width=0,
                      hovertemplate="%{fullData.name}｜%{x}<br>消费额：%{y:,.0f} 元<extra></extra>")
    fig.update_layout(yaxis_title="消费总额（元）", xaxis_title=None)
    return fig


def heatmap_week_hour(df: pd.DataFrame, t: dict, height: int = 330):
    """星期 × 小时消费热力图。"""
    order = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    pivot = (df.pivot_table(index="星期名称", columns="小时", values="消费金额",
                            aggfunc="sum", fill_value=0)
               .reindex(order).fillna(0))
    fig = px.imshow(
        pivot.values,
        x=[f"{h}时" for h in pivot.columns],
        y=pivot.index.tolist(),
        color_continuous_scale=[[0, t["panel_solid"]], [0.35, t["palette"][0]],
                                [0.7, t["palette"][3]], [1, t["warn"]]],
        aspect="auto",
    )
    fig = apply_theme(fig, t, height)
    fig.update_traces(
        hovertemplate="%{y} %{x}<br>消费总额：%{z:,.0f} 元<extra></extra>",
        colorbar=dict(thickness=10, len=0.85,
                      title=dict(text="元", side="right", font=dict(size=11, color=t["subtext"]))),
    )
    fig.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(l=6, r=6, t=24, b=6))
    return fig


# ------------------------------------------------------------------ 占比结构
def donut_category(df: pd.DataFrame, t: dict, height: int = 330):
    """消费类型占比（环形图）。"""
    g = df.groupby("消费类型")["消费金额"].sum().reset_index()
    fig = px.pie(g, names="消费类型", values="消费金额", hole=0.58,
                 color_discrete_sequence=t["palette"])
    fig = apply_theme(fig, t, height)
    fig.update_traces(
        textinfo="percent+label", textposition="outside",
        textfont=dict(size=12, color=t["text"]),
        marker=dict(line=dict(color=t["panel_solid"], width=2)),
        hovertemplate="<b>%{label}</b><br>消费额：%{value:,.0f} 元<br>占比：%{percent}<extra></extra>",
    )
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=24, b=10))
    return fig


def donut_campus(df: pd.DataFrame, t: dict, height: int = 300):
    """校区消费占比（环形图）。"""
    g = df.groupby("校区")["消费金额"].sum().reset_index()
    fig = px.pie(g, names="校区", values="消费金额", hole=0.62,
                 color_discrete_sequence=t["palette"][2:])
    fig = apply_theme(fig, t, height)
    fig.update_traces(
        textinfo="percent+label", textposition="inside",
        textfont=dict(size=12, color="#ffffff"),
        marker=dict(line=dict(color=t["panel_solid"], width=2)),
        hovertemplate="<b>%{label}</b><br>消费额：%{value:,.0f} 元<br>占比：%{percent}<extra></extra>",
    )
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=24, b=10))
    return fig


# ------------------------------------------------------------------ 高级组件
def radar_college(df: pd.DataFrame, t: dict, college: str, height: int = 340):
    """雷达图：指定学院 vs 全校平均（各消费类型人均消费，归一化到 0-100）。"""
    def per_capita(d: pd.DataFrame) -> pd.Series:
        return d.groupby("消费类型").apply(
            lambda x: x["消费金额"].sum() / max(x["学号"].nunique(), 1),
            include_groups=False,
        )

    all_mean = per_capita(df)
    sub = df[df["学院"] == college] if college else df
    cur = per_capita(sub) if len(sub) else all_mean * 0

    cats = all_mean.index.tolist()
    base = max(all_mean.max(), cur.max(), 1)
    r_all = (all_mean.reindex(cats).fillna(0) / base * 100).round(1)
    r_cur = (cur.reindex(cats).fillna(0) / base * 100).round(1)

    fig = go.Figure()
    fig.add_scatterpolar(r=r_all.tolist() + [r_all.iloc[0]], theta=cats + [cats[0]],
                         name="全校平均", fill="toself",
                         line=dict(color=t["subtext"], width=1.6),
                         fillcolor="rgba(128,128,128,.18)")
    fig.add_scatterpolar(r=r_cur.tolist() + [r_cur.iloc[0]], theta=cats + [cats[0]],
                         name=college or "当前筛选", fill="toself",
                         line=dict(color=t["accent"], width=2.4),
                         fillcolor="rgba(0,229,255,.22)" if t["accent"] == "#00e5ff" else "rgba(46,124,246,.22)")
    fig.update_layout(
        template=t["plot_template"], height=height,
        font=dict(family=FONT, size=12, color=t["text"]),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor="rgba(128,128,128,.25)",
                            tickfont=dict(size=10, color=t["subtext"])),
            angularaxis=dict(gridcolor="rgba(128,128,128,.25)",
                             tickfont=dict(size=11, color=t["text"])),
        ),
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center",
                    font=dict(size=11, color=t["subtext"])),
        margin=dict(l=20, r=20, t=26, b=20),
        hoverlabel=dict(bgcolor=t["panel_solid"], bordercolor=t["border"],
                        font=dict(family=FONT, size=12, color=t["text"])),
    )
    return fig


def gauge_target(value: float, target: float, t: dict, height: int = 300,
                 title: str = "人均消费目标达成率"):
    """进度仪表盘：实际值 / 目标值。"""
    ratio = 0.0 if target <= 0 else value / target * 100
    color = t["ok"] if ratio >= 80 else (t["palette"][3] if ratio >= 60 else t["warn"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(ratio, 1),
        number={"suffix": "%", "font": {"size": 34, "color": t["text"], "family": FONT}},
        delta={"reference": 100, "font": {"size": 13, "color": t["subtext"]},
               "suffix": "%", "valueformat": ".1f"},
        title={"text": f"{title}<br><span style='font-size:12px;color:{t['subtext']}'>"
                       f"实际 {value:,.0f} / 目标 {target:,.0f} 元</span>",
               "font": {"size": 13, "color": t["text"], "family": FONT}},
        gauge={
            "axis": {"range": [0, 150], "tickwidth": 1,
                     "tickcolor": t["subtext"],
                     "tickfont": {"size": 10, "color": t["subtext"]}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 1, "bordercolor": t["border"],
            "steps": [
                {"range": [0, 60], "color": "rgba(255,82,82,.22)"},
                {"range": [60, 80], "color": "rgba(255,196,0,.22)"},
                {"range": [80, 150], "color": "rgba(0,230,118,.22)"},
            ],
            "threshold": {"line": {"color": t["accent"], "width": 3},
                          "thickness": 0.8, "value": 100},
        },
    ))
    fig.update_layout(template=t["plot_template"], height=height,
                      paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=FONT, color=t["text"]),
                      margin=dict(l=18, r=18, t=20, b=10))
    return fig


def line_growth(df: pd.DataFrame, t: dict, height: int = 300):
    """月度消费额与环比增长率（柱 + 折线组合）。"""
    g = df.groupby("月份")["消费金额"].sum().reset_index()
    g["环比"] = (g["消费金额"].pct_change() * 100).round(2)
    fig = go.Figure()
    fig.add_bar(x=g["月份"], y=g["消费金额"], name="月度消费额",
                marker=dict(color=t["palette"][0], cornerradius=4),
                hovertemplate="%{x}<br>消费额：%{y:,.0f} 元<extra></extra>")
    fig.add_scatter(x=g["月份"], y=g["环比"], name="环比增长率", yaxis="y2",
                    mode="lines+markers+text",
                    text=[f"{v:.1f}%" if pd.notna(v) else "" for v in g["环比"]],
                    textposition="top center", textfont=dict(size=10, color=t["subtext"]),
                    line=dict(color=t["palette"][3], width=2.2),
                    marker=dict(size=7, color=t["palette"][3]),
                    hovertemplate="%{x}<br>环比：%{y:.2f}%<extra></extra>")
    fig = apply_theme(fig, t, height)
    fig.update_layout(
        yaxis=dict(title="消费额（元）", gridcolor="rgba(128,128,128,.22)"),
        yaxis2=dict(title=dict(text="环比 %", font=dict(size=11, color=t["subtext"])),
                    overlaying="y", side="right", showgrid=False, ticksuffix="%"),
        margin=dict(l=10, r=30, t=30, b=10),
    )
    return fig
