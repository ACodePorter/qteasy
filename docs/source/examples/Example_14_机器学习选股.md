# 机器学习选股策略（教学骨架版）

参考来源：`docs/_joinquant_migration_source/Example_14_机器学习选股.ipynb` 第一个 Markdown cell。

## 策略思路

- 原始思路为“滑窗特征 + SVM 二分类”；
- 教学骨架版强调 qteasy 的链路：`特征/预测` -> `信号` -> `回测`；
- 默认实现不在回测循环中重复重训练，而是用轻量规则近似模型输出，避免性能和可复现问题。

## 诚实说明

- 若要使用真实机器学习模型，建议在策略外离线训练并固化预测结果，再在策略中读取；
- 这样更容易避免前视偏差，并控制优化模式的运行成本。

```python
from examples.strategies.example_strategies import Example14MLSkeleton
import qteasy as qt

stg = Example14MLSkeleton()
op = qt.Operator(stg, signal_type='PS')
op.op_type = 'stepwise'
op.set_blender('1.0*s0')
res = qt.run(
    op,
    mode=1,
    asset_type='E',
    asset_pool=['600000.SH'],
    benchmark_asset='600000.SH',
    invest_start='20190101',
    invest_end='20211231',
    invest_cash_amounts=[1000000],
    trade_batch_size=100,
    sell_batch_size=1,
    trade_log=True,
)
```

## 可执行脚本

- `examples/strategy_example_14.py`

