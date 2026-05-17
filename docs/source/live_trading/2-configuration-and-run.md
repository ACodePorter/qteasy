# 模拟实盘：配置与运行

> 本章带您从「已有回测策略」到「第一次稳定启动模拟实盘」：该配哪些项、如何确认、启动后该看什么。

亲爱的用户，若您手里已经有一个能回测的 **Operator（交易员容器）**，本章就是进入 live 的最短路径。我们先把必要配置讲清楚，再谈可选的「策略快照」「启动门禁」等进阶项。

## 0. 适用场景

- 您已有可运行的 Operator，准备从回测进入模拟实盘
- 您希望先跑通最小路径，再逐步补充风控、门禁与运维细节

## 1. 核心概念（本章术语）

启动 live 前，请确认三者关系。在 qteasy 里，**Operator** 负责「算什么信号」，**live 账户**负责「记钱记仓」，**本地数据源**负责「给价给历史」——三者缺一，Trader 无法稳定运行。下表说明各自在 live 子系统中的位置及您要准备的内容。

**各列含义**：**角色**为组件名；**作用**为在 live 链路中的职责；**您需要准备什么**为启动前检查项。

**如何使用**：逐项打勾；若某一列准备不足，先补数据或账户再 `qt.run(op)`。

| 角色 | 作用 | 您需要准备什么 |
|------|------|----------------|
| **Operator** | 持有策略与信号逻辑 | 与回测时同一个 `op` 对象 |
| **live 账户** | 记录现金、持仓、订单 | `live_trade_account_id` 或 `live_trade_account_name` |
| **本地数据源** | 提供历史与实时行情 | 表数据覆盖策略频率（如分钟策略需分钟表） |

**LiveTradeConfig（live 配置快照）**：qteasy 在启动 Trader 前，会把分散在 `qt.configure(...)` 里的 live 相关项**校验并冻结**成一份不可变快照——像起飞前签字的检查单，避免运行中被意外改配置。您可在 Shell 里用 `liveconfig` 查看摘要。

## 2. 最小配置集

以下为常见**必配**项（不设或设错时，往往在启动阶段就会报错）。这些键通过 `qt.configure(...)` 写入全局配置，启动时并入 **LiveTradeConfig** 快照；它们决定「是不是 live、交易什么资产、用哪个账户、价从哪来、单交给谁撮合」。

**各列含义**：**配置键**为 `QT_CONFIG` 中的名称；**含义**为该键控制的 behavior；**不设会怎样**为常见后果（便于判断当前报错是否与此键有关）。

**如何使用**：首次 live 请全部显式设置；启动失败时对照「不设会怎样」列排查。示例见 §5 模板 A/B。

| 配置键 | 含义 | 不设会怎样 |
|--------|------|------------|
| `mode=0` | 进入 live / 模拟实盘 | 仍走回测或其他模式 |
| `asset_type` | 资产类型，如 `E` 股票、`FD` 场内基金 | 交易规则与数据表可能对不上 |
| `live_trade_account_id` 或 `live_trade_account_name` | 使用哪个模拟账户 | 无法绑定账本 |
| `live_trade_broker_type` | 券商类型，初学用 `simulator` | 无成交通道 |
| `live_price_acquire_channel` | 实时价渠道，如 `eastmoney` | 无法获取 live 价 |
| `live_price_acquire_freq` | 拉价频率，如 `15MIN` | 与策略步频不协调时可能缺数据 |

以下键**非启动硬性门槛**，但强烈建议确认——它们影响最小成交单位、日志落盘与磁盘占用。与上表同属 `qt.configure` 范围，可在同一脚本里一并写入。

**如何使用**：若成交数量「对不齐整手」或日志找不到文件，回头查本表对应行。

| 配置键 | 含义 | 不设会怎样 |
|--------|------|------------|
| `trade_batch_size` / `sell_batch_size` | 买卖最小单位 | 使用默认值 |
| `cash_decimal_places` / `amount_decimal_places` | 现金/数量小数位 | 使用默认值 |
| `sys_log_file_path` / `trade_log_file_path` | 系统/交易日志目录 | 使用包内默认路径 |
| `trade_log_keep_days` | 日志保留天数（含 risk 日志） | 默认 3 天自动清理 |

## 3. 查看配置快照

**Python**（脚本里自检）：

```python
from qteasy.live_config import build_live_trade_config
import qteasy as qt

cfg = build_live_trade_config(qt.QT_CONFIG)
print(cfg.to_summary_dict())
```

**CLI（Trader Shell）**：命令 `liveconfig`（别名 `live-config`）

- 默认：稳定字段子集
- 加 `--detail`：额外含启动门禁、策略快照等键

说明：Shell 内的 `liveconfig` 是根据当前 Trader **重新汇总**的摘要，不是启动那一刻对象的内存引用——但对您核对「现在生效的配置」足够用。

## 4. 配置键分组（主要 live 键）

live 相关配置键数量较多。为便于查阅，我们按**功能分组**归纳（非 API 全量列表；完整字段以 `LiveTradeConfig` 为准）。在 qteasy 中，这些键在启动前被校验并冻结——您改 `qt.configure` 后需重启 live 进程才能完全生效。

**各列含义**：**分组**为 live 子系统内的职责域；**代表键**列出该组最常改动的键（同组可能还有未列出的键）；**说明**为该组在运行中的作用。

**如何使用**：按您当前任务选分组——例如排日志问题看「日志」行并跳转 :doc:`5-artifacts-and-troubleshooting`；开分钟策略先看「行情与 refill」与策略步频是否匹配。

**示例**：子日频策略常改「行情与 refill」组的 `live_price_acquire_freq`，并视需要开启「策略快照（5-A）」组中的 `live_trade_split_strategy_prepare`。

| 分组 | 代表键 | 说明 |
|------|--------|------|
| 账户与 UI | `live_trade_account_id`, `live_trade_account_name`, `live_trade_ui_type` | 账户与 CLI / TUI 选择 |
| 行情与 refill | `live_price_acquire_channel`, `live_price_acquire_freq`, `live_trade_data_refill_channel`, `live_trade_*_refill_tables` | 实时价与定时补数据 |
| 交易规则 | `trade_batch_size`, `sell_batch_size`, `stock_delivery_period`, `cash_delivery_period`, `pt_buy_threshold`, `pt_sell_threshold` | 与回测语义对齐 |
| Broker | `live_trade_broker_type`, `live_trade_broker_params` | 默认 `simulator`；扩展见 :doc:`4-broker-adapter-and-integration` |
| 策略快照（5-A） | `live_trade_split_strategy_prepare`, `live_trade_prepare_lead_seconds`, `live_trade_strategy_snapshot_max_age_seconds` | 策略运行前预拉数据；详见 :doc:`6-trader-snapshot-gate` |
| 启动门禁（5-B） | `live_trade_startup_gate_mode`（`off` / `warn` / `block`） | 开盘前安全检查；CLI `gate` |
| 日志 | `sys_log_file_path`, `trade_log_file_path`, `trade_log_keep_days` | 含 `*.risk.log` 轮换；见 :doc:`5-artifacts-and-troubleshooting` |

完整字段以 `LiveTradeConfig` 为准；各键合法取值见配置校验逻辑。

## 5. 推荐配置模板

### 模板 A：股票（E + 模拟券商）

以下代码在 `qt.run(op)` **之前**执行，告诉 qteasy：用股票规则、东方财富 15 分钟价、模拟柜台成交。

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

### 模板 B：场内基金 / ETF（FD + 模拟券商）

与模板 A 相同，仅 `asset_type='FD'`，适用于 ETF 等示例路径。

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

### 模板 C：策略快照 + 启动门禁（冒烟 / 进阶）

与 :doc:`7-manual-smoke-live-grid-roadmap` 一致；建议在熟悉模板 A/B 后再开。

```python
qt.configure(
    live_trade_split_strategy_prepare=True,
    live_trade_prepare_lead_seconds=60,
    live_trade_strategy_snapshot_max_age_seconds=300.0,
    live_trade_startup_gate_mode='warn',  # 先 warn 观察，稳定后可试 block
)
```

## 6. 启动流程（分步说明）

1. **写好配置**：按 §2 完成 `qt.configure(...)`，确认账户 ID/名称。
2. **（可选）核对快照**：运行 §3 的 Python 片段，或启动后进 Shell 执行 `liveconfig --detail`。
3. **启动**：`qt.run(op)`；命令行示例常用 `--ui cli` 进入 **Trader Shell**。
4. **观察**：看状态、订单、日志是否按预期写入（§7）。

启动前快速打印几项关键配置：

```python
import qteasy as qt

for key in ('mode', 'asset_type', 'live_trade_broker_type',
            'live_price_acquire_channel', 'live_trade_startup_gate_mode'):
    print(key, qt.get_config(key)[key])
```

## 7. 启动后建议先看什么（CLI）

进入 Trader Shell 后，下列命令帮助您确认「配置是否生效、日志在哪、券商是否可受理、门禁是否通过」。它们对应 :doc:`8-cli-trader-capability-matrix` 中的运维子集——**不是** Shell 全部命令。

**各列含义**：**命令**为在提示符下输入的名称（含别名见矩阵章）；**典型用途**为该命令最常解决的疑问。

**如何使用**：启动后按表从上到下快速扫一遍；若某步异常，带着命令输出转 :doc:`5-artifacts-and-troubleshooting`。

**示例**：不确定日志路径 → 输入 `artifacts` → 打开返回的 `sys_log` 路径查看启动 trace。

| 命令 | 典型用途 |
|------|----------|
| `liveconfig` | 当前 live 配置摘要 |
| `artifacts` | 四键产物路径（日志在哪） |
| `gate` | 手动跑一次启动门禁（调试） |
| `broker status` | 模拟券商是否「已连接」 |
| `reconcile` | 对账快照 JSON |
| `run --task diagnose_pending_orders` | 在途单诊断（需 **DEBUG** 模式） |

命令全集见 :doc:`8-cli-trader-capability-matrix`。

### 7.1 Dashboard 与 interactive 模式

Trader Shell 启动后默认进入 **dashboard 模式**：单行状态区滚动显示下一任务倒计时、监视列表实时价与系统消息，无需输入命令即可观察运行节奏。需要手动下单、查配置或执行运维命令时，按 **Ctrl+C** 打开模式选单，或在 interactive（命令）模式下输入 **`dashboard`** 返回 dashboard。

| 模式 | 行为 |
|------|------|
| **dashboard** | 自动刷新状态行与监视价；Trader 主循环在后台继续运行 |
| **interactive（命令）** | 传统 `Cmd` 提示符，可输入 `buy`、`config`、`artifacts` 等命令 |

**Ctrl+C 模式选单（dashboard 或命令模式下均可用）**

- 在 **5 秒**内按 **1** → 进入命令模式；**2** → 回到 dashboard；**3** → 退出并停止 Trader  
- **无需按 Enter**，数字键立即生效  
- **5 秒内无输入** → 自动恢复中断前的模式  
- **选单等待期间再次按 Ctrl+C** → 立即退出（与选 **3** 等效）

若主循环发生未预期异常，Shell 会提示按 **1** 回到 dashboard 或 **3** 退出；**5 秒无输入**时默认回到 dashboard，Trader 继续运行。

## 8. 运行前检查清单

- [ ] 账户 ID/名称可用，且与策略资产池匹配  
- [ ] `asset_type` 与 `asset_pool` 一致（股票/基金不要混用规则）  
- [ ] `live_trade_broker_type` 为 `simulator`（或您已实现的类型）  
- [ ] live 价频率 **不低于** 策略运行步频（分钟策略需足够密的 live 价）  
- [ ] 日志路径合法、磁盘可写  
- [ ] `trade_log_keep_days` 符合您的留存预期（含 risk 日志）

## 9. 常见启动失败与处理

启动阶段报错时，现象往往集中在配置、账户、数据、路径、频率或启动门禁几类。下表按**您看到的现象**索引，避免在日志里盲目搜索。

**各列含义**：**现象**为启动或首屏时的表现；**可能原因**为常见根因（非穷尽）；**建议**为下一步操作。

**如何使用**：先匹配「现象」列；若仍无法解决，用 §7 命令导出 `liveconfig` 与 `artifacts` 路径，对照 :doc:`5-artifacts-and-troubleshooting` 决策树。

| 现象 | 可能原因 | 建议 |
|------|----------|------|
| 配置校验失败 | 某 live 键非法或互斥 | 按报错字段修正后重启 |
| 账户不可用 | ID/名称错误或未初始化 | 检查账户创建参数 |
| 数据不可用 | 渠道/频率/本地表缺失 | 检查 refill 与 `stock_1min` 等表 |
| 路径错误 | 日志目录不可写 | 检查 `sys_log_file_path` 等 |
| 频率不协调 | live 价比策略步频更稀 | 提高 `live_price_acquire_freq` 或降策略频 |
| gate block | 启动门禁 `block` 且检查未过 | 看 `gate` 输出与 trace 中 `failures` |

## 10. 相关跳转

- 风控与订单：:doc:`3-risk-and-order-lifecycle`
- 产物与排错：:doc:`5-artifacts-and-troubleshooting`
- Broker 适配：:doc:`4-broker-adapter-and-integration`
- 快照/门禁：:doc:`6-trader-snapshot-gate`
- 冒烟清单：:doc:`7-manual-smoke-live-grid-roadmap`
- CLI 对照：:doc:`8-cli-trader-capability-matrix`
- 完整演练：[tutorials/8-live-trade-risk-and-broker-walkthrough.md](../tutorials/8-live-trade-risk-and-broker-walkthrough.md)

## 11. 最小验收标准

- [ ] 可在 E 或 FD 路径下稳定启动  
- [ ] `liveconfig` / `artifacts` 输出符合预期  
- [ ] 能观察到至少一条：订单提交、风控拒绝或柜台受理  
- [ ] 若风控拒绝：能在 `risk_log` 找到记录；若柜台拒单：订单为 `rejected` 且 broker 号为空  
- [ ] 日志目录中能找到对应运行产物  
