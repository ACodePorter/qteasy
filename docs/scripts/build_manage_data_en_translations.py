# coding=utf-8
"""构建 manage_data_en_translations.json（manage_data 批次 E 全量 msgid→msgstr）。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS.parent.parent))

from qteasy.datatables import TABLE_SCHEMA  # noqa: E402

MISSING_PATH = SCRIPTS / 'manage_data_missing_after_fill.json'
OUT_PATH = SCRIPTS / 'manage_data_en_translations.json'

SEED_FILES = (
    'manage_data_obsolete_recovery.json',
    'manage_data_seed_hits.json',
    'glossary_seed_from_09.json',
)

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')

# ---------------------------------------------------------------------------
# 种子翻译（obsolete / seed_hits / glossary）
# ---------------------------------------------------------------------------

def _load_seeds() -> dict[str, str]:
    """合并已有种子翻译文件。"""
    merged: dict[str, str] = {}
    for name in SEED_FILES:
        path = SCRIPTS / name
        if path.is_file():
            merged.update(json.loads(path.read_text(encoding='utf-8')))
    return merged


# ---------------------------------------------------------------------------
# 文档/段落类 msgid 的规则翻译与显式覆盖
# ---------------------------------------------------------------------------

EXCHANGE_MAP = {
    '**SSE** 上交所——上海证券交易所': '**SSE** SSE — Shanghai Stock Exchange',
    '**SZSE** 深交所——深圳股票交易所': '**SZSE** SZSE — Shenzhen Stock Exchange',
    '**SHFE** 上期所——上海期货交易所': '**SHFE** SHFE — Shanghai Futures Exchange',
    '**DCE** 大商所——大连商品交易所': '**DCE** DCE — Dalian Commodity Exchange',
    '**CZCE** 郑商所——郑州商品交易所': '**CZCE** CZCE — Zhengzhou Commodity Exchange',
    '**CFFEX** 中金所——中国金融期货交易所': '**CFFEX** CFFEX — China Financial Futures Exchange',
    '**INE** 上能源——上海国际能源交易中心': '**INE** INE — Shanghai International Energy Exchange',
}

KLINE_FIELD_LIST = (
    'stock code, trade date/time, open, high, low, close, volume, turnover'
)
KLINE_FIELD_LIST_LOW = (
    'stock code, trade date, open, high, low, close, previous close, change (%), '
    'volume, turnover'
)
KLINE_FIELD_LIST_FUND = (
    'fund code, trade date/time, open, high, low, close, volume, turnover'
)
KLINE_FIELD_LIST_FUND_LOW = (
    'fund code, trade date, open, high, low, close, previous close, change (%), '
    'volume, turnover'
)

DOCS_EXPLICIT: dict[str, str] = {
    '***`df`***: 一个`DataFrame`，保存了需要写入数据表中的数据': (
        '***`df`***: A `DataFrame` holding data to write into a table'
    ),
    '***`end`***: 给出一个日期，格式为`“YYYYMMDD”`，如果数据表的主键包含时间或日期，'
    '那么根据筛选`start`与`end`之间的数据，`start/end`必须成对给出': (
        '***`end`***: A date in `“YYYYMMDD”` format. If the table primary key includes '
        'time or date, filter rows between `start` and `end`; `start`/`end` must be '
        'provided as a pair'
    ),
    '***`merge_type`***: 如果是`update`则更新数据表中已经存在的数据，如果是`ignore`则忽略重复的数据.': (
        '***`merge_type`***: If `update`, update existing rows in the table; if `ignore`, '
        'skip duplicate rows.'
    ),
    '***`shares`***: 给出一个证券代码或者逗号分隔的多个证券代码，如果数据表的主键中含有证券代码，'
    '那么根据该证券代码筛选输出的数据': (
        '***`shares`***: One security code or comma-separated codes. If the primary key '
        'includes a security code, filter output by those codes'
    ),
    '***`start`***: 给出一个日期，格式为`“YYYYMMDD”`，如果数据表的主键包含时间或日期，'
    '那么根据筛选`start`与`end`之间的数据，`start/end`必须成对给出': (
        '***`start`***: A date in `“YYYYMMDD”` format. If the table primary key includes '
        'time or date, filter rows between `start` and `end`; `start`/`end` must be '
        'provided as a pair'
    ),
    '***`table`***: 一个数据表的名称，需要写入数据的数据表': (
        '***`table`***: Name of the target table to write into'
    ),
    '**`columns`** -- 字段名': '**`columns`** -- column names',
    '**`dtypes`** -- 字段数据类型, `varchar`表示字符串类型，`int`表示整数类型，'
    '`float`表示浮点数类型，`date`表示日期类型，`text`表示文本类型': (
        '**`dtypes`** -- column data types: `varchar` for strings, `int` for integers, '
        '`float` for floats, `date` for dates, `text` for text'
    ),
    '**`is_prime_key`** -- 是否是主键，`Y`表示是主键，`N`表示不是主键': (
        '**`is_prime_key`** -- whether the column is part of the primary key; '
        '`Y` = yes, `N` = no'
    ),
    '**`remarks`** -- 字段备注': '**`remarks`** -- column remarks',
    '**业绩报表表** -- 这类数据表包含了上市公司的业绩报表数据，包括业绩快报、业绩预告、业绩预测等': (
        '**Earnings report tables** — Listed-company earnings reports: express reports, '
        'earnings guidance, forecasts, etc.'
    ),
    '**分红交易数据表** -- 这类数据表包含了上市公司的分红数据，以及股票大宗交易、股东交易等信息表': (
        '**Dividend & block-trade tables** — Dividend data, block trades, shareholder '
        'transactions, etc.'
    ),
    '**分表信息**：对于某些数据表，由于数据量极大，因此需要分表存储，与分表相关的属性包括分表数量以及分表字段等': (
        '**Sharding**: Some tables are sharded due to size; related attributes include '
        'shard count and shard key columns'
    ),
    '**参考数据表** -- 这类数据表包含了各种参考数据，例如宏观经济数据、行业数据、交易所数据等': (
        '**Reference tables** — Macro, industry, exchange, and other reference data'
    ),
    '**基本信息表** -- 这类数据表包含了股票、基金、指数、期货、期权等各种金融产品的基本信息': (
        '**Basics tables** — Basic information for stocks, funds, indices, futures, '
        'options, etc.'
    ),
    '**指标信息表** -- 这类数据表包含了各种指标的信息，例如技术指标、基本面指标、宏观经济指标等': (
        '**Indicator tables** — Technical, fundamental, macro, and other indicators'
    ),
    '**数据表用途**：表示该数据表的用途，不同用途的数据表可用的操作不同。不同的用途包括：'
    '`basics`表示基本信息表，`finance`表示财务数据表，`report`表示业绩报表表, '
    '`reference`表示参考数据表等': (
        '**Table use**: Purpose of the table; available operations differ by use. '
        'Examples: `basics` = basics, `finance` = financials, `report` = earnings '
        'reports, `reference` = reference data, etc.'
    ),
    '**数据表的`SCHEMA`**：数据表的`SCHEMA`定义了数据表的所有字段和数据类型': (
        '**Table `SCHEMA`**: Defines all columns and data types'
    ),
    '**数据频率**：表示存储的数据的频率，不同的数据频率包括：`mins`表示分钟级别数据，'
    '`d`表示日频数据，`w`表示周频数据，`m`表示月频数据，`q`表示季频数据，'
    '`y`表示年频数据，`none`表示无频率数据': (
        '**Frequency**: Stored data frequency — `mins` minute, `d` daily, `w` weekly, '
        '`m` monthly, `q` quarterly, `y` yearly, `none` not frequency-specific'
    ),
    '**行情数据表** -- 这类数据表包含了股票、基金、指数各个不同频率的K线行情数据': (
        '**Market data tables** — OHLCV K-line data for stocks, funds, and indices at '
        'various frequencies'
    ),
    '**财务数据表** -- 这类数据表包含了上市公司的财务报表数据，包括资产负债表、利润表、现金流量表等': (
        '**Financial statement tables** — Balance sheet, income statement, cash flow, etc.'
    ),
    '**资产类型**：表示该数据表包含的信息属于哪种资产类型。不同的资产类型包括：'
    '`E`表示股票，`IDX`表示指数，`FD`表示基金，`FT`表示期货，`OPT`表示期权等': (
        '**Asset type**: Asset class covered — `E` stock, `IDX` index, `FD` fund, '
        '`FT` futures, `OPT` options, etc.'
    ),
    'IPO新股列表: `new_share`': 'IPO new issues: `new_share`',
    'IPO新股列表包含了所有新股的基本信息，包括股票代码、申购代码、名称、上网发行日期、上市日期、'
    '发行总量、上网发行总量、发行价格、市盈率、个人申购上限、募集资金、中签率等信息。': (
        'The IPO new-issue table lists basic information for all new listings: stock code, '
        'subscription code, name, online issue date, listing date, total issue size, online '
        'issue size, issue price, P/E ratio, individual subscription cap, funds raised, '
        'winning rate, etc.'
    ),
    'STOXX欧洲50指数': 'STOXX Europe 50 Index',
    '`DataSource`对象会根据输入的筛选条件自动筛选数据，例如：': (
        '`DataSource` filters data automatically from your criteria, for example:'
    ),
    '`DataSource`对象会自动根据数据表的定义来进行正确的筛选，并忽略掉不必要的参数。'
    '例如，我们可以筛选出某两支股票的基本信息。对于股票基本信息来说，交易日期是个不必要的参数，'
    '此时`qteasy`会自动忽略掉`start`/`end`参数并给出提示信息。同样，`shares`参数也不一定只能匹配股票代码，'
    '对于基金、指数、甚至期货、期权，都可以同样匹配：': (
        '`DataSource` applies the correct filters for each table and ignores unnecessary '
        'parameters. For example, when querying basic info for two stocks, trade date is '
        'not required — `qteasy` ignores `start`/`end` with a notice. The `shares` '
        'parameter also works for funds, indices, futures, and options, not just stocks:'
    ),
    '`DataTable`是`qteasy`内置统一定义的数据存储表。包括：': (
        '`DataTable` is qteasy’s unified built-in storage table definition. It includes:'
    ),
    '`DataTables`——上市公司基本面数据': (
        '`DataTables` — Listed-company fundamental data'
    ),
    '`DataTables`——上市公司技术面指标及市场趋势': (
        '`DataTables` — Listed-company technical indicators and market trends'
    ),
    '`DataTables`——价格行情表': '`DataTables` — Price / OHLCV tables',
    '`DataTables`——基本信息表': '`DataTables` — Basics tables',
}


def _translate_table_use(msgid: str) -> str | None:
    """翻译「数据表用途 / 资产类型 / 数据频率」行。"""
    m = re.match(
        r'^数据表用途:\s*(.+?),\s*资产类型:\s*(.+?),\s*数据频率:\s*(.+?)(?:\s+分表规则：(.+))?$',
        msgid,
    )
    if not m:
        return None
    usage, asset, freq, part = m.group(1), m.group(2), m.group(3), m.group(4)
    out = f'Table use: {usage}, asset type: {asset}, frequency: {freq}'
    if part:
        out += f' Partition rule: {part}'
    return out


def _translate_kline_desc(msgid: str) -> str | None:
    """翻译「X K线行情表包含了...」类描述。"""
    m = re.match(
        r'^(.+?)表包含了(.+?)的(\d+分钟|\d+分钟|1分钟|5分钟|15分钟|30分钟|60分钟|分钟|'
        r'小时|日|周|月)K线行情数据，包括(.+?)等信息。$',
        msgid,
    )
    if not m:
        return None
    subject, scope, freq_label, _fields = m.groups()
    freq_en = {
        '1分钟': '1-minute', '5分钟': '5-minute', '15分钟': '15-minute',
        '30分钟': '30-minute', '60分钟': '60-minute', '分钟': 'minute',
        '小时': 'hourly', '日': 'daily', '周': 'weekly', '月': 'monthly',
    }.get(freq_label, freq_label)
    scope_en = scope.replace('所有', 'all ').replace('沪深市场', 'SSE/SZSE ')
    return (
        f'The {subject} table contains {scope_en}{freq_en} K-line data, including '
        f'{KLINE_FIELD_LIST}, etc.'
    )


def translate_docs(msgid: str) -> str | None:
    """文档类 msgid 规则/显式翻译。"""
    if msgid in EXCHANGE_MAP:
        return EXCHANGE_MAP[msgid]
    if msgid in DOCS_EXPLICIT:
        return DOCS_EXPLICIT[msgid]
    tu = _translate_table_use(msgid)
    if tu:
        return tu
    kd = _translate_kline_desc(msgid)
    if kd:
        return kd
    return None


# ---------------------------------------------------------------------------
# TABLE_SCHEMA remarks → 英文字段说明（871 条，见同目录 manage_data_field_en.json）
# ---------------------------------------------------------------------------

FIELD_PATH = SCRIPTS / 'manage_data_field_en.json'


def _load_field_translations() -> dict[str, str]:
    """加载字段名翻译表；若不存在则返回空 dict。"""
    if FIELD_PATH.is_file():
        return json.loads(FIELD_PATH.read_text(encoding='utf-8'))
    return {}


DOCS_PATH = SCRIPTS / 'manage_data_docs_en.json'


def _load_docs_translations() -> dict[str, str]:
    """加载文档类翻译表；若不存在则返回空 dict。"""
    if DOCS_PATH.is_file():
        return json.loads(DOCS_PATH.read_text(encoding='utf-8'))
    return {}


def build_mapping() -> tuple[dict[str, str], list[str]]:
    """构建完整 msgid→msgstr 映射，返回 (mapping, missing_list)。"""
    msgids: list[str] = json.loads(MISSING_PATH.read_text(encoding='utf-8'))
    mapping: dict[str, str] = {}
    mapping.update(_load_seeds())
    mapping.update(_load_field_translations())
    mapping.update(_load_docs_translations())

    missing: list[str] = []
    for msgid in msgids:
        if msgid in mapping:
            continue
        doc = translate_docs(msgid)
        if doc:
            mapping[msgid] = doc
            continue
        if not CHINESE_RE.search(msgid):
            mapping[msgid] = msgid
            continue
        missing.append(msgid)
    return mapping, missing


def main() -> int:
    """写出 manage_data_en_translations.json 并打印统计。"""
    msgids: list[str] = json.loads(MISSING_PATH.read_text(encoding='utf-8'))
    mapping, missing = build_mapping()

    if missing:
        print(f'WARNING: {len(missing)} msgids still untranslated', file=sys.stderr)
        for m in missing[:20]:
            print(f'  - {m[:100]}...' if len(m) > 100 else f'  - {m}', file=sys.stderr)
        if len(missing) > 20:
            print(f'  ... and {len(missing) - 20} more', file=sys.stderr)

    ordered = {m: mapping[m] for m in msgids}
    OUT_PATH.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f'wrote {OUT_PATH.name}: {len(ordered)} keys')
    print(f'untranslated: {len(missing)}')
    return 0 if not missing and len(ordered) == len(msgids) else 1


if __name__ == '__main__':
    raise SystemExit(main())
