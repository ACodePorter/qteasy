# coding=utf-8
"""示例策略统一实现库。"""

from __future__ import annotations

import numpy as np
import qteasy as qt
from qteasy import Parameter, StgData


def _safe_tail(arr: np.ndarray, length: int) -> np.ndarray:
    """返回数组尾部窗口，长度不足时返回全部。"""
    if arr.shape[0] <= length:
        return arr
    return arr[-length:]


def cross_sma_signal(close: np.ndarray, fast: int, slow: int) -> float:
    """双均线交叉信号，返回 PS 语义信号。"""
    from qteasy.tafuncs import sma

    s_ma = sma(close, slow)
    f_ma = sma(close, fast)
    s_today, s_last = s_ma[-1], s_ma[-2]
    f_today, f_last = f_ma[-1], f_ma[-2]
    if (f_last <= s_last) and (f_today >= s_today):
        return 1.0
    if (f_last >= s_last) and (f_today <= s_today):
        return -1.0
    return 0.0


def grid_like_positions(
        close_windows: np.ndarray,
        low_threshold: float,
        high_threshold: float,
        low_pos: float,
        hi_pos: float,
) -> np.ndarray:
    """类网格目标仓位（PT）。"""
    close_mean = np.nanmean(close_windows, axis=0)
    close_std = np.nanstd(close_windows, axis=0)
    current_close = close_windows[-1]
    hi_positive = close_mean + high_threshold * close_std
    low_positive = close_mean + low_threshold * close_std
    low_negative = close_mean - low_threshold * close_std
    hi_negative = close_mean - high_threshold * close_std
    pos = np.zeros_like(close_mean, dtype=float)
    pos = np.where(current_close > hi_positive, hi_pos, pos)
    pos = np.where((current_close <= hi_positive) & (current_close > low_positive), low_pos, pos)
    pos = np.where((current_close <= low_positive) & (current_close > low_negative), 0.0, pos)
    pos = np.where((current_close <= low_negative) & (current_close > hi_negative), -low_pos, pos)
    pos = np.where(current_close <= hi_negative, -hi_pos, pos)
    return pos


def index_enhance_weights(
        index_weight: np.ndarray,
        close_windows: np.ndarray,
        weight_threshold: float,
        init_weight: float,
        price_days: int,
) -> np.ndarray:
    """指数增强权重。"""
    wt = index_weight
    pre_close = close_windows[-price_days - 1:-1]
    close = close_windows[-price_days:]
    stock_returns = close - pre_close
    weights = init_weight * np.ones_like(wt, dtype=float)
    weights[wt < weight_threshold] = 0.0
    up_trends = np.all(stock_returns > 0, axis=0)
    down_trends = np.all(stock_returns < 0, axis=0)
    weights[up_trends] = 1.0
    weights[down_trends] = init_weight - (1.0 - init_weight)
    return weights * wt


def zscore_spread_signal(spread: np.ndarray, window: int, z_entry: float, z_exit: float) -> float:
    """基于价差 zscore 的方向信号。"""
    seg = _safe_tail(spread, window)
    mean = np.nanmean(seg)
    std = np.nanstd(seg) + 1e-12
    z = (seg[-1] - mean) / std
    if z > z_entry:
        return -1.0
    if z < -z_entry:
        return 1.0
    if abs(z) <= z_exit:
        return 0.0
    return 0.0


def donchian_turtle_signal(close: np.ndarray, entry_n: int, exit_n: int) -> float:
    """海龟简化版仓位信号。"""
    if close.shape[0] < max(entry_n, exit_n) + 2:
        return 0.0
    last = close[-1]
    entry_high = np.nanmax(close[-entry_n - 1:-1])
    entry_low = np.nanmin(close[-entry_n - 1:-1])
    exit_high = np.nanmax(close[-exit_n - 1:-1])
    exit_low = np.nanmin(close[-exit_n - 1:-1])
    if last >= entry_high:
        return 1.0
    if last <= entry_low:
        return -1.0
    if last <= exit_low:
        return 0.0
    if last >= exit_high:
        return 0.0
    return 0.0


class Example01CrossSMA(qt.RuleIterator):
    """示例01：双均线择时。"""

    def __init__(self, **kwargs):
        super().__init__(
            pars=[
                Parameter((5, 80), name='fast', par_type='int', value=10),
                Parameter((20, 200), name='slow', par_type='int', value=60),
            ],
            name='EX01_CROSS_SMA',
            description='示例01双均线择时策略',
            data_types=StgData('close', freq='d', asset_type='ANY', window_length=220),
            **kwargs,
        )

    def realize(self):
        fast, slow = self.get_pars('fast', 'slow')
        close = self.get_data('close_ANY_d')
        return cross_sma_signal(close, fast=fast, slow=slow)


class Example02AlphaEVEBITDA(qt.GeneralStg):
    """示例02：Alpha 选股（EV/EBITDA）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX02_ALPHA',
            description='示例02 Alpha 选股策略',
            pars=[Parameter((10, 50), name='top_n', par_type='int', value=30)],
            data_types=[
                StgData('total_mv', freq='d', asset_type='E', window_length=2),
                StgData('total_liab', freq='q', asset_type='E', window_length=2),
                StgData('c_cash_equ_end_period', freq='q', asset_type='E', window_length=2),
                StgData('ebitda', freq='q', asset_type='E', window_length=2),
            ],
            **kwargs,
        )

    def realize(self):
        top_n = self.get_pars('top_n')
        total_mv = self.get_data('total_mv_E_d')[-1]
        total_liab = self.get_data('total_liab_E_q')[-1]
        cash_equ = self.get_data('c_cash_equ_end_period_E_q')[-1]
        ebitda = self.get_data('ebitda_E_q')[-1]
        factor = (total_mv + total_liab - cash_equ) / np.where(ebitda == 0, np.nan, ebitda)
        factor = np.where(factor <= 0, np.nan, factor)
        signal = np.zeros_like(factor, dtype=float)
        valid = np.where(~np.isnan(factor))[0]
        if valid.size == 0:
            return signal
        ranked = valid[np.argsort(factor[valid])]
        selected = ranked[:min(top_n, ranked.size)]
        if selected.size > 0:
            signal[selected] = 1.0 / selected.size
        return signal


class Example03AuctionSelection(qt.GeneralStg):
    """示例03：集合竞价选股（日频近似版）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX03_AUCTION',
            description='示例03 集合竞价选股（日频近似）',
            pars=[Parameter((5, 25), name='n_day', par_type='int', value=10)],
            data_types=[
                StgData('open', freq='d', asset_type='E', window_length=40),
                StgData('close', freq='d', asset_type='E', window_length=40),
            ],
            **kwargs,
        )

    def realize(self):
        n_day = self.get_pars('n_day')
        opens = self.get_data('open_E_d')
        closes = self.get_data('close_E_d')
        factors = (opens[-30:] > closes[-30:]).astype(float).sum(axis=0)
        selected = np.where(factors > n_day)[0]
        signal = np.zeros_like(factors, dtype=float)
        if selected.size:
            signal[selected] = 1.0 / selected.size
        return signal


class Example04MultiFactor(qt.FactorSorter):
    """示例04：多因子选股（简化 Fama-French）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX04_MULTI_FACTOR',
            description='示例04 多因子选股',
            pars=[
                Parameter((0.05, 0.95), name='size_gate', par_type='float', value=0.5),
                Parameter((0.05, 0.45), name='pb_s', par_type='float', value=0.3),
                Parameter((0.55, 0.95), name='pb_l', par_type='float', value=0.7),
            ],
            data_types=[
                StgData('pb', freq='d', asset_type='E', window_length=30),
                StgData('total_mv', freq='d', asset_type='E', window_length=5),
                StgData('close', freq='d', asset_type='E', window_length=30),
                StgData('close-000300.SH', freq='d', asset_type='IDX', window_length=30),
            ],
            max_sel_count=10,
            sort_ascending=True,
            condition='less',
            ubound=0.0,
            lbound=-np.inf,
            **kwargs,
        )

    def realize(self):
        pb = self.get_data('pb_E_d')[-1]
        mv = self.get_data('total_mv_E_d')[-1]
        close = self.get_data('close_E_d')
        market = self.get_data('close-000300.SH_IDX_d')
        ret = close[-1] / np.where(close[-2] == 0, np.nan, close[-2]) - 1.0
        mkt_ret = market[-1] / np.where(market[-2] == 0, np.nan, market[-2]) - 1.0
        bp = np.where(pb == 0, np.nan, 1.0 / pb)
        alpha = ret - mkt_ret * np.nan_to_num(bp / np.nanmean(bp)) + np.nan_to_num(np.log1p(mv) * 0.0)
        return alpha


class Example05GridLike(qt.GeneralStg):
    """示例05：类网格交易。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX05_GRID_LIKE',
            description='示例05 类网格交易策略',
            pars=[
                Parameter((0.5, 3.0), name='low_th', par_type='float', value=2.0),
                Parameter((2.0, 8.0), name='high_th', par_type='float', value=3.0),
                Parameter((0.01, 0.6), name='low_pos', par_type='float', value=0.3),
                Parameter((0.1, 1.0), name='high_pos', par_type='float', value=0.5),
                Parameter((60, 500), name='lookback', par_type='int', value=300),
            ],
            data_types=StgData('close', freq='1min', asset_type='ANY', window_length=500),
            use_latest_data_cycle=False,
            **kwargs,
        )

    def realize(self):
        low_th, high_th, low_pos, high_pos, lookback = self.get_pars('low_th', 'high_th', 'low_pos', 'high_pos', 'lookback')
        close = self.get_data('close_ANY_1min')
        return grid_like_positions(_safe_tail(close, lookback), low_th, high_th, low_pos, high_pos)


class Example06IndexEnhancement(qt.GeneralStg):
    """示例06：指数增强选股。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX06_INDEX_ENH',
            description='示例06 指数增强选股',
            pars=[
                Parameter((0.01, 0.99), name='wt_gate', par_type='float', value=0.35),
                Parameter((0.51, 0.99), name='init_w', par_type='float', value=0.8),
                Parameter((2, 20), name='days', par_type='int', value=5),
            ],
            data_types=[
                StgData('wt_idx|000300.SH', freq='m', asset_type='E', window_length=2),
                StgData('close', freq='d', asset_type='E', window_length=40),
            ],
            **kwargs,
        )

    def realize(self):
        wt_gate, init_w, days = self.get_pars('wt_gate', 'init_w', 'days')
        wt = self.get_data('wt_idx|000300.SH_E_m')[-1]
        close = self.get_data('close_E_d')
        return index_enhance_weights(wt, close, wt_gate, init_w, days)


class Example07CrossSymbolSpread(qt.GeneralStg):
    """示例07：跨品种套利（教学等价版）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX07_CROSS_SYMBOL',
            description='示例07 跨品种套利（价差zscore）',
            pars=[
                Parameter((20, 200), name='window', par_type='int', value=60),
                Parameter((0.5, 4.0), name='z_entry', par_type='float', value=2.0),
                Parameter((0.1, 2.0), name='z_exit', par_type='float', value=0.6),
            ],
            data_types=StgData('close', freq='d', asset_type='ANY', window_length=260),
            **kwargs,
        )

    def realize(self):
        window, z_entry, z_exit = self.get_pars('window', 'z_entry', 'z_exit')
        close = self.get_data('close_ANY_d')
        if close.shape[1] < 2:
            return np.zeros(close.shape[1], dtype=float)
        spread = close[:, 0] - close[:, 1]
        s = zscore_spread_signal(spread, window, z_entry, z_exit)
        out = np.zeros(close.shape[1], dtype=float)
        out[0] = s
        out[1] = -s
        return out


class Example08CalendarSpread(qt.GeneralStg):
    """示例08：跨期套利（教学等价版）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX08_CALENDAR',
            description='示例08 跨期套利（协整近似版）',
            pars=[
                Parameter((20, 200), name='window', par_type='int', value=80),
                Parameter((0.5, 4.0), name='z_entry', par_type='float', value=1.8),
                Parameter((0.1, 2.0), name='z_exit', par_type='float', value=0.5),
            ],
            data_types=StgData('close', freq='d', asset_type='ANY', window_length=300),
            **kwargs,
        )

    def realize(self):
        window, z_entry, z_exit = self.get_pars('window', 'z_entry', 'z_exit')
        close = self.get_data('close_ANY_d')
        if close.shape[1] < 2:
            return np.zeros(close.shape[1], dtype=float)
        y = close[:, 0]
        x = close[:, 1]
        beta = np.nanmean(y / np.where(x == 0, np.nan, x))
        spread = y - beta * x
        s = zscore_spread_signal(spread, window, z_entry, z_exit)
        out = np.zeros(close.shape[1], dtype=float)
        out[0] = s
        out[1] = -s
        return out


class Example09IntradayRotation(qt.RuleIterator):
    """示例09：日内回转（教学等价版）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX09_INTRADAY',
            description='示例09 日内回转（MACD近似）',
            pars=[
                Parameter((6, 20), name='fast', par_type='int', value=12),
                Parameter((15, 40), name='slow', par_type='int', value=26),
            ],
            data_types=StgData('close', freq='5min', asset_type='ANY', window_length=200),
            use_latest_data_cycle=False,
            **kwargs,
        )

    def realize(self):
        from qteasy.tafuncs import ema

        fast, slow = self.get_pars('fast', 'slow')
        close = self.get_data('close_ANY_5min')
        ef = ema(close, fast)
        es = ema(close, slow)
        macd = ef[-1] - es[-1]
        if macd > 0:
            return 0.1
        if macd < 0:
            return -0.1
        return 0.0


class Example10MarketMakingApprox(qt.RuleIterator):
    """示例10：做市商交易（Bar级近似）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX10_MM_APPROX',
            description='示例10 做市商（均值回归近似）',
            pars=[
                Parameter((10, 120), name='window', par_type='int', value=30),
                Parameter((0.1, 3.0), name='band', par_type='float', value=1.0),
            ],
            data_types=StgData('close', freq='1min', asset_type='ANY', window_length=200),
            use_latest_data_cycle=False,
            **kwargs,
        )

    def realize(self):
        window, band = self.get_pars('window', 'band')
        close = self.get_data('close_ANY_1min')
        seg = _safe_tail(close, window)
        mean = np.nanmean(seg)
        std = np.nanstd(seg) + 1e-12
        z = (seg[-1] - mean) / std
        if z > band:
            return -0.2
        if z < -band:
            return 0.2
        return 0.0


class Example11Turtle(qt.RuleIterator):
    """示例11：海龟交易法（简化版）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX11_TURTLE',
            description='示例11 海龟交易法（简化）',
            pars=[
                Parameter((10, 80), name='entry_n', par_type='int', value=20),
                Parameter((5, 40), name='exit_n', par_type='int', value=10),
            ],
            data_types=StgData('close', freq='d', asset_type='ANY', window_length=260),
            **kwargs,
        )

    def realize(self):
        entry_n, exit_n = self.get_pars('entry_n', 'exit_n')
        close = self.get_data('close_ANY_d')
        return donchian_turtle_signal(close, entry_n=entry_n, exit_n=exit_n)


class Example12IndustryRotation(qt.GeneralStg):
    """示例12：行业轮动（指数代理版）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX12_INDUSTRY_ROT',
            description='示例12 行业轮动（行业指数代理）',
            pars=[Parameter((5, 60), name='lookback', par_type='int', value=20)],
            data_types=StgData('close', freq='d', asset_type='ANY', window_length=120),
            **kwargs,
        )

    def realize(self):
        lookback = self.get_pars('lookback')
        close = self.get_data('close_ANY_d')
        seg = _safe_tail(close, lookback + 1)
        ret = seg[-1] / np.where(seg[0] == 0, np.nan, seg[0]) - 1.0
        signal = np.zeros_like(ret, dtype=float)
        best = int(np.nanargmax(ret))
        signal[best] = 1.0
        return signal


class Example13ClassicGrid(qt.RuleIterator):
    """示例13：经典网格交易。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX13_CLASSIC_GRID',
            description='示例13 经典网格交易',
            pars=[
                Parameter((0.2, 2.0), name='grid_size', par_type='float', value=0.5),
                Parameter((100, 1000), name='batch', par_type='int', value=200),
                Parameter((0.0, 10000.0), name='base_grid', par_type='float', value=0.0),
            ],
            data_types=StgData('close', freq='5min', asset_type='ANY', window_length=60),
            use_latest_data_cycle=False,
            **kwargs,
        )

    def realize(self):
        grid_size, batch, base_grid = self.get_pars('grid_size', 'batch', 'base_grid')
        price = self.get_data('close_ANY_5min')[-1]
        if base_grid <= 0.01:
            result = float(batch * 5)
            base_grid = np.round(price / 0.1) * 0.1
        elif price - base_grid > grid_size:
            result = -float(batch)
            base_grid = base_grid + grid_size
        elif base_grid - price > grid_size:
            result = float(batch)
            base_grid = base_grid - grid_size
        else:
            result = 0.0
        self.par_values = (grid_size, batch, base_grid)
        return result


class Example14MLSkeleton(qt.RuleIterator):
    """示例14：机器学习选股（教学骨架）。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX14_ML_SKELETON',
            description='示例14 机器学习选股（轻量骨架）',
            pars=[
                Parameter((5, 60), name='lookback', par_type='int', value=15),
                Parameter((0.0, 0.2), name='up_gate', par_type='float', value=0.02),
            ],
            data_types=StgData('close', freq='d', asset_type='ANY', window_length=80),
            **kwargs,
        )

    def realize(self):
        lookback, up_gate = self.get_pars('lookback', 'up_gate')
        close = self.get_data('close_ANY_d')
        seg = _safe_tail(close, lookback + 1)
        pred = seg[-1] / np.where(seg[0] == 0, np.nan, seg[0]) - 1.0
        if pred > up_gate:
            return 1.0
        if pred < -up_gate:
            return -1.0
        return 0.0


class Example15LargeSmallRotation(qt.GeneralStg):
    """示例15：大小盘轮动。"""

    def __init__(self, **kwargs):
        super().__init__(
            name='EX15_LS_ROTATION',
            description='示例15 大小盘轮动投资策略',
            pars=[Parameter((5, 60), name='lookback', par_type='int', value=20)],
            data_types=StgData('close', freq='d', asset_type='ANY', window_length=100),
            **kwargs,
        )

    def realize(self):
        lookback = self.get_pars('lookback')
        close = self.get_data('close_ANY_d')
        seg = _safe_tail(close, lookback + 1)
        ret = seg[-1] / np.where(seg[0] == 0, np.nan, seg[0]) - 1.0
        signal = np.zeros_like(ret, dtype=float)
        best = int(np.nanargmax(ret))
        signal[best] = 1.0
        return signal


STRATEGY_CLASS_MAP = {
    1: Example01CrossSMA,
    2: Example02AlphaEVEBITDA,
    3: Example03AuctionSelection,
    4: Example04MultiFactor,
    5: Example05GridLike,
    6: Example06IndexEnhancement,
    7: Example07CrossSymbolSpread,
    8: Example08CalendarSpread,
    9: Example09IntradayRotation,
    10: Example10MarketMakingApprox,
    11: Example11Turtle,
    12: Example12IndustryRotation,
    13: Example13ClassicGrid,
    14: Example14MLSkeleton,
    15: Example15LargeSmallRotation,
}

