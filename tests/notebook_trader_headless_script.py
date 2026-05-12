# coding=utf-8
# ======================================
# File: notebook_trader_headless_script.py
# Author: Jackie PENG / David
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-05-10
# Desc:
#   Notebook 友好的无头 Trader 集成测试脚本（分九阶段执行；阶段 9 对齐路线图 5-A/5-B），
# 默认使用 qteasy.cfg 对应的 QT_DATA_SOURCE；可选隔离文件型数据源回放。
# 下一交易日集中冒烟：见 docs/source/live_trading/7-manual-smoke-live-grid-roadmap.rst 。
# ======================================

from __future__ import annotations

import os
import time
import threading
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest import mock

import numpy as np
import pandas as pd

import qteasy as qt
from qteasy import DataSource, Operator
from qteasy.broker import SimulatorBroker
from qteasy.trader import Trader
from qteasy.trade_recording import (
    new_account,
    get_account,
    get_or_create_position,
    update_position,
    get_account_positions,
    query_trade_orders,
    read_trade_order_detail,
    read_trade_results_by_order_id,
)
from qteasy.trading_util import (
    submit_order,
    cancel_order,
    process_trade_result,
    process_account_delivery,
)
from qteasy.datatables import get_built_in_table_schema

from tests.trader_test_helpers import clear_tables, write_minimal_stock_daily


def _repo_root_for_subprocess() -> str:
    """本文件位于仓库 ``tests/`` 下，由此得到仓库根目录，供子进程 unittest 的 cwd / PYTHONPATH 使用。"""
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))


def _unittest_subprocess_env() -> Dict[str, str]:
    """构造子进程环境：在 PYTHONPATH 前部插入仓库根，使 ``import tests.*`` 可用。"""
    repo = _repo_root_for_subprocess()
    env = os.environ.copy()
    prev = env.get('PYTHONPATH', '').strip()
    if prev:
        parts = [p for p in prev.split(os.pathsep) if p]
        if repo not in parts:
            env['PYTHONPATH'] = repo + os.pathsep + prev
        else:
            env['PYTHONPATH'] = prev
    else:
        env['PYTHONPATH'] = repo
    return env


# %% [markdown]
# # Notebook 无头 Trader 测试脚本（9 阶段；第 9 阶段对齐路线图 5-A/5-B）
#
# 用法（建议在 notebook 分 cell 执行）：
# 1. `session = create_headless_notebook_session()`  # 默认 QT_DATA_SOURCE + 固定回放日
#    真实时钟：`create_headless_notebook_session(use_real_time=True)`
#    路线图 5-A/5-B 相关：`create_headless_notebook_session(..., live_trade_smoke_overrides={...})`
#    （在 Trader.start 之前写入 QT_CONFIG；shutdown_session 会尝试恢复被覆盖的键）
# 2. 依次运行 `stage1_...` 到 `stage9_...` 再 `stage8_...`（各 stage 可传 `info=True` 查看中文范围说明）
#    Stage1 在 `run_commands=True` 时会自动设置子进程 `cwd` 与 `PYTHONPATH` 指向本仓库根，无需在 notebook 里改 sys.path。
#    整类 unittest 可能极久，非死锁；可用 `unittest_timeout_s`（默认 3600s）或 `None` 取消限时。
# 3. 若中途调试，最后执行 `shutdown_session(session)`


@dataclass
class NotebookDayRecord:
    """记录一次“实盘日模板”检查过程的结构化信息。"""

    stage1_preflight: Dict[str, Any] = field(default_factory=dict)
    stage2_opening_baseline: Dict[str, Any] = field(default_factory=dict)
    stage3_intraday_points: Dict[str, Any] = field(default_factory=dict)
    stage4_phase35_checks: Dict[str, Any] = field(default_factory=dict)
    stage5_stage0to3_checks: Dict[str, Any] = field(default_factory=dict)
    stage6_closing_reconcile: Dict[str, Any] = field(default_factory=dict)
    stage7_exceptions_and_logs: Dict[str, Any] = field(default_factory=dict)
    stage9_phase5_ab: Dict[str, Any] = field(default_factory=dict)
    stage8_conclusion: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HeadlessNotebookSession:
    """无头 Trader notebook 会话容器。"""

    trader: Trader
    datasource: DataSource
    broker: SimulatorBroker
    trader_thread: Optional[threading.Thread] = None
    broker_thread: Optional[threading.Thread] = None
    use_real_time: bool = False
    record: NotebookDayRecord = field(default_factory=NotebookDayRecord)
    #: ``create_headless_notebook_session(..., live_trade_smoke_overrides=...)`` 写入前的键快照，供 shutdown 恢复。
    qt_smoke_restore: Optional[Dict[str, Any]] = None


def _print_stage_scope(title: str, lines: List[str], *, enabled: bool) -> None:
    """当 enabled 为 True 时，用中文打印本阶段的测试范围与目的。"""
    if not enabled:
        return
    print(f'\n【{title}】测试范围与目的')
    for line in lines:
        print(line)


NOTEBOOK_ASSET_POOL: List[str] = ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']


def _build_notebook_operator() -> Operator:
    """创建一个多策略组、不同运行时机的 Operator。"""
    op = Operator()
    op.add_strategy('dma', run_timing='10:00', run_freq='d')
    op.add_strategy('macd', run_timing='11:00', run_freq='d')
    op.add_strategy('rsi', run_timing='14:30', run_freq='d')
    # 压低窗口参数，减少 notebook 演示所需样本长度
    op.set_parameter(stg_id='dma', window_length=5)
    op.set_parameter(stg_id='macd', window_length=5)
    op.set_parameter(stg_id='rsi', window_length=5)
    return op


def _configure_notebook_operator(op: Operator, asset_pool: List[str]) -> None:
    """为 notebook 演示 Operator 设置资产池与各策略组混合器。"""
    op.set_shares(asset_pool)
    for group_id in op.group_ids:
        op.set_group_parameters(group_id, blender_str='s0')
    print(' notebook operator groups:', op.group_ids)


def _create_isolated_datasource() -> DataSource:
    """创建隔离文件型数据源并清空表（仅用于可重复回放，不写入 QT_DATA_SOURCE）。"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_test_trader_notebook')
    os.makedirs(data_dir, exist_ok=True)
    ds = DataSource('file', file_type='csv', file_loc=data_dir, allow_drop_table=True)
    clear_tables(ds)
    return ds


def _prepare_isolated_replay_data(ds: DataSource, account_id: int = 1) -> None:
    """在隔离数据源上写入最小账户、持仓与日线样本。"""
    _seed_account_and_positions(ds, account_id=account_id)
    write_minimal_stock_daily(
        datasource=ds,
        symbols=['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ'],
        start_date='2023-02-01',
        end_date='2023-06-30',
    )


def _sys_op_trade_results_has_broker_result_id_column(ds: DataSource) -> bool:
    """判断当前数据源物理表是否包含 broker_result_id 列（与内置 schema 可能不一致）。"""
    if getattr(ds, 'source_type', None) == 'db':
        try:
            if not ds._db_table_exists('sys_op_trade_results'):
                return False
            schema = ds._get_db_table_schema('sys_op_trade_results')
            return 'broker_result_id' in schema
        except Exception:
            return False
    try:
        preview = ds.read_sys_table_data('sys_op_trade_results')
        return 'broker_result_id' in preview.columns
    except Exception:
        return False


def _seed_account_and_positions(ds: DataSource, account_id: int = 1) -> None:
    """写入最小账户与初始持仓。"""
    new_account(user_name='notebook_headless_user', cash_amount=100000.0, data_source=ds)
    seeds = [
        ('000001.SZ', 200.0, 200.0),
        ('000002.SZ', 200.0, 200.0),
        ('000004.SZ', 100.0, 100.0),
    ]
    for sym, qty, avail in seeds:
        pos_id = get_or_create_position(account_id=account_id, symbol=sym, position_type='long', data_source=ds)
        update_position(position_id=pos_id, data_source=ds, qty_change=qty, available_qty_change=avail)


def create_headless_notebook_session(
    debug: bool = True,
    use_real_time: bool = False,
    account_id: int = 1,
    use_isolated_datasource: bool = False,
    live_trade_smoke_overrides: Optional[Dict[str, Any]] = None,
) -> HeadlessNotebookSession:
    """创建可在 notebook 中逐步执行的无头 Trader 会话。

    Parameters
    ----------
    debug : bool, default True
        是否开启 Trader / Broker 调试输出。
    use_real_time : bool, default False
        True 时使用本机真实时钟（不设置 ``force_current_date``）；False 时固定回放日 2023-05-10。
    account_id : int, default 1
        交易账户 ID；连接 QT_DATA_SOURCE 时须已存在对应账户与持仓。
    use_isolated_datasource : bool, default False
        True 时使用仓库内隔离 CSV 数据源并写入演示账户/行情；False 时使用 ``qt.QT_DATA_SOURCE``。
    live_trade_smoke_overrides : dict or None, optional
        在 ``Trader._run_task('start')`` 之前调用 ``qt.configure(**...)``，用于路线图 **5-A/5-B**
        冒烟（如 ``live_trade_split_strategy_prepare``、``live_trade_startup_gate_mode``）。
        传入的键会在 ``shutdown_session`` 时尽力恢复为会话创建前的值。

    Returns
    -------
    HeadlessNotebookSession
        已执行 ``start`` 与 ``register_broker`` 的无头会话。
    """
    qt_smoke_restore: Optional[Dict[str, Any]] = None
    if live_trade_smoke_overrides:
        qt_smoke_restore = {}
        for k in live_trade_smoke_overrides:
            qt_smoke_restore[k] = qt.QT_CONFIG.get(k)
        qt.configure(**live_trade_smoke_overrides)
    if use_isolated_datasource:
        ds = _create_isolated_datasource()
        _prepare_isolated_replay_data(ds, account_id=account_id)
    else:
        ds = qt.QT_DATA_SOURCE

    print('\n[create_headless_notebook_session] session bootstrap')
    print(' use_real_time:', use_real_time)
    print(' use_isolated_datasource:', use_isolated_datasource)
    print(' account_id:', account_id)
    print(' datasource source_type:', getattr(ds, 'source_type', type(ds).__name__))

    op = _build_notebook_operator()
    _configure_notebook_operator(op, NOTEBOOK_ASSET_POOL)
    broker = SimulatorBroker(data_source=ds)
    trader = Trader(
        operator=op,
        account_id=account_id,
        broker=broker,
        datasource=ds,
        asset_pool=','.join(NOTEBOOK_ASSET_POOL),
        asset_type='E',
        exchange='SSE',
        market_open_time_am='09:30:00',
        market_close_time_am='11:30:00',
        market_open_time_pm='13:00:00',
        market_close_time_pm='15:00:00',
        live_price_freq='15min',
        live_price_channel='eastmoney',
        live_data_channel='eastmoney',
        cash_delivery_period=0,
        stock_delivery_period=0,
        debug=debug,
    )
    if use_real_time:
        trader.force_current_date = None
    else:
        trader.force_current_date = pd.to_datetime('2023-05-10').date()
    # 避免 QT_DATA_SOURCE 上历史断点覆盖本次 notebook Operator（常见仅剩 Group_1）
    trader.clear_break_point()
    trader._run_task('start')
    if trader.operator.group_ids != op.group_ids:
        print(' warning: operator groups after start differ from notebook op:', trader.operator.group_ids)
        _configure_notebook_operator(trader.operator, NOTEBOOK_ASSET_POOL)
    if not use_real_time:
        trader.live_price = pd.DataFrame(
            index=trader.asset_pool,
            data={'price': [12.0] * len(trader.asset_pool)},
        )
    print(' trader effective datetime:', trader.get_current_tz_datetime())
    print(' trader is_trade_day:', trader.is_trade_day)
    # 与 run_live_trade 一致：Broker.run() 要求 is_registered，否则线程内抛 RuntimeError
    trader.register_broker(debug=debug)
    return HeadlessNotebookSession(
        trader=trader,
        datasource=ds,
        broker=broker,
        use_real_time=use_real_time,
        qt_smoke_restore=qt_smoke_restore,
    )


def stage1_preflight_tests(
    session: HeadlessNotebookSession,
    run_commands: bool = False,
    info: bool = False,
    unittest_timeout_s: Optional[float] = 3600.0,
) -> Dict[str, Any]:
    """阶段1：开盘前测试记录（可选执行命令）。

    Parameters
    ----------
    unittest_timeout_s : float or None, optional
        单条 unittest 子进程的最长等待秒数；默认 3600（1 小时）。子进程仍在跑时主线程会阻塞在
        ``subprocess.run`` 上，并非死锁。``None`` 表示不限制时长（整类 ``TestDataSource`` 可能极久）。
    """
    _print_stage_scope(
        '阶段1 stage1_preflight_tests',
        [
            '范围：Notebook 实盘日前预检清单。',
            '目的：列出可选执行的 unittest 命令（交易工具函数与数据源）；根据 run_commands 决定是否在本机实际跑子进程并收集尾部输出，便于确认环境是否就绪。',
        ],
        enabled=info,
    )
    print('\n[Stage1] Preflight tests')
    cmds = [
        '/opt/anaconda3/envs/py39/bin/python -m unittest tests.test_trading.TestTradingUtilFuncs -v',
        '/opt/anaconda3/envs/py39/bin/python -m unittest tests.test_datasource.TestDataSource -v',
    ]
    result: Dict[str, Any] = {
        'commands': cmds,
        'executed': [],
        'unittest_timeout_s': unittest_timeout_s,
    }
    if run_commands:
        repo_root = _repo_root_for_subprocess()
        tests_pkg = os.path.join(repo_root, 'tests', '__init__.py')
        if not os.path.isfile(tests_pkg):
            print(
                ' stage1 warning: expected tests package not found at',
                tests_pkg,
                '(unittest subprocess may still fail)',
            )
        else:
            print(' stage1 unittest repo_root:', repo_root)
        if unittest_timeout_s is not None:
            print(
                ' stage1 note: each subprocess has timeout=',
                unittest_timeout_s,
                's; use unittest_timeout_s=None for no limit (may run a very long time).',
            )
        else:
            print(
                ' stage1 note: no subprocess timeout (full classes may take many minutes; this is not a deadlock).',
            )
        env = _unittest_subprocess_env()
        for cmd in cmds:
            print(' stage1 running:', cmd)
            try:
                cp = subprocess.run(
                    cmd,
                    shell=True,
                    text=True,
                    capture_output=True,
                    cwd=repo_root,
                    env=env,
                    timeout=unittest_timeout_s,
                )
                result['executed'].append({
                    'command': cmd,
                    'return_code': cp.returncode,
                    'stdout_tail': '\n'.join((cp.stdout or '').splitlines()[-15:]),
                    'stderr_tail': '\n'.join((cp.stderr or '').splitlines()[-15:]),
                    'timed_out': False,
                })
            except subprocess.TimeoutExpired as e:
                tail_out = '\n'.join((e.stdout or '').splitlines()[-15:]) if e.stdout else ''
                tail_err = '\n'.join((e.stderr or '').splitlines()[-15:]) if e.stderr else ''
                msg = (
                    f'SubprocessTimeout: unittest exceeded unittest_timeout_s={unittest_timeout_s!r} seconds. '
                    f'Increase unittest_timeout_s or pass unittest_timeout_s=None for no limit.'
                )
                result['executed'].append({
                    'command': cmd,
                    'return_code': None,
                    'stdout_tail': tail_out,
                    'stderr_tail': (msg + '\n' + tail_err).strip(),
                    'timed_out': True,
                })
    print(' run_commands:', run_commands)
    print(' preflight command count:', len(cmds))
    session.record.stage1_preflight = result
    return result


def stage2_opening_baseline(session: HeadlessNotebookSession, info: bool = False) -> Dict[str, Any]:
    """阶段2：开盘前账户/持仓/订单基线。"""
    _print_stage_scope(
        '阶段2 stage2_opening_baseline',
        [
            '范围：当前会话专用 DataSource 上的账户与持仓。',
            '目的：打印开盘前账户现金字段、各标的持仓与订单条数，作为后续阶段对比的基线快照。',
        ],
        enabled=info,
    )
    print('\n[Stage2] Opening baseline')
    account = get_account(session.trader.account_id, data_source=session.datasource)
    positions = get_account_positions(session.trader.account_id, data_source=session.datasource)
    orders = query_trade_orders(session.trader.account_id, data_source=session.datasource)
    baseline = {
        'account': account,
        'positions': positions.copy(),
        'orders_count': len(orders),
    }
    print(' account:', {k: account[k] for k in ['cash_amount', 'available_cash', 'total_invest']})
    print(' positions:\n', positions[['symbol', 'position', 'qty', 'available_qty', 'cost']])
    print(' open/history orders count:', len(orders))
    session.record.stage2_opening_baseline = baseline
    return baseline


def stage3_intraday_runtime(
    session: HeadlessNotebookSession,
    sleep_s: float = 1.0,
    info: bool = False,
) -> Dict[str, Any]:
    """阶段3：无头运行、任务调度与关键时间点。"""
    _print_stage_scope(
        '阶段3 stage3_intraday_runtime',
        [
            '范围：Broker / Trader 后台线程与任务队列。',
            '目的：启动已注册的 SimulatorBroker 与 Trader.run() 主循环，按序投递 wakeup、run_strategy、pause、resume，并记录时间戳与 status / 下一计划任务 / 队列长度，验证无头调度链路。',
        ],
        enabled=info,
    )
    print('\n[Stage3] Headless runtime, task flow and timestamps')
    if session.broker_thread is None or not session.broker_thread.is_alive():
        session.broker_thread = threading.Thread(target=session.broker.run, daemon=True)
        session.broker_thread.start()
    if session.trader_thread is None or not session.trader_thread.is_alive():
        session.trader_thread = threading.Thread(target=session.trader.run, daemon=True)
        session.trader_thread.start()
    time.sleep(sleep_s)
    t0 = pd.Timestamp.now().isoformat()
    session.trader.add_task('wakeup')
    time.sleep(sleep_s)
    t1 = pd.Timestamp.now().isoformat()
    session.trader.add_task('run_strategy', 0)
    time.sleep(sleep_s)
    t2 = pd.Timestamp.now().isoformat()
    session.trader.add_task('pause')
    time.sleep(sleep_s)
    t3 = pd.Timestamp.now().isoformat()
    session.trader.add_task('resume')
    time.sleep(sleep_s)
    t4 = pd.Timestamp.now().isoformat()

    runtime_result = {
        'timestamps': {
            'before_wakeup': t0,
            'after_wakeup': t1,
            'after_run_strategy_0': t2,
            'after_pause': t3,
            'after_resume': t4,
        },
        'status': session.trader.status,
        'next_task': session.trader.next_task,
        'count_down_to_next_task': session.trader.count_down_to_next_task,
        'queue_size': session.trader.task_queue.qsize(),
    }
    print(' status:', runtime_result['status'])
    print(' next_task:', runtime_result['next_task'])
    print(' count_down_to_next_task:', runtime_result['count_down_to_next_task'])
    print(' task_queue_size:', runtime_result['queue_size'])
    session.record.stage3_intraday_points = runtime_result
    return runtime_result


def stage4_phase35_checks(session: HeadlessNotebookSession, info: bool = False) -> Dict[str, Any]:
    """阶段4：阶段3.5核心检查（提交/撤单/幂等/读写一致）。"""
    _print_stage_scope(
        '阶段4 stage4_phase35_checks',
        [
            '范围：手工下单、成交回报入账、撤单、交割与订单历史查询。',
            '目的：验证阶段 3.5 相关能力：含 broker_result_id 时的幂等重复回报、撤单路径、process_account_delivery 与 history_orders 读写一致性。',
        ],
        enabled=info,
    )
    print('\n[Stage4] Phase3.5 checks: submit/cancel/idempotent consistency')
    trader = session.trader
    ds = session.datasource

    result_columns, _, _, _ = get_built_in_table_schema('sys_op_trade_results')
    supports_broker_result_id = (
        'broker_result_id' in result_columns
        and _sys_op_trade_results_has_broker_result_id_column(ds)
    )
    print(' supports broker_result_id (builtin schema):', 'broker_result_id' in result_columns)
    print(' supports broker_result_id (physical table):', supports_broker_result_id)

    # 1) 手动提交一个订单
    trade_order = trader.submit_trade_order(
        symbol='000001.SZ',
        position='long',
        direction='buy',
        order_type='market',
        qty=100,
        price=10.0,
    )
    print(' submitted trade_order:', trade_order)
    order_id = int(trade_order.get('order_id', -1))
    if order_id <= 0:
        raise RuntimeError('submit_trade_order failed in stage4')

    # 2) 用手工成交回报执行入账，并做重复回报幂等检查
    raw: Dict[str, Any] = {
        'order_id': order_id,
        'filled_qty': 100.0,
        'price': 10.1,
        'transaction_fee': 1.5,
        'canceled_qty': 0.0,
    }
    if supports_broker_result_id:
        raw['broker_result_id'] = f'nb-fill-{order_id}-001'
    full_1 = process_trade_result(raw.copy(), data_source=ds)
    duplicate_mode = 'unknown'
    duplicate_error = ''
    try:
        full_2 = process_trade_result(raw.copy(), data_source=ds)
        duplicate_mode = 'idempotent_return'
    except Exception as e:
        # 对旧版本（无幂等键）允许记录“重复回报被拒绝”结果，便于人眼检查
        full_2 = {'error': str(e)}
        duplicate_mode = 'rejected_or_non_idempotent'
        duplicate_error = str(e)
    results = read_trade_results_by_order_id(order_id=order_id, data_source=ds)
    print(' first full result:', full_1)
    print(' second full result (duplicate):', full_2)
    print(' result rows after duplicate fill:', len(results))

    # 3) 再提一笔订单做撤单验证
    trade_order_2 = trader.submit_trade_order(
        symbol='000002.SZ',
        position='long',
        direction='buy',
        order_type='market',
        qty=50,
        price=9.8,
    )
    order_id_2 = int(trade_order_2.get('order_id', -1))
    cancelled_id = cancel_order(order_id_2, data_source=ds, config={
        'cash_delivery_period': trader.cash_delivery_period,
        'stock_delivery_period': trader.stock_delivery_period,
    })
    order_detail_2 = read_trade_order_detail(order_id_2, data_source=ds)
    print(' cancel return id:', cancelled_id)
    print(' canceled order detail:', order_detail_2)

    # 4) 做一次交割处理并输出订单历史
    delivery_results = process_account_delivery(
        account_id=trader.account_id,
        data_source=ds,
        cash_delivery_period=trader.cash_delivery_period,
        stock_delivery_period=trader.stock_delivery_period,
    )
    history_df = trader.history_orders(with_trade_results=True)
    print(' delivery result count:', len(delivery_results))
    print(' history orders with results:\n', history_df.tail(10))

    out = {
        'supports_broker_result_id': supports_broker_result_id,
        'first_order_id': order_id,
        'duplicate_result_rows': len(results),
        'duplicate_mode': duplicate_mode,
        'duplicate_error': duplicate_error,
        'duplicate_result_id_equal': bool(
            isinstance(full_2, dict)
            and ('result_id' in full_2)
            and int(full_1['result_id']) == int(full_2['result_id'])
        ),
        'second_order_id': order_id_2,
        'second_order_status': order_detail_2.get('status'),
        'history_rows': len(history_df),
    }
    session.record.stage4_phase35_checks = out
    return out


def stage5_stage0to3_regression(session: HeadlessNotebookSession, info: bool = False) -> Dict[str, Any]:
    """阶段5：顺带回归阶段0~3能力点。"""
    _print_stage_scope(
        '阶段5 stage5_stage0to3_regression',
        [
            '范围：Trader 消息队列、任务注册表与 Broker 公开 API 可用性。',
            '目的：排空 message_queue 做轻量材料收集，结合当前 status、日程长度与 next_task，额外统计 skip_reason 与 task_registry 中的 skipped/rejected 任务，用于人工对照阶段 0~3 与 4-B（重入/SKIP 分桶）是否异常。',
        ],
        enabled=info,
    )
    print('\n[Stage5] Regression checks for phase0~3 capabilities')
    trader = session.trader
    messages: List[str] = []
    while not trader.message_queue.empty():
        messages.append(str(trader.message_queue.get_nowait()))
    skip_reason_hits: Dict[str, int] = {}
    for msg in messages:
        if 'skip_reason=' not in msg:
            continue
        reason = msg.split('skip_reason=', 1)[1].split()[0].strip().strip('.,;')
        skip_reason_hits[reason] = skip_reason_hits.get(reason, 0) + 1
    skipped_tasks = [
        {
            'task_id': task.task_id,
            'name': task.name,
            'status': task.status,
            'reentry_policy': task.reentry_policy,
            'last_error': task.last_error,
        }
        for task in trader._task_registry.values()
        if task.status in ['skipped', 'rejected']
    ]
    checks = {
        'trace_like_messages_count': len(messages),
        'contains_task_keywords': any(('task' in m.lower()) or ('run strategy' in m.lower()) for m in messages),
        'status_now': trader.status,
        'schedule_size': len(trader.task_daily_schedule),
        'next_task': trader.next_task,
        'broker_poll_api_available': {
            'poll_fills': callable(getattr(session.broker, 'poll_fills', None)),
            'poll_messages': callable(getattr(session.broker, 'poll_messages', None)),
        },
        'skip_reason_hits': skip_reason_hits,
        'skipped_or_rejected_tasks': skipped_tasks,
    }
    print(' trace/message count:', checks['trace_like_messages_count'])
    print(' contains task keywords:', checks['contains_task_keywords'])
    print(' status:', checks['status_now'])
    print(' schedule size:', checks['schedule_size'])
    print(' next task:', checks['next_task'])
    print(' broker poll API available:', checks['broker_poll_api_available'])
    print(' skip_reason hits:', checks['skip_reason_hits'])
    print(' skipped/rejected tasks count:', len(checks['skipped_or_rejected_tasks']))
    session.record.stage5_stage0to3_checks = checks
    return checks


def stage6_closing_reconcile(session: HeadlessNotebookSession, info: bool = False) -> Dict[str, Any]:
    """阶段6：收盘后对账（本地侧快照）。"""
    _print_stage_scope(
        '阶段6 stage6_closing_reconcile',
        [
            '范围：会话数据源上的账户资金、持仓与订单状态分布。',
            '目的：在本地侧做一次「收盘」快照：现金、持仓表、submitted / partial-filled 订单数量，便于与阶段 2 基线或外部对账材料比对。',
        ],
        enabled=info,
    )
    print('\n[Stage6] Closing reconcile snapshot (local)')
    trader = session.trader
    ds = session.datasource
    account = get_account(trader.account_id, data_source=ds)
    positions = get_account_positions(trader.account_id, data_source=ds)
    open_orders = query_trade_orders(trader.account_id, status='submitted', data_source=ds)
    partial_orders = query_trade_orders(trader.account_id, status='partial-filled', data_source=ds)
    snapshot = {
        'cash_amount': account['cash_amount'],
        'available_cash': account['available_cash'],
        'positions': positions[['symbol', 'position', 'qty', 'available_qty', 'cost']].copy(),
        'open_orders_count': len(open_orders),
        'partial_orders_count': len(partial_orders),
    }
    print(' cash:', snapshot['cash_amount'], ' available_cash:', snapshot['available_cash'])
    print(' positions:\n', snapshot['positions'])
    print(' open_orders_count:', snapshot['open_orders_count'])
    print(' partial_orders_count:', snapshot['partial_orders_count'])
    session.record.stage6_closing_reconcile = snapshot
    return snapshot


def stage7_exception_and_rollback_probe(
    session: HeadlessNotebookSession,
    use_db_probe: bool = False,
    info: bool = False,
) -> Dict[str, Any]:
    """阶段7：异常与日志摘要（可选 DB 回滚探针）。"""
    _print_stage_scope(
        '阶段7 stage7_exception_and_rollback_probe',
        [
            '范围：异常路径说明与（可选）独立测试库上的事务回滚探针。',
            '目的：默认仅记录说明；当 use_db_probe=True 时，在测试库中构造订单并在 process_trade_result 中途注入错误，观察整笔事务是否回滚、成交表是否未落脏数据。',
        ],
        enabled=info,
    )
    print('\n[Stage7] Exception/log summary and optional rollback probe')
    summary: Dict[str, Any] = {
        'db_rollback_probe_enabled': use_db_probe,
        'db_rollback_probe_executed': False,
        'db_rollback_probe_passed': None,
        'notes': [],
    }
    if not use_db_probe:
        summary['notes'].append('DB rollback probe skipped by user setting.')
        session.record.stage7_exceptions_and_logs = summary
        print(' DB rollback probe skipped.')
        return summary

    # 可选：仅在你愿意时用 DB 数据源做一次“中途异常整体回滚”探针
    qt_config = qt.QT_CONFIG
    ds_db = DataSource(
        'db',
        host=qt_config['test_db_host'],
        port=qt_config['test_db_port'],
        user=qt_config['test_db_user'],
        password=qt_config['test_db_password'],
        db_name=qt_config['test_db_name'],
        allow_drop_table=True,
    )
    clear_tables(ds_db)
    _seed_account_and_positions(ds_db, account_id=1)
    order_id = int(save_order_for_probe(ds_db))
    before = read_trade_results_by_order_id(order_id=order_id, data_source=ds_db)
    result_columns, _, _, _ = get_built_in_table_schema('sys_op_trade_results')
    supports_broker_result_id = 'broker_result_id' in result_columns
    raw: Dict[str, Any] = {
        'order_id': order_id,
        'filled_qty': 10.0,
        'price': 10.0,
        'transaction_fee': 0.1,
        'canceled_qty': 0.0,
    }
    if supports_broker_result_id:
        raw['broker_result_id'] = f'db-probe-{order_id}'
    summary['db_rollback_probe_executed'] = True
    try:
        with mock.patch('qteasy.trading_util.update_position', side_effect=RuntimeError('rollback-probe-error')):
            process_trade_result(raw.copy(), data_source=ds_db)
    except RuntimeError:
        pass
    after = read_trade_results_by_order_id(order_id=order_id, data_source=ds_db)
    summary['db_rollback_probe_passed'] = len(before) == len(after) == 0
    print(' DB rollback probe before/after rows:', len(before), len(after))
    print(' DB rollback probe passed:', summary['db_rollback_probe_passed'])
    session.record.stage7_exceptions_and_logs = summary
    return summary


def _schedule_task_name_counts(trader: Trader) -> Dict[str, int]:
    """从 ``task_daily_schedule`` legacy 元组中粗略统计任务名出现次数。"""
    counts: Dict[str, int] = {}
    for row in trader.task_daily_schedule:
        if not row:
            continue
        if len(row) >= 2 and isinstance(row[1], str):
            name = row[1]
            counts[name] = counts.get(name, 0) + 1
    return counts


def stage9_phase5_ab_smoke(session: HeadlessNotebookSession, info: bool = False) -> Dict[str, Any]:
    """阶段9：路线图 5-A（split + 快照标记）与 5-B（启动门禁）集中冒烟。"""
    _print_stage_scope(
        '阶段9 stage9_phase5_ab_smoke',
        [
            '范围：全局 QT_CONFIG 中与 5-A/5-B 相关的键、当日日程是否含 prepare_strategy_snapshot、'
            '重复调用 run_startup_gate 的返回值、Operator.is_ready。',
            '目的：下一交易日对照《7-manual-smoke-live-grid-roadmap》做无头侧快速验收；'
            '完整语义仍以真实 ``qt.run`` / ``live_grid_multi`` 手动方案为准。',
        ],
        enabled=info,
    )
    print('\n[Stage9] Phase 5-A / 5-B smoke (snapshot split + startup gate)')
    trader = session.trader
    cfg = qt.QT_CONFIG
    keys = (
        'live_trade_split_strategy_prepare',
        'live_trade_strategy_snapshot_max_age_seconds',
        'live_trade_prepare_lead_seconds',
        'live_trade_startup_gate_mode',
    )
    qt_subset = {k: cfg.get(k) for k in keys}
    print(' QT_CONFIG subset (5-A/5-B):', qt_subset)

    sched_counts = _schedule_task_name_counts(trader)
    print(' schedule task name counts:', sched_counts)
    prep_n = int(sched_counts.get('prepare_strategy_snapshot', 0))
    run_n = int(sched_counts.get('run_strategy', 0))

    op_ready = bool(trader.operator.is_ready(tell_me_why=False, raise_error=False))
    gate_ok = bool(trader.run_startup_gate())
    gate_allowed = bool(getattr(trader, '_startup_gate_trading_allowed', True))

    split_on = bool(qt_subset.get('live_trade_split_strategy_prepare'))
    acceptance = {
        'qt_config_subset': qt_subset,
        'schedule_prepare_count': prep_n,
        'schedule_run_strategy_count': run_n,
        'prepare_leq_run_when_split': (not split_on) or (prep_n <= run_n),
        'operator_is_ready': op_ready,
        'gate_re_run_ok': gate_ok,
        'startup_gate_trading_allowed': gate_allowed,
    }
    print(' operator_is_ready:', op_ready)
    print(' run_startup_gate (repeat):', gate_ok, ' trading_allowed:', gate_allowed)
    print(' acceptance (auto checks):', acceptance)

    session.record.stage9_phase5_ab = acceptance
    return acceptance


def save_order_for_probe(ds_db: DataSource) -> int:
    """为回滚探针创建并提交一笔订单。"""
    from qteasy.trade_recording import save_parsed_trade_orders
    order_id = int(save_parsed_trade_orders(
        account_id=1,
        symbols=['000001.SZ'],
        positions=['long'],
        directions=['buy'],
        quantities=[10.0],
        prices=[10.0],
        data_source=ds_db,
    )[0])
    submit_order(order_id, data_source=ds_db)
    return order_id


def stage8_conclusion(session: HeadlessNotebookSession, info: bool = False) -> Dict[str, Any]:
    """阶段8：当日结论与下一步建议。"""
    _print_stage_scope(
        '阶段8 stage8_conclusion',
        [
            '范围：汇总阶段 4、5、7、9 写入 record 的关键标志。',
            '目的：根据幂等检查结果、日程、可选 DB 探针与 5-A/5-B 冒烟字段，给出是否适合进入下一阶段的主观判定与后续操作建议（打印 ready_for_next_phase、risk_level、next_steps）。',
        ],
        enabled=info,
    )
    print('\n[Stage8] Conclusion and next actions')
    s4 = session.record.stage4_phase35_checks
    s5 = session.record.stage5_stage0to3_checks
    s7 = session.record.stage7_exceptions_and_logs
    s9 = session.record.stage9_phase5_ab
    duplicate_ok = bool(
        (s4.get('supports_broker_result_id') and s4.get('duplicate_result_id_equal', False))
        or ((not s4.get('supports_broker_result_id')) and s4.get('duplicate_mode') in ['rejected_or_non_idempotent'])
    )
    passed = bool(
        duplicate_ok
        and s5.get('schedule_size', 0) > 0
        and (s7.get('db_rollback_probe_passed') in [None, True])
        and (not s9 or s9.get('operator_is_ready', True))
        and (not s9 or s9.get('prepare_leq_run_when_split', True))
    )
    result = {
        'ready_for_next_phase': passed,
        'risk_level': 'low' if passed else 'medium',
        'stage9_phase5_ab': s9,
        'next_steps': [
            'Run next trade day smoke + broker-side reconciliation.',
            'Keep this script as source material to convert into unittest.',
            'When behavior changes, compare stage4/stage6 snapshots first.',
            'For live_grid_multi manual checklist: docs/source/live_trading/7-manual-smoke-live-grid-roadmap.rst',
        ],
    }
    print(' ready_for_next_phase:', result['ready_for_next_phase'])
    print(' risk_level:', result['risk_level'])
    print(' next_steps:', result['next_steps'])
    session.record.stage8_conclusion = result
    return result


def shutdown_session(session: HeadlessNotebookSession) -> None:
    """停止无头 Trader 会话线程。"""
    print('\n[Shutdown] Stopping headless trader session')
    if session.trader is not None:
        try:
            # 对齐 TraderRuntime 停机语义：由 stop() 统一收敛状态与线程退出，避免直接改 status。
            session.trader.stop(wait=True, timeout=10.0, include_post_close=True)
            if session.trader_thread is not None:
                session.trader_thread.join(timeout=2.0)
            if session.broker_thread is not None:
                session.broker_thread.join(timeout=2.0)
        except Exception as e:
            print(' shutdown warning:', e)
    prev = getattr(session, 'qt_smoke_restore', None)
    if prev:
        try:
            qt.configure(**prev)
            print(' restored QT_CONFIG keys from live_trade_smoke_overrides:', list(prev.keys()))
        except Exception as e:
            print(' qt_smoke_restore warning:', e)
        session.qt_smoke_restore = None
    print(' shutdown done')


if __name__ == '__main__':
    # 作为脚本快速演示：默认隔离数据源，避免直跑时改写 QT_DATA_SOURCE。
    s = create_headless_notebook_session(debug=True, use_isolated_datasource=True)
    try:
        stage1_preflight_tests(s, run_commands=False)
        stage2_opening_baseline(s)
        stage3_intraday_runtime(s)
        stage4_phase35_checks(s)
        stage5_stage0to3_regression(s)
        stage6_closing_reconcile(s)
        stage7_exception_and_rollback_probe(s, use_db_probe=False)
        stage9_phase5_ab_smoke(s, info=True)
        stage8_conclusion(s)
    except KeyboardInterrupt:
        print('\n[Interrupted] KeyboardInterrupt captured, will stop headless session.')
    finally:
        shutdown_session(s)
