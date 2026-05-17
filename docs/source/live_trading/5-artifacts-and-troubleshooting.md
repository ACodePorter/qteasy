# 产物清单与排错

> 本章是模拟实盘的「急救手册」：日志在哪、先查哪个文件、常见故障按什么顺序排查。

亲爱的用户，live 运行会在磁盘上留下几类固定「产物」。把它们当成四个专用文件夹，出问题时按图索骥，比在海量输出里盲找高效得多。

## 0. 适用场景

- 您已在 live 模式运行，遇到提交失败、拒单、状态异常、在途单对不齐  
- 您希望按**固定顺序**定位问题，减少反复重启  
- 您需要核对日志路径、轮换策略与 `broker_order_id` 是否回写  

## 1. 核心概念：四键产物

qteasy 为每个 live 账户提供 **四个固定键名** 的路径（文件可以尚不存在，路径仍然有效）。在 live 子系统的可观测性设计中，这四类产物分别对应「系统怎么跑、成交明细、异常恢复、风控审计」——排错时请先判断问题属于哪一类，再打开对应文件，而不是在一个日志里全文搜索。

**各列含义**：**键名**为 `list_live_trade_artifacts` / CLI `artifacts` 返回的 dict 键；**是什么**为文件类型；**什么时候该打开它**为典型触发场景。

**如何使用**：按 :doc:`3-risk-and-order-lifecycle` 判断拒单类型 → 风控查 `risk_log`，成交查 `trade_log`；启动/门禁/trace 查 `sys_log`。

| 键名 | 是什么 | 什么时候该打开它 |
|------|--------|------------------|
| `sys_log` | 系统运行日志 | 任务调度、启动门禁、trace、一般报错 |
| `trade_log` | 交易明细 CSV | 成交、费用、持仓变化明细 |
| `break_point` | 断点恢复文件（键名是 `break_point`） | 异常退出后想恢复 Trader 状态 |
| `risk_log` | 风控拒单审计（`*.risk.log`） | **怀疑风控拒单**时优先 |

**示例（API 与 CLI）**：

```python
import qteasy as qt
arts = qt.list_live_trade_artifacts(account_id=1, data_source=qt.QT_DATA_SOURCE)
print(arts['sys_log'], arts['trade_log'], arts['break_point'], arts['risk_log'])
# 若 CLI 提示 risk 拒单，可单独打开：
print(arts['risk_log'])
```

在 Trader Shell 也可输入 `artifacts`（别名 `ls-artifacts`）获得相同四键路径。

**路径规则（简要）**：

- 相对路径相对于 qteasy 根目录；绝对路径与 `~/...` 家目录均支持  
- `sys_log_file_path` / `trade_log_file_path` 可在运行中用 `qt.configure(...)` 修改并立即生效  

## 2. 日志轮换

长期 live 会积累 CSV 与 risk 日志。qteasy 按 **`trade_log_keep_days`**（默认 3 天）清理过期文件。

- **API**：`qt.rotate_trade_logs(days=None)`  
- **CLI**：`rotatelogs`（别名 `rotate-logs`），可选 `--days N`  

清理范围（在当前交易日志目录下）：

- `trade_log_*.csv` / `trade_summary_*.csv` / `value_curve_*.csv`  
- `*.risk.log`  

每次新 Python 进程导入 qteasy 时会**自动轮换一次**；您也可在运维时手动执行上述命令。

## 3. 建议排错顺序（决策树）

请按顺序自问，避免跳步：

**Step 1 — 界面上有没有英文拒因？**  
- 有，且像 `Order rejected by risk rule [...]` → 走 **风控路径**（Step 3）  
- 有 `Order submission failed` 等 → 走 **提交/连接路径**（Step 4）  
- 没有明显报错但行为不对 → Step 6  

**Step 2 — 打开 `artifacts`，确认四个路径可写、文件是否在增长**

**Step 3 — 风控拒单**  
- 查 `risk_log` 中 `<RISK REJECTED>` 与 `rule_id`  
- **不应**出现新的订单表行（与柜台拒单不同）  

**Step 4 — 柜台受理 / 连接**  
- `broker status`：`is_connected` 是否为真（simulator 上表示适配层可受理）  
- 订单表：是否有 `rejected` 且 broker 号为空（柜台拒单）  

**Step 5 — 在途单不一致**  
- DEBUG 模式下：`run --task diagnose_pending_orders`  
- 或 Shell：`reconcile` 看 JSON  

**Step 6 — 配置是否如我所想**  
- `liveconfig --detail` 核对快照  

**Step 7 — 对照 trade_log 与订单状态序列**，以日志**最终状态**为准  

## 4. 高频故障剧本

每节统一：**现象 → 先查什么 → 常见原因 → 下一步**。

### A. 订单被风控拒绝

- **现象**：CLI 英文拒因；提交结果为空 `{}`  
- **先查**：`risk_log` 含 `<RISK REJECTED>`；订单表**无**新行  
- **常见原因**：超单笔上限、不在白名单、非交易时段等  
- **下一步**：调整规则或订单参数，同场景复测；详见 :doc:`3-risk-and-order-lifecycle`  

### B. 提交失败（非风控）

- **现象**：无有效提交记录，或本地校验报错  
- **先查**：`broker status`、现金/持仓是否够、`sys_log` 错误栈  
- **常见原因**：未 connect、字段不合法、资源不足  
- **下一步**：修复连接或字段后重试  

### C. 柜台受理拒单

- **现象**：订单表有行，`status=rejected`，`broker_order_id` 为空  
- **先查**：trace、受理返回的 `reason`  
- **常见原因**：模拟券商规则不接受该委托（与风控无关）  
- **下一步**：对照 :doc:`6-trader-snapshot-gate` 拒单表，勿与风控混淆  

### D. 长期 partial-filled

- **现象**：订单一直是部分成交  
- **先查**：累计成交量 vs 委托数量  
- **常见原因**：回报尚未凑满；或行情导致分批成交慢  
- **下一步**：结合成交回报判断是否应变为 `filled`  

### E. 收盘后状态不确定

- **现象**：收盘后不知在途单如何处理  
- **先查**：`post_close` 相关 trace、`reconcile` JSON  
- **下一步**：核对撤单与最终状态  

### F. broker_order_id / 在途单异常

当本地订单状态、券商委托号或在途单列表「对不上」时，现象多样但都可归入下表几类。本表位于 live **5-C 可观测**范畴，与 :doc:`6-trader-snapshot-gate` 诊断字段一致；simulator 上远端列常为空，属正常。

**各列含义**：**现象**为您观察到的矛盾；**先查**为第一证据来源；**下一步**为建议动作（只读诊断为主，不自动改单）。

**如何使用**：匹配「现象」行 → 执行「先查」→ 若仍不明，DEBUG 下 `run --task diagnose_pending_orders`。

| 现象 | 先查 | 下一步 |
|------|------|--------|
| 风控拒单 | `risk_log`，无新订单行 | 调规则 |
| 柜台拒单 | 订单 `rejected`，broker 空 | trace / reason |
| 已 submitted 但无 broker id | 受理 ACK 与回写 | :doc:`4-broker-adapter-and-integration` |
| 本地与远端在途不一致 | DEBUG：`run --task diagnose_pending_orders` | 只读诊断；simulator 远端常为空 |

CLI 辅助：`reconcile`、`gate`。

### G. 界面与日志不一致

- **现象**：CLI 提示与事后查日志感觉矛盾  
- **先查**：按**时间顺序**对齐同一订单 ID 的全链路记录  
- **下一步**：以日志**最终状态**为准复盘  

## 5. 运维建议

- 定期看交易日志目录占用；必要时 `rotatelogs --days N`  
- 关键运行日保存 `liveconfig --detail` 输出截图或文本  
- 长跑或发版前对照 :doc:`7-manual-smoke-live-grid-roadmap`  

## 6. 快速检查清单

- [ ] 账户正确  
- [ ] 配置生效（`liveconfig`）  
- [ ] 风控是否拒绝（`risk_log`）  
- [ ] 券商是否可受理（`broker status`）  
- [ ] 受理成功是否回写 `broker_order_id`  
- [ ] 四键路径可读（`artifacts`）  

## 7. 常用英文提示与中文含义

```text
Order rejected by risk rule [MAX_ORDER_QTY]: order quantity exceeds limit
```

**含义**：本地风控规则 **MAX_ORDER_QTY** 拒绝——数量超限。查 `risk_log`，不是券商拒单。

```text
<RISK REJECTED> rule_id='MAX_ORDER_QTY' reason='...' symbol='000001.SZ' ...
```

**含义**：同上，结构化风控日志行，便于搜索。

```text
Order submission failed.
```

**含义**：提交链路失败（非风控通过后的柜台拒单），查连接与 `sys_log`。

```text
[NOT_IMPLEMENTED] sync_from_broker is reserved for QMT broker integration (S2.1-b).
```

**含义**：`sync` 命令尚未实现真实远端同步，属预期提示，不是运行故障。

## 8. 相关跳转

- 启动与配置：:doc:`2-configuration-and-run`  
- 生命周期：:doc:`3-risk-and-order-lifecycle`  
- 快照/门禁/拒单：:doc:`6-trader-snapshot-gate`  
- 手工冒烟：:doc:`7-manual-smoke-live-grid-roadmap`  
- CLI 对照：:doc:`8-cli-trader-capability-matrix`  
- Broker：:doc:`4-broker-adapter-and-integration`  
- 实操教程：[tutorials/8-live-trade-risk-and-broker-walkthrough.md](../tutorials/8-live-trade-risk-and-broker-walkthrough.md)  
