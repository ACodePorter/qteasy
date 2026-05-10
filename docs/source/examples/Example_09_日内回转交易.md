# 日内回转交易策略（教学等价版）

参考来源：`docs/_joinquant_migration_source/Example_09_日内回转交易.ipynb` 第一个 Markdown cell。

## 策略思路

- 使用分钟级价格计算 MACD；
- MACD 为正时加仓、为负时减仓；
- 通过 `VS` 信号输出固定交易数量，形成日内回转风格。

## 诚实说明

- 原始策略强调 A 股日内回转，但真实 A 股存在 T+1 约束；
- 本示例仅演示 qteasy 的日内信号处理链路，不等同于真实可执行的 A 股 T+0 回转；
- 若需要贴近实盘，请改用 ETF 或期货标的，并校准交易制度参数。

```python
from examples.strategies.example_strategies import Example09IntradayRotation
import qteasy as qt

stg = Example09IntradayRotation()
op = qt.Operator(stg, signal_type='VS')
op.op_type = 'stepwise'
op.set_blender('1.0*s0')
res = qt.run(
    op,
    mode=1,
    asset_type='E',
    asset_pool=['600000.SH'],
    benchmark_asset='600000.SH',
    invest_start='20230101',
    invest_end='20231231',
    invest_cash_amounts=[1000000],
    trade_batch_size=100,
    sell_batch_size=1,
    trade_log=True,
)
```

## 可执行脚本

- `examples/strategy_example_09.py`

