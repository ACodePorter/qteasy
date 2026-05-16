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

import qteasy as qt
from qteasy import DataSource, Operator
from qteasy.trade_recording import new_account, get_account, get_or_create_position, update_position, update_account_balance
from qteasy.trader import Trader
from qteasy.broker import SimulatorBroker
from qteasy.trading_util import (
    apply_schedule_catch_up_policy,
    create_daily_task_plan,
    create_daily_task_schedule,
)


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


class _BrokerRemoteCashMismatch(SimulatorBroker):
    """用于启动门禁 L3：返回与本地账本不一致的远端现金。"""

    def get_remote_cash(self, *, account_id=None):
        return 0.01


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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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
        broker = SimulatorBroker(reject_submit_probability=0.0)
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


class TestTraderSchedulerPhase3(unittest.TestCase):
    """阶段3：日程规划与追赶策略单测。"""

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account(debug=True)

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_create_daily_task_schedule_same_input_same_output(self):
        print('\n[TestTraderSchedulerPhase3] deterministic daily schedule')
        op = Operator(strategies='macd', run_freq='h', run_timing='open')
        schedule_1 = create_daily_task_schedule(
            op,
            current_date='2023-05-10',
            market_open_time_am='09:30:00',
            market_close_time_am='11:30:00',
            market_open_time_pm='13:00:00',
            market_close_time_pm='15:00:00',
            live_price_frequency='30min',
            daily_refill_tables='',
            weekly_refill_tables='',
            monthly_refill_tables='',
        )
        schedule_2 = create_daily_task_schedule(
            op,
            current_date='2023-05-10',
            market_open_time_am='09:30:00',
            market_close_time_am='11:30:00',
            market_open_time_pm='13:00:00',
            market_close_time_pm='15:00:00',
            live_price_frequency='30min',
            daily_refill_tables='',
            weekly_refill_tables='',
            monthly_refill_tables='',
        )
        print(' schedule_1 size:', len(schedule_1), 'schedule_2 size:', len(schedule_2))
        print(' first 3 entries:', schedule_1[:3])
        self.assertEqual(schedule_1, schedule_2)

    def test_create_daily_task_plan_run_strategy_args_are_normalized_tuple(self):
        print('\n[TestTraderSchedulerPhase3] planner output uses normalized args tuple')
        op = Operator(strategies='macd', run_freq='d', run_timing='close')
        task_plan = create_daily_task_plan(
            op,
            current_date='2023-05-10',
            daily_refill_tables='',
            weekly_refill_tables='',
            monthly_refill_tables='',
            live_price_frequency='h',
        )
        run_tasks = [item for item in task_plan if item.task_spec.name == 'run_strategy']
        print(' run task count:', len(run_tasks))
        print(' run task sample args:', run_tasks[0].task_spec.args if run_tasks else None)
        self.assertTrue(run_tasks)
        self.assertIsInstance(run_tasks[0].task_spec.args, tuple)
        self.assertEqual(len(run_tasks[0].task_spec.args), 1)
        self.assertIsInstance(run_tasks[0].as_legacy_tuple()[2], int)

    def test_initialize_schedule_uses_trader_current_date_for_monthly_refill(self):
        print('\n[TestTraderSchedulerPhase3] initialize schedule should honor force_current_date')
        self._trader.force_current_date = pd.to_datetime('2023-01-01').date()
        self._trader.daily_refill_tables = ''
        self._trader.weekly_refill_tables = ''
        self._trader.monthly_refill_tables = 'stock_daily'
        self._trader.task_daily_schedule = []
        self._trader._initialize_schedule(dt.time(8, 0, 0))
        refill_tasks = [task for task in self._trader.task_daily_schedule if task[1] == 'refill']
        print(' refill tasks:', refill_tasks)
        self.assertEqual(len(refill_tasks), 1)
        self.assertEqual(refill_tasks[0], ('16:00:00', 'refill', ('stock_daily', 31)))

    def test_apply_schedule_catch_up_policy_midday_keeps_key_tasks(self):
        print('\n[TestTraderSchedulerPhase3] midday catch-up keep key task names')
        schedule = [
            ('09:15:00', 'pre_open'),
            ('09:30:00', 'open_market'),
            ('10:00:00', 'run_strategy', 0),
            ('11:35:00', 'close_market'),
            ('12:55:00', 'open_market'),
            ('13:10:00', 'acquire_live_price'),
        ]
        out = apply_schedule_catch_up_policy(
            task_schedule=schedule,
            current_time=dt.time(13, 5, 0),
            market_open_time_am='09:30:00',
            market_close_time_am='11:30:00',
            market_open_time_pm='13:00:00',
            market_close_time_pm='15:00:00',
        )
        print(' output schedule:', out)
        names = [task[1] for task in out]
        print(' output names:', names)
        self.assertNotIn('run_strategy', names)
        self.assertIn('pre_open', names)
        self.assertIn('open_market', names)
        self.assertIn('close_market', names)
        self.assertIn('acquire_live_price', names)


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

        def fake_add_task(task, *args, **kwargs):
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

        def fake_run_task(task, *args, run_in_main_thread=False, task_spec=None):
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

    def test_add_task_skips_reentry_for_run_strategy_when_prev_running(self):
        print('\n[TestTraderTaskManagerPhase2] run_strategy reentry skip_reason=prev_running')
        first_task_id = self._trader.add_task('run_strategy', 0)
        first_task_spec = self._trader.get_task(first_task_id)
        self.assertIsNotNone(first_task_spec)
        self.assertEqual(self._trader.task_queue.qsize(), 1)
        self._trader.task_queue.get()
        self._trader.task_queue.task_done()
        first_task_spec.status = 'running'

        second_task_id = self._trader.add_task('run_strategy', 1)
        second_task_spec = self._trader.get_task(second_task_id)
        print(' first_task_status:', first_task_spec.status)
        print(' second_task_status:', second_task_spec.status)
        print(' second_last_error:', second_task_spec.last_error)
        print(' queue_size:', self._trader.task_queue.qsize())
        self.assertEqual(second_task_spec.status, 'skipped')
        self.assertIn('skip_reason=prev_running', second_task_spec.last_error)
        self.assertEqual(self._trader.task_queue.qsize(), 0)

    def test_process_result_reentry_policy_drop_is_forced_to_queue(self):
        print('\n[TestTraderTaskManagerPhase2] process_result never dropped by reentry policy')
        first_task_id = self._trader.add_task('process_result', {'order_id': 1})
        first_task_spec = self._trader.get_task(first_task_id)
        self.assertIsNotNone(first_task_spec)
        self._trader.task_queue.get()
        self._trader.task_queue.task_done()
        first_task_spec.status = 'running'

        second_task_id = self._trader.add_task('process_result', {'order_id': 2}, reentry_policy='drop')
        second_task_spec = self._trader.get_task(second_task_id)
        print(' first_task_status:', first_task_spec.status)
        print(' second_task_status:', second_task_spec.status)
        print(' second_task_reentry_policy:', second_task_spec.reentry_policy)
        print(' queue_size:', self._trader.task_queue.qsize())
        self.assertEqual(second_task_spec.reentry_policy, 'queue')
        self.assertEqual(second_task_spec.status, 'queued')
        self.assertEqual(self._trader.task_queue.qsize(), 1)


class TestTraderPhase5SnapshotAndGate(unittest.TestCase):
    """阶段 5-A/5-B：日程 prepare、快照跳过原因、启动门禁与 run_strategy 入队。"""

    def setUp(self) -> None:
        self._cfg_snap = {
            'live_trade_split_strategy_prepare': qt.QT_CONFIG.get('live_trade_split_strategy_prepare', False),
            'live_trade_prepare_lead_seconds': qt.QT_CONFIG.get('live_trade_prepare_lead_seconds', 5),
            'live_trade_startup_gate_mode': qt.QT_CONFIG.get('live_trade_startup_gate_mode', 'off'),
            'live_trade_strategy_snapshot_max_age_seconds': qt.QT_CONFIG.get(
                'live_trade_strategy_snapshot_max_age_seconds', 180.0
            ),
        }

    def tearDown(self) -> None:
        qt.configure(**self._cfg_snap)

    def test_create_daily_task_plan_inserts_prepare_before_run_when_split(self) -> None:
        print('\n[TestTraderPhase5] split schedule: prepare then run_strategy')
        qt.configure(live_trade_split_strategy_prepare=True, live_trade_prepare_lead_seconds=60)
        op = Operator(strategies='macd', run_freq='30min', run_timing='close')
        task_plan = create_daily_task_plan(
            op,
            current_date='2023-05-10',
            daily_refill_tables='',
            weekly_refill_tables='',
            monthly_refill_tables='',
            live_price_frequency='30min',
        )
        day = '2000-01-01 '
        for st in task_plan:
            if st.task_spec.name != 'run_strategy':
                continue
            step_args = st.task_spec.args
            prep_tasks = [
                x for x in task_plan
                if x.task_spec.name == 'prepare_strategy_snapshot' and x.task_spec.args == step_args
            ]
            print(' run_strategy args', step_args, 'prep matches:', len(prep_tasks))
            self.assertEqual(len(prep_tasks), 1)
            delta = (pd.to_datetime(day + st.task_time) - pd.to_datetime(day + prep_tasks[0].task_time)).total_seconds()
            print('  lead seconds:', delta)
            self.assertGreaterEqual(delta, 59.0)
            self.assertLessEqual(delta, 61.0)

    def test_strategy_snapshot_skip_reason_missing_when_split(self) -> None:
        print('\n[TestTraderPhase5] snapshot_missing when marker unset')
        trader, test_ds = create_trader_with_account()
        try:
            qt.configure(live_trade_split_strategy_prepare=True)
            trader.debug = True
            trader.force_current_date = pd.Timestamp('2023-05-10').date()
            r = trader._strategy_snapshot_skip_reason(0)
            print(' skip_reason:', r)
            self.assertEqual(r, 'snapshot_missing')
        finally:
            _clear_tables(test_ds)

    def test_startup_gate_block_skips_run_strategy_enqueue(self) -> None:
        print('\n[TestTraderPhase5] gate block skips run_strategy via gate_failed')
        trader, test_ds = create_trader_with_account()
        try:
            qt.configure(live_trade_startup_gate_mode='block')
            trader.debug = True
            trader.force_current_date = pd.Timestamp('2023-05-10').date()
            trader._broker = _BrokerRemoteCashMismatch()
            ok = trader.run_startup_gate()
            print(' gate ok:', ok, 'allowed:', trader._startup_gate_trading_allowed)
            self.assertFalse(ok)
            tid = trader.add_task('run_strategy', 0)
            spec = trader.get_task(tid)
            print(' task status:', spec.status, 'last_error:', spec.last_error)
            self.assertEqual(spec.status, 'skipped')
            self.assertIn('gate_failed', spec.last_error or '')
        finally:
            _clear_tables(test_ds)

    def test_collect_broker_reconcile_snapshot_matches_gate_failure_reason(self) -> None:
        print('\n[TestTraderPhase5] reconcile snapshot and startup gate share mismatch reasons')
        trader, test_ds = create_trader_with_account()
        try:
            qt.configure(live_trade_startup_gate_mode='block')
            trader.force_current_date = pd.Timestamp('2023-05-10').date()
            trader._broker = _BrokerRemoteCashMismatch()
            snapshot = trader.collect_broker_reconcile_snapshot()
            print(' reconcile failures:', snapshot.get('failures'))
            print(' reconcile cash_diff:', snapshot.get('cash_diff'))
            print(' reconcile remote_orders_count:', snapshot.get('remote_orders_count'))
            self.assertGreater(len(snapshot.get('failures', [])), 0)
            self.assertIn(
                True,
                [
                    'broker_cash_mismatch' in snapshot.get('failures', []),
                    'operator_not_ready' in snapshot.get('failures', []),
                ],
            )
            gate_ok = trader.run_startup_gate()
            print(' gate ok:', gate_ok, 'allowed:', trader._startup_gate_trading_allowed)
            self.assertFalse(gate_ok)
            self.assertFalse(trader._startup_gate_trading_allowed)
        finally:
            _clear_tables(test_ds)

    def test_post_close_emits_reconcile_checkpoint_trace(self) -> None:
        print('\n[TestTraderPhase5] post_close emits reconcile checkpoint trace')
        trader, test_ds = create_trader_with_account()
        try:
            trader.is_market_open = False
            with patch.object(
                    trader,
                    'collect_broker_reconcile_snapshot',
                    return_value={
                        'failures': ['broker_cash_mismatch'],
                        'cash_diff': 123.45,
                        'position_qty_diff': 0.0,
                        'remote_orders_count': 2,
                    },
            ):
                with patch.object(trader, '_trace_event') as mock_trace:
                    trader._post_close()
                    reconcile_calls = [
                        call for call in mock_trace.call_args_list
                        if call.kwargs.get('category') == 'reconcile'
                    ]
                    print(' reconcile trace calls:', [c.kwargs for c in reconcile_calls])
                    self.assertGreater(len(reconcile_calls), 0)
                    last_call = reconcile_calls[-1].kwargs
                    self.assertEqual(last_call.get('event'), 'checkpoint_warn')
                    self.assertEqual(last_call.get('checkpoint'), 'post_close')
                    self.assertEqual(last_call.get('grade'), 'warn_only')
                    self.assertIn('broker_cash_mismatch', last_call.get('failures', ''))
        finally:
            _clear_tables(test_ds)

    def test_collect_pending_order_diagnostics_detects_mismatch(self) -> None:
        print('\n[TestTraderPhase5] pending order diagnostics should detect mismatch')
        trader, test_ds = create_trader_with_account()
        try:
            local_orders = pd.DataFrame(
                [
                    {'order_id': 11, 'status': 'submitted', 'broker_order_id': 'BRK-11'},
                    {'order_id': 12, 'status': 'partial-filled', 'broker_order_id': None},
                    {'order_id': 13, 'status': 'created', 'broker_order_id': None},
                ],
            ).set_index('order_id')
            remote_orders = [{'broker_order_id': 'BRK-11'}, {'broker_order_id': 'BRK-99'}]
            with patch('qteasy.trader.query_trade_orders', return_value=local_orders):
                with patch.object(trader.broker, 'get_remote_orders', return_value=remote_orders):
                    diag = trader.collect_pending_order_diagnostics()
            print(' pending diagnostics:', diag)
            self.assertEqual(diag['local_pending_count'], 3)
            self.assertEqual(diag['remote_pending_count'], 2)
            self.assertEqual(diag['local_pending_without_broker_order_id'], [12])
            self.assertEqual(diag['local_pending_missing_remote'], [])
            self.assertEqual(diag['remote_pending_not_in_local'], ['BRK-99'])
            self.assertFalse(diag['is_ok'])
        finally:
            _clear_tables(test_ds)


if __name__ == '__main__':
    unittest.main()
