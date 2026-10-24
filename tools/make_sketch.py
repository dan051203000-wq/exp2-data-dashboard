import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp

fig, ax = plt.subplots(figsize=(12.5, 7), dpi=150)
fig.patch.set_facecolor("#0d1424"); ax.set_facecolor("#0d1424")
ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.invert_yaxis(); ax.axis("off")

def box(x, y, w, h, label, color="#2b6cff", fc="#16203a", fs=11):
    r = mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35",
                          fc=fc, ec=color, lw=1.6)
    ax.add_patch(r)
    ax.text(x + w/2, y + h/2, label, ha="center", va="center", color="#eaf2ff",
            fontsize=fs, fontweight="bold", fontfamily="Microsoft YaHei")

box(1, 3, 14, 56, "控制台侧边栏", "#2b6cff", "#101a33", 10)
for i, lab in enumerate(["主题切换", "时间筛选", "校区/学院筛选", "消费类型筛选",
                          "金额区间滑块", "预警阈值滑块", "实时模式开关", "重置按钮"]):
    ax.text(8, 12 + i * 6, lab, ha="center", color="#8fa8cc", fontsize=8.5,
            fontfamily="Microsoft YaHei")

box(17, 3, 82, 6, "看板标题栏 · 数据源/统计周期/更新时间 · 实时状态徽标", "#20c997", fs=9.5)
box(17, 11, 82, 4.5, "预警提示条（触发时显示，默认显示运行正常）", "#ff4d6d", fs=9)
for i, lab in enumerate(["消费总额", "消费笔数", "活跃人数", "人均消费额", "日均消费额", "环比增长率"]):
    box(17 + i * 13.9, 17.5, 12.6, 6, lab, "#2b6cff", fs=8.5)
ax.text(17.5, 26.2, "① 数据概览区 · KPI 数据卡片 ×6", color="#5bc0ff", fontsize=9,
        fontfamily="Microsoft YaHei")

box(17, 29, 41, 9, "各学院消费总额对比（柱状图，点击下钻）", "#ffd43b", fs=9)
box(59.5, 29, 39.5, 9, "消费类型占比（环形图）", "#ffd43b", fs=9)
box(17, 39.5, 26.5, 8.5, "消费场景 TOP8 排行榜", "#ffd43b", fs=9)
box(45, 39.5, 26.5, 8.5, "时段消费分布（柱+折线双轴）", "#ffd43b", fs=9)
box(73, 39.5, 26, 8.5, "支付方式对比（柱状图）", "#ffd43b", fs=9)
ax.text(17.5, 49.3, "② 维度统计区 · 分类对比 / 排行 / 结构", color="#ffd43b",
        fontsize=9, fontfamily="Microsoft YaHei")

box(17, 51.5, 49.5, 7.5, "每日消费趋势（折线图 + 7日均线）", "#20c997", fs=9)
box(68, 51.5, 31, 7.5, "星期×小时 热力图 / 雷达图 / 仪表盘", "#20c997", fs=9)
ax.text(17.5, 60.3, "③ 趋势分析区 · 时间演化 / 热力 / 雷达 / 目标", color="#20c997",
        fontsize=9, fontfamily="Microsoft YaHei")

plt.tight_layout(pad=0.3)
plt.savefig("docs/layout_sketch.png", dpi=150, facecolor="#0d1424", bbox_inches="tight")
print("saved")
