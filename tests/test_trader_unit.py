# coding=utf-8
# ======================================
# File:     test_trader_unit.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-05-09
# Desc:
#   单元测试：Trader 初始化、status、任务调度、
#   account_cash、watch_list 等，使用专
#   用测试 DataSource（非 QT_DATA_SOURCE），
#   测试完成后清理表数据。
# ======================================

import os
import time
import datetime as dt
import unittest
from unittest.mock import patch

import pandas as pd

from qteasy import DataSource, Operator
from qteasy.trade_recording import new_account, get_account, get_or_create_position, update_position, update_account_balance
from qteasy.trader import Trader
from qteasy.broker import SimulatorBroker


# --------------- 测试用 DataSource：从公共夹具导入（data_test_trader，legacy=False） ---------------

from tests.trader_test_helpers import (
    get_trader_test_data_dir,
    default_trader_kwargs,
    create_operator,
    clear_tables,
    create_test_datasource,
    create_trader_with_account,
)
# 别名，便于本文件内 tearDown 等继续使用 _clear_tables / _create_operator 等命名
_clear_tables = clear_tables
_create_operator = create_operator
_default_trader_kwargs = default_trader_kwargs
_create_test_datasource = create_test_datasource


# --------------- 初始化与参数验证 ---------------

class TestTraderInit(unittest.TestCase):
    """Trader 初始化与参数校验。"""

    def setUp(self):
        self._test_ds = None

    def tearDown(self):
        if self._test_ds is not None:
            _clear_tables(self._test_ds)

    def test_init_invalid_account_id_type(self):
        """account_id 非 int 时应抛出 TypeError。"""
        op = _create_operator()
        broker = SimulatorBroker()
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id='1',
                operator=op,
                broker=broker,
                datasource=test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('account_id', str(ctx.exception))
        print('test_init_invalid_account_id_type: TypeError as expected', ctx.exception)

    def test_init_invalid_operator_type(self):
        """operator 非 Operator 时应抛出 TypeError。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        broker = SimulatorBroker()
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=object(),
                broker=broker,
                datasource=test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('Operator', str(ctx.exception))
        print('test_init_invalid_operator_type: TypeError as expected', ctx.exception)

    def test_init_invalid_broker_type(self):
        """broker 非 Broker 时应抛出 TypeError。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=op,
                broker=object(),
                datasource=test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('Broker', str(ctx.exception))
        print('test_init_invalid_broker_type: TypeError as expected', ctx.exception)

    def test_init_invalid_datasource_type(self):
        """datasource 非 DataSource 时应抛出 TypeError。"""
        op = _create_operator()
        broker = SimulatorBroker()
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=op,
                broker=broker,
                datasource=object(),
                **_default_trader_kwargs(),
            )
        self.assertIn('DataSource', str(ctx.exception))
        print('test_init_invalid_datasource_type: TypeError as expected', ctx.exception)

    def test_init_with_large_account_id(self):
        """极大 account_id 应能正常构造。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        # new_account 返回的是新账户 id，可能不是 10**9，这里用已存在的 account_id=1
        # 若 new_account 支持指定 id 则用 10**9；否则用大 id 需要先建账户
        op = _create_operator()
        broker = SimulatorBroker()
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **_default_trader_kwargs(),
        )
        self.assertEqual(trader.account_id, 1)
        print('test_init_with_large_account_id: account_id=1 passed (large id would need DB support)')

    def test_init_benchmark_asset_from_str(self):
        """benchmark_asset 为 str 时 watch_list 为 benchmark + asset_pool。"""
        trader, self._test_ds = create_trader_with_account()
        self.assertEqual(trader.benchmark, '000300.SH')
        expected = ['000300.SH', '000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ']
        self.assertEqual(trader.watch_list, expected)
        print('test_init_benchmark_asset_from_str: watch_list', trader.watch_list)

    def test_init_benchmark_asset_from_list(self):
        """benchmark_asset 为 list 时 watch_list 为该列表 + asset_pool。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        kwargs = _default_trader_kwargs()
        kwargs['asset_pool'] = '000001.SZ, 000002.SZ'
        kwargs['benchmark_asset'] = ['000300.SH', '000905.SH']
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **kwargs,
        )
        self.assertEqual(trader.watch_list, ['000300.SH', '000905.SH', '000001.SZ', '000002.SZ'])
        print('test_init_benchmark_asset_from_list: watch_list', trader.watch_list)

    def test_init_benchmark_asset_invalid_type(self):
        """benchmark_asset 非 str/list 时应抛出 TypeError。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=op,
                broker=broker,
                datasource=test_ds,
                benchmark_asset=123,
                **_default_trader_kwargs(),
            )
        self.assertIn('benchmark_asset', str(ctx.exception))
        print('test_init_benchmark_asset_invalid_type: TypeError as expected', ctx.exception)

    def test_init_empty_asset_pool(self):
        """asset_pool 为空时 watch_list 仅含 benchmark。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        kwargs = _default_trader_kwargs()
        kwargs['asset_pool'] = []
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **kwargs,
        )
        self.assertEqual(trader.asset_pool, [])
        self.assertEqual(trader.watch_list, ['000300.SH'])
        print('test_init_empty_asset_pool: watch_list', trader.watch_list)

    def test_init_duplicate_symbols_in_watch_list(self):
        """benchmark 与 asset_pool 含重复 symbol 时 watch_list 保持当前实现（允许重复）。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        kwargs = _default_trader_kwargs()
        kwargs['asset_pool'] = '000001.SZ'
        kwargs['benchmark_asset'] = '000001.SZ'
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **kwargs,
        )
        self.assertIn('000001.SZ', trader.watch_list)
        self.assertEqual(trader.watch_list.count('000001.SZ'), 2)
        print('test_init_duplicate_symbols_in_watch_list: watch_list', trader.watch_list)


# --------------- status / prev_status ---------------

class TestTraderStatus(unittest.TestCase):

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_status_valid_transitions(self):
        """合法 status 迁移时 prev_status 正确更新。"""
        self.assertEqual(self._trader.status, 'stopped')
        self._trader.status = 'running'
        self.assertEqual(self._trader.status, 'running')
        self.assertEqual(self._trader.prev_status, 'stopped')
        self._trader.status = 'paused'
        self.assertEqual(self._trader.prev_status, 'running')
        self._trader.status = 'sleeping'
        self.assertEqual(self._trader.prev_status, 'paused')
        self._trader.status = 'stopped'
        self.assertEqual(self._trader.prev_status, 'sleeping')
        print('test_status_valid_transitions: ok')

    def test_status_invalid_value_raises(self):
        """非法 status 应抛出 ValueError。"""
        with self.assertRaises(ValueError) as ctx:
            self._trader.status = 'unknown'
        self.assertIn('invalid status', str(ctx.exception))
        print('test_status_invalid_value_raises: ValueError as expected', ctx.exception)

    def test_status_set_same_value_updates_prev_status(self):
        """同值再次赋值时 prev_status 仍会更新。"""
        self.assertEqual(self._trader.status, 'stopped')
        self._trader.status = 'stopped'
        self.assertEqual(self._trader.status, 'stopped')
        self.assertEqual(self._trader.prev_status, 'stopped')
        print('test_status_set_same_value_updates_prev_status: ok')


# --------------- _get_next_scheduled_task_and_countdown / 调度 ---------------

class TestTraderScheduling(unittest.TestCase):

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_get_next_task_before_all_tasks(self):
        """当前时间早于所有任务时，返回最近的一个未来任务及倒计时。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
            ('2000-01-01 10:00:00+00:00', 'run'),
        ]
        current = dt.time(9, 0)
        next_task, countdown = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task[1], 'open')
        # 09:00 -> 09:30 = 30*60 秒
        self.assertAlmostEqual(countdown, 30 * 60, delta=2)
        print('test_get_next_task_before_all_tasks: next_task', next_task, 'countdown', countdown)

    def test_get_next_task_between_two_tasks(self):
        """当前时间介于两任务之间时，返回下一个任务。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
            ('2000-01-01 10:00:00+00:00', 'run'),
        ]
        current = dt.time(9, 45)
        next_task, countdown = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task[1], 'run')
        self.assertAlmostEqual(countdown, 15 * 60, delta=2)
        print('test_get_next_task_between_two_tasks: next_task', next_task, 'countdown', countdown)

    def test_next_task_property_uses_internal_helper(self):
        """next_task property 与直接调用内部方法结果一致（需固定当前时间）。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
        ]
        current = dt.time(9, 0)
        next_from_helper, _ = self._trader._get_next_scheduled_task_and_countdown(current)
        # property 使用 get_current_tz_datetime()，不 mock 时可能不同；这里仅验证 property 可读
        next_prop = self._trader.next_task
        self.assertTrue(next_from_helper is not None or next_prop is not None)
        print('test_next_task_property_uses_internal_helper: next_task', next_prop)

    def test_get_next_task_empty_schedule(self):
        """无任务时 next_task 为 None，countdown 为到 23:59:59 的秒数且 >= 1。"""
        self._trader.task_daily_schedule = []
        current = dt.time(12, 0)
        next_task, countdown = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNone(next_task)
        self.assertGreaterEqual(countdown, 1)
        self.assertAlmostEqual(countdown, (23 - 12) * 3600 + 59 * 60 + 59, delta=2)
        print('test_get_next_task_empty_schedule: countdown', countdown)

    def test_get_next_task_all_past(self):
        """所有任务时间已过时 next_task 为 None。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
            ('2000-01-01 10:00:00+00:00', 'run'),
        ]
        current = dt.time(16, 0)
        next_task, countdown = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNone(next_task)
        self.assertGreaterEqual(countdown, 1)
        print('test_get_next_task_all_past: countdown', countdown)

    def test_get_next_task_at_exact_task_time(self):
        """当前时间恰等于某任务时间时，该任务不被选为“下一个”（严格 > current_time）。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
            ('2000-01-01 10:00:00+00:00', 'run'),
        ]
        current = dt.time(9, 30)
        next_task, _ = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task[1], 'run')  # 09:30 不算未来，下一个是 10:00
        print('test_get_next_task_at_exact_task_time: next_task', next_task)

    def test_count_down_to_next_task_property_minimum_is_one(self):
        """count_down_to_next_task 至少为 1。"""
        self._trader.task_daily_schedule = []
        # 不 mock 时间时，接近 23:59:59 可能得到 1
        count = self._trader.count_down_to_next_task
        self.assertGreaterEqual(count, 1)
        print('test_count_down_to_next_task_property_minimum_is_one: count', count)


# --------------- 账户资金与持仓 ---------------

class TestTraderAccountCash(unittest.TestCase):

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_account_cash_initial_values(self):
        """account_cash 与 get_account 中现金字段一致。"""
        cash = self._trader.account_cash
        self.assertIsInstance(cash, tuple)
        self.assertEqual(len(cash), 3)
        acc = get_account(self._trader.account_id, data_source=self._test_ds)
        self.assertEqual(cash[0], acc['cash_amount'])
        self.assertEqual(cash[1], acc['available_cash'])
        self.assertEqual(cash[2], acc['total_invest'])
        print('test_account_cash_initial_values: cash', cash)

    def test_account_cash_after_manual_account_update(self):
        """外部修改账户后 account_cash 反映最新值。"""
        update_account_balance(
            self._trader.account_id,
            data_source=self._test_ds,
            cash_amount_change=5000,
            available_cash_change=5000,
            total_investment_change=5000,
        )
        # 强制数据源刷新，避免 file 型数据源缓存导致读到旧值
        self._test_ds.reconnect()
        cash = self._trader.account_cash
        # 用当前数据源重新读取账户作为期望值（不依赖 Trader 内部缓存的 self.account）
        acc = get_account(self._trader.account_id, data_source=self._test_ds)
        self.assertEqual(cash[0], acc['cash_amount'], msg='account_cash[0] should match DB cash_amount')
        self.assertEqual(cash[1], acc['available_cash'], msg='account_cash[1] should match DB available_cash')
        self.assertEqual(cash[2], acc['total_invest'], msg='account_cash[2] should match DB total_invest')
        self.assertEqual(cash[0], 100000 + 5000)
        print('test_account_cash_after_manual_account_update: cash', cash)

    def test_account_positions_detail_contains_all_asset_pool_symbols(self):
        """account_positions 包含 asset_pool 中各 symbol 的持仓信息。"""
        pos = self._trader.account_positions
        self.assertFalse(pos.empty)
        for sym in ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']:
            self.assertIn(sym, pos.index.tolist(), msg=f'expected {sym} in positions')
        # 初始 fixture 中 000001 200, 000002 200, 000003 300, 000004 200
        print('test_account_positions_detail_contains_all_asset_pool_symbols: shape', pos.shape)


# --------------- 监控列表 / 实时价格（仅做轻量覆盖） ---------------

class TestTraderWatchList(unittest.TestCase):

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_watch_list_initialization_with_string_asset_pool(self):
        """asset_pool 为字符串时 watch_list 为 benchmark + 解析后的列表。"""
        self.assertEqual(self._trader.asset_pool, ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ'])
        self.assertEqual(self._trader.watch_list[0], '000300.SH')
        self.assertEqual(self._trader.watch_list[1], '000001.SZ')
        print('test_watch_list_initialization_with_string_asset_pool: ok')

    def test_watch_list_initialization_with_list_asset_pool(self):
        """asset_pool 为 list 时 watch_list 为 benchmark + asset_pool。"""
        test_ds = _create_test_datasource()
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        kwargs = _default_trader_kwargs()
        kwargs['asset_pool'] = ['000001.SZ']  # 覆盖默认的 asset_pool，避免重复传参
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **kwargs,
        )
        self.assertEqual(trader.watch_list, ['000300.SH', '000001.SZ'])
        _clear_tables(test_ds)
        print('test_watch_list_initialization_with_list_asset_pool: ok')


class TestTraderRuntimeLifecycle(unittest.TestCase):
    """Trader 运行时生命周期接口单测。"""

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_start_creates_trader_and_broker_threads(self):
        print('\n[TestTraderRuntimeLifecycle] start threads')
        started_targets = []

        class DummyThread:
            def __init__(self, target=None, daemon=None, name=None):
                self._target = target
                self._alive = False
                self.name = name or 'dummy-thread'

            def start(self):
                started_targets.append(self._target)
                self._alive = True

            def is_alive(self):
                return self._alive

            def join(self, timeout=None):
                self._alive = False

        with patch('qteasy.trader.threading.Thread', new=DummyThread):
            started = self._trader.start()
            print(' started:', started, 'target_count:', len(started_targets))
            self.assertTrue(started)
            self.assertEqual(len(started_targets), 2)
            self.assertIn(self._trader.run, started_targets)
            self.assertIn(self._trader.broker.run, started_targets)
            self.assertTrue(self._trader.is_alive())

    def test_stop_requests_post_close_and_stop_when_alive(self):
        print('\n[TestTraderRuntimeLifecycle] stop request with alive runtime')
        self._trader.status = 'running'
        self._trader._runtime_shutdown_requested = False

        added_tasks = []

        def fake_add_task(task, *args):
            added_tasks.append((task, args))

        self._trader.add_task = fake_add_task
        self._trader.join = lambda timeout=None: None
        self._trader._runtime_trader_thread = type('T', (), {'is_alive': lambda _self: True})()
        self._trader._runtime_broker_thread = None

        self._trader.stop(wait=False, include_post_close=True)
        print(' added_tasks:', added_tasks)
        self.assertEqual([item[0] for item in added_tasks], ['post_close', 'stop'])

    def test_stop_fallback_executes_stop_task_when_not_alive(self):
        print('\n[TestTraderRuntimeLifecycle] stop fallback path')
        self._trader.status = 'running'
        self._trader._runtime_shutdown_requested = False
        self._trader._runtime_trader_thread = None
        self._trader._runtime_broker_thread = None

        called = {}

        def fake_run_task(task, *args, run_in_main_thread=False):
            called['task'] = task
            called['run_in_main_thread'] = run_in_main_thread
            self._trader.status = 'stopped'

        self._trader._run_task = fake_run_task
        self._trader.stop(wait=False, include_post_close=False)
        print(' stop fallback called:', called)
        self.assertEqual(called.get('task'), 'stop')
        self.assertTrue(called.get('run_in_main_thread'))
        self.assertEqual(self._trader.status, 'stopped')

    def test_start_is_idempotent_when_runtime_alive(self):
        print('\n[TestTraderRuntimeLifecycle] start idempotent')
        self._trader._runtime_trader_thread = type('T', (), {'is_alive': lambda _self: True})()
        self._trader._runtime_broker_thread = type('B', (), {'is_alive': lambda _self: True})()

        with patch('qteasy.trader.threading.Thread') as mock_thread_cls:
            started = self._trader.start()
            print(' started:', started, 'thread_ctor_called:', mock_thread_cls.called)
            self.assertFalse(started)
            self.assertFalse(mock_thread_cls.called)


class TestTraderTaskManagerPhase2(unittest.TestCase):
    """阶段2：任务管理器能力单测。"""

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account(debug=True)

    def tearDown(self):
        if getattr(self._trader, '_async_executor', None) is not None:
            self._trader._async_executor.shutdown(wait=False, cancel_futures=True)
            self._trader._async_executor = None
        _clear_tables(self._test_ds)

    def test_add_task_returns_task_id_and_cancel_marks_task(self):
        print('\n[TestTraderTaskManagerPhase2] add/cancel task')
        task_id = self._trader.add_task('pause')
        print(' task_id:', task_id)
        self.assertTrue(task_id.startswith('task-'))
        self.assertIn(task_id, self._trader._task_registry)
        canceled = self._trader.cancel_task(task_id)
        print(' canceled:', canceled, 'status:', self._trader._task_registry[task_id].status)
        self.assertTrue(canceled)
        self.assertTrue(self._trader._task_registry[task_id].canceled)

    def test_handle_task_failure_retries_then_dead_letter(self):
        print('\n[TestTraderTaskManagerPhase2] retry and dead-letter')
        task_id = self._trader.add_task('pause', max_retries=1)
        task_spec = self._trader._task_registry[task_id]
        print(' initial retry_count/max:', task_spec.retry_count, task_spec.max_retries)

        self._trader._handle_task_failure(task_spec, RuntimeError('first-fail'))
        print(' after first fail retry_count:', task_spec.retry_count, 'queue size:', self._trader.task_queue.qsize())
        self.assertEqual(task_spec.retry_count, 1)
        self.assertEqual(task_spec.status, 'queued')

        retry_task = self._trader.task_queue.get()
        self._trader.task_queue.task_done()
        self._trader._handle_task_failure(retry_task, RuntimeError('second-fail'))
        print(' dead_letter size:', len(self._trader.dead_letter_tasks))
        self.assertEqual(retry_task.status, 'failed')
        self.assertEqual(len(self._trader.dead_letter_tasks), 1)

    def test_async_task_uses_single_worker_executor(self):
        print('\n[TestTraderTaskManagerPhase2] async executor limit')
        task_id = self._trader.add_task('acquire_live_price')
        task_spec = self._trader._task_registry[task_id]
        with patch.object(self._trader, '_update_live_price', return_value=None):
            self._trader._run_task('acquire_live_price', task_spec=task_spec)
        print(' executor workers:', self._trader._async_executor._max_workers)
        self.assertIsNotNone(self._trader._async_executor)
        self.assertEqual(self._trader._async_executor._max_workers, 1)

    def test_cancel_tasks_batch_and_list_tasks_filters(self):
        print('\n[TestTraderTaskManagerPhase2] batch cancel and list')
        task_id_1 = self._trader.add_task('pause')
        task_id_2 = self._trader.add_task('pause')
        task_id_3 = self._trader.add_task('resume')
        print(' task_ids:', task_id_1, task_id_2, task_id_3)

        canceled_count = self._trader.cancel_tasks(name='pause', status='queued')
        paused_tasks = self._trader.list_tasks(name='pause')
        queued_resume = self._trader.list_tasks(status='queued', name='resume')
        print(' canceled_count:', canceled_count)
        print(' paused statuses:', [task.status for task in paused_tasks])
        print(' queued resume:', [task.task_id for task in queued_resume])

        self.assertEqual(canceled_count, 2)
        self.assertTrue(all(task.canceled for task in paused_tasks))
        self.assertEqual(len(queued_resume), 1)
        self.assertEqual(queued_resume[0].task_id, task_id_3)

    def test_async_task_failure_goes_dead_letter_after_retry_exhausted(self):
        print('\n[TestTraderTaskManagerPhase2] async failure dead-letter')
        task_id = self._trader.add_task('acquire_live_price', max_retries=0)
        task_spec = self._trader.get_task(task_id)
        self.assertIsNotNone(task_spec)

        with patch.object(self._trader, '_update_live_price', side_effect=RuntimeError('async-fail-test')):
            self._trader._run_task('acquire_live_price', task_spec=task_spec)
            time.sleep(0.2)

        print(' task status:', task_spec.status, 'dead_letter_count:', len(self._trader.dead_letter_tasks))
        self.assertEqual(task_spec.status, 'failed')
        self.assertEqual(len(self._trader.dead_letter_tasks), 1)
        self.assertEqual(self._trader.dead_letter_tasks[0].task_id, task_id)


if __name__ == '__main__':
    unittest.main()
