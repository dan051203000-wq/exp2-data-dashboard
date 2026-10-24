# 校园一卡通消费数据看板（实验2）

《Python 程序设计》实验2「数据看板的设计与实现」的作业代码。

看板跑的是校园一卡通消费流水，用 Streamlit 搭的界面，Pandas 做数据清洗，Plotly 画图表。基础任务 5 项做完了，进阶 3 项、扩展 5 项也顺手做了。

Python 3.11 / Streamlit 1.66 / Pandas 3.1 / Plotly 7.1

![暗色整页](screenshots/02-overview-dark-full.png)

---

## 跑起来

```bash
pip install -r requirements.txt
streamlit run app.py
```

然后浏览器打开 `http://localhost:8501`。

仓库里已经带了生成好的原始数据（`data/raw_campus_card_data.csv`）和清洗后的数据（`data/clean_campus_card_data.csv`），直接跑就行。想把数据也重新生成一遍：

```bash
python generate_data.py    # 造 6040 条原始流水，里面混了脏数据
python preprocess.py       # 清洗成 5905 条，看板直接读这个
```

截图和报告是另外两个脚本，看板开着的时候另开一个终端跑：

```bash
python tools/capture_screenshots.py    # 截图到 screenshots/
python tools/make_report.py            # 生成实验报告 docx
```

`pip` 太慢就加清华源：`-i https://pypi.tuna.tsinghua.edu.cn/simple`

---

## 数据是怎么来的

真实的一卡通数据拿不到，所以我自己写了个生成器。

模拟了 4 个校区、10 个学院、420 个学生，一整个秋季学期（2025-09-01 到 2025-12-31）的消费记录。生成的时候按真实作息调过参数：早中晚三个饭点有明显的消费高峰，周末消费量降到平时的七成左右，再叠点随机噪声。

光有干净数据练不到预处理，所以我又手动往里掺了三类脏东西：

| 脏数据类型 | 数量 |
|---|---|
| 完全重复的流水 | 54 条 |
| 消费场景/支付方式字段为空 | 61 处 |
| 异常金额（-999 元、99999 元）和学期外的日期 | 20 条 |

清洗走的是「去重 → 补空值 → 剔异常 → 派生维度」四步。空值用众数补，异常值先用 0 < 金额 ≤ 500 的业务规则筛一遍，再用 IQR 补一刀。最后 6040 条进去，5905 条出来，保留率 97.76%。

这一步不多余。如果不清洗，一笔 99999 元的异常记录能把「人均消费」这个 KPI 直接拉到没法看。

---

## 目录

```
exp2-data-dashboard/
├── app.py                    # 看板主程序
├── generate_data.py          # 模拟数据生成
├── preprocess.py             # 数据清洗
├── requirements.txt
├── data/                     # 原始数据 + 清洗后数据
├── utils/
│   ├── style.py              # 主题和全局 CSS
│   ├── charts.py             # 10 类 Plotly 图表
│   └── data_loader.py        # 数据加载和缓存
├── tools/
│   ├── capture_screenshots.py  # 自动截图
│   ├── make_sketch.py          # 画版面草图
│   ├── make_report.py          # 生成实验报告
│   └── test_charts.py          # 图表自测
├── docs/                     # 实验报告
└── screenshots/              # 8 张截图
```

---

## 看板里有什么

**概览区**：6 张 KPI 卡片，消费总额、笔数、活跃人数、人均、日均、环比增长率。数字带滚动效果。

**维度区**：各学院消费总额柱状图、消费类型环形图、场景 TOP8 排行、时段分布、支付方式对比。

**趋势区**：每日消费折线图（带 7 日均线）、星期 × 小时的消费热力图、学院雷达图、人均目标仪表盘。

**明细区**：清洗后的流水表格，能筛能导出。

侧边栏有五个筛选维度（时间、校区、学院、消费类型、金额区间），改任何一个，全页图表跟着变。柱状图上直接点某根柱子，会下钻到那个学院，旁边的图表同步过滤。

还有几样东西：

- **主题切换**：暗色和亮色两套，CSS 变量控制
- **预警监控**：两个阈值滑块，日均消费额或者大单占比超线了，顶部弹红色预警条，对应 KPI 会变色
- **实时模式**：模拟数据流，秒级刷新
- **多终端**：测过 2560px 大屏和 430px 手机
- **导出**：CSV / Excel 一键下载

演示的时候可以直接用 URL 参数跳到某个状态：

| 参数 | 效果 |
|---|---|
| `?theme=亮色简约风` | 切到亮色主题 |
| `?college=计算机学院` | 直接进该学院下钻态 |
| `?thr_daily=300&thr_big=0.5` | 压低阈值触发预警 |

---

## 截图

| 暗色整页 | 亮色主题 |
|:---:|:---:|
| ![暗色整页](screenshots/02-overview-dark-full.png) | ![亮色](screenshots/03-light-theme.png) |

| 点击柱体联动下钻 | 触发预警 |
|:---:|:---:|
| ![下钻](screenshots/04-drilldown-college.png) | ![预警](screenshots/05-alert-warning.png) |

| 移动端（430px） | 2560px 大屏 |
|:---:|:---:|
| ![移动端](screenshots/07-mobile.png) | ![大屏](screenshots/08-bigscreen-2560.png) |

---

## 踩过的坑

有几个坑卡了我一阵，记下来省得以后再撞：

**Plotly 7 不让用 `titlefont` 了。** 坐标轴标题的写法从 `titlefont=dict(size=11)` 改成了 `title=dict(text="", font=dict(...))`。报错信息不太直白，我最后是写了个自测脚本把所有图表跑一遍才定位到的（`tools/test_charts.py`）。

**KPI 滚动动画把页面刷爆了。** 我本来在循环里反复调 `st.markdown`，结果是追加而不是替换，页面上堆了几十张一模一样的 KPI 卡片。改成用 `st.empty()` 占位、原地更新才对。

**chromedriver 起不来。** selenium 装了但驱动进程被拦，换了几组启动参数都没用。最后绕开 selenium，直接用 WebSocket 连 Chrome DevTools Protocol 截图，不依赖 chromedriver（`tools/capture_screenshots.py`）。

**自动化点击点不准。** 脚本里点了柱子但联动没反应，实际是我调完 `scrollIntoView` 立刻就去取坐标，页面还没滚完，点偏了。改成用 Promise 包一层、滚动完延时再取坐标，顺手把 `mouseMoved` 事件也补上。

**CSS 别碰 Streamlit 的内部 DOM。** 我一开始用 `[data-testid="stVerticalBlockBorderWrapper"]` 之类的选择器写卡片样式，结果这些属性随版本会变，一升级就失效。后来改成对 `st.plotly_chart` 和 `st.dataframe` 的输出容器直接注入样式，稳多了。

---

## 还差的地方

数据是自己造的，跟真实消费肯定有出入。预警阈值现在写死在滑块范围里，理论上应该跟着历史数据自动算基线。手机上图表字号偏小，窄屏还能再优化。
