CLI 与 Trader 能力对照表
==========================

亲爱的用户，本章汇总 **Trader Shell**（命令行界面）里有哪些命令、分别解决什么问题。Shell 里 help 与即时输出为**英文**；下表说明为中文。

> **如何进入 Shell**  
> ``qt.run(op, mode=0, ...)`` 且 ``live_trade_ui_type='cli'``，或运行示例时加 ``--ui cli``。进入后您可在提示符下输入命令，像与交易员对话。

适用范围
--------

- 进入方式：``qt.run(op, mode=0, ...)`` 且 ``live_trade_ui_type='cli'``（或示例 ``--ui cli``）  
- **DEBUG 模式**：``run --task ...`` 及若干调试任务仅在 Trader ``debug=True`` 时可用（启动加 ``--debug``，或 Shell 内 ``debug`` 命令切换）  
- 用户可见 help / 输出为 **英文**；本文档说明为中文  

命令别名
--------

Trader Shell 支持**短别名**，便于少打字。别名在 qteasy 内部 rewrite 为正式命令名后再执行——help 与日志仍以正式名为准。下表仅列运维相关别名；完整命令面见后文「能力对照表」。

**各列含义**：**您输入的别名**为 Shell 接受的写法；**内部命令**为实际调用的 ``do_*`` 处理器名。

**如何使用**：习惯用连字符写法时查左列；脚本或文档引用正式名时用右列。例如排错文档写 ``gate``，您也可输入 ``startup-gate``。

**示例**：查日志路径时输入 ``ls-artifacts`` 与 ``artifacts`` 效果相同。

.. list-table::
   :header-rows: 1
   :widths: 28 22

   * - 您输入的别名
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

本表是 **Trader / Broker 公有能力** 与 **Shell 命令** 的主索引：左侧是「qteasy 能做什么」，中间是「您该输入什么」，右侧是「当前版本是否已实现」。在 live 子系统中，CLI 是运维与冒烟的主入口之一；API 列供您在 Notebook 或脚本中调用同一能力。

**各列含义**：

- **能力**：Trader/Broker 侧功能域  
- **典型用途**：您何时需要用它（排错场景）  
- **绑定 API（摘要）**：Python 侧入口（非完整签名）  
- **CLI 命令**：Shell 中名称；``—`` 表示无直接 CLI  
- **状态**：``已支持`` / ``预留``（尚未实现）  

**如何使用**：按「典型用途」找行——例如要找日志目录 → 找「查日志文件落在哪」→ 用 ``artifacts``。状态为 ``预留`` 时勿当作故障（如 ``sync``）。

**示例**：启动后想核对 live 配置 → 典型用途「核对当前 live 配置是否生效」→ 命令 ``liveconfig`` 或 ``live-config``。

.. list-table::
   :header-rows: 1
   :widths: 22 24 18 18 18

   * - 能力
     - 典型用途
     - 绑定 API（摘要）
     - CLI 命令
     - 状态
   * - 状态 / 暂停 / 退出
     - 看是否在跑、暂停/恢复、退出 Shell
     - ``status``, ``pause``, ``resume``, ``stop`` 等
     - ``status`` ``pause`` ``resume`` ``bye`` …
     - 已支持
   * - 手动下单 / 撤单
     - 人工试单或撤单
     - ``submit_trade_order``, ``cancel``
     - ``buy`` ``sell`` ``cancel ORDER_ID``
     - 已支持
   * - 配置读写
     - 查看或改运行中配置
     - ``get_config`` / ``update_config``
     - ``config``
     - 已支持
   * - 磁盘产物路径
     - **查日志文件落在哪**
     - ``qt.list_live_trade_artifacts``
     - ``artifacts`` / ``ls-artifacts``
     - 已支持
   * - Live 配置摘要
     - **核对当前 live 配置是否生效**
     - ``build_live_trade_config`` → ``to_summary_dict``
     - ``liveconfig`` / ``live-config``
     - 已支持
   * - 任务队列
     - 看排队任务、取消任务
     - ``list_tasks`` / ``cancel_task`` 等
     - ``tasks`` / ``task``
     - 已支持
   * - 启动门禁
     - **手动跑一次开盘前检查**
     - ``run_startup_gate``
     - ``gate`` / ``startup-gate``
     - 已支持
   * - 对账快照
     - 收盘等时点看对账 JSON
     - ``collect_broker_reconcile_snapshot``
     - ``reconcile`` / ``snapshot-reconcile``
     - 已支持
   * - 在途单诊断
     - 本地 vs 远端在途单差异（只读）
     - ``collect_pending_order_diagnostics``
     - ``run --task diagnose_pending_orders``（DEBUG）
     - 已支持
   * - 日志轮换
     - **手动清理过期 CSV / risk 日志**
     - ``qt.rotate_trade_logs``
     - ``rotatelogs`` / ``rotate-logs``
     - 已支持
   * - Broker 会话
     - 看模拟券商是否「已连接」
     - ``connect`` / ``disconnect`` / ``is_connected``
     - ``broker status|connect|disconnect``
     - 已支持
   * - 远端状态同步
     - 从真实券商拉状态（尚未实现）
     - （预留 ``sync_from_broker`` 类 API）
     - ``sync`` / ``pull-state``
     - **预留**
   * - 主循环生命周期
     - 脚本/Notebook 侧启停
     - ``start`` / ``run`` / ``join``
     - —
     - 仅 Operator / Notebook

DEBUG ``run --task`` 白名单
---------------------------

仅在 **DEBUG** 模式下可通过 ``run --task TASK`` 手动触发（启动时 ``--debug`` 或 Shell 内 ``debug``）：

- ``process_result``  
- ``pre_open`` / ``open_market`` / ``close_market`` / ``post_close``  
- ``refill``（参数经 ``--args`` 传入）  
- ``diagnose_pending_orders``  

Broker 子命令
-------------

- ``broker status`` — 打印券商名、连接状态等  
- ``broker connect`` — 建立适配层会话（simulator 为标志位）  
- ``broker disconnect`` — 断开会话  

预留：sync
----------

``sync`` / ``pull-state`` 执行时会提示尚未实现，例如：

.. code-block:: text

   [NOT_IMPLEMENTED] sync_from_broker is reserved for QMT broker integration (S2.1-b).

**含义**：真实「从券商同步持仓/订单」尚未接入；看到此提示是预期行为，不是故障。

相关文档
--------

- 快照 / 门禁 / 拒单：:doc:`6-trader-snapshot-gate`  
- 手工冒烟：:doc:`7-manual-smoke-live-grid-roadmap`  
- 产物与排错：:doc:`5-artifacts-and-troubleshooting`  
- 配置与启动：:doc:`2-configuration-and-run`  
