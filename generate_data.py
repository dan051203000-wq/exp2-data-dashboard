# -*- coding: utf-8 -*-
"""
任务2（数据准备）：生成"校园一卡通消费"模拟数据集。

为了完整演示"数据预处理"环节，原始数据被人为注入了以下几类脏数据：
    1. 重复记录（同一订单号重复上传）
    2. 缺失值（学号为空 / 消费金额为空 / 学院为空）
    3. 异常值（金额为 0 或负数、单笔金额远超一卡通 300 元限额）
    4. 时间异常（学期外日期、凌晨 2-5 点的消费记录）
    5. 格式异常（学号位数不合法）

运行：
    python generate_data.py
输出：
    data/raw_campus_card_data.csv
"""

import os

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- 基础配置
SEED = 20250901          # 固定随机种子，保证数据可复现
N_STUDENTS = 420         # 学生人数
N_RECORDS = 6000         # 有效消费记录条数
TERM_START = "2025-09-01"
TERM_END = "2025-12-31"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

rng = np.random.default_rng(SEED)

COLLEGES = [
    "计算机学院", "电子信息学院", "机械工程学院", "经济管理学院",
    "外国语学院", "艺术设计学院", "医学院", "土木工程学院",
]
GRADES = ["2022级", "2023级", "2024级", "2025级"]
CAMPUSES = ["中心校区", "东校区", "新校区"]
GENDERS = ["男", "女"]
PAY_METHODS = ["一卡通刷卡", "扫码支付"]

# 消费类型 -> 具体消费场景
SCENE_MAP = {
    "餐饮": ["一食堂", "二食堂", "三食堂", "教工餐厅", "清真餐厅"],
    "购物": ["校园超市", "文具店", "水果店"],
    "学习": ["图书馆打印", "自习室预约", "教材中心"],
    "医疗": ["校医院"],
    "生活服务": ["开水房", "公共浴室", "洗衣房"],
}

# 消费类型 -> 金额分布（正态 + 裁剪）
AMOUNT_RULE = {
    "餐饮": (14.0, 6.0, 3.0, 45.0),
    "购物": (28.0, 18.0, 3.0, 120.0),
    "学习": (6.0, 4.0, 0.5, 30.0),
    "医疗": (45.0, 30.0, 5.0, 260.0),
    "生活服务": (5.0, 3.0, 1.0, 20.0),
}

# 时段 -> 消费类型权重（模拟真实校园消费习惯）
HOUR_CATEGORY_WEIGHT = {
    #  hour: [餐饮, 购物, 学习, 医疗, 生活服务]
    6:  [0.80, 0.10, 0.02, 0.00, 0.08],
    7:  [0.82, 0.08, 0.04, 0.01, 0.05],
    8:  [0.75, 0.10, 0.10, 0.01, 0.04],
    9:  [0.45, 0.15, 0.32, 0.04, 0.04],
    10: [0.35, 0.20, 0.35, 0.05, 0.05],
    11: [0.80, 0.10, 0.06, 0.02, 0.02],
    12: [0.86, 0.07, 0.04, 0.01, 0.02],
    13: [0.70, 0.15, 0.12, 0.01, 0.02],
    14: [0.35, 0.22, 0.35, 0.04, 0.04],
    15: [0.30, 0.28, 0.34, 0.04, 0.04],
    16: [0.35, 0.25, 0.32, 0.04, 0.04],
    17: [0.78, 0.12, 0.05, 0.02, 0.03],
    18: [0.80, 0.09, 0.05, 0.01, 0.05],
    19: [0.62, 0.18, 0.12, 0.01, 0.07],
    20: [0.40, 0.25, 0.20, 0.02, 0.13],
    21: [0.30, 0.24, 0.20, 0.01, 0.25],
    22: [0.25, 0.22, 0.15, 0.01, 0.37],
}
HOURS = list(HOUR_CATEGORY_WEIGHT.keys())
CATEGORIES = list(SCENE_MAP.keys())
HOUR_WEIGHT = np.array([6, 8, 7, 4, 4, 12, 14, 7, 4, 4, 5, 11, 13, 9, 6, 5, 3], dtype=float)
HOUR_WEIGHT = HOUR_WEIGHT / HOUR_WEIGHT.sum()

SURNAMES = list("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾")
GIVEN_CHARS = list(
    "伟芳娜秀敏静丽强磊洋艳勇军杰娟涛明超秀霞平刚桂英华文玉梅红萍鹏辉建华"
    "晨曦雨泽子轩浩然梓涵欣怡思远嘉禾若曦博文宇宁"
)


def _make_students() -> pd.DataFrame:
    """生成学生基础信息表。"""
    surnames = rng.choice(SURNAMES, N_STUDENTS)
    given = ["".join(rng.choice(GIVEN_CHARS, 2)) for _ in range(N_STUDENTS)]
    grade_year = rng.choice(["2022", "2023", "2024", "2025"], N_STUDENTS, p=[0.24, 0.26, 0.25, 0.25])
    return pd.DataFrame({
        "学号": [f"{y}{rng.integers(100000, 999999)}" for y in grade_year],
        "姓名": [s + g for s, g in zip(surnames, given)],
        "学院": rng.choice(COLLEGES, N_STUDENTS),
        "年级": [y + "级" for y in grade_year],
        "性别": rng.choice(GENDERS, N_STUDENTS, p=[0.52, 0.48]),
        "校区": rng.choice(CAMPUSES, N_STUDENTS, p=[0.45, 0.30, 0.25]),
    })


def _make_records(students: pd.DataFrame) -> pd.DataFrame:
    """生成消费流水。"""
    # --- 日期：学期内 122 天，周末消费活跃度略低
    dates = pd.date_range(TERM_START, TERM_END, freq="D")
    day_weight = np.where(dates.day_of_week.values >= 5, 0.7, 1.0)
    day_weight = day_weight / day_weight.sum()
    rec_date = pd.to_datetime(rng.choice(dates.values, N_RECORDS, p=day_weight))

    rec_hour = rng.choice(HOURS, N_RECORDS, p=HOUR_WEIGHT)
    rec_min = rng.integers(0, 60, N_RECORDS)
    rec_sec = rng.integers(0, 60, N_RECORDS)
    consume_time = pd.to_datetime({
        "year": rec_date.year,
        "month": rec_date.month,
        "day": rec_date.day,
        "hour": rec_hour,
        "minute": rec_min,
        "second": rec_sec,
    })

    # --- 按小时权重抽取消费类型
    cat_idx = np.empty(N_RECORDS, dtype=int)
    for h, w in HOUR_CATEGORY_WEIGHT.items():
        mask = rec_hour == h
        if mask.any():
            cat_idx[mask] = rng.choice(len(CATEGORIES), mask.sum(), p=np.array(w) / sum(w))
    category = np.array(CATEGORIES)[cat_idx]

    # --- 按类型生成金额
    amount = np.empty(N_RECORDS)
    for i, c in enumerate(CATEGORIES):
        mu, sigma, low, high = AMOUNT_RULE[c]
        mask = category == c
        amount[mask] = np.clip(rng.normal(mu, sigma, mask.sum()), low, high)
    amount = np.round(amount, 2)

    # --- 场景 & 支付方式
    scene = np.array([rng.choice(SCENE_MAP[c]) for c in category])
    pay = rng.choice(PAY_METHODS, N_RECORDS, p=[0.62, 0.38])

    # --- 关联学生
    stu_idx = rng.integers(0, len(students), N_RECORDS)
    stu = students.iloc[stu_idx].reset_index(drop=True)

    df = pd.DataFrame({
        "订单号": [f"YKT{20250901000000 + i}" for i in range(N_RECORDS)],
        "学号": stu["学号"].values,
        "姓名": stu["姓名"].values,
        "学院": stu["学院"].values,
        "年级": stu["年级"].values,
        "校区": stu["校区"].values,
        "消费时间": consume_time,
        "消费类型": category,
        "消费场景": scene,
        "消费金额": amount,
        "支付方式": pay,
    })
    return df


def inject_dirty_data(df: pd.DataFrame) -> pd.DataFrame:
    """人为注入脏数据，模拟真实采集环境。"""
    df = df.copy()
    n = len(df)

    # 1) 重复记录：随机复制 40 条追加到末尾
    dup = df.sample(40, random_state=SEED).copy()
    df = pd.concat([df, dup], ignore_index=True)

    # 2) 缺失值
    df.loc[rng.choice(n, 30, replace=False), "消费金额"] = np.nan          # 金额缺失 30 条
    df.loc[rng.choice(n, 18, replace=False), "学院"] = np.nan              # 学院缺失 18 条
    df.loc[rng.choice(n, 12, replace=False), "学号"] = None                # 学号缺失 12 条
    df.loc[rng.choice(n, 10, replace=False), "姓名"] = None                # 姓名缺失 10 条

    # 3) 异常金额：0 元、负数、以及远超一卡通单笔 300 元限额的大额
    idx_zero = rng.choice(n, 12, replace=False)
    df.loc[idx_zero, "消费金额"] = 0.0
    idx_neg = rng.choice(n, 8, replace=False)
    df.loc[idx_neg, "消费金额"] = -rng.uniform(1, 30, 8).round(2)
    idx_big = rng.choice(n, 15, replace=False)
    df.loc[idx_big, "消费金额"] = rng.uniform(500, 5000, 15).round(2)

    # 4) 时间异常：学期外日期（寒假）
    idx_out = rng.choice(n, 14, replace=False)
    df.loc[idx_out, "消费时间"] = pd.to_datetime("2026-01-20") + pd.to_timedelta(
        rng.integers(0, 18, 14), unit="h"
    )
    # 时间异常：凌晨 2-5 点（非营业时段）
    idx_night = rng.choice(n, 16, replace=False)
    night = df.loc[idx_night, "消费时间"] + pd.to_timedelta(
        -(df.loc[idx_night, "消费时间"].dt.hour.values - rng.integers(2, 5, 16)), unit="h"
    )
    df.loc[idx_night, "消费时间"] = night

    # 5) 学号格式异常
    idx_bad = rng.choice(n, 10, replace=False)
    df.loc[idx_bad, "学号"] = [f"X{rng.integers(100, 999)}" for _ in range(10)]

    return df.sample(frac=1, random_state=SEED).reset_index(drop=True)


def main() -> None:
    students = _make_students()
    records = _make_records(students)
    raw = inject_dirty_data(records)

    out_path = os.path.join(DATA_DIR, "raw_campus_card_data.csv")
    raw.to_csv(out_path, index=False, encoding="utf-8-sig")

    print("=" * 62)
    print("校园一卡通消费模拟数据生成完成")
    print("=" * 62)
    print(f"输出路径 : {out_path}")
    print(f"数据规模 : {raw.shape[0]} 行 × {raw.shape[1]} 列")
    print(f"时间范围 : {raw['消费时间'].min()} ~ {raw['消费时间'].max()}")
    print("\n--- 注入的脏数据统计（供预处理环节对照）---")
    print(f"重复订单号     : {raw['订单号'].duplicated().sum()} 条")
    print(f"消费金额缺失   : {raw['消费金额'].isna().sum()} 条")
    print(f"学院缺失       : {raw['学院'].isna().sum()} 条")
    print(f"学号缺失       : {raw['学号'].isna().sum()} 条")
    print(f"金额 <= 0      : {(raw['消费金额'] <= 0).sum()} 条")
    print(f"金额 > 300     : {(raw['消费金额'] > 300).sum()} 条")
    out_of_term = (raw["消费时间"].dt.date > pd.Timestamp(TERM_END).date()).sum()
    print(f"学期外日期     : {out_of_term} 条")


if __name__ == "__main__":
    main()
