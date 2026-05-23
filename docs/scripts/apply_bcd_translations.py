# coding=utf-8
"""Phase 1 批次 B/C/D：应用 references 与 api 剩余中文条目英文翻译。"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import polib

from translations_bcd_simulation import CLI_SIMULATION, SIMULATION_OVERVIEW, TUI_SIMULATION

ROOT = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'en' / 'LC_MESSAGES'

# 历史数据章节：先运行 build_bcd_translations.py 与 gen_bcd_history_translations.py
try:
    from translations_bcd_history import GET_HISTORY_DATA, HISTORICAL_DATA_TYPES
except ImportError:
    HISTORICAL_DATA_TYPES = {}
    GET_HISTORY_DATA = {}

# msgid -> msgstr（精确匹配）
TRANSLATIONS: dict[str, dict[str, str]] = {
    'api/data_source.po': {
        '在 DataSource 上执行最小事务封装（DB 真事务，file 为 no-op）。': (
            'Run a minimal transaction wrapper on DataSource (real DB transaction; no-op for file storage).'
        ),
        '需要在事务中执行的可调用对象': 'Callable to run inside the transaction',
        '传递给 ``action`` 的位置参数': 'Positional arguments passed to ``action``',
        '传递给 ``action`` 的关键字参数': 'Keyword arguments passed to ``action``',
        '``action`` 的返回值': 'Return value of ``action``',
    },
    'api/Strategies.po': {
        '本页提供 Strategy 相关核心类的 API 自动文档入口。 设计思路与使用教程请参考：': (
            'This page is the autodoc entry for core Strategy classes. For design notes and tutorials, see:'
        ),
        '设计文档：``design/10-live-trading-s1.3-architecture.md``': (
            'Design: ``design/10-live-trading-s1.3-architecture.md``'
        ),
        '策略管理文档：``manage_strategies/*``': 'Strategy management: ``manage_strategies/*``',
        '实操教程：``tutorials/*``': 'Hands-on tutorials: ``tutorials/*``',
        '量化投资策略的抽象基类，所有具体策略都应从本类继承并实现交易信号生成逻辑。': (
            'Abstract base class for quantitative strategies; concrete strategies inherit from it and '
            'implement signal generation logic.'
        ),
        '一个完整的策略通常由三部分组成：可调参数（pars）、所需历史数据的声明 （data_types + window_length 等）以及基于这些数据生成信号的 ``realize()`` 逻辑。 在策略运行过程中，可通过 ``get_pars()`` 和 ``get_data()`` 访问参数与数据，输出 的实数信号再由 Operator 按 PT/PS/VS 信号语义解析为实际交易指令。关于自定义策略 实现步骤与 PT/PS/VS 的详细说明，见文档「交易策略与 BaseStrategy」相关章节。': (
            'A complete strategy usually has three parts: tunable parameters (``pars``), declared historical '
            'data (``data_types``, ``window_length``, etc.), and ``realize()`` logic that turns data into signals. '
            'During runs, use ``get_pars()`` and ``get_data()``; the Operator parses numeric signals as PT/PS/VS '
            'trade instructions. See the “Trading Strategies and BaseStrategy” docs for custom strategies and '
            'PT/PS/VS details.'
        ),
        '示例': 'Example',
        'BaseStrategy 为抽象基类，通常通过继承实现自定义策略。下面示例展示其类型信息（稳定输出）：': (
            '``BaseStrategy`` is abstract; implement custom strategies by subclassing. The example below shows '
            'stable type output:'
        ),
        '打印所有相关信息和主要属性': 'Print all related information and main attributes',
        '是否打印更多的信息': 'Whether to print extra details',
        '是否打印策略的运行状态': 'Whether to print strategy run state',
        '策略的ID，如果为None，则打印策略的名称，否则打印策略的ID': (
            'Strategy ID; if None, print the strategy name instead'
        ),
        '额外的信息，可以是任何字符串，会被打印在策略主信息之后，参数和数据之前': (
            'Extra text printed after main info and before parameters and data'
        ),
        '返回类型': 'Return type',
        '快速更新策略的参数值': 'Quickly update strategy parameter values',
        '策略参数的值，元组中的每个元素是按顺序排列的所有参数值，如果 没有设置参数，则必须传入kwargs参数': (
            'Parameter values as a tuple in parameter order; if parameters are not set, pass ``kwargs`` instead'
        ),
        '以字典形式传入具体需要更新的参数值，键为参数名，值为参数值': (
            'Update specific parameters via a dict mapping names to values'
        ),
        '通用交易策略类，用户需要完整定义策略的所有交易逻辑，并在realize()方法中定义策略的信号输出。': (
            'General strategy class: define full trading logic and signal output in ``realize()``.'
        ),
        '规则迭代策略类。这一类策略不考虑每一只股票的区别，将同一套规则同时迭代应用到所有的股票上。': (
            'Rule iterator strategy: apply the same rule to every share without per-share distinction.'
        ),
        'RuleIterator策略类的特殊功能是可以对同一套交易规则，将不同的参数应用到投资组合中的不同股票上。 例如，用户可以设计一个均线交叉策略，并将其应用到投资组合中的所有股票上，同时可以为每只股票 设定不同的均线周期参数。关于Strategy类的更详细说明，请参见qteasy的文档。': (
            '``RuleIterator`` can apply different parameters per share for the same rule—for example, different '
            'MA periods per stock. See qteasy docs for more on Strategy classes.'
        ),
        '**多标的且每股参数不同**：须通过 ``update_par_values({股票代码: (p1, p2, ...), ...})`` 传入与 ``share_names`` 一致的股票代码键；若仅用位置元组初始化，多标的时全体共享一套运行时参数（见 用户文档《三种策略基类》中 RuleIterator 一节）。字典中可用键名 ``default`` 为未单独列出的标的 提供同一套默认初值；不支持 ``others`` 等其它保留键名。': (
            '**Per-share parameters**: pass ``update_par_values({code: (p1, p2, ...), ...})`` with keys matching '
            '``share_names``; a positional tuple shares one runtime parameter set across shares (see RuleIterator '
            'in “Three Strategy Base Classes”). Use ``default`` for shares not listed explicitly; ``others`` is not '
            'supported.'
        ),
        'Parameter 用于定义策略可调参数的类型、范围与取值方式。': (
            '``Parameter`` defines tunable strategy parameter type, range, and value semantics.'
        ),
        '可调参数对象，可以是离散型、连续型、枚举型或者数组型参数，在交易策略中对策略的运行结果产生影响。': (
            'Tunable parameter object (discrete, continuous, enum, or array) affecting strategy results.'
        ),
        '获取参数的当前值': 'Get the current parameter value',
        '设置参数的当前值': 'Set the current parameter value',
        '需要设置的参数值，若参数为枚举型，则value可以是枚举值中的一个；若参数为离散型或连续型，则value可以是一个整数或浮点数': (
            'Value to set; for enums, one enum value; for discrete/continuous types, int or float'
        ),
        '抛出': 'Raises',
        '当value不在数轴的可用值中时，抛出ValueError异常': (
            '``ValueError`` if ``value`` is not on the allowed axis'
        ),
        '更新参数的范围': 'Update parameter bounds',
        '数轴的上下界或枚举值，当数轴类型为conti或discr时，bounds_or_enum为一个长度为2的列表或元组，分别代表数轴的上下界； 当数轴类型为enum时，bounds_or_enum为一个列表或元组，其中的元素为该数轴上所有可用的值': (
            'For ``conti``/``discr``, a length-2 list/tuple of lower/upper bounds; for ``enum``, a list/tuple of '
            'allowed values'
        ),
        '当输入的数轴类型不在可选值中时，抛出ValueError异常': (
            '``ValueError`` if the axis type is not supported'
        ),
    },
    'references/3-back-test-strategy.po': {
        '策略序号': 'Strategy index',
        "支持`'&|~'`以及`'and/or/not'`形式的逻辑运算符": (
            "Supports logical operators in forms like `'&|~'` and `'and/or/not'`"
        ),
    },
    'references/1-simulation-overview.po': SIMULATION_OVERVIEW,
    'references/5-simulate-operation-in-CLI.po': CLI_SIMULATION,
    'references/6-simulate-operation-in-TUI.po': TUI_SIMULATION,
    'references/2-historical_data_types.po': HISTORICAL_DATA_TYPES,
    'references/2-get-history-data.po': GET_HISTORY_DATA,
}


def apply_file(rel_path: str, mapping: dict[str, str]) -> None:
    """将 mapping 应用到指定 po 文件。"""
    path = ROOT / rel_path
    po = polib.pofile(str(path))
    filled = 0
    for entry in po:
        if entry.obsolete or not entry.msgid:
            continue
        if entry.msgid in mapping:
            entry.msgstr = mapping[entry.msgid]
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
            filled += 1
    po.metadata['PO-Revision-Date'] = '2026-05-23 15:00+0800'
    po.metadata['Last-Translator'] = 'Jackie PENG'
    if po.metadata.get('Language-Team'):
        po.metadata['Language-Team'] = 'English'
    # 清除文件头 fuzzy（sphinx-intl 首次生成时常带此标记）
    po.save(str(path))
    # 清除文件头 #, fuzzy
    text = path.read_text(encoding='utf-8')
    if '\n#, fuzzy\n' in text:
        path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
    remaining = sum(1 for e in po if e.msgid and not e.msgstr and not e.obsolete)
    print(f'{rel_path}: filled={filled}, remaining={remaining}')


def main() -> int:
    """入口。"""
    for rel, mapping in TRANSLATIONS.items():
        apply_file(rel, mapping)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
