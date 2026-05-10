# 海龟交易法策略（教学简化版）

参考来源：`docs/_joinquant_migration_source/Example_11_海龟交易法.ipynb` 第一个 Markdown cell。

## 策略思路

- 使用唐奇安通道的突破信号作为开仓依据；
- 价格突破上轨做多，跌破下轨做空；
- 结合较短周期通道控制退出（简化版海龟规则）。

## qteasy 实现

- 策略类：`Example11Turtle`；
- 信号类型：`PT`；
- 默认脚本使用单标的教学版，便于验证链路和参数优化流程。

```python
from examples.strategies.example_strategies import Example11Turtle
import qteasy as qt

stg = Example11Turtle()
op = qt.Operator(stg, signal_type='PT')
op.op_type = 'stepwise'
op.set_blender('1.0*s0')
res = qt.run(
    op,
    mode=1,
    asset_type='E',
    asset_pool=['000001.SZ'],
    benchmark_asset='000001.SZ',
    invest_start='20190101',
    invest_end='20211231',
    invest_cash_amounts=[1000000],
    trade_batch_size=100,
    sell_batch_size=1,
    allow_sell_short=True,
    trade_log=True,
)
```

## 可执行脚本

- `examples/strategy_example_11.py`

