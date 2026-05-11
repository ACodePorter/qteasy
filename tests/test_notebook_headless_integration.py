# coding=utf-8
# ======================================
# File: test_notebook_headless_integration.py
# Author: Jackie PENG / David
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-05-11
# Desc:
#   将 notebook 无头八阶段中与阶段 0～3.5 相关的链路固化为 unittest：
#   使用隔离 file DataSource + 固定回放日（非真实时钟、非 QT_DATA_SOURCE）。
# ======================================

from __future__ import annotations

import unittest

from tests.notebook_trader_headless_script import (
    create_headless_notebook_session,
    stage4_phase35_checks,
    stage5_stage0to3_regression,
)


class TestNotebookHeadlessSmoke(unittest.TestCase):
    """无头 notebook 脚本关键路径的回归（隔离数据源）。"""

    def test_isolated_session_operator_three_groups(self) -> None:
        """阶段 0～3 相关：会话创建后 Operator 三策略组与日程非空。"""
        print('\n[TestNotebookHeadlessSmoke] isolated session, three strategy groups')
        session = create_headless_notebook_session(
            debug=False,
            use_real_time=False,
            use_isolated_datasource=True,
        )
        gids = session.trader.operator.group_ids
        print(' group_ids:', gids)
        self.assertEqual(gids, ['Group_1', 'Group_2', 'Group_3'])
        self.assertGreater(len(session.trader.task_daily_schedule), 0)
        print(' schedule_len:', len(session.trader.task_daily_schedule))

    def test_stage4_phase35_idempotent_cancel_delivery_isolated(self) -> None:
        """阶段 3.5：隔离库上 submit → process_trade_result 幂等 → 撤单 → 交割与 history_orders。"""
        print('\n[TestNotebookHeadlessSmoke] stage4 phase3.5 chain on isolated datasource')
        session = create_headless_notebook_session(
            debug=False,
            use_real_time=False,
            use_isolated_datasource=True,
        )
        out = stage4_phase35_checks(session, info=False)
        print(' stage4 out keys:', sorted(out.keys()))
        print(' supports_broker_result_id:', out.get('supports_broker_result_id'))
        print(' duplicate_mode:', out.get('duplicate_mode'))
        print(' duplicate_result_id_equal:', out.get('duplicate_result_id_equal'))
        print(' duplicate_result_rows:', out.get('duplicate_result_rows'))
        print(' second_order_status:', out.get('second_order_status'))

        self.assertGreater(out.get('first_order_id', 0), 0)
        self.assertEqual(out.get('second_order_status'), 'canceled')

        if out.get('supports_broker_result_id'):
            self.assertEqual(out.get('duplicate_mode'), 'idempotent_return')
            self.assertTrue(out.get('duplicate_result_id_equal'))
            self.assertEqual(out.get('duplicate_result_rows'), 1)
            self.assertEqual(out.get('duplicate_error'), '')
        else:
            self.assertIn(
                out.get('duplicate_mode'),
                ('rejected_or_non_idempotent', 'idempotent_return'),
            )

        from qteasy.trade_recording import read_trade_order_detail

        od = read_trade_order_detail(int(out['second_order_id']), data_source=session.datasource)
        print(' second order detail status/qty:', od.get('status'), od.get('qty'))
        self.assertEqual(od.get('status'), 'canceled')

        s5 = stage5_stage0to3_regression(session, info=False)
        print(' stage5 schedule_size:', s5.get('schedule_size'))
        self.assertGreater(int(s5.get('schedule_size', 0)), 0)


if __name__ == '__main__':
    unittest.main()
