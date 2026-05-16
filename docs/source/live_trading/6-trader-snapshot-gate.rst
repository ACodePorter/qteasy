Trader 主链路快照与启动门禁（阶段 5-A / 5-B / 5-C）
======================================================

本页记录 **阶段 5-A（策略前市场数据准备与 ``run_strategy`` 分工）**、**阶段 5-B（启动门禁）**
与 **阶段 5-C（账本/日志/恢复可观测性）** 的语义、相关配置键及合入后建议在 **下一交易日** 人工观察的要点。

阶段边界（5-A / 5-B / 5-C）
---------------------------

- **5-A**：在 ``live_trade_split_strategy_prepare=True`` 时，将策略运行前的重 I/O（数据刷新、
  ``prepare_data_buffer``、实时价等）前移到 ``prepare_strategy_snapshot``，供后续 ``run_strategy`` 复用快照。
- **5-B**：``run_startup_gate`` 在启动/当日日程生成后校验 Operator 就绪、主历史表与（可选）Broker 远端账本；
  ``block`` 模式下失败可阻止 ``run_strategy`` 入队。
- **5-C**：本地订单与 ``broker_order_id`` 映射、``*.risk.log`` 与 trade 日志轮换、``reconcile`` 检查点 trace、
  在途单只读诊断。**不含**自动改单/补偿流程，**不含**真实 QMT 远端查询（见 S2.1）。

5-A：``prepare_strategy_snapshot`` 与快照复用
----------------------------------------------

- 配置 ``live_trade_split_strategy_prepare=True`` 时，``create_daily_task_plan`` 会在每个
  ``run_strategy`` 计划时刻之前插入 ``prepare_strategy_snapshot``（提前量由
  ``live_trade_prepare_lead_seconds`` 控制，``0`` 表示与 ``run_strategy`` 同时刻入队，排序仍保证先 prepare）。
- ``prepare_strategy_snapshot`` 内同步执行原 ``run_strategy`` 前的重 I/O：子日频数据源刷新、
  ``check_and_prepare_live_trade_data``、``prepare_data_buffer`` / ``create_data_windows``、
  ``_update_live_price`` 及过程数据注入；完成后写入内存标记（交易日 + ``step_index`` + 单调时钟）。
- 随后 ``run_strategy`` 若判定快照在 ``live_trade_strategy_snapshot_max_age_seconds`` 内且
  ``step_index`` 一致，则**不再**重复上述拉取；否则记 ``snapshot_missing`` / ``snapshot_stale`` 并跳过本步策略执行。
- 在 split 开启时，``run_strategy`` 与 ``prepare_strategy_snapshot`` 均在 **主线程同步** 执行
 （与 ``acquire_live_price`` 的异步线程池分离），避免 ``Operator`` 跨线程无锁访问。

5-B：``run_startup_gate`` 与 ``run_strategy`` 入队
--------------------------------------------------

- ``live_trade_startup_gate_mode``：``off`` 关闭；``warn`` 失败仅记录 trace，仍允许交易；
  ``block`` 失败则 ``run_startup_gate`` 返回 ``False``，且 ``add_task('run_strategy', …)`` 会以
  ``skip_reason=gate_failed`` 拒绝入队。
- ``Trader._start`` 在生成当日日程后调用 ``run_startup_gate()``（非交易日快速跳过）。
- 门禁分层（可观测失败码拼入 trace ``failures``）：

  - L1：``Operator.is_ready``、账户存在；
  - L2：主历史表是否在数据源表清单中（按 ``asset_type`` 映射 ``stock_daily`` / ``fund_daily`` / ``index_daily``）；
  - L3（可选）：若 ``Broker.get_remote_cash`` / ``get_remote_positions`` 返回非空，则与本地账本比对；
    未实现远端 API 的券商返回占位 ``None``/空列表时不做此项硬断言。

与 **下一交易日** 基于 ``examples/live_grid_multi.py`` 的 **全阶段手工冒烟清单**（路线图 0～5-C / 阶段 11）见同目录文档
:doc:`7-manual-smoke-live-grid-roadmap`；本页覆盖 5-A/5-B/5-C 技术语义与配置要点。

5-C：账本/日志/恢复（长期运行可观测）
-------------------------------------

本次在 5-A/5-B 基础上补充了三类长期运行能力，便于排障与审计：

- **订单受理映射（新增列）**：``sys_op_trade_orders`` 增加可空 ``broker_order_id`` 与 ``broker_name``。
  在 ``submit_with_ack`` 返回 ``accepted=True`` 后立即回写；若受理拒单，字段保持空值且状态为 ``rejected``。
- **日志轮换覆盖扩展**：``rotate_trade_logs()`` 现在除 ``trade_log`` / ``trade_summary`` /
  ``value_curve`` 外，也会清理超期 ``*.risk.log``（按 ``trade_log_keep_days``，优先文件名时间戳，失败退回 ``mtime``）。
- **恢复诊断与检查点 trace**：

  - ``pre_open`` / ``post_close`` 结束后会输出 ``reconcile`` 分类检查点 trace（``checkpoint_passed`` /
    ``checkpoint_warn``，含 ``cash_diff`` / ``position_qty_diff`` / ``remote_orders_count``）；
  - 新增只读诊断任务 ``diagnose_pending_orders``，用于输出「本地在途单 vs Broker 远端在途单」差异摘要。

说明：5-C **不**启用自动改单/自动补偿；真实 QMT ``get_remote_*`` 真数据属于 **S2.1**，Simulator 上远端字段多为占位。

风控拒单 vs 柜台拒单
--------------------

两类「拒单」语义不同，排障时须区分：

.. list-table::
   :header-rows: 1
   :widths: 22 28 18 32

   * - 路径
     - 本地 ``sys_op_trade_orders``
     - ``broker_order_id``
     - 审计
   * - **风控拒单**（``RiskManager`` 前置）
     - **不入库**（``submit_trade_order`` 返回空 ``{}``）
     - —
     - ``*.risk.log`` + ``<RISK REJECTED>`` 消息
   * - **柜台受理拒单**（``submit_with_ack accepted=False``）
     - 有行，``status=rejected``
     - **空**
     - 订单表 + trace
   * - **受理成功**
     - ``submitted`` 等
     - **回写**
     - 订单表 + trace

``diagnose_pending_orders`` 的主要输出字段
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``local_pending_count``：本地在途订单数（``created`` / ``submitted`` / ``partial-filled``）。
- ``remote_pending_count``：远端在途订单数（按 ``broker_order_id`` 或远端订单 ID 统计）。
- ``local_pending_without_broker_order_id``：本地 ``submitted``/``partial-filled`` 但缺少 ``broker_order_id`` 的订单 ID 列表。
- ``local_pending_missing_remote``：本地有 ``broker_order_id`` 但远端不存在的委托号列表。
- ``remote_pending_not_in_local``：远端存在但本地未发现映射的委托号列表。

``rotate_trade_logs`` 与 ``*.risk.log``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- 扫描目录为模块级 **`QT_TRADE_LOG_PATH`**；通过 ``qt.configure(trade_log_file_path=...)`` 热修改后会随
  ``_refresh_log_paths()`` 更新（与 ``list_live_trade_artifacts`` 一致）。
- 匹配 ``trade_log_*.csv``、``trade_summary_*.csv``、``value_curve_*.csv`` 与 ``*.risk.log``。
- CSV 类文件优先从文件名解析 ``%Y%m%d_%H%M%S``；``*.risk.log`` 通常无时间戳，退回 **mtime** 判断。
- 无头验收参考 ``tests/notebook_trader_headless_script.py`` 中 ``stage11_phase5_c_smoke`` 的 risk 轮换段。

CLI 与 DEBUG 任务（运维 / 冒烟）
--------------------------------

Trader Shell（``--ui cli``）可用命令（用户可见英文 help）：

- ``gate`` / ``startup-gate`` — 手动 ``run_startup_gate()``
- ``reconcile`` / ``snapshot-reconcile`` — ``collect_broker_reconcile_snapshot()`` JSON
- ``run --task diagnose_pending_orders`` — 在 **DEBUG** 模式下触发在途单诊断
- ``artifacts`` / ``ls-artifacts`` — 四键产物路径（``sys_log`` / ``trade_log`` / ``break_point`` / ``risk_log``）
- ``rotatelogs`` / ``rotate-logs`` — 手动 ``qt.rotate_trade_logs(days=...)``（使用当前 ``QT_TRADE_LOG_PATH``）
- ``broker status|connect|disconnect`` — Broker 会话状态（Simulator 上 connect 仅为适配层标志）
- ``sync`` / ``pull-state`` — **stub**，预留 S2.1-b ``sync_from_broker``

下一交易日验证建议
--------------------

- **5-A**：关注 ``live_strategy`` trace 中 ``strategy_market_inputs_ready`` 与 ``strategy_run_skipped`` 比例；
  子日频策略确认 ``acquire_live_price`` 频率不低于策略步频，避免 ``snapshot_stale`` 过高。
- **5-B**：先用 ``warn`` 灰度，核对 ``startup_gate`` trace 中 ``gate_warn`` / ``gate_failed`` 与
  ``failures`` 字段；CLI 可执行 ``gate`` 复验；确认无误后再切 ``block``。
- **5-C**：收盘后核对 ``reconcile`` trace、``diagnose_pending_orders`` 字段；必要时 ``rotatelogs --days N`` 验证 risk 日志清理。
