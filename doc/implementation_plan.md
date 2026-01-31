# Ripple Scout v1.0 实施计划 (Implementation Plan)

## 1. 项目概览 (Project Overview)
**目标：** 构建 "Ripple Scout" (涟漪侦察兵)，一个受 Physical AI 启发的股票监控系统，旨在捕捉产业链价值传递的“涟漪”。
**策略：** "上游雷达 (Upstream Radar)" -> "下游 VCP 检测 (Downstream VCP Detection)"。
**约束：** v1 版本使用免费数据 API (`yfinance`)，简化功能，并聚焦于“核心产品”逻辑的验证。

## 2. 系统架构 (v1 MVP)

- **语言：** Python 3.10+
- **数据源：** `yfinance` (Yahoo Finance 免费 API)。
- **存储：** 本地 JSON/CSV 文件 (v1 版本暂不需要复杂数据库)。
- **前端：** Streamlit。
- **调度：** 简单的 Python 脚本/Cron 定时任务，或通过 Streamlit 手动触发。
- **回测支持 (Backtesting):** 所有核心模块将接受 `target_date` 参数 (默认为 Today)，以便使用历史数据进行验证。

## 3. 分阶段实施路线图 (Phased Implementation Roadmap)

### 第一阶段：核心扫描引擎 (The "Pattern Matcher")
**目标：** 实现 VCP (波动收缩模式) 和 "Spark" (异动) 检测算法。
- **输入：** 候选股票列表 (Candidates)。
- **逻辑：**
    1.  **VCP 检测 (VCP Detection):**
        - 计算收缩波段 (T1, T2, T3)。
        - 计算 "紧凑度" (Tightness): 过去 10 天收盘价的标准差。
    2.  **Spark 指标 (Spark Indicators):**
        - RSI (相对强弱指数) 检查 (> 50 且 处于上升趋势)。
        - 量价背离 (价格平稳，成交量放大)。
        - 突破检测 (价格 > 50日均线 + 成交量 > 2倍平均值)。
    3.  **时间参数 (Time Parameters):**
        - **回溯窗口 (Lookback Window):** VCP 趋势确认需要过去 50-200 天的数据。
        - **信号时效 (Signal Freshness):** 只关注最近 N 天 (如 3 天) 内发生的信号，过滤陈旧突破。
        - **目标日期 (Target Date):** 用于回测，系统将“假装”今天是 `target_date` 运行扫描。
- **输出：** 根据评分过滤后的“可操作”股票列表。

### 第二阶段：知识图谱 (The "Linkage Engine") - 简化版
### 第二阶段：知识图谱 (The "Linkage Engine") - 核心数据已就绪
**目标：** 使用用户提供的 12 只核心股票 (Core 12) 及其下游映射。
- **Core 12 List:** NVDA, TSLA, META, MSFT, TSM, AAPL, GOOGL, CEG, AVGO, PLTR, TER, AMZN.
- **数据源:** 用户已提供完整的 `config/core_neighbors.json` 数据结构。
- **逻辑：** 扫描器将加载此 JSON，当核心股票触发信号时，遍历其对应的 `neighbors` 列表。

### 第三阶段：上游信号 (The "Radar") - 简化版
**目标：** 使用 `yfinance` 追踪上游动向。
- **局限性：** 免费 API 很难直接获取 SEC 文件中详细的 Capex/采购承诺数据，无需复杂的爬虫难以实现。
- **v1 代替方案：**
    - 追踪 *上游核心股* 的 **价格/成交量趋势** (例如：如果 NVDA 突破，则触发对它邻居的扫描)。
    - **时间同步 (Time Sync):** 引入 `lag_days` (滞后天数) 参数。如果上游核心股在 T 日爆发，扫描下游 Candidate 在 [T, T+lag] 时间窗口内的反应。
    - 通过 `yfinance` 很难可靠地获取台股 (如 TSMC) 每月 10 号的精准营收数据。除非找到特定的免费源，v1 版本将跳过此特定触发器。

    > [!NOTE]
    > **关于 SEC EDGAR 爬虫:**
    > 从 RSS 抓取 XML 是可行的，但**解析复杂度较高**。"Purchase Obligations" 往往没有标准的 XBRL 标签，常隐藏在文本附注中。
    > **v2 进阶方案:** 可以引入 LLM (如 GPT-4) 来阅读 10-K 的特定章节 (Commitments Note) 并提取该数字。v1 建议先用“价格/成交量”代理。

### 第四阶段：可视化 (Streamlit Dashboard)
**目标：** 用户界面。
- **功能：**
    - 今日“警报”看板。
    - “涟漪视图” (Ripple View)：选择一只核心股票，查看其关联 Candidate 的状态。
    - 图表：展示选中 Candidate 的价格走势图，并标注 VCP 形态。

## 4. 目录结构 (Directory Structure)
```
ripple-scout/
├── data/               # 股票数据本地缓存
├── doc/                # 文档
├── src/
│   ├── data_loader.py  # yfinance 封装
│   ├── scanner.py      # VCP 和 Spark 逻辑
│   ├── graph.py        # 邻居关系管理
│   └── app.py          # Streamlit UI
├── config/
│   └── neighbors.json  # 知识图谱 (配置)
├── requirements.txt
└── README.md
```

## 5. 验证计划 (Verification Plan)
- **单元测试：** 使用已知的历史案例 (如 SNDK 的历史数据点，如果有，或使用模拟数据) 测试 VCP 逻辑。
- **手动测试：** 对当前“热门”板块运行扫描器，看它是否能筛选出已知的领涨股。
