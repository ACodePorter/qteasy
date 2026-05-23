# coding=utf-8
"""模拟实盘 references 页翻译条目（msgid 精确匹配）。"""

SIMULATION_OVERVIEW = {
    '模拟实盘功能总览（API 视角）': 'Simulated Live Trading Overview (API Perspective)',
    '本文从 API 和功能清单角度介绍 qteasy 的模拟实盘能力。   如需手把手操作，请阅读 `tutorials/8-live-trade-risk-and-broker-walkthrough.md`。': (
        'This page introduces qteasy simulated live trading from an API and capability-list perspective. '
        'For a step-by-step walkthrough, read `tutorials/8-live-trade-risk-and-broker-walkthrough.md`.'
    ),
    '0. 文档边界': '0. Document Scope',
    '本页只给出“对象/接口清单 + 行为速查 + 跳转索引”': (
        'This page only provides object/API lists, behavior quick reference, and navigation links'
    ),
    '不展开步骤教程、不展开底层实现推导': (
        'It does not include step tutorials or low-level implementation derivations'
    ),
    '1. 核心对象与职责': '1. Core Objects and Responsibilities',
    '对象': 'Object',
    '主要职责': 'Main Responsibility',
    '常见入口': 'Typical Entry',
    '运行策略与生成信号': 'Run strategies and generate signals',
    '下单协同、风控衔接、状态维护': 'Order coordination, risk integration, state maintenance',
    'live 运行主链路': 'Live-trading main path',
    '规则链评估与放行/拒绝决策': 'Rule-chain evaluation and accept/reject decisions',
    '提交、取消、回报、远端查询': 'Submit, cancel, fill reports, remote queries',
    '订单与成交字典契约校验': 'Order and fill dict contract validation',
    '提交前与回报后': 'Before submit and after fills',
    '2. 功能分区清单': '2. Capability Areas',
    '功能区': 'Area',
    '核心能力': 'Core Capability',
    '对应页面': 'Related Page',
    '配置与启动': 'Configuration and startup',
    'live 配置校验与运行快照': 'Live config validation and run snapshot',
    '下单与风控': 'Orders and risk control',
    '提交前评估、拒单可见性': 'Pre-submit evaluation and visible rejections',
    '成交与状态': 'Fills and status',
    '分批成交与状态收敛': 'Partial fills and status convergence',
    '适配与扩展': 'Adapters and extension',
    'adapter API 与兼容边界': 'Adapter API and compatibility boundaries',
    '日志与排错': 'Logs and troubleshooting',
    '`sys_log/trade_log/risk_log` 排查顺序': (
        '`sys_log` / `trade_log` / `risk_log` investigation order'
    ),
    '3. S1.3 行为变化速查': '3. S1.3 Behavior Changes (Quick Reference)',
    "`asset_type='FD'` 的模拟实盘可运行性增强": (
        "Improved simulated live runnability for `asset_type='FD'`"
    ),
    '风控拒单在 CLI/TUI 中更可见': 'Risk rejections are more visible in CLI/TUI',
    'Broker 适配层接口补齐，便于后续柜台接入': (
        'Broker adapter API completed for future broker integration'
    ),
    '分批成交状态显示更一致': 'More consistent partial-fill status display',
    '4. 入口索引': '4. Entry Index',
    'API 自动文档：`api/api_reference.rst`': 'API autodoc: `api/api_reference.rst`',
    '5. 相关阅读': '5. Related Reading',
    '模块总览：`live_trading/1-overview.md`': 'Module overview: `live_trading/1-overview.md`',
    '配置运行：`live_trading/2-configuration-and-run.md`': (
        'Configuration and run: `live_trading/2-configuration-and-run.md`'
    ),
    '风控与生命周期：`live_trading/3-risk-and-order-lifecycle.md`': (
        'Risk and lifecycle: `live_trading/3-risk-and-order-lifecycle.md`'
    ),
    '排错手册：`live_trading/5-artifacts-and-troubleshooting.md`': (
        'Troubleshooting: `live_trading/5-artifacts-and-troubleshooting.md`'
    ),
}

CLI_SIMULATION = {
    '本文从命令与能力清单角度说明 CLI 中的模拟实盘功能。   如需按步骤操作，请阅读 `tutorials/8-live-trade-risk-and-broker-walkthrough.md`。': (
        'This page describes simulated live trading in the CLI from a command and capability-list perspective. '
        'For step-by-step operation, read `tutorials/8-live-trade-risk-and-broker-walkthrough.md`.'
    ),
    '0. 文档边界': '0. Document Scope',
    '本页是命令能力索引，不是逐步教程': 'This page is a command capability index, not a step-by-step tutorial',
    '重点回答“有什么命令、看什么反馈、跳到哪里排查”': (
        'Focus: which commands exist, what feedback to read, and where to troubleshoot'
    ),
    '1. 命令能力分组': '1. Command Groups',
    '**运行控制**：启动、暂停、恢复、结束': '**Run control**: start, pause, resume, stop',
    '**交易操作**：买入、卖出、撤单': '**Trading**: buy, sell, cancel',
    '**状态查询**：订单、成交、持仓、账户': '**Status queries**: orders, fills, positions, account',
    '**诊断与日志**：系统消息、错误提示、任务状态': (
        '**Diagnostics and logs**: system messages, errors, task status'
    ),
    '2. 核心反馈语义': '2. Core Feedback Semantics',
    '拒单时可看到英文摘要（含 `rule_id` / `reason`）': (
        'Rejections show an English summary (with `rule_id` / `reason`)'
    ),
    '分批成交状态更容易在查询结果中识别': 'Partial-fill status is easier to spot in query results',
    '收盘后处理行为通过统一 Broker API 协调': 'After-close handling is coordinated via the unified Broker API',
    '2.1 手工下单的订单类型语义（buy/sell）': '2.1 Manual Order Types (buy/sell)',
    "`buy/sell ... -p 正数`：按**限价单**提交（`order_type='limit'`）": (
        "``buy/sell ... -p <positive>``: submit a **limit** order (``order_type='limit'``)"
    ),
    "`buy/sell ...`（不带 `-p`）或 `-p 0`：按**市价单**提交（`order_type='market'`），CLI 会在下单前使用最新实时价补齐价格字段": (
        "``buy/sell ...`` without ``-p``, or with ``-p 0``: submit a **market** order "
        "(``order_type='market'``); CLI fills price from the latest live quote before submit"
    ),
    '在 `SimulatorBroker` 中，撮合判定的关键差异如下：': (
        'In ``SimulatorBroker``, key matching differences are:'
    ),
    '订单类型': 'Order type',
    '主要成交条件（简化）': 'Main fill condition (simplified)',
    '`limit` 限价单': '``limit`` (limit order)',
    '卖单：实时价 `>=` 挂卖价（含偏差）；买单：实时价 `<=` 挂买价（含偏差）': (
        'Sell: live price ``>=`` limit sell (with tolerance); buy: live price ``<=`` limit buy (with tolerance)'
    ),
    '`market` 市价单': '``market`` (market order)',
    '实时涨跌幅位于非涨跌停区间时优先按市价撮合；若接近涨跌停，成交概率显著下降': (
        'Prefer market fill when price is not near limit up/down; fill probability drops near limits'
    ),
    '示例（用户可见反馈）：': 'Example (user-visible feedback):',
    '3. 快速问题分流（CLI 视角）': '3. Quick Triage (CLI View)',
    '下单后没有订单记录：优先检查风控拒单提示': (
        'No order after submit: check risk rejection messages first'
    ),
    '有订单但无成交：检查 broker 回报与行情条件': (
        'Order but no fill: check broker reports and market conditions'
    ),
    '状态长时间不变：检查回报是否持续到达': (
        'Status stuck: check whether fill reports keep arriving'
    ),
    '4. 命令-文档映射': '4. Command–Document Map',
    '关注点': 'Concern',
    '先看哪里': 'Check First',
    '运行是否配置正确': 'Run configuration correct',
    '订单为何被拒或未成交': 'Why order rejected or unfilled',
    '日志如何排查': 'How to investigate logs',
    '完整实操路径': 'Full hands-on path',
    '5. 跳转导航': '5. Navigation',
    '机制说明：`live_trading/3-risk-and-order-lifecycle.md`': (
        'Mechanism: `live_trading/3-risk-and-order-lifecycle.md`'
    ),
    '排错手册：`live_trading/5-artifacts-and-troubleshooting.md`': (
        'Troubleshooting: `live_trading/5-artifacts-and-troubleshooting.md`'
    ),
}

TUI_SIMULATION = {
    '本文从功能清单角度介绍 TUI 的模拟实盘能力。   如需手把手步骤，请阅读 `tutorials/8-live-trade-risk-and-broker-walkthrough.md`。': (
        'This page introduces TUI simulated live trading from a capability-list perspective. '
        'For step-by-step guidance, read `tutorials/8-live-trade-risk-and-broker-walkthrough.md`.'
    ),
    '0. 文档边界': '0. Document Scope',
    '本页是 TUI 能力索引，不替代步骤教程': 'This page is a TUI capability index, not a step tutorial',
    '重点回答“在界面上看哪里、发生异常先看什么”': (
        'Focus: where to look on screen and what to check first when something goes wrong'
    ),
    '1. 面板与交互能力': '1. Panels and Interactions',
    '账户与资金状态展示': 'Account and cash status display',
    '订单提交与撤单交互': 'Order submit and cancel interactions',
    '成交与历史信息查看': 'Fill and history views',
    '系统日志与风险反馈显示': 'System log and risk feedback display',
    '2. 核心反馈语义': '2. Core Feedback Semantics',
    '风控拒单摘要在交互中更容易识别': 'Risk rejection summaries are easier to spot in the UI',
    '订单状态变化（特别是分批成交）更一致': 'Order status changes (especially partial fills) are more consistent',
    '日志链路更清晰，便于从界面跳转排查': 'Clearer log trail for troubleshooting from the UI',
    '示例（用户可见反馈）：': 'Example (user-visible feedback):',
    '3. 快速问题分流（TUI 视角）': '3. Quick Triage (TUI View)',
    '“界面没报错但下单失败”通常是风控拒绝，不是系统崩溃': (
        '“No UI error but order failed” is usually risk rejection, not a crash'
    ),
    '“订单一直 partial-filled”需要结合累计成交量判断最终状态': (
        '“Order stays partial-filled” — judge final status from cumulative filled volume'
    ),
    '4. 面板-文档映射': '4. Panel–Document Map',
    '关注点': 'Concern',
    '先看哪里': 'Check First',
    '运行启动与配置核对': 'Startup and config check',
    '拒单/状态解释': 'Rejection / status explanation',
    '日志排障': 'Log troubleshooting',
    '完整实操路径': 'Full hands-on path',
    '5. 跳转导航': '5. Navigation',
    '配置与运行：`live_trading/2-configuration-and-run.md`': (
        'Config and run: `live_trading/2-configuration-and-run.md`'
    ),
    '生命周期：`live_trading/3-risk-and-order-lifecycle.md`': (
        'Lifecycle: `live_trading/3-risk-and-order-lifecycle.md`'
    ),
    '排错手册：`live_trading/5-artifacts-and-troubleshooting.md`': (
        'Troubleshooting: `live_trading/5-artifacts-and-troubleshooting.md`'
    ),
}
