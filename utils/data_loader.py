# -*- coding: utf-8 -*-
"""数据读取、时间维度派生与实时数据源模拟。"""

from __future__ import annotations

import os
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_PATH = os.path.join(BASE_DIR, "data", "clean_campus_card_data.csv")

PERIOD_RULE = [(6, 10, "早餐"), (10, 14, "午餐"), (14, 16, "下午茶"),
               (16, 20, "晚餐"), (20, 24, "夜宵")]
WEEK_MAP = {"Mon": "周一", "Tue": "周二", "Wed": "周三", "Thu": "周四",
            "Fri": "周五", "Sat": "周六", "Sun": "周日"}


def derive_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """补派生时间维度列（新增数据后需要重新派生）。"""
    df = df.copy()
    df["消费时间"] = pd.to_datetime(df["消费时间"])
    df["日期"] = df["消费时间"].dt.date
    df["小时"] = df["消费时间"].dt.hour
    df["星期"] = df["消费时间"].dt.day_of_week
    df["星期名称"] = df["消费时间"].dt.strftime("%a").map(WEEK_MAP)
    df["月份"] = df["消费时间"].dt.to_period("M").astype(str)
    df["是否周末"] = df["星期"] >= 5

    def to_period(h: int) -> str:
        for start, end, name in PERIOD_RULE:
            if start <= h < end:
                return name
        return "其他"

    df["时段"] = df["小时"].apply(to_period)
    return df


@st.cache_data(show_spinner="正在加载清洗后的消费数据…")
def load_clean_data() -> pd.DataFrame:
    """读取预处理后的干净数据。"""
    df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig")
    return derive_time_features(df)


def simulate_live_records(base: pd.DataFrame, n: int, now: datetime | None = None) -> pd.DataFrame:
    """
    扩展1：模拟实时交易流水（替代静态本地数据，实现真正的数据源接入）。

    以真实历史记录为模板，按当前时刻生成 n 条新流水，字段结构与清洗后数据一致。
    真实工程场景下，此处可替换为接口请求 / 数据库增量查询。
    """
    now = now or datetime.now()
    rng = np.random.default_rng(int(now.timestamp()))
    sample = base.sample(n, random_state=int(now.timestamp()) % 100000).copy()
    sample["订单号"] = [f"LIVE{int(now.timestamp() * 1000)}{i}" for i in range(n)]
    sample["消费时间"] = now
    sample["消费金额"] = np.round(
        np.clip(rng.normal(base["消费金额"].mean(), base["消费金额"].std() / 2, n), 1, 120), 2
    )
    sample["支付方式"] = rng.choice(["一卡通刷卡", "扫码支付"], n, p=[0.62, 0.38])
    return derive_time_features(sample)
