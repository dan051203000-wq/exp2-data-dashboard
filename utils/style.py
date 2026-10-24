# -*- coding: utf-8 -*-
"""看板视觉样式：配色方案、科技风背景、卡片动画、响应式与大屏适配。"""

from __future__ import annotations

# ------------------------------------------------------------------ 配色方案
# 主色（科技蓝）、辅助色（紫/青/金）、强调色、背景色
THEMES = {
    "暗色科技风": {
        "bg": "#060b18",
        "panel": "rgba(16, 26, 48, 0.72)",
        "panel_solid": "#101a30",
        "border": "rgba(0, 229, 255, 0.22)",
        "text": "#e8f1ff",
        "subtext": "#8fa6c8",
        "accent": "#00e5ff",
        "accent2": "#7c4dff",
        "warn": "#ff5252",
        "ok": "#00e676",
        "plot_template": "plotly_dark",
        "glow_g1": "#123a5c",
        "glow_g2": "#2b1b5e",
        "grid_alpha": 0.035,
        "palette": ["#00e5ff", "#7c4dff", "#00e676", "#ffc400",
                    "#ff5252", "#40c4ff", "#ff4081", "#b2ff59"],
    },
    "亮色简约风": {
        "bg": "#f4f7fb",
        "panel": "rgba(255, 255, 255, 0.92)",
        "panel_solid": "#ffffff",
        "border": "rgba(46, 124, 246, 0.20)",
        "text": "#12233f",
        "subtext": "#5a6b85",
        "accent": "#2e7cf6",
        "accent2": "#7c4dff",
        "warn": "#e02020",
        "ok": "#00a870",
        "plot_template": "plotly_white",
        "glow_g1": "#dbe8ff",
        "glow_g2": "#e8ddff",
        "grid_alpha": 0.0,
        "palette": ["#2e7cf6", "#7c4dff", "#00b894", "#f5a623",
                    "#eb4d5c", "#00b8d9", "#f06292", "#66bb6a"],
    },
}


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["暗色科技风"])


# ------------------------------------------------------------------ 全局 CSS
def build_css(t: dict) -> str:
    return f"""
<style>
/* ===== 背景：科技风渐变 + 网格底纹 ===== */
[data-testid="stAppViewContainer"] {{
    background:
        radial-gradient(1200px 620px at 12% -12%, {t['glow_g1']} 0%, transparent 62%),
        radial-gradient(980px 520px at 100% 0%, {t['glow_g2']} 0%, transparent 58%),
        {t['bg']};
}}
[data-testid="stAppViewContainer"]::before {{
    content: "";
    position: absolute; inset: 0; pointer-events: none;
    background-image:
        linear-gradient(rgba(255,255,255,{t['grid_alpha']}) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,{t['grid_alpha']}) 1px, transparent 1px);
    background-size: 42px 42px;
}}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.1rem; padding-bottom: 1.6rem; max-width: 1900px; }}

/* ===== 标题栏 ===== */
.dash-title {{
    display:flex; align-items:center; justify-content:space-between;
    gap:16px; flex-wrap:wrap;
    padding: 14px 20px; margin-bottom: 14px;
    border: 1px solid {t['border']};
    border-radius: 14px;
    background: {t['panel']};
    backdrop-filter: blur(8px);
    animation: fadeInUp .5s ease both;
}}
.dash-title h1 {{
    margin:0; font-size: 26px; letter-spacing:1px; font-weight:700;
    color:{t['text']};
    background: linear-gradient(90deg, {t['accent']}, {t['accent2']});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.dash-title .sub {{ color:{t['subtext']}; font-size:13px; margin-top:4px; }}
.live-dot {{
    display:inline-block; width:9px; height:9px; border-radius:50%;
    background:{t['ok']}; margin-right:6px;
    box-shadow: 0 0 0 0 {t['ok']};
    animation: pulse 1.6s infinite;
}}
@keyframes pulse {{
    0% {{ box-shadow: 0 0 0 0 rgba(0,230,118,.7); }}
    70% {{ box-shadow: 0 0 0 10px rgba(0,230,118,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(0,230,118,0); }}
}}

/* ===== 卡片容器：样式直接作用在图表/表格元素上，不依赖 Streamlit 内部 DOM ===== */
div[data-testid="stPlotlyChart"],
div[data-testid="stVegaLiteChart"],
div[data-testid="stDataFrame"] {{
    border: 1px solid {t['border']} !important;
    border-radius: 14px !important;
    background: {t['panel']} !important;
    backdrop-filter: blur(6px);
    padding: 8px 8px 4px 8px !important;
    animation: fadeInUp .55s ease both;
    transition: transform .25s ease, box-shadow .25s ease;
}}
div[data-testid="stPlotlyChart"]:hover,
div[data-testid="stDataFrame"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 26px rgba(0,0,0,.24);
}}
.card-title {{
    font-size:14px; font-weight:600; color:{t['text']};
    margin:0 0 2px 0; letter-spacing:.5px;
}}
.card-hint {{ font-size:11px; color:{t['subtext']}; margin:0 0 8px 0; }}
/* 卡片标题行 */
.card-head {{
    display:flex; align-items:baseline; gap:10px; flex-wrap:wrap;
    margin: 4px 0 2px 4px;
    animation: fadeInUp .4s ease both;
}}
.card-head .t {{
    font-size:14px; font-weight:700; color:{t['text']}; letter-spacing:.5px;
}}
.card-head .t::before {{
    content:""; display:inline-block; width:4px; height:14px;
    border-radius:2px; margin-right:8px; vertical-align:-1px;
    background: linear-gradient(180deg, {t['accent']}, {t['accent2']});
}}
.card-head .h {{ font-size:11px; color:{t['subtext']}; }}
.section-tag {{
    display:inline-block; padding:2px 10px; border-radius:20px;
    font-size:12px; font-weight:600; margin: 10px 0 8px 0;
    color:{t['accent']}; border:1px solid {t['border']};
    background: rgba(0,229,255,.08);
}}
@keyframes fadeInUp {{
    from {{ opacity:0; transform: translateY(16px); }}
    to   {{ opacity:1; transform: none; }}
}}

/* ===== KPI 数值卡片 ===== */
.kpi {{
    position:relative; overflow:hidden;
    border:1px solid {t['border']}; border-radius:14px;
    padding:14px 16px; background:{t['panel']};
    backdrop-filter: blur(6px);
    animation: fadeInUp .5s ease both;
}}
.kpi .label {{ font-size:12px; color:{t['subtext']}; letter-spacing:.5px; }}
.kpi .value {{
    font-size:30px; font-weight:800; line-height:1.25;
    color:{t['text']}; font-variant-numeric: tabular-nums;
}}
.kpi .unit {{ font-size:13px; font-weight:600; color:{t['subtext']}; margin-left:3px; }}
.kpi .delta {{ font-size:12px; font-weight:600; margin-top:2px; }}
.up   {{ color: {t['warn']}; }}    /* 国内习惯：上升=红 */
.down {{ color: {t['ok']}; }}      /* 下降=绿 */
.kpi::after {{
    content:""; position:absolute; right:-30px; top:-30px;
    width:90px; height:90px; border-radius:50%;
    background: radial-gradient(circle, {t['accent']}33, transparent 70%);
}}
.kpi.warn {{
    border-color:{t['warn']} !important;
    animation: warnBlink 1.5s infinite;
}}
@keyframes warnBlink {{
    0%,100% {{ box-shadow: 0 0 0 rgba(255,82,82,0); }}
    50%     {{ box-shadow: 0 0 18px rgba(255,82,82,.75); }}
}}

/* ===== 预警提示条 ===== */
.alert-bar {{
    border:1px solid {t['warn']}; border-radius:12px;
    padding:10px 14px; margin:6px 0 12px 0;
    background: rgba(255,82,82,.10);
    color:{t['text']}; font-size:13px; font-weight:600;
    animation: warnBlink 1.5s infinite;
}}

/* ===== 表格 ===== */
[data-testid="stDataFrame"] {{ border-radius: 12px; overflow:hidden; }}

/* ===== 大屏适配（超宽屏放大字号） ===== */
@media (min-width: 1920px) {{
    .kpi .value {{ font-size: 36px; }}
    .dash-title h1 {{ font-size: 32px; }}
}}

/* ===== 移动端适配（窄屏纵向堆叠） ===== */
@media (max-width: 900px) {{
    [data-testid="stHorizontalBlock"] {{ flex-direction: column !important; }}
    [data-testid="stHorizontalBlock"] > div {{ min-width: 100% !important; }}
    .kpi .value {{ font-size: 24px; }}
    .dash-title h1 {{ font-size: 20px; }}
    .block-container {{ padding-left: .8rem; padding-right: .8rem; }}
}}
</style>
"""


def render_css(t: dict) -> None:
    import streamlit as st

    st.markdown(build_css(t), unsafe_allow_html=True)


# ------------------------------------------------------------------ 组件片段
def kpi_html(label: str, value: str, unit: str = "", delta: str = "",
             delta_dir: str = "flat", warn: bool = False) -> str:
    """生成一张 KPI 数值卡片（HTML 片段）。"""
    cls = {"up": "up", "down": "down"}.get(delta_dir, "")
    delta_html = f'<div class="delta {cls}">{delta}</div>' if delta else ""
    return (
        f'<div class="kpi{" warn" if warn else ""}">'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}<span class="unit">{unit}</span></div>'
        f"{delta_html}</div>"
    )


def section_title(text: str) -> str:
    return f'<div class="section-tag">{text}</div>'


def card(st, title: str, hint: str = ""):
    """
    卡片：标题行（.card-head）+ 内容区。

    内容区（图表 / 表格）的外观由 CSS 直接作用在其元素上，
    不依赖 Streamlit 内部 DOM 结构，升级 Streamlit 版本也不会失效。
    """
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        hint_html = f'<span class="h">{hint}</span>' if hint else ""
        st.markdown(f'<div class="card-head"><span class="t">{title}</span>{hint_html}</div>',
                    unsafe_allow_html=True)
        with st.container():
            yield

    return _ctx()


def card_open(title: str, hint: str = "") -> str:
    hint_html = f'<p class="card-hint">{hint}</p>' if hint else ""
    return (
        '<div class="dash-card">'
        f'<p class="card-title">{title}</p>{hint_html}'
    )


CARD_CLOSE = "</div>"
