# 模拟实盘交易——CLI 功能清单

本文从命令与能力清单角度说明 CLI 中的模拟实盘功能。  
如需按步骤操作，请阅读 `tutorials/8-live-trade-risk-and-broker-walkthrough.md`。

## 0. 文档边界

- 本页是命令能力索引，不是逐步教程
- 重点回答“有什么命令、看什么反馈、跳到哪里排查”

## 1. 命令能力分组

- **运行控制**：启动、暂停、恢复、结束
- **交易操作**：买入、卖出、撤单
- **状态查询**：订单、成交、持仓、账户
- **诊断与日志**：系统消息、错误提示、任务状态

## 2. 核心反馈语义

- 拒单时可看到英文摘要（含 `rule_id` / `reason`）
- 分批成交状态更容易在查询结果中识别
- 收盘后处理行为通过统一 Broker API 协调

## 2.1 手工下单的订单类型语义（buy/sell）

- `buy/sell ... -p 正数`：按**限价单**提交（`order_type='limit'`）
- `buy/sell ...`（不带 `-p`）或 `-p 0`：按**市价单**提交（`order_type='market'`），CLI 会在下单前使用最新实时价补齐价格字段

在 `SimulatorBroker` 中，撮合判定的关键差异如下：

| 订单类型 | 主要成交条件（简化） |
|---|---|
| `limit` 限价单 | 卖单：实时价 `>=` 挂卖价（含偏差）；买单：实时价 `<=` 挂买价（含偏差） |
| `market` 市价单 | 实时涨跌幅位于非涨跌停区间时优先按市价撮合；若接近涨跌停，成交概率显著下降 |

示例（用户可见反馈）：

```text
Order rejected by risk rule [MAX_ORDER_QTY]: order quantity exceeds limit
```

## 3. 快速问题分流（CLI 视角）

- 下单后没有订单记录：优先检查风控拒单提示
- 有订单但无成交：检查 broker 回报与行情条件
- 状态长时间不变：检查回报是否持续到达

## 4. 命令-文档映射

| 关注点 | 先看哪里 |
|---|---|
| 运行是否配置正确 | `live_trading/2-configuration-and-run.md` |
| 订单为何被拒或未成交 | `live_trading/3-risk-and-order-lifecycle.md` |
| 日志如何排查 | `live_trading/5-artifacts-and-troubleshooting.md` |
| 完整实操路径 | `tutorials/8-live-trade-risk-and-broker-walkthrough.md` |

## 5. 跳转导航

- 机制说明：`live_trading/3-risk-and-order-lifecycle.md`
- 排错手册：`live_trading/5-artifacts-and-troubleshooting.md`
- API 参考：`api/api_reference.rst`