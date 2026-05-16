# 产物清单与排错

本页提供 live 运行时最常用的排错路径与运维建议，对齐 S1.3 P5 产物 API 与 Trader 路线图 5-C 可观测能力。

## 0. 适用场景

- 你已经在 live 模式运行，但遇到“提交失败 / 拒单 / 状态异常 / 在途单对不齐”等问题
- 你希望按固定顺序快速定位问题来源，减少盲目排查
- 你需要核对磁盘产物路径、日志轮换与 `broker_order_id` 映射

## 1. 关键产物与用途（四键 API）

系统为每个 live 账户枚举 **固定四键** 磁盘产物路径（文件可不存在，路径仍有效）：

| 键名 | 典型用途 |
|------|----------|
| `sys_log` | 系统运行、任务调度、trace 事件 |
| `trade_log` | 交易明细 CSV |
| `break_point` | 断点恢复文件（注意键名为 `break_point`，非 `breakpoint`） |
| `risk_log` | 风控拒单审计（`*.risk.log`） |

**API**（推荐）：

```python
import qteasy as qt

arts = qt.list_live_trade_artifacts(account_id=1, data_source=qt.QT_DATA_SOURCE)
print(arts['sys_log'], arts['trade_log'], arts['break_point'], arts['risk_log'])
```

**CLI**（Trader Shell）：`artifacts` 或别名 `ls-artifacts`。

路径解析规则：

- 相对路径相对于 `QT_ROOT_PATH`；绝对路径与 `~/...` 家目录经 `_resolve_path` 解析
- `sys_log_file_path` / `trade_log_file_path` 支持运行时热修改（`qt.configure(...)` 后刷新 `QT_SYS_LOG_PATH` / `QT_TRADE_LOG_PATH`）

建议把四类产物分别用于四类问题：

- 运行是否正常：优先看 `sys_log`
- 下单为何被拒（风控）：优先看 `risk_log` 与 `<RISK REJECTED>` 消息
- 柜台受理/成交：优先看 `trade_log` 与订单表
- 恢复与断点：看 `break_point`

## 2. 日志轮换

**API**：`qt.rotate_trade_logs(days=None)` — `days` 为 `None` 时使用全局 `trade_log_keep_days`（默认 3）。

**CLI**：`rotatelogs` 或别名 `rotate-logs`；可选 `--days N`。

清理范围（目录为当前 `QT_TRADE_LOG_PATH`）：

- `trade_log_*.csv` / `trade_summary_*.csv` / `value_curve_*.csv`（优先文件名时间戳，失败退回 mtime）
- `*.risk.log`（通常无时间戳，按 mtime 判断）

进程加载 `qteasy` 时会按 `trade_log_keep_days` **自动轮换一次**；运维可手动再次调用上述 API/CLI。

## 3. 建议排错顺序

1. 先看即时界面反馈（CLI/TUI）
2. 再看 `sys_log` 的错误、trace 与 `reconcile` / `startup_gate` 事件
3. 若是 **风控** 拒单，检查 `risk_log` 的 `rule_id` / `reason`（通常 **无** 新订单表行）
4. 若是 **柜台受理** 拒单，查订单表 `status=rejected` 且 `broker_order_id` 为空
5. 在途单不一致时，使用只读诊断（见 §4 剧本 F）
6. 最后对照订单与成交记录确认状态是否符合预期

如果是“看起来没报错但行为不对”，建议再补一步：

7. 回看本次运行配置快照（`liveconfig` / `live-config` CLI，或 `build_live_trade_config`）

## 4. 高频故障剧本

### A. 订单被风控拒绝

- 现象：CLI 显示英文拒因；`submit_trade_order` 返回空 `{}`
- 排查：`risk_log` 含 `<RISK REJECTED>`；**不应**出现新的 `sys_op_trade_orders` 行
- 处理：调整规则阈值或订单参数，复测同一场景

### B. 提交失败（非风控）

- 现象：未产生有效提交记录，或本地校验失败
- 排查：连接状态（CLI `broker status`）、契约字段、现金/持仓校验
- 处理：先修复连接/字段问题，再重试并对照 `sys_log`

### C. 柜台受理拒单

- 现象：订单表有行，`status=rejected`，`broker_order_id` / `broker_name` **为空**
- 排查：`submit_with_ack` 返回 `accepted=False` 与 `reason`；trace 事件
- 处理：与 **风控拒单** 区分（见 :doc:`6-trader-snapshot-gate`）

### D. 状态理解偏差

- 现象：订单长期 `partial-filled`
- 排查：确认累计成交量与目标量关系
- 处理：结合 `poll_fills` 回报判断是否应转为 `filled`

### E. 收盘后订单处理疑问

- 现象：收盘后订单状态变化不确定
- 排查：查看 `post_close` reconcile 检查点 trace 与撤单记录
- 处理：按收盘处理策略核对最终状态

### F. broker_order_id / 在途单异常

| 现象 | 排查 | 处理 |
|------|------|------|
| 风控拒单 | `risk_log` 有 `<RISK REJECTED>`，无新订单行 | 调规则；详见 :doc:`6-trader-snapshot-gate` |
| 柜台受理拒单 | 订单行 `rejected`，broker 字段空 | trace / broker `reason` |
| 受理成功无 broker id | `submitted` 但 `broker_order_id` 空 | 查 `submit_with_ack` 与 Trader 回写 |
| 在途单不一致 | `collect_pending_order_diagnostics()` 或 DEBUG 下 `run --task diagnose_pending_orders` | 只读诊断；Simulator 远端常为空 |

CLI 辅助：`reconcile` / `snapshot-reconcile` 打印对账 JSON；`gate` 手动触发启动门禁。

### G. 界面与日志不一致

- 现象：CLI/TUI 提示与日志感知不一致
- 排查：按时间顺序对齐界面反馈和日志条目
- 处理：以日志中的最终状态为准，复核同一订单 ID 的全链路记录

## 5. 运维建议

- 定期检查 `QT_TRADE_LOG_PATH` 容量；按需 `rotatelogs --days N`
- 保留至少一段可复盘窗口，便于问题复现
- 对关键运行日保存配置快照（`liveconfig --detail`）与日志头信息
- 冒烟与回归清单见 :doc:`7-manual-smoke-live-grid-roadmap`

## 6. 快速检查清单

- 账户是否正确
- 配置是否生效（`liveconfig`）
- 风控是否拒绝（`risk_log`）
- broker 是否连通（`broker status`，`is_connected`）
- 受理后是否回写 `broker_order_id`（成功路径）
- 回报是否满足契约
- 日志是否完整可读（四键路径 `artifacts`）

## 7. 常用英文提示样例

```text
Order rejected by risk rule [MAX_ORDER_QTY]: order quantity exceeds limit
```

```text
<RISK REJECTED> rule_id='MAX_ORDER_QTY' reason='...' symbol='000001.SZ' ...
```

```text
Order submission failed.
```

```text
[NOT_IMPLEMENTED] sync_from_broker is reserved for QMT broker integration (S2.1-b).
```

## 8. 相关跳转

- 启动与配置：:doc:`2-configuration-and-run`
- 生命周期：:doc:`3-risk-and-order-lifecycle`
- 快照/门禁/拒单语义：:doc:`6-trader-snapshot-gate`
- 手工冒烟：:doc:`7-manual-smoke-live-grid-roadmap`
- CLI 命令对照：:doc:`8-cli-trader-capability-matrix`
- Broker 适配：:doc:`4-broker-adapter-and-integration`
- 实操教程：`tutorials/8-live-trade-risk-and-broker-walkthrough.md`
