CLI 与 Trader 能力对照表
==========================

本页汇总 **Trader Shell**（``--ui cli``）与 ``Trader`` / ``Broker`` 公有能力的对应关系，
供运维、冒烟与 S2.1 接入前核对命令面。实现真源：``qteasy/trader_cli.py``。

适用范围
--------

- 进入方式：``qt.run(op, mode=0, ...)`` 且 ``live_trade_ui_type='cli'``（或示例 ``--ui cli``）
- **DEBUG 模式**：``run --task ...`` 及手动 ``run_strategy`` 仅在 Trader ``debug=True`` 时可用
- 用户可见 help / 输出为 **英文**；本文档说明为中文

命令别名（precmd）
------------------

Shell 将下列别名 rewrite 为内部命令名：

.. list-table::
   :header-rows: 1
   :widths: 28 22

   * - 用户输入别名
     - 内部命令
   * - ``ls-artifacts``
     - ``artifacts``
   * - ``live-config``
     - ``liveconfig``
   * - ``startup-gate``
     - ``gate``
   * - ``snapshot-reconcile``
     - ``reconcile``
   * - ``rotate-logs``
     - ``rotatelogs``
   * - ``pull-state``
     - ``sync``

能力对照表
----------

.. list-table::
   :header-rows: 1
   :widths: 26 28 22 24

   * - Trader / Broker 能力
     - 绑定 API（摘要）
     - CLI 命令
     - 状态
   * - 状态 / 暂停 / 退出
     - ``status``, ``pause``, ``resume``, ``stop`` 等
     - ``status`` ``pause`` ``resume`` ``bye`` …
     - 已有
   * - 手动下单 / 撤单
     - ``submit_trade_order``, broker ``cancel``
     - ``buy`` ``sell`` ``cancel ORDER_ID``
     - 已有
   * - 配置读写
     - ``get_config`` / ``update_config``
     - ``config``
     - 已有
   * - 磁盘产物路径
     - ``qt.list_live_trade_artifacts``
     - ``artifacts`` / ``ls-artifacts``
     - implemented
   * - Live 配置摘要
     - ``build_live_trade_config`` → ``to_summary_dict``
     - ``liveconfig`` / ``live-config``
     - implemented
   * - 任务队列
     - ``list_tasks`` / ``get_task`` / ``cancel_task``
     - ``tasks`` / ``task``
     - implemented
   * - 启动门禁
     - ``run_startup_gate``
     - ``gate`` / ``startup-gate``
     - implemented
   * - 对账快照
     - ``collect_broker_reconcile_snapshot``
     - ``reconcile`` / ``snapshot-reconcile``
     - implemented
   * - 在途单诊断
     - ``_diagnose_pending_orders`` / ``collect_pending_order_diagnostics``
     - ``run --task diagnose_pending_orders``（DEBUG）
     - implemented
   * - 日志轮换
     - ``qt.rotate_trade_logs``
     - ``rotatelogs`` / ``rotate-logs``
     - implemented
   * - Broker 会话
     - ``connect`` / ``disconnect`` / ``is_connected``
     - ``broker status|connect|disconnect``
     - implemented
   * - 远端状态同步
     - （S2.1-b ``sync_from_broker`` 类 API，尚未实现）
     - ``sync`` / ``pull-state``
     - **stub**
   * - 主循环生命周期
     - ``start`` / ``run`` / ``join``
     - —
     - 仅 Operator / Notebook

DEBUG ``run --task`` 白名单
---------------------------

仅在 **DEBUG** 模式下可通过 ``run --task TASK`` 手动触发：

- ``process_result``
- ``pre_open``
- ``open_market``
- ``close_market``
- ``post_close``
- ``refill``（参数经 ``--args`` 传入）
- ``diagnose_pending_orders``

Broker 子命令
-------------

``broker``  positional 子命令（``BROKER_SUBCOMMANDS``）：

- ``status`` — 打印 ``broker_name``、``status``、``is_connected``、``is_registered``
- ``connect`` — 调用 ``broker.connect()``（Simulator 为适配层标志）
- ``disconnect`` — 调用 ``broker.disconnect()``

stub 行为说明
-------------

``sync`` / ``pull-state`` 执行时打印固定前缀并返回失败，例如：

.. code-block:: text

   [NOT_IMPLEMENTED] sync_from_broker is reserved for QMT broker integration (S2.1-b).

S2.1 实现远端同步后，help 标注由 ``(stub)`` 迁移为 ``(implemented)``，测试与本文档同步更新。

相关文档
--------

- 快照 / 门禁 / 拒单语义：:doc:`6-trader-snapshot-gate`
- 手工冒烟阶段 11：:doc:`7-manual-smoke-live-grid-roadmap`
- 产物与排错：:doc:`5-artifacts-and-troubleshooting`
- 配置与启动：:doc:`2-configuration-and-run`
