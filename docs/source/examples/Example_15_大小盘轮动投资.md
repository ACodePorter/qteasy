# 大小盘轮动投资策略（教学等价版）

参考来源：`docs/_joinquant_migration_source/Example_15_大小盘轮动投资策略.ipynb`。  
说明：该 notebook 的首个 Markdown cell 为空，本文按策略名称与后续代码意图给出教学实现。

## 策略思路

- 选取大盘/中小盘代理指数；
- 比较近 N 日相对强弱；
- 将组合权重集中到强势标的，实现大小盘轮动。

## qteasy 实现

- 策略类：`Example15LargeSmallRotation`；
- 信号类型：`PT`；
- 默认指数池：`000300.SH`、`000905.SH`、`000852.SH`。

```python
from examples.strategies.example_strategies import Example15LargeSmallRotation
import qteasy as qt

stg = Example15LargeSmallRotation()
op = qt.Operator(stg, signal_type='PT')
op.op_type = 'stepwise'
op.set_blender('1.0*s0')
res = qt.run(
    op,
    mode=1,
    asset_type='IDX',
    asset_pool=['000300.SH', '000905.SH', '000852.SH'],
    benchmark_asset='000300.SH',
    invest_start='20190101',
    invest_end='20211231',
    invest_cash_amounts=[1000000],
    trade_batch_size=0.01,
    sell_batch_size=0.01,
    trade_log=True,
)
```

## 可执行脚本

- `examples/strategy_example_15.py`

