# coding=utf-8
"""运行 qteasy 示例策略。"""

from __future__ import annotations

import os
import shutil
from typing import Any

import qteasy as qt

from examples.strategies.example_strategies import STRATEGY_CLASS_MAP


def _example_config(example_id: int) -> dict[str, Any]:
    """返回示例策略运行参数。"""
    if example_id == 1:
        return dict(
            signal_type='PS',
            op_type='batch',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='IDX',
                asset_pool=['000300.SH'],
                benchmark_asset='000300.SH',
                invest_start='20190101',
                invest_end='20211231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=0.01,
                sell_batch_size=0.01,
                trade_log=True,
            ),
        )
    if example_id in (2, 3, 4):
        shares = qt.filter_stock_codes(index='000300.SH', date='20220101')
        return dict(
            signal_type='PT',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='E',
                asset_pool=shares,
                benchmark_asset='000300.SH',
                invest_start='20190101',
                invest_end='20211231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=100,
                sell_batch_size=1,
                trade_log=True,
            ),
        )
    if example_id == 6:
        shares = qt.filter_stock_codes(index='000300.SH', date='20220101')
        return dict(
            signal_type='PT',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='E',
                asset_pool=shares,
                benchmark_asset='000300.SH',
                invest_start='20200401',
                invest_end='20221231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=100,
                sell_batch_size=1,
                trade_log=True,
            ),
        )
    if example_id == 5:
        return dict(
            signal_type='PT',
            op_type='batch',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='IDX',
                asset_pool=['000300.SH'],
                benchmark_asset='000300.SH',
                invest_start='20220325',
                invest_end='20221231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=0.01,
                sell_batch_size=0.01,
                allow_sell_short=True,
                trade_log=True,
            ),
        )
    if example_id in (7, 8):
        return dict(
            signal_type='PT',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='IDX',
                asset_pool=['000300.SH', '000905.SH'],
                benchmark_asset='000300.SH',
                invest_start='20190101',
                invest_end='20211231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=0.01,
                sell_batch_size=0.01,
                allow_sell_short=True,
                trade_log=True,
            ),
        )
    if example_id == 9:
        return dict(
            signal_type='VS',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='E',
                asset_pool=['600000.SH'],
                benchmark_asset='600000.SH',
                invest_start='20230101',
                invest_end='20231231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=100,
                sell_batch_size=1,
                trade_log=True,
            ),
        )
    if example_id == 10:
        return dict(
            signal_type='VS',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='E',
                asset_pool=['000651.SZ'],
                benchmark_asset='000651.SZ',
                invest_start='20230101',
                invest_end='20231231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=100,
                sell_batch_size=1,
                trade_log=True,
            ),
        )
    if example_id == 11:
        return dict(
            signal_type='PT',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='E',
                asset_pool=['000001.SZ'],
                benchmark_asset='000001.SZ',
                invest_start='20190101',
                invest_end='20211231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=100,
                sell_batch_size=1,
                allow_sell_short=True,
                trade_log=True,
            ),
        )
    if example_id in (12, 15):
        return dict(
            signal_type='PT',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='IDX',
                asset_pool=['000300.SH', '000905.SH', '000852.SH'],
                benchmark_asset='000300.SH',
                invest_start='20190101',
                invest_end='20211231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=0.01,
                sell_batch_size=0.01,
                trade_log=True,
            ),
        )
    if example_id == 13:
        return dict(
            signal_type='VS',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='E',
                asset_pool=['000651.SZ'],
                benchmark_asset='000651.SZ',
                invest_start='20230101',
                invest_end='20231231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=100,
                sell_batch_size=1,
                backtest_price_adj='none',
                trade_log=True,
            ),
        )
    if example_id == 14:
        return dict(
            signal_type='PS',
            op_type='stepwise',
            set_blender='1.0*s0',
            run_kwargs=dict(
                mode=1,
                asset_type='E',
                asset_pool=['600000.SH'],
                benchmark_asset='600000.SH',
                invest_start='20190101',
                invest_end='20211231',
                invest_cash_amounts=[1_000_000],
                trade_batch_size=100,
                sell_batch_size=1,
                trade_log=True,
            ),
        )
    raise ValueError(f'Unsupported example id: {example_id}')


def run_example_strategy(example_id: int):
    """运行指定示例策略并返回结果。"""
    strategy_class = STRATEGY_CLASS_MAP[example_id]
    cfg = _example_config(example_id)
    log_dir_rel = os.path.join('examples', 'tradelogs', f'example_{example_id:02d}')
    log_dir_abs = os.path.join(os.path.dirname(__file__), '..', 'tradelogs', f'example_{example_id:02d}')
    os.makedirs(log_dir_abs, exist_ok=True)
    qt.configure(sys_log_file_path=log_dir_rel, trade_log_file_path=log_dir_rel)
    strategy = strategy_class()
    op = qt.Operator(strategy, signal_type=cfg['signal_type'])
    op.op_type = cfg['op_type']
    op.set_blender(cfg['set_blender'])
    run_kwargs = dict(cfg['run_kwargs'])
    run_kwargs['sys_log_file_path'] = log_dir_rel
    run_kwargs['trade_log_file_path'] = log_dir_rel
    print(f'\\n[Example{example_id:02d}] start backtest in {log_dir_abs}')
    result = qt.run(op, **run_kwargs)
    if isinstance(result, dict):
        for key in ('trade_log', 'trade_summary', 'complete_values_file'):
            src = result.get(key)
            if isinstance(src, str) and os.path.isfile(src):
                dst = os.path.join(log_dir_abs, os.path.basename(src))
                if os.path.abspath(src) != os.path.abspath(dst):
                    shutil.copy2(src, dst)
    print(f'[Example{example_id:02d}] done')
    return result

