# Broker 适配层与集成

本页面向需要扩展或接入新 Broker 的用户与开发者，说明 S1.3 适配层边界、Facade 包装、受理 ACK 与 S2.1（QMT）预留。

## 0. 适用场景

- 你希望对接新的 broker（或未来 QMT/miniQMT），并保持与现有 Trader 逻辑兼容
- 你需要先打通“提交 -> 回报 -> 状态更新”的最小闭环，再逐步增强远端查询与对账

## 1. 架构分层

典型 live 路径：

```text
Operator.run_live_trade()
  -> Trader
       -> BrokerFacade（包装内层 Broker）
            -> SimulatorBroker / SimpleBroker / （未来 QmtBroker）
```

要点：

- **BrokerFacade** 由 [`qt_operator.run_live_trade`](qteasy/qt_operator.py) 创建，对外统一适配层 API
- Facade **透传** `connect` / `disconnect` / `submit` / `submit_with_ack` / `poll_fills` / `get_remote_*` 等
- 与 legacy 链路 **共享** `order_queue` / `result_queue`，保证历史消费路径仍可工作
- CLI：`broker status|connect|disconnect` 映射会话状态（`is_connected` 只读属性）

## 2. 核心接口

S1.3 中 Broker 适配层新增/明确了以下接口：

- `connect()` / `disconnect()`
- `is_connected`（只读，反映适配层会话是否已建立）
- `submit(order)` / `submit_with_ack(order)`
- `cancel(broker_order_id)`
- `poll_fills(timeout=0.0)` / `poll_messages(timeout=0.0)`
- `get_remote_orders(account_id=None)`
- `get_remote_positions(account_id=None)`
- `get_remote_cash(account_id=None)`

### 2.1 接口职责对照

| 接口 | 语义 | Simulator 现状 | S2.1（QMT）目标 |
|------|------|----------------|-----------------|
| `connect` / `disconnect` | 适配层会话 | 设置内部连接标志；非真实柜台登录 | miniQMT/xtt 登录与断线重连 |
| `submit` / `submit_with_ack` | 同步受理 | ACK 含 `accepted`、`broker_order_id`、`reason` 等 | 柜台真实受理结果 |
| `poll_fills` | 异步回报 | 模拟成交队列 | 真实成交推送或轮询 |
| `get_remote_*` | 远端账本查询 | 多为空列表 / `None` 占位 | gate、reconcile、`sync` 的真源 |
| `cancel` | 撤单 | 模拟实现 | QMT 撤单 ID 映射 |

建议按“最小闭环优先”理解：

- 连接语义：`connect` / `disconnect` / `is_connected`
- 交易语义：`submit_with_ack` / `cancel`
- 回报语义：`poll_fills`
- 查询语义：`get_remote_*`（S2.1-b 后才具备业务意义）

## 3. `submit_with_ack` 与本地订单

受理路径与 **风控拒单** 不同（风控在更前置，不入订单表）：

- **`accepted=True`**：Trader 回写 `sys_op_trade_orders.broker_order_id` / `broker_name`
- **`accepted=False`**：本地订单可为 `status=rejected`，broker 字段 **保持空**
- 详细对比表见 :doc:`6-trader-snapshot-gate`

契约校验：提交前订单 dict、回报 raw result 均经 `trade_io` 校验，不满足时应尽早失败。

## 4. 新旧链路并存关系

- 适配层提供“**同步受理 + 异步回报**”扩展路径
- legacy `run()+queue` 机制保持可用，确保历史行为兼容
- Trader 主循环经 `poll_fills` 消费回报，避免直接依赖内部队列细节
- 收盘处理等路径通过 Broker 统一 API 协调

## 5. 工厂注册与 S2.1 预留

**注册新 Broker 类型**：

```python
from qteasy.broker import register_broker_factory

register_broker_factory('my_broker', MyBrokerFactory)
# 配置 live_trade_broker_type='my_broker'
```

**CLI 远端同步（stub）**：

- `sync` / 别名 `pull-state` — 当前打印 `[NOT_IMPLEMENTED] ... S2.1-b`，预留 `sync_from_broker` 类 API
- 真实 QMT 接入拆工：S2.1-a（Broker 类）→ S2.1-b（`get_remote_*` 真实现）→ 替换 stub

## 6. 边界语义提醒

- 未连接时调用 `submit` / `poll_fills`（适配层路径）应给出明确 `RuntimeError`
- `cancel` 对未知 `broker_order_id` 应返回稳定、可预期的 `False`
- 轮询超时应返回空列表，而非脏数据
- Simulator 上 `connect` **不代表** 真实柜台会话，仅表示适配层可受理

## 7. 最小接入清单（建议）

1. 实现 `connect` / `disconnect` 与 `is_connected` 语义
2. 打通 `submit_with_ack -> poll_fills` 回路
3. 确保回报字段可通过 `trade_io` 契约校验
4. 实现 `cancel` 与异常路径
5. 实现 `get_remote_*`（若需 gate/reconcile/sync）
6. 在 CLI/TUI 下验证：`broker status`、`reconcile`、订单映射

## 8. 最小验收标准

- [ ] `connect` 后 `is_connected=True`，可正常 `submit_with_ack`
- [ ] 受理成功后本地订单含 `broker_order_id`
- [ ] 受理拒单时本地 `rejected` 且 broker 字段空
- [ ] `poll_fills` 回报可通过契约校验
- [ ] 未连接 / 未知订单 / 超时等边界行为稳定
- [ ] Facade 路径下 CLI `broker` / `reconcile` 可观测

## 9. 相关跳转

- 生命周期与风控：:doc:`3-risk-and-order-lifecycle`
- 产物与排错：:doc:`5-artifacts-and-troubleshooting`
- 快照/门禁：:doc:`6-trader-snapshot-gate`
- CLI 对照：:doc:`8-cli-trader-capability-matrix`
- 设计说明：`design/10-live-trading-s1.3-architecture.md`
