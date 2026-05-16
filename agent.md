# FundCrawler 项目 AI 快速理解指南

## 项目概览
- **项目名称**: FundCrawler
- **主要功能**: 自动化爬取基金数据并推送至企业微信
- **核心目的**: 获取ETF和场外基金的实时数据，生成可视化图表并通过企业微信分享

## 核心文件结构

### 主要入口文件
- [main.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/main.py): 程序主入口，处理命令行参数，协调整个流程
- [fund_core.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/fund_core.py): 核心逻辑，协调ETF和场外基金数据抓取

### 数据获取模块
- [get_etf.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/get_etf.py): 获取ETF基金数据，包括30天高低价差值
- [get_fund_realtime.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/get_fund_realtime.py): 获取基金实时持仓数据
- [crawler_otc.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/crawler_otc.py): 场外基金爬虫实现
- [get_market_volume.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/get_market_volume.py): 获取市场成交量数据

### 持仓管理模块
- [holdings/](file:///Users/zhangyan/PycharmProjects/FundCrawler/holdings/): 持仓管理目录
  - [load_holdings.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/holdings/load_holdings.py): 加载基金持仓配置
  - [get_holdings.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/holdings/get_holdings.py): 获取持仓信息

### 工具模块
- [utils/](file:///Users/zhangyan/PycharmProjects/FundCrawler/utils/): 工具函数目录
  - [init_driver.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/utils/init_driver.py): 初始化浏览器驱动
  - [schedule_manager.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/utils/schedule_manager.py): 管理定时任务
  - [send_wechat.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/utils/send_wechat.py): 发送企业微信消息
  - [utils.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/utils/utils.py): 通用工具函数，包括生成基金图片

### 配置文件
- [config.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/config.py): 项目配置，包括基金代码、企业微信配置等

## 关键配置

### 基金代码配置 ([config.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/config.py))
- ETF基金: [ETF_FUND_CODES](file:///Users/zhangyan/PycharmProjects/FundCrawler/config.py#L15-L15)
- 场外基金: [OTC_FUND_CODES](file:///Users/zhangyan/PycharmProjects/FundCrawler/config.py#L16-L25) 按类别组织（科技、医疗、消费等）

### 定时任务配置
- 执行时间: [SCHEDULE_TIME](file:///Users/zhangyan/PycharmProjects/FundCrawler/config.py#L29-L29) - ["14:00", "14:45"]
- 自动退出时间: [AUTO_EXIT_TIME](file:///Users/zhangyan/PycharmProjects/FundCrawler/config.py#L30-L30) - "15:01"

## 核心工作流程

1. **启动**: [main.py](file:///Users/zhangyan/PycharmProjects/FundCrawler/main.py) 解析命令行参数，根据模式决定是单次执行还是定时执行
2. **ETF数据获取**: 调用 [get_etf_fund_data()](file:///Users/zhangyan/PycharmProjects/FundCrawler/get_etf.py#L14-L130) 获取ETF基金数据
3. **场外基金数据获取**: 
   - 通过 [crawl_otc_funds()](file:///Users/zhangyan/PycharmProjects/FundCrawler/fund_core.py#L22-L70) 函数遍历场外基金
   - 使用Selenium获取实时持仓数据
   - 获取历史净值数据
4. **数据整合**: 将ETF和场外基金数据合并
5. **市场数据获取**: 获取上证指数、深证成指等市场数据
6. **图表生成**: 使用 [utils.generate_fund_image()](file:///Users/zhangyan/PycharmProjects/FundCrawler/utils/utils.py#L232-L372) 生成可视化图表
7. **企业微信推送**: 通过 [send_image_to_wechat()](file:///Users/zhangyan/PycharmProjects/FundCrawler/utils/send_wechat.py#L88-L126) 发送图片到企业微信

## 重要实现细节

### 浏览器驱动管理
- 支持Safari和Chrome浏览器
- 通过 [init_driver()](file:///Users/zhangyan/PycharmProjects/FundCrawler/utils/init_driver.py#L8-L32) 和 [close_driver()](file:///Users/zhangyan/PycharmProjects/FundCrawler/crawler_otc.py#L21-L25) 管理浏览器实例

### 反爬虫措施
- 请求间有适当的延时
- 使用Selenium模拟真实浏览器行为

### 错误处理机制
- 数据获取失败时保留基本信息
- 实现降级方案以确保程序稳定运行

### 环境兼容性
- 针对macOS环境进行了优化
- 解决了launchd环境下Python模块导入的问题

## 文件依赖关系

```
main.py
├── fund_core.py
│   ├── get_etf.py
│   ├── crawler_otc.py
│   │   ├── init_driver.py
│   │   └── get_fund_realtime.py
│   └── holdings/
│       └── load_holdings.py
├── get_market_volume.py
├── utils/
│   ├── utils.py (生成图片)
│   └── send_wechat.py (推送微信)
└── config.py
```

## 关键数据结构

- ETF基金数据: 包含代码、类型、名称、净值、涨跌幅、30天高低点差值等
- 场外基金数据: 包含代码、持仓占比、估算涨跌、历史趋势等
- 市场数据: 包含指数名称、当前价、涨跌幅、成交量等