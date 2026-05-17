# 跨期套利交易策略（教学等价版）

参考来源：`docs/_joinquant_migration_source/Example_08_跨期套利.ipynb` 第一个 Markdown cell。

## 策略思路

- 使用同品种不同到期合约构造价差；
- 用滚动窗口估计价差偏离程度（zscore）；
- 价差上穿上轨做空价差，下穿下轨做多价差；
- 回归到中性区间时平仓。

## qteasy 实现说明

- 本示例策略类为 `Example08CalendarSpread`；
- 为了教学稳定性，默认脚本使用指数日频做跨期逻辑近似；
- 若切换到真实期货合约，请同时处理换月逻辑，并在文档中记录换月规则。

```python
from examples.strategies.example_strategies import Example08CalendarSpread
import qteasy as qt

stg = Example08CalendarSpread()
op = qt.Operator(stg, signal_type='PT')
op.op_type = 'stepwise'
op.set_blender('1.0*s0')
res = qt.run(
    op,
    mode=1,
    asset_type='IDX',
    asset_pool=['000300.SH', '000905.SH'],
    benchmark_asset='000300.SH',
    invest_start='20190101',
    invest_end='20211231',
    invest_cash_amounts=[1000000],
    trade_batch_size=0.01,
    sell_batch_size=0.01,
    allow_sell_short=True,
    trade_log=True,
)
```

## 可执行脚本

- `examples/strategy_example_08.py`

