# 项目确认问题 (Ripple Scout v1.0)

为了确保实施计划准确且有价值，请澄清以下几点：

## 1. 关于“12 只核心股票” (The "Core 12" List)
文档中提到了“12 只核心股票”（例如 NVDA, CCJ），但没有列出完整的清单。
- **问题：** 您手头有具体的 12 个代码 (Ticker) 列表吗？还是我们暂时先用一个占位列表（例如“七巨头”+其他几只）？
NVDA
TSLA
META
MSFT
TSM
AAPL
GOOGL
CEG
AVGO
PLTR
TER
AMZN

## 2. 知识图谱来源 (Knowledge Graph Source)
第二阶段需要将核心股票映射到候选股票（邻居）。
- **问题：** 您是否已经有了 `Core12_Neighbors.json` 或者一份现成的关系列表？
- **选项：** 如果没有，对于 v1 版本，我们可以：
    1.  手动创建一个小样本（例如 NVDA -> SMCI, VRT）。
    2.  尝试用简单的搜索手动填充。
{
  "NVDA": {
    "sector": "AI Compute / GPU",
    "kpi_to_watch": "Purchase Commitments / Inventory",
    "neighbors": ["MU", "SNDK", "VRT", "SMCI", "AMKR", "MRVL", "ALTR"],
    "ripple_logic": "显卡生产需要存储(HBM)、散热设备、先进封装以及高速连接芯片。"
  },
  "TSLA": {
    "sector": "Physical AI / EV",
    "kpi_to_watch": "Optimus Production Volume / FSD Version Release",
    "neighbors": ["TER", "ON", "ALB", "LIDR", "AEVA", "STM", "MP"],
    "ripple_logic": "机器人与自动驾驶带动功率半导体(SiC)、激光雷达、稀土永磁及测试设备。"
  },
  "META": {
    "sector": "Social / Open AI Ecosystem",
    "kpi_to_watch": "Capex Guidance (Infrastructure)",
    "neighbors": ["ANET", "AAOI", "DELL", "SMCI", "COHR", "EQIX"],
    "ripple_logic": "开源模型爆发带动数据中心交换机、光模块以及高密度服务器的需求。"
  },
  "MSFT": {
    "sector": "Cloud / Software",
    "kpi_to_watch": "Azure Growth / AI Capex",
    "neighbors": ["PLTR", "CRWD", "ANET", "VRT", "MOD", "STLD"],
    "ripple_logic": "云端扩张带动网络架构、散热系统、网络安全以及建设用钢材(数据中心框架)。"
  },
  "TSM": {
    "sector": "Foundry",
    "kpi_to_watch": "Monthly Revenue (10th of each month)",
    "neighbors": ["ASML", "AMAT", "LRCX", "KLAC", "ASX", "MKSI"],
    "ripple_logic": "晶圆出货量是所有下游硬件的先导指标，同时带动半导体设备商。"
  },
  "AAPL": {
    "sector": "Edge AI / Consumer Electronics",
    "kpi_to_watch": "iPhone/Mac Inventory Levels",
    "neighbors": ["CRUS", "LITE", "TTMI", "SWKS", "QRVO", "DSY"],
    "ripple_logic": "端侧AI升级带动声学芯片、光学镜头、柔性电路板及射频前端。"
  },
  "GOOGL": {
    "sector": "Search / Custom AI Chips (TPU)",
    "kpi_to_watch": "Cloud Capex / TPU Deployment",
    "neighbors": ["AVGO", "FN", "MOD", "WOLF", "AMBA"],
    "ripple_logic": "自研芯片路线带动定制化ASIC设计合作伙伴及特定的光纤连接技术。"
  },
  "CEG": {
    "sector": "Nuclear / Energy",
    "kpi_to_watch": "New Power Purchase Agreements (PPA)",
    "neighbors": ["VST", "PWR", "HUBB", "FCX", "HWM", "ETN"],
    "ripple_logic": "核能协议签署预示着电网更新、变压器需求、铜矿消耗及重型工业组件爆发。"
  },
  "AVGO": {
    "sector": "Connectivity / Networking",
    "kpi_to_watch": "Networking Revenue Growth",
    "neighbors": ["TEL", "APH", "COHR", "LUNA", "KEYS"],
    "ripple_logic": "高速网络需求直接利好连接器、光纤收发器及测试仪器供应商。"
  },
  "PLTR": {
    "sector": "AI Software / Decision",
    "kpi_to_watch": "Commercial Customer Growth",
    "neighbors": ["C3AI", "OKTA", "SNOW", "PATH", "MSTR"],
    "ripple_logic": "软件落地成功预示着企业对云端存储、自动化工作流及网络安全支出的增加。"
  },
  "TER": {
    "sector": "Robotics / Semi Test",
    "kpi_to_watch": "Industrial Automation Bookings",
    "neighbors": ["CGNX", "ROK", "HDRIF", "ISRG", "ZBRA"],
    "ripple_logic": "协作机器人渗透率提升利好机器视觉、减速器、工业自动化及扫码识别硬件。"
  },
  "AMZN": {
    "sector": "Logistics / AWS",
    "kpi_to_watch": "AWS Capex / Warehouse Automation Spend",
    "neighbors": ["SYNA", "OMRN", "FDX", "RIVN", "STG"],
    "ripple_logic": "物流自动化与云扩张利好传感器芯片、仓储机器人组件及第三方物流技术。"
  }
}

## 3. 上游数据 (Capex/营收)
单纯依靠免费 API（如 `yfinance`）很难直接爬取 SEC 文件，获取台股特定日期的月度营收数据也比较复杂。
- **问题：** 您是否接受在 v1 版本中**简化第三阶段**？
- **建议：** 不使用 Capex/营收作为触发器，而是使用 **核心股票的价格/成交量动作** 作为触发器。（例如：“如果 NVDA 放量上涨 5%，就去扫描它的邻居”）。

## 4. 现货价格数据 (Spot Price Data)
- **问题：** 文档提到了具体的现货价格（TrendForce）。您有具体的 URL 或 API 来源吗？
- **建议：** 如果没有，我们将在 v1 中省略这一点，或者寻找广泛的 ETF 作为替代（例如用 SOXX 代表半导体现货趋势）。
