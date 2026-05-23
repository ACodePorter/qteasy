# coding=utf-8
"""Phase 1 收尾：应用剩余 en 译文并清除文件头 fuzzy。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import polib

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from fill_en_po import apply_po

ROOT = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'en' / 'LC_MESSAGES'

TAIL: dict[str, dict[str, str]] = {
    'CODE_OF_CONDUCT.po': {
        'CODE OF CONDUCT': 'CODE OF CONDUCT',
        'All typical collaboration codes of conduct apply:': (
            'All typical collaboration codes of conduct apply:'
        ),
        'Treat people fairly, with respect, and overall [be a mensch](https://www.google.com/search?q=mensch).': (
            'Treat people fairly, with respect, and overall [be a mensch](https://www.google.com/search?q=mensch).'
        ),
    },
    'LICENSE.po': {
        'License': 'License',
        'Copyright <2019> <JACKIE PENG>': 'Copyright <2019> <JACKIE PENG>',
        'Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:': (
            'Redistribution and use in source and binary forms, with or without modification, are '
            'permitted provided that the following conditions are met:'
        ),
        'Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.': (
            'Redistributions of source code must retain the above copyright notice, this list of '
            'conditions and the following disclaimer.'
        ),
        'Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.': (
            'Redistributions in binary form must reproduce the above copyright notice, this list of '
            'conditions and the following disclaimer in the documentation and/or other materials '
            'provided with the distribution.'
        ),
        'Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.': (
            'Neither the name of the copyright holder nor the names of its contributors may be used '
            'to endorse or promote products derived from this software without specific prior written permission.'
        ),
        'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.': (
            'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY '
            'EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF '
            'MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE '
            'COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, '
            'EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE '
            'GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED '
            'AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING '
            'NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED '
            'OF THE POSSIBILITY OF SUCH DAMAGE.'
        ),
    },
    'back_testing/1. overview.po': {
        '回测在 qteasy 中通过 **qt.run(op, mode=1, ...)** 触发，用于在历史数据上模拟策略运行，得到资金曲线、交易记录与绩效指标，为评价与优化策略提供依据。': (
            'In qteasy, backtests are triggered via **``qt.run(op, mode=1, ...)``**, simulating strategy '
            'runs on historical data to produce equity curves, trade logs, and performance metrics for '
            'evaluation and optimization.'
        ),
        '总体介绍': 'Overview',
        '**入口**：`qt.run(operator, mode=1, ...)`，其中 `mode=1` 表示回测模式。': (
            '**Entry point**: ``qt.run(operator, mode=1, ...)`` where ``mode=1`` selects backtest mode.'
        ),
        '**回测能提供**：资金曲线（净值、累计收益）、逐笔交易记录、绩效指标（如夏普、回撤、胜率等）。': (
            '**Backtest outputs**: equity curve (NAV, cumulative return), per-trade log, performance metrics '
            '(Sharpe, drawdown, win rate, etc.).'
        ),
        '回测流程概览': 'Backtest workflow overview',
        '**配置**：资产池（asset_pool）、回测区间（invest_start、invest_end）、初始/分批资金（invest_cash_amounts 等）。': (
            '**Configure**: asset pool (``asset_pool``), date range (``invest_start``, ``invest_end``), '
            'initial/staged cash (``invest_cash_amounts``, etc.).'
        ),
        '**准备数据**：确保 DataSource 中有所需历史数据。': (
            '**Prepare data**: ensure required history is available in ``DataSource``.'
        ),
        '**按时间步运行 Operator**：在每个 run_timing 时刻调用策略生成信号。': (
            '**Run Operator step by step**: call strategies at each ``run_timing`` to generate signals.'
        ),
        '**模拟成交**：按信号与成本、交易单位等规则生成买卖与持仓。': (
            '**Simulate fills**: apply signals with costs, lot sizes, and related rules to update positions.'
        ),
        '**输出结果与可选报告**：返回结果对象（如 Backtester）、可选 trade_log、visual 图表等。': (
            '**Output**: result object (e.g. ``Backtester``), optional ``trade_log``, visual charts, etc.'
        ),
        '本目录各章导航': 'Chapters in this section',
        '**2. 如何运行回测** — 入口、配置方式、回测运行参数完整列表、最小示例。': (
            '**2. How to run a backtest** — entry point, configuration, full parameter list, minimal example.'
        ),
        '**3. 回测结果的结构** — 返回值、结果字段完整列表、资金曲线与绩效指标。': (
            '**3. Backtest result structure** — return value, field reference, equity curve and metrics.'
        ),
        '**4. 交易过程记录** — 开启 trade_log、日志内容、查看与保存。': (
            '**4. Trade process log** — enabling ``trade_log``, contents, viewing and saving.'
        ),
        '**5. 回测结果评价与分析** — 绩效指标列表、可视化、结果导出与分析思路。': (
            '**5. Evaluating backtest results** — metric list, visualization, export and analysis.'
        ),
        '更多策略与混合器用法见《回测并评价交易策略》references（如 references/3-back-test-strategy.md、4-build-in-strategy-blender.md）。': (
            'For more on strategies and blenders, see references (e.g. '
            '``references/3-back-test-strategy.md``, ``4-build-in-strategy-blender.md``).'
        ),
    },
    'qteasy_2_migration_guide.po': {
        'QTEASY 2.0 版本迁移指引': 'QTEASY 2.0 Migration Guide',
        '本指引提供了 QTEASY 2.0 中的更改和改进的概述，以及如何将现有代码库迁移到新版本的说明。': (
            'This guide summarizes changes and improvements in QTEASY 2.0 and how to migrate existing code.'
        ),
        'QTEASY 2.0 中的主要改进': 'Major improvements in QTEASY 2.0',
        '引入了新的 `Parameter` 类来表示策略参数，`Operator` 现在可以使用 `Parameter` 实例来指定它需要的参数，并且用户可以以更灵活的方式设置参数，包括为不同的符号设置不同的参数值。': (
            'New ``Parameter`` class for strategy parameters; ``Operator`` accepts ``Parameter`` instances '
            'and supports flexible per-symbol parameter values.'
        ),
        '引入了新的 `Group` 类来表示策略组，`Operator` 现在将策略分成不同的组，每个组可以有自己的运行频率、运行时间和混合器，因此策略可以以更灵活和强大的方式运行。': (
            'New ``Group`` class for strategy groups; each group can have its own run frequency, timing, '
            'and blender for more flexible execution.'
        ),
        '改进了操作员Operator类的运行时间表 running schedule，现在所有策略都以更细粒度的级别运行，允许更灵活的运行时间和更准确的回测结果，并且运行计划是每个策略组确定的，允许不同组的策略以不同的频率和时间运行。': (
            'Improved ``Operator`` running schedule: finer-grained timing per group for more accurate '
            'backtests; groups can run at different frequencies and times.'
        ),
        '改进了策略利用历史数据的方式，现在策略能够在同一运行中利用不同频率和窗口长度的数据，并且数据以更高效的方式提取和分配给策略。': (
            'Strategies can use multiple frequencies and window lengths in one run; data is fetched and '
            'assigned more efficiently.'
        ),
        '改进了策略回测和优化的效率，现在回测和优化过程更高效，更好地利用系统资源，尤其是在使用多处理时性能显著提高。': (
            'Backtest and optimization are faster and use system resources better, especially with multiprocessing.'
        ),
        '引入了 `Operator` 中的跟踪模式（Tracing mode），允许用户通过在策略实现中定义跟踪点来更详细地跟踪每个策略组的回测结果，跟踪结果将保存在交易日志中。': (
            '``Operator`` tracing mode: define trace points in strategies; trace output is saved in trade logs.'
        ),
        '简化了交易策略实现方法realization的定义，现在用户可以通过更简单的API以更直观的方式获取历史数据和参数，并且可以使用用户定义的名称。': (
            'Simpler ``realize()`` API for history data and parameters with user-defined names.'
        ),
        '引入了更多的交易策略优化算法，使得用户可以针对不同的交易策略参数空间选择更适合的优化算法，同时提高了策略优化对系统资源的利用率，提高了优化速度。': (
            'More optimization algorithms for different parameter spaces and faster optimization.'
        ),
        '改进了交易策略回测 / 优化结果的评价分析流程，引入了更多的评价指标，提高了评价结果的直观性。': (
            'Richer evaluation metrics and clearer analysis for backtest/optimization results.'
        ),
        '已移除或变更的配置参数 / Removed or changed configuration parameters': (
            'Removed or changed configuration parameters'
        ),
        '以下配置键在 2.0 中已从内置配置中移除。若在 2.0 中仍通过 `qt.configure(..., only_built_in_keys=True)` 传入下列任一键，将触发 `KeyError`。': (
            'The following keys were removed from built-in config in 2.0. Passing any of them with '
            '``qt.configure(..., only_built_in_keys=True)`` raises ``KeyError``.'
        ),
        '删除的配置键': 'Removed configuration keys',
        '配置键': 'Config key',
        '说明与替代方式': 'Notes and alternatives',
        '**maximize_cash_usage**': '**maximize_cash_usage**',
        '已移除。回测时是否最大化利用同一批次交易获得的现金，已内聚到交易执行流程，不再通过配置暴露。无替代键，删除该键即可。': (
            'Removed. Maximizing reuse of cash from the same batch is handled inside trade execution; '
            'no replacement key—remove it.'
        ),
        '**benchmark_asset_type**': '**benchmark_asset_type**',
        '已移除。基准资产类型现由 `benchmark_asset` 的代码与数据源自动推断。仅需设置 `benchmark_asset`。': (
            'Removed. Benchmark asset type is inferred from ``benchmark_asset`` and the data source; '
            'set ``benchmark_asset`` only.'
        ),
        '**benchmark_dtype**': '**benchmark_dtype**',
        '已移除。基准价格类型由运行时间表与数据源自动推断。仅需设置 `benchmark_asset`。': (
            'Removed. Benchmark price type is inferred from the schedule and data source; '
            'set ``benchmark_asset`` only.'
        ),
        '变更的配置键': 'Changed configuration keys',
        '本次仅做删除，无重命名或合并类变更。': 'This release only removes keys; no renames or merges.',
        '升级操作建议': 'Upgrade checklist',
        '在 `qteasy.cfg` 或自有配置中搜索并删除上述三个键。': (
            'Search ``qteasy.cfg`` or your config and remove the three keys above.'
        ),
        '在代码中删除对 `qt.configure(..., maximize_cash_usage=...)`、`benchmark_asset_type`、`benchmark_dtype` 的传入。': (
            'Remove ``qt.configure(..., maximize_cash_usage=...)``, ``benchmark_asset_type``, and '
            '``benchmark_dtype`` from code.'
        ),
        '确认回测/优化仅依赖 `benchmark_asset` 即可得到正确基准。': (
            'Confirm backtests/optimization work with ``benchmark_asset`` alone.'
        ),
        '破坏性变更提示': 'Breaking changes',
        '在 2.0 中，若仍通过 `qt.configure(..., only_built_in_keys=True)` 传入上述任一已删除键，将触发 `KeyError`。使用 `only_built_in_keys=False` 时，这些键可被写入配置对象但不会参与任何运行逻辑。': (
            'In 2.0, ``qt.configure(..., only_built_in_keys=True)`` with any removed key raises ``KeyError``. '
            'With ``only_built_in_keys=False``, keys may be stored but are ignored at runtime.'
        ),
        'Migration Steps / 版本迁移步骤': 'Migration steps',
        '针对自定义交易策略': 'Custom trading strategies',
    },
    'tutorials/Tutorial 07 - 交易策略的部署及运行.po': {
        'TO BE COMPLETED': 'TO BE COMPLETED',
    },
}


def apply_mapping(rel_path: str, mapping: dict[str, str]) -> tuple[int, int]:
    """应用译文并清除文件头 fuzzy。"""
    path = ROOT / rel_path
    po = polib.pofile(str(path))
    filled = 0
    for entry in po:
        if entry.obsolete or not entry.msgid:
            continue
        if not entry.msgstr and entry.msgid in mapping:
            entry.msgstr = mapping[entry.msgid]
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
            filled += 1
    po.metadata['PO-Revision-Date'] = '2026-05-23 20:00+0800'
    po.metadata['Last-Translator'] = 'Jackie PENG'
    po.save(str(path))
    text = path.read_text(encoding='utf-8')
    if '\n#, fuzzy\n' in text:
        path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
    remaining = sum(1 for e in po if e.msgid and not e.msgstr and not e.obsolete)
    return filled, remaining


def clear_all_header_fuzzy() -> int:
    """清除 en 下所有 .po 文件头 #, fuzzy。"""
    count = 0
    for path in ROOT.rglob('*.po'):
        if path.name.endswith('~'):
            continue
        text = path.read_text(encoding='utf-8')
        if '\n#, fuzzy\n' in text:
            path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
            count += 1
    return count


def fix_en_rtd_links() -> int:
    """将 en msgstr 中残留的 /zh-cn/latest/ 替换为 /en/latest/。"""
    pattern = re.compile(r'https://qteasy\.readthedocs\.io/zh-cn/latest/', re.I)
    fixed_files = 0
    for path in ROOT.rglob('*.po'):
        if path.name.endswith('~'):
            continue
        text = path.read_text(encoding='utf-8')
        new_text, n = pattern.subn('https://qteasy.readthedocs.io/en/latest/', text)
        if n:
            path.write_text(new_text, encoding='utf-8')
            fixed_files += 1
    return fixed_files


def main() -> int:
    """入口。"""
    for rel, mapping in TAIL.items():
        filled, remaining = apply_mapping(rel, mapping)
        print(f'{rel}: filled={filled}, remaining={remaining}')

    # 多行 msgid 需单独处理 back_testing overview 首段
    bt_path = ROOT / 'back_testing/1. overview.po'
    po = polib.pofile(str(bt_path))
    for entry in po:
        if entry.obsolete or not entry.msgid:
            continue
        if (
            not entry.msgstr
            and 'qt.run(op, mode=1' in entry.msgid
            and '回测在 qteasy' in entry.msgid
        ):
            entry.msgstr = (
                'In qteasy, backtests are triggered via **``qt.run(op, mode=1, ...)``**, simulating '
                'strategy runs on historical data to produce equity curves, trade logs, and performance '
                'metrics for evaluation and optimization.'
            )
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
    po.save(str(bt_path))

    headers = clear_all_header_fuzzy()
    links = fix_en_rtd_links()
    print(f'cleared header fuzzy in {headers} files; fixed RTD links in {links} files')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
