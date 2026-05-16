# coding=utf-8
# ======================================
# File: test_notebook_headless_integration.py
# Author: Jackie PENG / David
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-05-11
# Desc:
#   将 notebook 无头脚本中与阶段 0～3.5 相关的链路固化为 unittest：
#   使用隔离 file DataSource + 固定回放日（非真实时钟、非 QT_DATA_SOURCE）。
# ======================================

from __future__ import annotations

import unittest

from tests.notebook_trader_headless_script import (
    create_headless_notebook_session,
    stage4_phase35_checks,
    stage5_stage0to3_regression,
    stage10_phase4_c_smoke,
    stage11_phase5_c_smoke,
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

    def test_stage10_phase4c_facade_registry_reconcile_isolated(self) -> None:
        """阶段 4-C：隔离库无头脚本验证 Facade、注册扩展与对账入口。"""
        print('\n[TestNotebookHeadlessSmoke] stage10 phase4-c smoke on isolated datasource')
        session = create_headless_notebook_session(
            debug=False,
            use_real_time=False,
            use_isolated_datasource=True,
        )
        out = stage10_phase4_c_smoke(session, info=False)
        print(' stage10 out keys:', sorted(out.keys()))
        print(' broker_type:', out.get('broker_type'))
        print(' broker_is_facade:', out.get('broker_is_facade'))
        print(' enqueue_order_exists:', out.get('enqueue_order_exists'))
        print(' registry_roundtrip_ok:', out.get('registry_roundtrip_ok'))
        print(' reconcile_is_ok:', out.get('reconcile_is_ok'))
        print(' reconcile_ok_for_smoke:', out.get('reconcile_ok_for_smoke'))
        print(' reconcile failures:', out.get('reconcile_snapshot', {}).get('failures'))
        self.assertTrue(out.get('broker_is_facade'))
        self.assertTrue(out.get('enqueue_order_exists'))
        self.assertTrue(out.get('registry_roundtrip_ok'))
        self.assertTrue(out.get('reconcile_ok_for_smoke'))

    def test_stage11_phase5c_order_mapping_rotation_and_diag_isolated(self) -> None:
        """阶段 5-C：隔离库无头脚本验证订单映射、risk 轮换、pending 诊断与 post_close 检查点。"""
        print('\n[TestNotebookHeadlessSmoke] stage11 phase5-c smoke on isolated datasource')
        session = create_headless_notebook_session(
            debug=False,
            use_real_time=False,
            use_isolated_datasource=True,
        )
        out = stage11_phase5_c_smoke(session, info=False)
        print(' stage11 out keys:', sorted(out.keys()))
        print(' artifacts_writable:', out.get('artifacts_writable'))
        print(' order_mapping_accept_ok:', out.get('order_mapping_accept_ok'))
        print(' order_mapping_reject_ok:', out.get('order_mapping_reject_ok'))
        print(' risk_rotation_ok:', out.get('risk_rotation_ok'))
        print(' pending_diag_has_fields:', out.get('pending_diag_has_fields'))
        print(' post_close_checkpoint_called:', out.get('post_close_checkpoint_called'))
        self.assertTrue(out.get('artifacts_writable'))
        self.assertTrue(out.get('order_mapping_accept_ok'))
        self.assertTrue(out.get('order_mapping_reject_ok'))
        self.assertTrue(out.get('risk_rotation_ok'))
        self.assertTrue(out.get('pending_diag_has_fields'))
        self.assertTrue(out.get('post_close_checkpoint_called'))


if __name__ == '__main__':
    unittest.main()
