# -*- coding: utf-8 -*-
"""图表自测：在本地逐个构建全部 Plotly 图形，快速暴露属性兼容问题。"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import charts                       # noqa: E402
from utils.style import THEMES                 # noqa: E402

CLEAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "clean_campus_card_data.csv")


def main():
    df = pd.read_csv(CLEAN, encoding="utf-8-sig")
    df["消费时间"] = pd.to_datetime(df["消费时间"])
    df["日期"] = df["消费时间"].dt.date
    df["小时"] = df["消费时间"].dt.hour
    df["星期名称"] = df["消费时间"].dt.strftime("%a").map(
        {"Mon": "周一", "Tue": "周二", "Wed": "周三", "Thu": "周四",
         "Fri": "周五", "Sat": "周六", "Sun": "周日"})
    df["月份"] = df["消费时间"].dt.to_period("M").astype(str)
    df["时段"] = "午餐"

    cases = [
        ("bar_college", lambda t: charts.bar_college(df, t, highlight="计算机学院")),
        ("bar_scene_top", lambda t: charts.bar_scene_top(df, t)),
        ("bar_period", lambda t: charts.bar_period(df, t)),
        ("bar_pay_method", lambda t: charts.bar_pay_method(df, t)),
        ("line_daily", lambda t: charts.line_daily(df, t)),
        ("stacked_month_type", lambda t: charts.stacked_month_type(df, t)),
        ("heatmap_week_hour", lambda t: charts.heatmap_week_hour(df, t)),
        ("donut_category", lambda t: charts.donut_category(df, t)),
        ("donut_campus", lambda t: charts.donut_campus(df, t)),
        ("radar_college", lambda t: charts.radar_college(df, t, "计算机学院")),
        ("gauge_target", lambda t: charts.gauge_target(214.0, 250.0, t)),
        ("line_growth", lambda t: charts.line_growth(df, t)),
    ]

    ok = fail = 0
    for theme_name, theme in THEMES.items():
        for name, fn in cases:
            try:
                fig = fn(theme)
                json_len = len(fig.to_json())
                ok += 1
                print(f"  ✔ [{theme_name}] {name:22s} json={json_len}")
            except Exception as e:
                fail += 1
                print(f"  ✘ [{theme_name}] {name:22s} {type(e).__name__}: "
                      f"{str(e).splitlines()[0][:160]}")
    print(f"\n通过 {ok} / 失败 {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
