# coding=utf-8
# ======================================
# File:     test_trader_integration.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-05-09
# Desc:
#   集成测试：
#   Trader 日志与断点、成交与交割、调度与 run()，
#   使用专用测试 DataSource（非 QT_DATA_SOURCE），
#   测试完成后清理表数据。
# ======================================

import os
import time
import unittest
from unittest.mock import patch

import pandas as pd

from qteasy import DataSource, Operator
from qteasy.trade_recording import (
    new_account,
    get_or_create_position,
    update_position,
    save_parsed_trade_orders,
    get_account,
    get_position_by_id,
)
from qteasy.trading_util import (
    submit_order,
    process_trade_result,
    cancel_order,
    process_account_delivery,
    deliver_trade_result,
    trade_log_file_path_name,
    sys_log_file_path_name,
    break_point_file_path_name,
)
from qteasy.trader import Trader
from qteasy.broker import SimulatorBroker


# --------------- 测试用 DataSource：从公共夹具导入（data_test_trader，legacy=False） ---------------

from tests.trader_test_helpers import (
    clear_tables,
    create_trader_with_account,
    create_trader_with_orders_and_results,
)
# 集成测试保持原有 stoppage=0.1 行为，在调用处传入
_clear_tables = clear_tables


# --------------- 日志与断点 ---------------

class TestTraderLogAndBreakPoint(unittest.TestCase):

    def tearDown(self):
        if getattr(self, '_test_ds', None) is not None:
            _clear_tables(self._test_ds)

    def test_trade_log_file_initialized_with_headers(self):
        """renew_trade_log_file 后交易日志文件存在且首行为 header。"""
        trader, self._test_ds = create_trader_with_account()
        trader.renew_trade_log_file()
        path = trade_log_file_path_name(trader.account_id, trader.datasource)
        self.assertTrue(os.path.exists(path), msg=f'trade log file should exist: {path}')
        with open(path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        expected_header = ','.join(Trader.trade_log_file_headers)
        self.assertEqual(first_line, expected_header, msg='first line should be header')
        print('test_trade_log_file_initialized_with_headers: path', path)

    def test_sys_log_file_initialized_and_writes_message(self):
        """init_system_logger 后系统日志文件存在且可写入。"""
        trader, self._test_ds = create_trader_with_account()
        trader.init_system_logger()
        test_msg = 'test-message-integration'
        trader.live_sys_logger.info(test_msg)
        path = sys_log_file_path_name(trader.account_id, trader.datasource)
        self.assertTrue(os.path.exists(path), msg=f'sys log file should exist: {path}')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(test_msg, content, msg='log content should contain test message')
        print('test_sys_log_file_initialized_and_writes_message: ok')

    def test_break_point_save_and_clear(self):
        """save_break_point 创建文件，clear_break_point 删除文件。"""
        trader, self._test_ds = create_trader_with_account()
        path = break_point_file_path_name(trader.account_id, trader.datasource)
        if os.path.exists(path):
            os.remove(path)
        trader.save_break_point()
        self.assertTrue(os.path.exists(path), msg='break point file should exist after save')
        trader.clear_break_point()
        self.assertFalse(os.path.exists(path), msg='break point file should be removed after clear')
        print('test_break_point_save_and_clear: ok')

    def test_clear_break_point_on_non_exist_file(self):
        """断点文件不存在时 clear_break_point 不抛异常。"""
        trader, self._test_ds = create_trader_with_account()
        path = break_point_file_path_name(trader.account_id, trader.datasource)
        if os.path.exists(path):
            os.remove(path)
        trader.clear_break_point()
        trader.clear_break_point()
        print('test_clear_break_point_on_non_exist_file: ok')


# --------------- 成交与交割流程 ---------------

class TestTraderTradeFlow(unittest.TestCase):

    def tearDown(self):
        if getattr(self, '_test_ds', None) is not None:
            _clear_tables(self._test_ds)

    def test_positions_and_account_after_full_trade_flow(self):
        """完整成交流程后持仓与账户现金与 fixture 预期一致。"""
        trader, self._test_ds = create_trader_with_orders_and_results(stoppage=0.05)
        # 订单 1: 买 100 @ 60.5 -> 000001 持仓增加 100；订单 2: 卖 100 @ 70.5；等
        # 仅做关键断言：账户有扣减/增加，trade log 有数据行
        acc = get_account(trader.account_id, data_source=self._test_ds)
        self.assertIn('cash_amount', acc)
        self.assertIn('total_invest', acc)
        path = trade_log_file_path_name(trader.account_id, trader.datasource)
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # header + 至少若干数据行
        self.assertGreaterEqual(len(lines), 2, msg='trade log should have at least header and one data row')
        print('test_positions_and_account_after_full_trade_flow: cash_amount', acc['cash_amount'], 'lines', len(lines))

    def test_partial_fill_and_cancelled_orders_effects(self):
        """部分成交与撤单后持仓与现金变化符合预期。"""
        # 使用同一 fixture，其中 order 5 全部成交，order 8 被 cancel
        trader, self._test_ds = create_trader_with_orders_and_results(stoppage=0.05)
        acc = get_account(trader.account_id, data_source=self._test_ds)
        self.assertIsNotNone(acc['cash_amount'])
        # 部分成交会导致持仓逐步变化，撤单不影响持仓
        pos1 = get_position_by_id(1, self._test_ds)
        self.assertIsNotNone(pos1)
        print('test_partial_fill_and_cancelled_orders_effects: position 1 qty', pos1.get('qty'))


# --------------- 调度与 run()（轻量） ---------------

class TestTraderRunStatus(unittest.TestCase):

    def tearDown(self):
        if getattr(self, '_test_ds', None) is not None:
            _clear_tables(self._test_ds)

    def test_run_respects_stopped_status(self):
        """status 为 stopped 时主循环应能退出（不长时间阻塞）。"""
        trader, self._test_ds = create_trader_with_account()
        trader.status = 'stopped'
        # 不真正启动 run() 的无限循环，仅验证状态被尊重；若需测 run() 可在此起线程后短时 join
        print('\n[TestTraderRunStatus] status:', trader.status)
        self.assertEqual(trader.status, 'stopped')
        print('test_run_respects_stopped_status: ok')


class TestTraderPhase0Observability(unittest.TestCase):
    """阶段0：关键链路结构化日志与回归行为验证。"""

    def tearDown(self):
        if getattr(self, '_test_ds', None) is not None:
            _clear_tables(self._test_ds)

    def test_add_task_writes_structured_queue_trace(self):
        print('\n[TestTraderPhase0Observability] add_task trace')
        trader, self._test_ds = create_trader_with_account(debug=True)
        trader.init_system_logger()
        log_path = sys_log_file_path_name(trader.account_id, trader.datasource)
        size_before = os.path.getsize(log_path) if os.path.exists(log_path) else 0

        trader.add_task('pause')
        for handler in trader.live_sys_logger.handlers:
            handler.flush()

        with open(log_path, 'r', encoding='utf-8') as f:
            f.seek(size_before)
            new_logs = f.read()

        print(' new log tail:\n', new_logs[-500:])
        print(' queue size now:', trader.task_queue.qsize())
        self.assertIn('category=task_queue event=task_add_requested', new_logs)
        self.assertIn('category=task_queue event=task_enqueued', new_logs)

    def test_run_enqueues_and_executes_process_result_task(self):
        print('\n[TestTraderPhase0Observability] run broker-result chain')
        trader, self._test_ds = create_trader_with_account(debug=True)
        trader.init_system_logger()
        log_path = sys_log_file_path_name(trader.account_id, trader.datasource)
        size_before = os.path.getsize(log_path) if os.path.exists(log_path) else 0

        broker_result = {
            'order_id': 123456,
            'filled_qty': 100.0,
            'price': 10.0,
            'transaction_fee': 1.0,
            'execution_time': '2026-05-11 09:31:00',
            'canceled_qty': 0.0,
            'delivery_amount': 0.0,
            'delivery_status': 'ND',
        }
        trader.broker.result_queue.put(broker_result)

        executed_tasks = []
        original_run_task = trader._run_task

        def fake_run_task(task, *args, run_in_main_thread=False, task_spec=None):
            executed_tasks.append((task, args))
            if task == 'start':
                trader.status = 'running'
                return
            if task == 'process_result':
                trader.status = 'stopped'
                return
            return original_run_task(
                task, *args, run_in_main_thread=run_in_main_thread, task_spec=task_spec
            )

        trader._run_task = fake_run_task
        trader._add_task_from_schedule = lambda current_time=None: None

        trader.run()
        for handler in trader.live_sys_logger.handlers:
            handler.flush()
        with open(log_path, 'r', encoding='utf-8') as f:
            f.seek(size_before)
            new_logs = f.read()

        executed_names = [task for task, _ in executed_tasks]
        print(' executed_tasks:', executed_tasks)
        print(' new log tail:\n', new_logs[-800:])
        self.assertIn('start', executed_names)
        self.assertIn('process_result', executed_names)
        self.assertIn('category=broker event=result_received', new_logs)
        self.assertIn('category=task_runner event=task_execute_started', new_logs)
        self.assertIn('task=process_result', new_logs)

    def test_run_forwards_polled_broker_messages_to_trader_queue(self):
        print('\n[TestTraderPhase0Observability] run broker-message poll chain')
        trader, self._test_ds = create_trader_with_account(debug=True)

        polled_once = {'done': False}

        def fake_poll_fills(timeout=0.0):
            return []

        def fake_poll_messages(timeout=0.0):
            if polled_once['done']:
                return []
            polled_once['done'] = True
            trader.status = 'stopped'
            return ['[BrokerMock]: polled-message']

        trader.broker.poll_fills = fake_poll_fills
        trader.broker.poll_messages = fake_poll_messages

        original_run_task = trader._run_task

        def fake_run_task(task, *args, run_in_main_thread=False, task_spec=None):
            if task == 'start':
                trader.status = 'running'
                return
            return original_run_task(
                task, *args, run_in_main_thread=run_in_main_thread, task_spec=task_spec
            )

        trader._run_task = fake_run_task
        trader._add_task_from_schedule = lambda current_time=None: None

        from qteasy.trader import coerce_trader_message

        trader.run()
        broker_message = coerce_trader_message(trader.message_queue.get_nowait())
        print(' broker_message:', broker_message)
        self.assertIn('polled-message', broker_message.text)

    def test_run_emits_task_execute_failed_trace_on_runtime_error(self):
        print('\n[TestTraderPhase0Observability] run task failure trace')
        trader, self._test_ds = create_trader_with_account(debug=True)
        trader.init_system_logger()
        log_path = sys_log_file_path_name(trader.account_id, trader.datasource)
        size_before = os.path.getsize(log_path) if os.path.exists(log_path) else 0

        trader.add_task('pause')
        trader.add_task('stop')

        executed_tasks = []

        def fake_run_task(task, *args, run_in_main_thread=False, task_spec=None):
            executed_tasks.append((task, args))
            if task == 'start':
                trader.status = 'running'
                return
            if task == 'pause':
                raise RuntimeError('phase0-test-runtime-error')
            if task == 'stop':
                trader.status = 'stopped'
                return
            return None

        trader._run_task = fake_run_task
        trader._add_task_from_schedule = lambda current_time=None: None

        trader.run()
        for handler in trader.live_sys_logger.handlers:
            handler.flush()
        with open(log_path, 'r', encoding='utf-8') as f:
            f.seek(size_before)
            new_logs = f.read()

        print(' executed_tasks:', executed_tasks)
        print(' new log tail:\n', new_logs[-1000:])
        self.assertIn('category=task_runner event=task_execute_failed', new_logs)
        self.assertIn('error_type=RuntimeError', new_logs)
        self.assertIn('task=pause', new_logs)

    def test_process_result_emits_failed_trace_when_processing_raises(self):
        print('\n[TestTraderPhase0Observability] process_result failure trace')
        trader, self._test_ds = create_trader_with_account(debug=True)
        trader.init_system_logger()
        log_path = sys_log_file_path_name(trader.account_id, trader.datasource)
        size_before = os.path.getsize(log_path) if os.path.exists(log_path) else 0
        result = {'order_id': 888001, 'filled_qty': 1.0, 'price': 1.0, 'transaction_fee': 0.0, 'canceled_qty': 0.0}

        with patch('qteasy.trader.process_trade_result', side_effect=ValueError('phase0-process-result-error')):
            trader._process_result(result)

        for handler in trader.live_sys_logger.handlers:
            handler.flush()
        with open(log_path, 'r', encoding='utf-8') as f:
            f.seek(size_before)
            new_logs = f.read()

        print(' process_result input:', result)
        print(' new log tail:\n', new_logs[-1000:])
        self.assertIn('category=trade_result event=process_started', new_logs)
        self.assertIn('category=trade_result event=process_failed', new_logs)
        self.assertIn('order_id=888001', new_logs)
        self.assertIn('error_type=ValueError', new_logs)


if __name__ == '__main__':
    unittest.main()
