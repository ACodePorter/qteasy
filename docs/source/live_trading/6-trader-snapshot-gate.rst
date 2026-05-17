策略快照、启动门禁与长期可观测（5-A / 5-B / 5-C）
======================================================

亲爱的用户，本章介绍三项**进阶**能力：策略运行前的**数据快照**、开盘前的**启动门禁**、以及长跑时的**对账与日志**。若您尚未跑通基础 live，请先阅读 :doc:`2-configuration-and-run`。

> **本章解决什么问题**  
> 分钟级策略若在每一步都重复拉数据，既慢又容易缺行情；开盘前若配置或数据未就绪就下单，风险大。我们把这些检查做成可配置机制，并在日志里留痕，便于您复盘。

内部代号对照（维护者/冒烟文档会用到）
--------------------------------------

在 qteasy live 演进中，**5-A / 5-B / 5-C** 分别指策略快照、启动门禁与长期可观测三类能力。冒烟文档与维护者笔记会使用代号；作为用户，您只需记住右侧「用户向名称」即可。下表建立代号与日常说法的对应关系——阅读本章后文时，可将「5-B」理解为「启动门禁」。

**各列含义**：**代号**为内部阶段编号；**用户向名称**为文档推荐叫法；**一句话**为该能力在 live 链路中的位置。

**如何使用**：看到正文出现 ``5-A`` 等代号时查本表；配置键名称见 :doc:`2-configuration-and-run` §4「策略快照」「启动门禁」行。

.. list-table::
   :header-rows: 1
   :widths: 12 38 50

   * - 代号
     - 用户向名称
     - 一句话
   * - **5-A**
     - 策略快照
     - 策略运行前预先拉好数据，本步复用，减少重复 IO
   * - **5-B**
     - 启动门禁
     - 开盘/run 前检查就绪状态，失败可告警或阻断
   * - **5-C**
     - 长期可观测
     - 订单与券商号映射、risk 日志轮换、对账与在途单诊断

5-A：策略快照（prepare_strategy_snapshot）
------------------------------------------

**您可以把它理解为**：每次策略要「上考场」前，先把试卷和材料在案头摆好；真正答题时不再临时跑去打印室。

- 当 ``live_trade_split_strategy_prepare=True`` 时，qteasy 会在每个 ``run_strategy`` 计划时刻**之前**插入 ``prepare_strategy_snapshot`` 任务（提前量由 ``live_trade_prepare_lead_seconds`` 控制；``0`` 表示同刻入队，但排序仍保证先 prepare）。
- ``prepare_strategy_snapshot`` 内完成原先 ``run_strategy`` 前的重活：子日频数据刷新、准备数据缓冲、更新 live 价、注入过程数据等；完成后在内存留下「快照有效」标记（交易日 + 步序号 + 时间）。
- 随后 ``run_strategy`` 若发现快照仍在 ``live_trade_strategy_snapshot_max_age_seconds`` 内且步序号一致，则**不再重复**上述拉取；否则记 ``snapshot_missing`` / ``snapshot_stale`` 并**跳过本步策略**（避免用过期数据算信号）。
- 开启 split 时，``prepare_strategy_snapshot`` 与 ``run_strategy`` 在**主线程同步**执行（与异步拉 live 价的任务分离），避免多线程同时碰 Operator。

**与真实行为的差异**：快照在内存中，进程重启后需重新 prepare；不是磁盘上的永久缓存。

5-B：启动门禁（run_startup_gate）
----------------------------------

**您可以把它理解为**：发车前的**安全检查**——策略是否就绪、必要数据表是否在、（可选）本地账本是否与券商端一致。

- ``live_trade_startup_gate_mode``：

  - ``off`` — 关闭门禁  
  - ``warn`` — 失败只记日志/trace，**仍允许**交易（建议灰度先用）  
  - ``block`` — 失败则拒绝 ``run_strategy`` 入队（``skip_reason=gate_failed``）

- Trader 在生成当日日程后会调用门禁（非交易日快速跳过）。
- 检查分层（失败码会写入 trace ``failures``）：

  - **L1**：Operator 是否就绪、账户是否存在  
  - **L2**：主历史表是否在数据源中（按 ``asset_type`` 映射日频表等）  
  - **L3**（可选）：若 Broker 返回非空远端现金/持仓，则与本地比对；未实现远端 API 时不硬比  

手工冒烟全清单见 :doc:`7-manual-smoke-live-grid-roadmap`。

5-C：账本、日志与恢复可观测
----------------------------

在 5-A/5-B 之上，便于**长跑排障与审计**（**不含**自动改单/补偿；真实 QMT 远端查询属后续版本）：

- **订单 ↔ 券商号映射**：受理成功后回写 ``broker_order_id`` / ``broker_name``；受理拒单则 ``rejected`` 且 broker 字段空。
- **日志轮换扩展**：``rotate_trade_logs`` 除 trade CSV 外也清理超期 ``*.risk.log``（规则见 :doc:`5-artifacts-and-troubleshooting`）。
- **对账与诊断 trace**：

  - ``pre_open`` / ``post_close`` 后输出 ``reconcile`` 检查点（``checkpoint_passed`` / ``checkpoint_warn`` 等）  
  - DEBUG 任务 ``diagnose_pending_orders``：只读对比本地与远端在途单差异  

给新手的结论：两种「拒单」
--------------------------

在 live 订单链路中，「被拒」可能发生在 **RiskManager 复核台**（风控）或 **Broker 受理**（柜台）两个站点，证据位置完全不同。:doc:`3-risk-and-order-lifecycle` 已从流程角度说明；下表从**订单表与 broker_order_id** 角度给出对照，供排错时快速对号入座。

**各列含义**：**路径**为拒单/成功类型；**本地订单表**是否新增行；**broker_order_id** 是否回写；**审计**建议优先打开的文件或表。

**如何使用**：CLI 有 risk 英文拒因且无新订单 → 第一行；订单列表出现 ``rejected`` 且 broker 号空 → 第二行；有 broker 号 → 第三行，再查成交状态。

**示例**：``risk_log`` 含 ``<RISK REJECTED>`` 且 ``orders`` 无对应新单 → 风控拒单，勿去查券商 connect。

.. list-table::
   :header-rows: 1
   :widths: 22 28 18 32

   * - 路径
     - 本地订单表
     - broker_order_id
     - 审计
   * - **风控拒单**
     - **不入库**
     - —
     - ``*.risk.log`` + ``<RISK REJECTED>``
   * - **柜台受理拒单**
     - 有行，``rejected``
     - **空**
     - 订单表 + trace
   * - **受理成功**
     - ``submitted`` 等
     - **回写**
     - 订单表 + trace

diagnose_pending_orders 输出字段（简要）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``local_pending_count`` — 本地在途单数  
- ``remote_pending_count`` — 远端在途单数（simulator 常为空）  
- ``local_pending_without_broker_order_id`` — 已提交但缺券商号的本地单  
- ``local_pending_missing_remote`` — 本地有券商号但远端不存在  
- ``remote_pending_not_in_local`` — 远端有、本地未映射  

CLI 与 DEBUG（运维）
--------------------

Trader Shell（``--ui cli``）常用命令（help 为英文）：

- ``gate`` / ``startup-gate`` — 手动跑启动门禁  
- ``reconcile`` / ``snapshot-reconcile`` — 对账 JSON  
- ``run --task diagnose_pending_orders`` — 在途单诊断（需 **DEBUG**）  
- ``artifacts`` / ``ls-artifacts`` — 四键产物路径  
- ``rotatelogs`` / ``rotate-logs`` — 手动日志轮换  
- ``broker status|connect|disconnect`` — 券商会话（simulator 为标志位）  
- ``sync`` / ``pull-state`` — **预留**，尚未实现真实远端同步  

下一交易日观察建议
------------------

- **5-A**：trace 里 ``strategy_run_skipped`` 是否过多；live 价频率是否不低于策略步频。  
- **5-B**：先用 ``warn``，核对 ``gate_warn`` / ``gate_failed``；CLI ``gate`` 复验后再试 ``block``。  
- **5-C**：收盘 ``reconcile``、``diagnose_pending_orders``；必要时 ``rotatelogs --days N`` 验证 risk 清理。  

相关文档
--------

- 配置：:doc:`2-configuration-and-run`  
- 排错：:doc:`5-artifacts-and-troubleshooting`  
- 冒烟：:doc:`7-manual-smoke-live-grid-roadmap`  
- CLI：:doc:`8-cli-trader-capability-matrix`  
