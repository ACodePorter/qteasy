# coding=utf-8
# ======================================
# File:     live_grid_multi.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2021-08-29
# Desc:
#   Create a grid trading strategy for
# multiple stocks with different trade
# parameters
# ======================================

import numpy as np

import os
import sys

sys.path.insert(0, os.path.abspath('../'))

if __name__ == '__main__':
    from qteasy.utilfuncs import get_qt_argparser

    import qteasy as qt
    from qteasy import Operator, Parameter


    class MultiGridTrade(qt.RuleIterator):
        """网格交易策略, 同时监控多只股票并进行网格交易"""

        def realize(self):
            # RuleIterator.generate() 按标的循环：每次 realize 仅处理当前标的；par_values 为该股元组，
            # 数据已由框架切片为当前列（一维窗口）。多参数写回用 self._generate_share_index + multi_pars。
            pars = self.par_values
            if not isinstance(pars, (tuple, list)) or len(pars) != 3:
                raise TypeError(
                        f'expected par_values tuple (grid_size, trade_batch, base_grid), got {type(pars)}: {pars}')
            grid_size, trade_batch, base_grid = float(pars[0]), int(pars[1]), float(pars[2])

            h = self.get_data(self.data_type_ids[0])
            ha = np.asarray(h, dtype=float).ravel()
            if ha.size == 0 or np.all(np.isnan(ha)):
                return 0.0
            price = float(ha[-1])

            if base_grid <= 0.01:
                trade_signal = float(np.round(200000 / price, -2))
                base_grid = float(np.round(price, 1))
            elif price - base_grid > grid_size:
                trade_signal = float(-trade_batch)
                base_grid += grid_size
            elif base_grid - price > grid_size:
                trade_signal = float(trade_batch)
                base_grid -= grid_size
            else:
                trade_signal = 0.0

            if not np.isnan(base_grid):
                base_grid = float(np.round(base_grid, 2))

            if self.allow_multi_par and self.multi_pars is not None:
                idx = getattr(self, '_generate_share_index', None)
                if idx is not None:
                    mp = list(self.multi_pars)
                    mp[idx] = (grid_size, trade_batch, base_grid)
                    self.multi_pars = tuple(mp)

            return trade_signal


    parser = get_qt_argparser()
    args = parser.parse_args()
    alpha = MultiGridTrade(
            name='MultiGridTrade',
            description='多重网格交易策略，同时监控多只股票，使用不同的策略参数（网格大小和交易批量）执行网格交易',
            pars=[Parameter((0.1, 2), par_type='float', name='grid_size'),
                  Parameter((100, 3000), par_type='int', name='trade_batch'),
                  Parameter((0, 400), par_type='float', name='base_grid')],
            data_types=[qt.StgData('close', freq='5min', asset_type='E', window_length=10)],
    )
    asset_pool = ['000651.SZ', '600036.SH', '601398.SH']
    par_values = {'000651.SZ': (0.3, 500, 0),
                  '600036.SH': (0.3, 600, 0),
                  '601398.SH': (0.1, 1000, 0)}  # 当基准网格为0时，代表首次运行，此时买入20000股，并设置当前价为基准网格

    alpha.allow_multi_par = True  # 允许多参数输入
    op = Operator(alpha, signal_type='VS', op_type='step', run_timing='close', run_freq='5min')
    op.set_shares(asset_pool)
    alpha.update_par_values(par_values)
    datasource = qt.QT_DATA_SOURCE

    if args.restart:
        # clean up all trade data in current account
        from qteasy.trade_recording import delete_account

        delete_account(account_id=args.account, data_source=datasource, keep_account_id=True)

    print('in live_grid_multi:', "config['live_trade_daily_refill_tables'] = 'stock_1min...fund_hourly'")
    qt.configure(
            mode=0,
            time_zone='Asia/Shanghai',
            asset_type='E',
            asset_pool=asset_pool,
            benchmark_asset='000651.SZ',
            trade_batch_size=100,
            sell_batch_size=1,
            live_trade_account_id=args.account,
            live_trade_account_name=args.new_account,
            live_trade_debug_mode=args.debug,
            live_trade_broker_type='simulator',
            live_trade_ui_type=args.ui,
            hist_dnld_parallel=2,
            watched_price_refresh_interval=5,
            # live_trade_daily_refill_tables='stock_1min, stock_5min, stock_15min, stock_30min, stock_hourly, '
            #                                'index_1min, index_5min, index_15min, index_30min, index_hourly, '
            #                                'fund_1min, fund_5min, fund_15min, fund_30min, fund_hourly',
            # live_trade_weekly_refill_tables='stock_daily, index_daily, fund_daily',
            live_trade_data_refill_batch_size=20,
            live_trade_data_refill_batch_interval=3,
    )

    qt.run(op)