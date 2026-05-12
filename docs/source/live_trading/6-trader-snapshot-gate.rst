Trader 主链路快照与启动门禁（阶段 5-A / 5-B）
================================================

本页记录 **阶段 5-A（策略前市场数据准备与 ``run_strategy`` 分工）** 与 **阶段 5-B（启动门禁）**
的语义、相关配置键及合入后建议在 **下一交易日** 人工观察的要点。

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

与 **下一交易日** 基于 ``examples/live_grid_multi.py`` 的 **全阶段手工冒烟清单**（路线图 0～5-A/B）见同目录文档
:doc:`7-manual-smoke-live-grid-roadmap`；本页仅覆盖 5-A/5-B 技术语义与配置要点。

下一交易日验证建议
--------------------

- **5-A**：关注 ``live_strategy`` trace 中 ``strategy_market_inputs_ready`` 与 ``strategy_run_skipped`` 比例；
  子日频策略确认 ``acquire_live_price`` 频率不低于策略步频，避免 ``snapshot_stale`` 过高。
- **5-B**：先用 ``warn`` 灰度，核对 ``startup_gate`` trace 中 ``gate_warn`` / ``gate_failed`` 与
  ``failures`` 字段；确认无误后再切 ``block``。
