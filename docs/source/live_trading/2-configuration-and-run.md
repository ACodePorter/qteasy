# live_trading 配置与运行

本页给出最小可运行路径，并说明 `LiveTradeConfig` 校验链、5-A/5-B 相关键与日志/risk 配置。

## 0. 适用场景

- 你已经有可运行的 `Operator`，准备从回测进入模拟实盘
- 你希望先跑通最小路径，再逐步补充风控、门禁与运维细节

## 1. 前置条件

- 已创建可用的 `Operator` 与策略组
- 本地数据源可用（可支持运行频率的数据）
- 已设置或准备设置 live 账户参数

## 2. 最小配置集

常见必配项包括：

- `mode=0`
- `asset_type`
- `live_trade_account_id` 或 `live_trade_account_name`
- `live_trade_broker_type`（通常为 `simulator`）
- `live_price_acquire_channel`
- `live_price_acquire_freq`

建议同时显式确认以下运行相关配置：

- `trade_batch_size` / `sell_batch_size`
- `cash_decimal_places` / `amount_decimal_places`
- `sys_log_file_path` / `trade_log_file_path` / `trade_log_keep_days`

## 3. LiveTradeConfig 与校验链

live 运行前，系统通过 `build_live_trade_config(QT_CONFIG, **overrides)` 构造 **不可变** 配置快照 `LiveTradeConfig`，并传入 `Operator.run_live_trade` → `Trader`。

- Python：`from qteasy.live_config import build_live_trade_config`
- CLI 只读摘要：`liveconfig` 或别名 `live-config`
  - 默认：`to_summary_dict()` 稳定子集
  - `--detail`：额外含 `live_trade_startup_gate_mode`、`live_trade_split_strategy_prepare` 等
- **说明**：Shell 内 `liveconfig` 由当前 `trader.get_config()` **重建**摘要，非持有构造时对象引用

## 4. 配置键分组（主要 live 键）

| 分组 | 代表键 | 说明 |
|------|--------|------|
| 账户与 UI | `live_trade_account_id`, `live_trade_account_name`, `live_trade_ui_type` | CLI / TUI 入口 |
| 行情与 refill | `live_price_acquire_channel`, `live_price_acquire_freq`, `live_trade_data_refill_channel`, `live_trade_*_refill_tables` | 数据准备与定时 refill |
| 交易规则 | `trade_batch_size`, `sell_batch_size`, `stock_delivery_period`, `cash_delivery_period`, `pt_buy_threshold`, `pt_sell_threshold` | 与回测语义对齐 |
| Broker | `live_trade_broker_type`, `live_trade_broker_params` | 默认 `simulator`；扩展见 :doc:`4-broker-adapter-and-integration` |
| 5-A snapshot | `live_trade_split_strategy_prepare`, `live_trade_prepare_lead_seconds`, `live_trade_strategy_snapshot_max_age_seconds` | 策略前 I/O 与快照复用，见 :doc:`6-trader-snapshot-gate` |
| 5-B gate | `live_trade_startup_gate_mode`（`off` / `warn` / `block`） | 启动门禁；CLI `gate` |
| 日志 | `sys_log_file_path`, `trade_log_file_path`, `trade_log_keep_days` | 含 `*.risk.log` 轮换；见 :doc:`5-artifacts-and-troubleshooting` |

完整字段列表以 `qteasy.live_config.LiveTradeConfig` 与 `_arg_validators` 为准。

## 5. 推荐配置模板

### 模板 A：股票路径（E + simulator）

```python
import qteasy as qt

qt.configure(
    mode=0,
    asset_type='E',
    live_trade_broker_type='simulator',
    live_price_acquire_channel='eastmoney',
    live_price_acquire_freq='15MIN',
    trade_log_keep_days=3,
)
```

### 模板 B：基金路径（FD + simulator）

```python
import qteasy as qt

qt.configure(
    mode=0,
    asset_type='FD',
    live_trade_broker_type='simulator',
    live_price_acquire_channel='eastmoney',
    live_price_acquire_freq='15MIN',
    trade_log_keep_days=3,
)
```

### 模板 C：5-A / 5-B 冒烟 override（在 `qt.run` 之前写入）

与 :doc:`7-manual-smoke-live-grid-roadmap` 无头脚本 override 一致：

```python
qt.configure(
    live_trade_split_strategy_prepare=True,
    live_trade_prepare_lead_seconds=60,
    live_trade_strategy_snapshot_max_age_seconds=300.0,
    live_trade_startup_gate_mode='warn',  # 灰度；稳定后可试 'block'
)
```

## 6. 启动流程

1. 完成配置并检查账户参数
2. （可选）`build_live_trade_config(qt.QT_CONFIG)` 或 CLI `liveconfig --detail` 确认快照
3. 调用 `qt.run(op)` 进入 live 运行（`--ui cli` 进入 Trader Shell）
4. 观察运行状态、订单变化与日志输出

启动前配置确认示例：

```python
import qteasy as qt

for key in ('mode', 'asset_type', 'live_trade_broker_type',
            'live_price_acquire_channel', 'live_trade_startup_gate_mode'):
    print(key, qt.get_config(key)[key])
```

## 7. 启动后关键观测点（CLI）

- `liveconfig` — 当前 live 摘要
- `artifacts` — 四键产物路径
- `gate` — 手动触发启动门禁（smoke/debug）
- `broker status` — `is_connected` / `broker_name`
- `reconcile` — 对账快照 JSON
- DEBUG 模式：`run --task diagnose_pending_orders`

命令全集见 :doc:`8-cli-trader-capability-matrix`。

## 8. 运行前检查清单

- 账户 ID/名称是否可用
- `asset_type` 与资产池是否匹配
- broker 类型是否与当前测试目的一致
- 数据获取频率是否与策略运行频率协调
- 日志路径合法且可写
- `trade_log_keep_days` 是否符合运维预期（含 risk 日志）

## 9. 常见启动失败与处理

- **配置校验失败**：先修复 `LiveTradeConfig` 提示字段，再重启
- **账户不可用**：检查账户 ID/名称及初始化参数
- **数据不可用**：检查数据渠道与频率设置
- **路径问题**：检查日志路径配置是否合法且可写
- **频率不协调**：检查策略运行频率与 live 价格频率是否匹配
- **gate block**：查看 `live_trade_startup_gate_mode` 与 `gate` / trace `failures`

## 10. 相关跳转

- 风控与状态：:doc:`3-risk-and-order-lifecycle`
- 产物与排错：:doc:`5-artifacts-and-troubleshooting`
- Broker 适配：:doc:`4-broker-adapter-and-integration`
- 快照/门禁：:doc:`6-trader-snapshot-gate`
- 冒烟清单：:doc:`7-manual-smoke-live-grid-roadmap`
- CLI 对照：:doc:`8-cli-trader-capability-matrix`
- 完整演练：`tutorials/8-live-trade-risk-and-broker-walkthrough.md`

## 11. 最小验收标准

- [ ] 可在 E 或 FD 路径下稳定启动
- [ ] `liveconfig` / `artifacts` 输出符合预期
- [ ] 可观察到一条订单提交、风控拒绝或柜台受理事件
- [ ] 若风控拒绝，可读 `risk_log`；若柜台拒单，订单表 `rejected` 且 broker 字段空
- [ ] 日志目录中可找到对应运行产物
