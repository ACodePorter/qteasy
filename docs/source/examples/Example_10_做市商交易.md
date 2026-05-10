# 做市商交易策略（教学近似版）

参考来源：`docs/_joinquant_migration_source/Example_10_做市商交易.ipynb` 第一个 Markdown cell。

## 策略思路

- 真实做市策略依赖逐笔盘口、挂撤单队列和成交优先级；
- qteasy 回测层是 Bar 级撮合抽象，本示例以“均值回归双边挂单”近似做市行为；
- 当价格偏离均值上轨时卖出，偏离下轨时买入，中间区域观望。

## 诚实说明

- 本示例不是交易所级别的真实做市仿真；
- 仅用于讲解 qteasy 在高频风格场景下的 `VS` 信号和 stepwise 回测流程。

```python
from examples.strategies.example_strategies import Example10MarketMakingApprox
import qteasy as qt

stg = Example10MarketMakingApprox()
op = qt.Operator(stg, signal_type='VS')
op.op_type = 'stepwise'
op.set_blender('1.0*s0')
res = qt.run(
    op,
    mode=1,
    asset_type='E',
    asset_pool=['000651.SZ'],
    benchmark_asset='000651.SZ',
    invest_start='20230101',
    invest_end='20231231',
    invest_cash_amounts=[1000000],
    trade_batch_size=100,
    sell_batch_size=1,
    trade_log=True,
)
```

## 可执行脚本

- `examples/strategy_example_10.py`

