# coding=utf-8
# ======================================
# File: notebook_trader_headless_script.py
# Author: Jackie PENG / David
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-05-10
# Desc:
#   Notebook 友好的无头 Trader 集成测试脚本（分八阶段执行），
# 使用专用测试 DataSource（非 QT_DATA_SOURCE），
# 测试结束后清理表数据。
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


# %% [markdown]
# # Notebook 无头 Trader 测试脚本（8 阶段）
#
# 用法（建议在 notebook 分 cell 执行）：
# 1. `session = create_headless_notebook_session()`
# 2. 依次运行 `stage1_...` 到 `stage8_...`
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
    stage8_conclusion: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HeadlessNotebookSession:
    """无头 Trader notebook 会话容器。"""

    trader: Trader
    datasource: DataSource
    broker: SimulatorBroker
    trader_thread: Optional[threading.Thread] = None
    broker_thread: Optional[threading.Thread] = None
    record: NotebookDayRecord = field(default_factory=NotebookDayRecord)


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


def _create_datasource() -> DataSource:
    """创建 notebook 测试专用数据源。"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_test_trader_notebook')
    os.makedirs(data_dir, exist_ok=True)
    ds = DataSource('file', file_type='csv', file_loc=data_dir, allow_drop_table=True)
    clear_tables(ds)
    return ds


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


def create_headless_notebook_session(debug: bool = True) -> HeadlessNotebookSession:
    """创建可在 notebook 中逐步执行的无头 Trader 会话。"""
    ds = _create_datasource()
    _seed_account_and_positions(ds, account_id=1)
    write_minimal_stock_daily(
        datasource=ds,
        symbols=['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ'],
        start_date='2023-02-01',
        end_date='2023-06-30',
    )

    op = _build_notebook_operator()
    broker = SimulatorBroker()
    trader = Trader(
        operator=op,
        account_id=1,
        broker=broker,
        datasource=ds,
        asset_pool='000001.SZ,000002.SZ,000004.SZ,000005.SZ',
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
    trader.force_current_date = pd.to_datetime('2023-05-10').date()
    trader._run_task('start')
    trader.operator.set_shares(trader.asset_pool)
    trader.operator.set_group_parameters('Group_1', blender_str='s0')
    trader.operator.set_group_parameters('Group_2', blender_str='s0')
    trader.operator.set_group_parameters('Group_3', blender_str='s0')
    trader.live_price = pd.DataFrame(index=trader.asset_pool, data={'price': [12.0] * len(trader.asset_pool)})
    return HeadlessNotebookSession(trader=trader, datasource=ds, broker=broker)


def stage1_preflight_tests(session: HeadlessNotebookSession, run_commands: bool = False) -> Dict[str, Any]:
    """阶段1：开盘前测试记录（可选执行命令）。"""
    print('\n[Stage1] Preflight tests')
    cmds = [
        '/opt/anaconda3/envs/py39/bin/python -m unittest tests.test_trading.TestTradingUtilFuncs -v',
        '/opt/anaconda3/envs/py39/bin/python -m unittest tests.test_datasource.TestDataSource -v',
    ]
    result: Dict[str, Any] = {'commands': cmds, 'executed': []}
    if run_commands:
        for cmd in cmds:
            cp = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            result['executed'].append({
                'command': cmd,
                'return_code': cp.returncode,
                'stdout_tail': '\n'.join(cp.stdout.splitlines()[-15:]),
                'stderr_tail': '\n'.join(cp.stderr.splitlines()[-15:]),
            })
    print(' run_commands:', run_commands)
    print(' preflight command count:', len(cmds))
    session.record.stage1_preflight = result
    return result


def stage2_opening_baseline(session: HeadlessNotebookSession) -> Dict[str, Any]:
    """阶段2：开盘前账户/持仓/订单基线。"""
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


def stage3_intraday_runtime(session: HeadlessNotebookSession, sleep_s: float = 1.0) -> Dict[str, Any]:
    """阶段3：无头运行、任务调度与关键时间点。"""
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

    info = {
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
    print(' status:', info['status'])
    print(' next_task:', info['next_task'])
    print(' count_down_to_next_task:', info['count_down_to_next_task'])
    print(' task_queue_size:', info['queue_size'])
    session.record.stage3_intraday_points = info
    return info


def stage4_phase35_checks(session: HeadlessNotebookSession) -> Dict[str, Any]:
    """阶段4：阶段3.5核心检查（提交/撤单/幂等/读写一致）。"""
    print('\n[Stage4] Phase3.5 checks: submit/cancel/idempotent consistency')
    trader = session.trader
    ds = session.datasource

    result_columns, _, _, _ = get_built_in_table_schema('sys_op_trade_results')
    supports_broker_result_id = 'broker_result_id' in result_columns
    print(' supports broker_result_id:', supports_broker_result_id)

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


def stage5_stage0to3_regression(session: HeadlessNotebookSession) -> Dict[str, Any]:
    """阶段5：顺带回归阶段0~3能力点。"""
    print('\n[Stage5] Regression checks for phase0~3 capabilities')
    trader = session.trader
    messages: List[str] = []
    while not trader.message_queue.empty():
        messages.append(str(trader.message_queue.get_nowait()))
    checks = {
        'trace_like_messages_count': len(messages),
        'contains_task_keywords': any(('task' in m.lower()) or ('run strategy' in m.lower()) for m in messages),
        'status_now': trader.status,
        'schedule_size': len(trader.task_daily_schedule),
        'next_task': trader.next_task,
    }
    print(' trace/message count:', checks['trace_like_messages_count'])
    print(' contains task keywords:', checks['contains_task_keywords'])
    print(' status:', checks['status_now'])
    print(' schedule size:', checks['schedule_size'])
    print(' next task:', checks['next_task'])
    session.record.stage5_stage0to3_checks = checks
    return checks


def stage6_closing_reconcile(session: HeadlessNotebookSession) -> Dict[str, Any]:
    """阶段6：收盘后对账（本地侧快照）。"""
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


def stage7_exception_and_rollback_probe(session: HeadlessNotebookSession, use_db_probe: bool = False) -> Dict[str, Any]:
    """阶段7：异常与日志摘要（可选 DB 回滚探针）。"""
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


def stage8_conclusion(session: HeadlessNotebookSession) -> Dict[str, Any]:
    """阶段8：当日结论与下一步建议。"""
    print('\n[Stage8] Conclusion and next actions')
    s4 = session.record.stage4_phase35_checks
    s5 = session.record.stage5_stage0to3_checks
    s7 = session.record.stage7_exceptions_and_logs
    duplicate_ok = bool(
        (s4.get('supports_broker_result_id') and s4.get('duplicate_result_id_equal', False))
        or ((not s4.get('supports_broker_result_id')) and s4.get('duplicate_mode') in ['rejected_or_non_idempotent'])
    )
    passed = bool(
        duplicate_ok
        and s5.get('schedule_size', 0) > 0
        and (s7.get('db_rollback_probe_passed') in [None, True])
    )
    result = {
        'ready_for_next_phase': passed,
        'risk_level': 'low' if passed else 'medium',
        'next_steps': [
            'Run next trade day smoke + broker-side reconciliation.',
            'Keep this script as source material to convert into unittest.',
            'When behavior changes, compare stage4/stage6 snapshots first.',
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
            session.trader.add_task('stop')
            time.sleep(0.8)
            session.trader.status = 'stopped'
        except Exception as e:
            print(' shutdown warning:', e)
    print(' shutdown done')


if __name__ == '__main__':
    # 作为脚本快速演示：可直接运行，也可在 notebook 分阶段调用。
    s = create_headless_notebook_session(debug=True)
    stage1_preflight_tests(s, run_commands=False)
    stage2_opening_baseline(s)
    stage3_intraday_runtime(s)
    stage4_phase35_checks(s)
    stage5_stage0to3_regression(s)
    stage6_closing_reconcile(s)
    stage7_exception_and_rollback_probe(s, use_db_probe=False)
    stage8_conclusion(s)
    shutdown_session(s)
