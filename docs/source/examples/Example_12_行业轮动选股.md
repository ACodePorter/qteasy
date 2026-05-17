# 行业轮动选股策略（教学等价版）

参考来源：`docs/_joinquant_migration_source/Example_12_行业轮动选股.ipynb` 第一个 Markdown cell。

## 策略思路

- 每月比较行业代理指数近 N 日收益；
- 选择收益最强的行业代理标的；
- 将仓位集中在最强行业上（教学版）。

## qteasy 实现说明

- 策略类：`Example12IndustryRotation`；
- 默认采用指数代理池（`000300.SH`、`000905.SH`、`000852.SH`）演示轮动逻辑；
- 若切换到“行业成分股 + 市值筛选”版本，可在此基础上扩展二阶段选股。

```python
from examples.strategies.example_strategies import Example12IndustryRotation
import qteasy as qt

stg = Example12IndustryRotation()
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

- `examples/strategy_example_12.py`

