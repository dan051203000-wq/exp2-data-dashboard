# -*- coding: utf-8 -*-
"""
任务2（数据预处理）：对原始一卡通流水做清洗与维度整理。

处理流程：
    1. 去重          —— 按订单号删除重复上传记录
    2. 缺失值处理    —— 关键字段缺失直接剔除；消费金额按"消费类型"中位数填充；
                        学院缺失统一标记为"未登记"
    3. 异常值剔除    —— 金额 <= 0、金额 > 300（一卡通单笔限额）、学期外日期、
                        非营业时段（02:00-05:00）、学号格式不合法
    4. 维度整理      —— 派生日期、小时、星期、时段、月份、是否周末等统计维度
    5. 结果落地      —— data/clean_campus_card_data.csv，可直接供可视化使用

运行：
    python preprocess.py
"""

import os

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_PATH = os.path.join(DATA_DIR, "raw_campus_card_data.csv")
CLEAN_PATH = os.path.join(DATA_DIR, "clean_campus_card_data.csv")

TERM_START = pd.Timestamp("2025-09-01")
TERM_END = pd.Timestamp("2025-12-31 23:59:59")
AMOUNT_LIMIT = 300.0          # 校园一卡通单笔消费限额（元）


def load_raw() -> pd.DataFrame:
    """读取原始数据，统一字段类型。"""
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    df["消费时间"] = pd.to_datetime(df["消费时间"], errors="coerce")
    df["消费金额"] = pd.to_numeric(df["消费金额"], errors="coerce")
    for col in ["学号", "姓名", "学院", "年级", "校区", "消费类型", "消费场景", "支付方式"]:
        df[col] = df[col].astype("string").str.strip()
    return df


def clean(df: pd.DataFrame):
    """执行完整清洗流程，返回 (清洗后数据, 清洗日志 DataFrame)。"""
    log = []
    n0 = len(df)

    def record(step: str, before: int, after: int, note: str = ""):
        log.append({"处理步骤": step, "处理前行数": before,
                    "处理后行数": after, "处理条数": before - after, "说明": note})

    # ---------- 1. 去重 ----------
    before = len(df)
    df = df.drop_duplicates(subset=["订单号"], keep="first")
    record("删除重复记录", before, len(df), "同一订单号重复上传，仅保留首次")

    # ---------- 2. 缺失值处理 ----------
    # 2.1 关键字段缺失 —— 直接剔除
    before = len(df)
    key_cols = ["学号", "姓名", "消费时间", "消费类型", "消费场景"]
    df = df.dropna(subset=key_cols)
    df = df[~(df[key_cols].apply(lambda s: s.astype("string").str.strip() == "").any(axis=1))]
    record("剔除关键字段缺失/空串", before, len(df), "学号、姓名、时间、类型、场景缺失无法用于分析")

    # 2.2 消费金额缺失 —— 按消费类型中位数填充
    before = len(df)
    filled = 0
    if df["消费金额"].isna().any():
        filled = int(df["消费金额"].isna().sum())
        median_by_cat = df.groupby("消费类型")["消费金额"].transform("median")
        df["消费金额"] = df["消费金额"].fillna(median_by_cat)
        df["消费金额"] = df["消费金额"].fillna(df["消费金额"].median())
    df = df.dropna(subset=["消费金额"])
    record("消费金额缺失填充", before, len(df), f"按消费类型中位数填充 {filled} 条，避免直接丢弃造成样本偏差")

    # 2.3 学院缺失 —— 标记为未登记
    n_fill_college = int(df["学院"].isna().sum())
    df["学院"] = df["学院"].fillna("未登记")
    log.append({"处理步骤": "学院缺失标记", "处理前行数": len(df), "处理后行数": len(df),
                "处理条数": n_fill_college, "说明": "填充为“未登记”，保留该笔消费记录的金额价值"})

    # ---------- 3. 异常值剔除 ----------
    before = len(df)
    df = df[df["消费金额"] > 0]
    record("剔除金额 <= 0", before, len(df), "0 元与负数属于系统冲正/测试单，非真实消费")

    before = len(df)
    df = df[df["消费金额"] <= AMOUNT_LIMIT]
    record(f"剔除金额 > {AMOUNT_LIMIT:.0f} 元", before, len(df), "超出一卡通单笔限额，判定为采集异常")

    before = len(df)
    df = df[(df["消费时间"] >= TERM_START) & (df["消费时间"] <= TERM_END)]
    record("剔除学期外日期", before, len(df), f"仅保留 {TERM_START.date()} ~ {TERM_END.date()} 学期内数据")

    before = len(df)
    hour = df["消费时间"].dt.hour
    df = df[~hour.between(2, 5)]
    record("剔除非营业时段", before, len(df), "02:00-05:00 为系统结算窗口，不属于真实消费")

    before = len(df)
    df = df[df["学号"].str.fullmatch(r"\d{10}", na=False)]
    record("剔除学号格式异常", before, len(df), "学号应为 10 位数字，格式不合法判定为脏数据")

    # ---------- 4. 维度整理（特征工程） ----------
    df = df.copy()
    df["日期"] = df["消费时间"].dt.date
    df["小时"] = df["消费时间"].dt.hour
    df["星期"] = df["消费时间"].dt.day_of_week          # 0=周一
    df["星期名称"] = df["消费时间"].dt.strftime("%a").map(
        {"Mon": "周一", "Tue": "周二", "Wed": "周三", "Thu": "周四",
         "Fri": "周五", "Sat": "周六", "Sun": "周日"}
    )
    df["月份"] = df["消费时间"].dt.to_period("M").astype(str)
    df["是否周末"] = df["星期"] >= 5

    def to_period(h: int) -> str:
        if 6 <= h < 10:
            return "早餐"
        if 10 <= h < 14:
            return "午餐"
        if 14 <= h < 16:
            return "下午茶"
        if 16 <= h < 20:
            return "晚餐"
        return "夜宵"

    df["时段"] = df["小时"].apply(to_period)
    df["消费金额"] = df["消费金额"].round(2)

    df = df.sort_values("消费时间").reset_index(drop=True)
    log_df = pd.DataFrame(log)
    log_df.loc[len(log_df)] = {
        "处理步骤": "合计", "处理前行数": n0, "处理后行数": len(df),
        "处理条数": n0 - len(df), "说明": f"数据保留率 {len(df) / n0 * 100:.2f}%",
    }
    return df, log_df


def main() -> None:
    raw = load_raw()
    clean_df, log_df = clean(raw)

    clean_df.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")

    print("=" * 78)
    print("校园一卡通消费数据 · 预处理完成")
    print("=" * 78)
    print(log_df.to_string(index=False))
    print("\n--- 清洗后数据概览 ---")
    print(f"数据规模 : {clean_df.shape[0]} 行 × {clean_df.shape[1]} 列")
    print(f"时间范围 : {clean_df['消费时间'].min()} ~ {clean_df['消费时间'].max()}")
    print("\n消费类型分布：")
    print(clean_df["消费类型"].value_counts().to_string())
    print("\n数值字段统计：")
    print(clean_df[["消费金额"]].describe().round(2).to_string())
    print(f"\n输出路径 : {CLEAN_PATH}")


if __name__ == "__main__":
    main()
