# 跨品种套利交易策略（教学等价版）

参考来源：`docs/_joinquant_migration_source/Example_07_跨品种套利.ipynb` 第一个 Markdown cell。  
说明：原 notebook 已标注“信息有问题需要更正”，本示例以 qteasy 可稳定复现的教学实现为准。

## 策略思路

- 选取两个高相关交易标的，构造价差 `spread = p1 - p2`；
- 在滚动窗口内计算价差均值与标准差，得到 zscore；
- 当 zscore 高于上阈值时做空价差（卖出第一个、买入第二个），低于下阈值时做多价差；
- 回归到退出阈值附近时平仓。

## qteasy 实现说明

- 本文使用 `PT` 信号，策略类为 `Example07CrossSymbolSpread`；
- 为降低数据依赖，示例脚本默认使用日频指数对（教学近似），不是原始分钟期货合约对；
- 若你本地具备期货分钟数据，可将脚本中的 `asset_type/asset_pool/freq` 替换为期货版本。

```python
from examples.strategies.example_strategies import Example07CrossSymbolSpread
import qteasy as qt

stg = Example07CrossSymbolSpread()
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

- `examples/strategy_example_07.py`

