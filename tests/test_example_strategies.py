# coding=utf-8
# ======================================
# File: test_example_strategies.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-05-10
# Desc:
# Unittest for example strategy implementations.
# ======================================

import unittest
import numpy as np

from examples.strategies.example_strategies import (
    STRATEGY_CLASS_MAP,
    cross_sma_signal,
    grid_like_positions,
    index_enhance_weights,
    zscore_spread_signal,
    donchian_turtle_signal,
)


class TestExampleStrategyHelpers(unittest.TestCase):

    def test_cross_sma_signal(self):
        print('\n[TestExample01] 双均线信号计算')
        close = np.array([1, 1, 1, 2, 3, 4, 5], dtype=float)
        sig = cross_sma_signal(close, fast=2, slow=4)
        print(' close:', close)
        print(' signal:', sig)
        self.assertIn(sig, (-1.0, 0.0, 1.0))

    def test_grid_like_positions(self):
        print('\n[TestExample05] 类网格目标仓位计算')
        close_windows = np.array(
            [
                [10.0, 10.0],
                [10.1, 10.1],
                [10.2, 9.9],
                [10.3, 9.8],
                [10.5, 9.7],
            ],
            dtype=float,
        )
        pos = grid_like_positions(close_windows, 1.0, 2.0, 0.3, 0.5)
        print(' close_windows:\n', close_windows)
        print(' positions:', pos)
        self.assertEqual(pos.shape, (2,))
        self.assertTrue(np.all(np.isfinite(pos)))

    def test_index_enhance_weights(self):
        print('\n[TestExample06] 指数增强权重计算')
        wt = np.array([0.4, 0.2, 0.6], dtype=float)
        close = np.array(
            [
                [10.0, 9.0, 8.0],
                [10.2, 8.9, 8.1],
                [10.4, 8.8, 8.2],
                [10.5, 8.7, 8.3],
            ],
            dtype=float,
        )
        weights = index_enhance_weights(wt, close, 0.3, 0.8, 2)
        print(' index_weight:', wt)
        print(' close:\n', close)
        print(' output weights:', weights)
        self.assertEqual(weights.shape, wt.shape)
        self.assertTrue(np.all(np.isfinite(weights)))

    def test_zscore_spread_signal(self):
        print('\n[TestExample07_08] 价差zscore信号')
        spread = np.array([0, 1, 0, -1, 0, 2, 3], dtype=float)
        sig = zscore_spread_signal(spread, 5, 1.0, 0.2)
        print(' spread:', spread)
        print(' signal:', sig)
        self.assertIn(sig, (-1.0, 0.0, 1.0))

    def test_turtle_signal(self):
        print('\n[TestExample11] 海龟突破信号')
        close = np.array([10, 10.1, 10.2, 10.3, 10.5, 10.8, 11.0], dtype=float)
        sig = donchian_turtle_signal(close, entry_n=3, exit_n=2)
        print(' close:', close)
        print(' signal:', sig)
        self.assertIn(sig, (-1.0, 0.0, 1.0))


class TestExampleStrategyClasses(unittest.TestCase):

    def _assert_strategy_ok(self, example_id: int):
        stg_cls = STRATEGY_CLASS_MAP[example_id]
        stg = stg_cls()
        print(f'\n[TestExample{example_id:02d}] strategy init check')
        print(' class:', stg_cls.__name__)
        print(' data_types:', stg.data_types)
        print(' par_count:', stg.par_count)
        self.assertGreaterEqual(stg.par_count, 1)
        self.assertGreaterEqual(len(stg.data_types), 1)

    def test_example_01(self):
        self._assert_strategy_ok(1)

    def test_example_02(self):
        self._assert_strategy_ok(2)

    def test_example_03(self):
        self._assert_strategy_ok(3)

    def test_example_04(self):
        self._assert_strategy_ok(4)

    def test_example_05(self):
        self._assert_strategy_ok(5)

    def test_example_06(self):
        self._assert_strategy_ok(6)

    def test_example_07(self):
        self._assert_strategy_ok(7)

    def test_example_08(self):
        self._assert_strategy_ok(8)

    def test_example_09(self):
        self._assert_strategy_ok(9)

    def test_example_10(self):
        self._assert_strategy_ok(10)

    def test_example_11(self):
        self._assert_strategy_ok(11)

    def test_example_12(self):
        self._assert_strategy_ok(12)

    def test_example_13(self):
        self._assert_strategy_ok(13)

    def test_example_14(self):
        self._assert_strategy_ok(14)

    def test_example_15(self):
        self._assert_strategy_ok(15)


if __name__ == '__main__':
    unittest.main()

