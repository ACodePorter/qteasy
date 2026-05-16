模拟实盘手动冒烟方案（live_grid_multi × 路线图阶段 0～5-A/B）
======================================================================

本文档供 **下一交易日** 使用 **新测试账户、从零持仓** 做一次集中手工验证；策略基线采用仓库示例
``examples/live_grid_multi.py``（5 分钟 VS + 多标的网格）。路线图权威表述见
``.cursor/plans/trader架构升级路线图_0650f0d5.plan.md``（仓库或 Cursor 计划目录中的同名文件）。

与无头脚本的关系
----------------

- 仓库 ``tests/notebook_trader_headless_script.py`` 提供 **十一阶段** 无头冒烟（含 **阶段 9：5-A/5-B**、
  **阶段 10：4-C**、**阶段 11：5-C**），
  可在 Notebook 中分 cell 调用；**本手册**侧重 **真实 ``qt.run`` + 示例策略 + 人眼验收**。
- 建议节奏：**交易日盘中/收盘后** 按本手册走 live；**非交易时段或回放日** 用无头脚本做架构回归。

一、环境与前置条件
------------------

1. **解释器**：``/opt/anaconda3/envs/py39/bin/python``；工作目录为 qteasy 仓库根（与 ``examples/live_grid_multi.py`` 中 ``sys.path`` 一致）。
2. **新账户、无持仓**：

   - 使用 ``get_qt_argparser`` 的 ``-n/--new_account <用户名>`` 创建新账户；或
   - 使用已有 ``account_id`` 且 ``--restart`` 清空该账户交易记录（示例脚本内 ``delete_account(..., keep_account_id=True)``），
     并确认 ``sys_op_positions`` 无持仓后再启动。
3. **数据**：子日频策略需已具备 ``stock_1min``（或示例中启用的 refill 表）覆盖测试区间；首次运行可接受较长 refill。
4. **日志**：确认 ``qteasy.cfg`` / ``qt.configure`` 下 ``sys_log_file_path``、``trade_log_file_path`` 可写，便于阶段 0/5 验收。

二、启动命令模板（与示例对齐）
------------------------------

在仓库根目录执行（按你的账户与 UI 调整）::

   /opt/anaconda3/envs/py39/bin/python examples/live_grid_multi.py \\
       -a <ACCOUNT_ID> -n <NEW_USER_NAME_OR_OMIT> \\
       --ui cli \\
       [--debug] [--restart]

说明：

- **无持仓冷启动**：建议新建 ``-n`` 账户 **或** ``--restart`` 后人工确认持仓为空。
- 示例内 ``asset_pool``、``par_values``、``run_freq='5min'`` 与 ``live_trade_*`` 配置可按冒烟范围微调；**不要**在不明环境下放大 ``trade_batch`` 以免资金压力。

三、路线图阶段与手工验收（逐项打勾）
------------------------------------

下列「阶段」对应路线图 **0 / 1 / 2 / 3 / 3.5 / 4-A / 4-B / 5-A / 5-B**；每项均给出 **操作建议** 与 **验收标准**。

阶段 0：基线、状态机与可观测性
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**：启动后观察 CLI/TUI 或日志中 ``Trader`` 状态迁移（``stopped`` → ``sleeping``/``running`` 等）、任务入队/出队、Broker 侧日志。
- **验收**：

  - 状态机与白名单任务语义与文档一致，无未解释死锁；
  - 至少能通过日志还原一次「启动 → 日程生成 → 关键任务」的时间顺序（原则 6、7）。

阶段 1：运行时生命周期（headless 友好）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**：使用 **显式** ``stop``/退出流程结束会话（勿强杀后无说明）；若用 Notebook，可配合无头脚本的 ``shutdown_session`` 理解停止序列。
- **验收**：进程退出后无僵尸线程；断点/日志无异常截断；与「UI 仅调运行时 API」一致（不在本手册展开 UI 细节）。

阶段 2：任务管理、受控并发、重试/死信
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**：在 **非交易时段** 或可控窗口内，观察 ``acquire_live_price``、``run_strategy``、``process_result`` 的调度；刻意快速重复投递（若 UI 支持）或依赖日程自然重入。
- **验收**：

  - 主循环与异步任务边界可理解；异常任务有重试/死信或明确日志（原则 4）；
  - 若触发 **SKIP**，日志/消息中含 ``skip_reason=...`` 可统计分桶（与阶段 4-B 衔接）。

阶段 3：日程与 catch-up
~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**：对比 **同一配置、同一交易日** 两次生成的关键任务时刻（或对比无头脚本 ``schedule_size`` / ``next_task``）；若有 **盘中启动**，对照路线图「catch-up」预期。
- **验收**：日程输出可复现；错过窗口后的补跑/不补跑行为与文档或配置一致（原则 1）。

阶段 3.5：成交入账幂等与原子性
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**：完成至少一笔 **模拟成交** 后，在 **隔离环境** 或备份库上重复回放同一成交结果（若你有自定义脚本）；日常冒烟以「成交前后账户/持仓/订单状态一致、无重复扣款」为主。
- **验收**：重复/乱序路径下台帐最终一致；无「半提交」导致的现金与持仓矛盾（原则 2）。

阶段 4-A：Broker 公开 API、主循环不直掏队列
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**：正常跑满半个交易日；关注是否仍有 **弃用路径** 直接依赖 ``broker.result_queue`` 的报错（若版本已收口，应无此类栈）。
- **验收**：成交回报经 ``poll_fills``/等价路径消费；Trader 主循环与示例路径可稳定运行整日（与路线图「4-A/4-B 已整日验证」一致）。

阶段 4-B：任务重入与 SKIP_REASON 分桶
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**：在日志中检索 ``skip_reason=``（如 ``prev_running``、``already_queued``、``gate_failed``、``snapshot_missing``、``snapshot_stale``）。
- **验收**：SKIP 原因可人工归类；与运维分桶字段一致（原则 4、路线图 4-B）。

阶段 5-A：主链路 snapshot（prepare_strategy_snapshot）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**（建议分两步）：

  1. ``qt.configure(live_trade_split_strategy_prepare=False)``：基线行为，确认 ``run_strategy`` 前仍有一次完整数据准备（与旧版一致）。
  2. ``live_trade_split_strategy_prepare=True``，并设置合理的 ``live_trade_prepare_lead_seconds``、
     ``live_trade_strategy_snapshot_max_age_seconds``；**须在 ``qt.run``/创建 Trader 之前** 写入配置，
     以便日程插入 ``prepare_strategy_snapshot``。
- **验收**：

  - 日程或日志中可见 **每个** ``run_strategy`` 步前有 ``prepare_strategy_snapshot``（或同刻排序先 prepare）；
  - 未出现大量无解释的 ``snapshot_stale``/``snapshot_missing``；若出现，核对 **前置任务频率 ≥ 策略步频** 与 ``max_age``。

阶段 5-B：启动门禁（startup gate）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **操作**（建议分档）：

  1. ``live_trade_startup_gate_mode='warn'``：人为制造轻微不一致（如仅测试环境改 Broker 返回值），确认 **仅告警、不阻断**。
  2. ``live_trade_startup_gate_mode='block'``：确认严重失败时 **首笔** ``run_strategy`` 不入队或 ``skip_reason=gate_failed``，且系统日志/trace 可解释。
- **验收**：门禁结果可观测；``block`` 不误杀正常交易日（先 ``warn`` 灰度）。

四、与示例策略强相关的补充检查（live_grid_multi）
--------------------------------------------------

- **多标的 VS + multi_pars**：确认各标的 ``base_grid`` 在首日初始化后写入符合预期；成交与持仓按标的维度变化。
- **子日频数据**：若开启示例中大段 ``live_trade_daily_refill_tables``，关注 refill 批次与耗时；冒烟日可先 **关闭** 大表 refill 以缩短路径，仅保留 ``stock_1min`` 等最小集合。
- **验收**：无持仓起步下，首日大额「初始化买单」符合示例逻辑且资金/费用合理；无 NaN 价格误成交（项目既有 NaN 约定）。

五、Notebook 集中冒烟（可选）
-----------------------------

在 Notebook 中（已 ``import qteasy as qt``）::

    from tests.notebook_trader_headless_script import (
        create_headless_notebook_session,
        stage1_preflight_tests,
        stage2_opening_baseline,
        stage3_intraday_runtime,
        stage4_phase35_checks,
        stage5_stage0to3_regression,
        stage6_closing_reconcile,
        stage7_exception_and_rollback_probe,
        stage9_phase5_ab_smoke,
        stage10_phase4_c_smoke,
        stage11_phase5_c_smoke,
        stage8_conclusion,
        shutdown_session,
    )

    # 可选：在 start 前注入 5-A/5-B 配置（shutdown_session 会恢复这些键）
    overrides = {
        'live_trade_split_strategy_prepare': True,
        'live_trade_prepare_lead_seconds': 60,
        'live_trade_startup_gate_mode': 'warn',
    }
    session = create_headless_notebook_session(
        use_real_time=True,
        use_isolated_datasource=False,
        account_id=<你的测试账户ID>,
        live_trade_smoke_overrides=overrides,
    )
    # 依次执行 stage1 … stage7、stage9、stage10、stage11、stage8，最后：
    shutdown_session(session)

六、当日收工清单（简表）
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 12 28 40

   * - 路线图阶段
     - 你执行的动作摘要
     - 验收（满足则打勾）
   * - 0
     - 看日志/状态机
     - 可还原关键路径；无神秘阻塞
   * - 1
     - 规范 stop/退出
     - 资源释放正常
   * - 2
     - 观察任务与 SKIP
     - 异步边界清晰；``skip_reason`` 可统计
   * - 3
     - 核对日程/catch-up
     - 同配置可复现
   * - 3.5
     - 成交与重复回放（可选）
     - 台帐一致、无半提交
   * - 4-A
     - 整日 sim 路径
     - 无直掏内部队列类错误
   * - 4-B
     - 检索 skip_reason
     - 分桶字段齐全
   * - 5-A
     - split 开/关对比
     - prepare 与 run 顺序正确；stale 可解释
   * - 5-B
     - warn / block 分档
     - 告警可懂；block 不误杀

.. note::

   **4-C BrokerFacade**、**5-C 账本/日志长期收口** 仍以路线图正文为准；本冒烟方案 **不** 替代其专项验收。

七、交易日/非交易日记录模板（5-C）
--------------------------------

建议每次冒烟后填写以下模板，便于回归对照与异常分级：

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - 记录项
     - 交易日（开市）建议
     - 非交易日（休市）建议
   * - 版本与环境
     - 记录 ``git commit``、``py39``、核心配置键（``live_trade_*``、``trade_log_keep_days``）
     - 同左；并注明是否走 ``use_real_time=False`` 回放
   * - 启动门禁
     - 记录 ``run_startup_gate`` 结果（``warn`` / ``block``）与 ``failures`` 字段
     - 记录“非交易日跳过”行为与日志关键字
   * - 订单受理映射
     - 抽样核对 ``sys_op_trade_orders.broker_order_id`` / ``broker_name``；受理拒单应为空且 ``rejected``
     - 至少跑一笔受理成功 + 一笔受理拒单（可用 patch/模拟）并记录结果
   * - 对账与恢复诊断
     - 记录 ``post_close`` 检查点 trace（``checkpoint_passed``/``checkpoint_warn``）与 ``cash_diff`` / ``position_qty_diff``
     - 记录 ``diagnose_pending_orders`` 输出字段是否齐全、差异是否可解释
   * - 日志轮换
     - 核对 ``trade_log`` 与 ``*.risk.log`` 在保留策略下无异常膨胀
     - 可在隔离目录执行一次 ``rotate_trade_logs(days=30)`` 验证旧 risk 文件清理
   * - 结论
     - 通过 / 待查 / 阻塞；若阻塞，附 top1 错误与回滚点
     - 通过 / 待查 / 阻塞；附下一交易日跟进动作
