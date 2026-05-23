# coding=utf-8
"""生成 manage_data_docs_en.json（402 条文档类 msgid 翻译）。"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

SEED_FILES = (
    'manage_data_obsolete_recovery.json',
    'manage_data_seed_hits.json',
    'glossary_seed_from_09.json',
)


def _load_seeds() -> dict[str, str]:
    merged: dict[str, str] = {}
    for name in SEED_FILES:
        merged.update(json.loads((SCRIPTS / name).read_text(encoding='utf-8')))
    return merged


def translate_table_use(msgid: str) -> str | None:
    """翻译数据表用途三元组行。"""
    m = re.match(
        r'^数据表用途:\s*(.+?),\s*资产类型:\s*(.+?),\s*数据频率:\s*(.+?)(?:\s+分表规则：(.+))?$',
        msgid,
    )
    if not m:
        return None
    usage, asset, freq, part = m.groups()
    out = f'Table use: {usage}, asset type: {asset}, frequency: {freq}'
    if part:
        out += f' Partition rule: {part}'
    return out


def _en_subject(subject: str) -> str:
    """将表描述主语翻译为英文。"""
    subject_map = {
        '场内基金15分钟K线行情': 'on-exchange fund 15-min K-line quotes',
        '场内基金30分钟K线行情': 'on-exchange fund 30-min K-line quotes',
        '场内基金5分钟K线行情': 'on-exchange fund 5-min K-line quotes',
        '场内基金60分钟K线行情': 'on-exchange fund 60-min K-line quotes',
        '场内基金分钟K线行情': 'on-exchange fund 1-min K-line quotes',
        '场内基金小时K线行情': 'on-exchange fund hourly K-line quotes',
        '场内基金日K线行情': 'on-exchange fund daily K-line quotes',
        '场内基金周K线行情': 'on-exchange fund weekly K-line quotes',
        '场内基金月K线行情': 'on-exchange fund monthly K-line quotes',
        '指数15分钟K线行情': 'index 15-min K-line quotes',
        '指数30分钟K线行情': 'index 30-min K-line quotes',
        '指数5分钟K线行情': 'index 5-min K-line quotes',
        '指数60分钟K线行情': 'index 60-min K-line quotes',
        '指数分钟K线行情': 'index 1-min K-line quotes',
        '指数小时K线行情': 'index hourly K-line quotes',
        '指数日K线行情': 'index daily K-line quotes',
        '指数周K线行情': 'index weekly K-line quotes',
        '指数月K线行情': 'index monthly K-line quotes',
        '期权15分钟K线行情': 'option 15-min K-line quotes',
        '期权30分钟K线行情': 'option 30-min K-line quotes',
        '期权5分钟K线行情': 'option 5-min K-line quotes',
        '期权60分钟K线行情': 'option 60-min K-line quotes',
        '期权分钟K线行情': 'option 1-min K-line quotes',
        '期权小时K线行情': 'option hourly K-line quotes',
        '期货15分钟K线行情': 'futures 15-min K-line quotes',
        '期货30分钟K线行情': 'futures 30-min K-line quotes',
        '期货5分钟K线行情': 'futures 5-min K-line quotes',
        '期货60分钟K线行情': 'futures 60-min K-line quotes',
        '期货分钟K线行情': 'futures 1-min K-line quotes',
        '期货小时K线行情': 'futures hourly K-line quotes',
        '股票15分钟K线行情': 'stock 15-min K-line quotes',
        '股票30分钟K线行情': 'stock 30-min K-line quotes',
        '股票5分钟K线行情': 'stock 5-min K-line quotes',
        '股票60分钟K线行情': 'stock 60-min K-line quotes',
        '股票分钟K线行情': 'stock 1-min K-line quotes',
        '股票周线行情': 'stock weekly K-line quotes',
        '股票日线行情': 'stock daily K-line quotes',
        '股票月线行情': 'stock monthly K-line quotes',
    }
    return subject_map.get(subject, subject)


def _en_scope(scope: str) -> str:
    """翻译范围短语。"""
    return (
        scope.replace('所有沪深市场场内基金', 'all SSE/SZSE on-exchange funds')
        .replace('所有沪深市场指数', 'all SSE/SZSE indices')
        .replace('所有沪深市场期货', 'all SSE/SZSE futures')
        .replace('所有沪深市场期权', 'all SSE/SZSE options')
        .replace('所有股票', 'all stocks')
        .replace('所有指数', 'all indices')
        .replace('所有', 'all ')
    )


def translate_kline(msgid: str) -> str | None:
    """翻译 K 线行情表描述。"""
    m = re.match(
        r'^(.+?)表包含了(.+?)的(\d+分钟|1分钟|5分钟|15分钟|30分钟|60分钟|分钟|小时)K线行情数据，包括(.+?)等信息。$',
        msgid,
    )
    if not m:
        return None
    subject, scope, freq, _ = m.groups()
    freq_map = {
        '1分钟': '1-minute', '5分钟': '5-minute', '15分钟': '15-minute',
        '30分钟': '30-minute', '60分钟': '60-minute', '分钟': '1-minute', '小时': 'hourly',
    }
    subj_en = _en_subject(subject)
    scope_en = _en_scope(scope)
    return (
        f'The {subj_en} table contains {scope_en} {freq_map.get(freq, freq)} K-line data, '
        f'including code, trade date/time, open, high, low, close, volume, turnover, etc.'
    )


def translate_lowfreq_kline(msgid: str) -> str | None:
    """翻译日/周/月 K 线低频描述。"""
    m = re.match(
        r'^(.+?)表包含了(.+?)的(周|月|日)(?:K)?线行情数据，中低频K线行情相比中高频数据，'
        r'多出了昨收价、涨跌幅、涨跌额等数据，同时成交量和成交额的单位也不一样。$',
        msgid,
    )
    if not m:
        return None
    subject, scope, freq = m.groups()
    freq_map = {'日': 'daily', '周': 'weekly', '月': 'monthly'}
    subj_en = _en_subject(subject)
    scope_en = _en_scope(scope)
    return (
        f'The {subj_en} table contains {scope_en} {freq_map[freq]} K-line data. '
        f'Compared with intraday bars, lower-frequency bars add previous close, change (%), '
        f'and change amount; volume and turnover units also differ.'
    )


def translate_hourly_table(msgid: str) -> str | None:
    """翻译 XX小时K线行情表（无标题前缀）。"""
    m = re.match(
        r'^(.+?)小时K线行情表包含了(.+?)的60分钟K线行情数据，包括(.+?)等信息。$',
        msgid,
    )
    if not m:
        return None
    subject, scope, _ = m.groups()
    subj_en = _en_subject(subject)
    scope_en = _en_scope(scope)
    return (
        f'The {subj_en} table contains {scope_en} 60-minute K-line data, '
        f'including code, trade date/time, open, high, low, close, volume, turnover, etc.'
    )


def translate_daily_table(msgid: str) -> str | None:
    """翻译 XX日K线行情表（无标题前缀）。"""
    m = re.match(
        r'^(.+?)日K线行情表包含了(.+?)的日线行情数据，包括(.+?)等信息。$',
        msgid,
    )
    if not m:
        return None
    subject, scope, _ = m.groups()
    subj_en = _en_subject(subject + '日K线行情' if not subject.endswith('行情') else subject)
    scope_en = _en_scope(scope)
    return (
        f'The {subj_en} table contains {scope_en} daily OHLCV data, '
        f'including code, trade date, open, high, low, close, previous close, change (%), '
        f'volume, turnover, etc.'
    )


def translate_weekly_monthly_kline(msgid: str) -> str | None:
    """翻译 XX周/月K线行情表（含昨收价）。"""
    m = re.match(
        r'^(.+?(?:周|月))K线行情表包含了(.+?)的(周|月)K线行情数据，包括(.+?)等信息。$',
        msgid,
    )
    if not m:
        return None
    subject_full, scope, freq, _ = m.groups()
    subject = subject_full[:-1]  # drop trailing 周/月
    freq_en = 'weekly' if freq == '周' else 'monthly'
    subj_en = _en_subject(subject + ('周K线行情' if freq == '周' else '月K线行情'))
    scope_en = _en_scope(scope)
    return (
        f'The {subj_en} table contains {scope_en} {freq_en} K-line data, '
        f'including code, trade date, open, high, low, close, previous close, change (%), '
        f'volume, turnover, etc.'
    )


def translate_futures_ohlcv(msgid: str) -> str | None:
    """翻译期货日/周/月线行情表（含昨收盘价）。"""
    m = re.match(
        r'^期货(周线|日线|月线)行情表包含了(.+?)的(周|日|月)线行情数据，包括(.+?)等信息。$',
        msgid,
    )
    if not m:
        return None
    _, scope, freq, _ = m.groups()
    freq_en = {'周': 'weekly', '日': 'daily', '月': 'monthly'}[freq]
    scope_en = _en_scope(scope)
    return (
        f'The futures {freq_en} quote table contains {scope_en} {freq_en} OHLCV data, '
        f'including futures code, trade date, open, high, low, close, previous close, '
        f'change (%), volume, turnover, etc.'
    )


# 显式翻译（402 条中非规则覆盖部分）
DOCS: dict[str, str] = {
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
    '**CFFEX** 中金所——中国金融期货交易所': (
        '**CFFEX** CFFEX — China Financial Futures Exchange'
    ),
    '**CZCE** 郑商所——郑州商品交易所': '**CZCE** CZCE — Zhengzhou Commodity Exchange',
    '**DCE** 大商所——大连商品交易所': '**DCE** DCE — Dalian Commodity Exchange',
    '**INE** 上能源——上海国际能源交易中心': (
        '**INE** INE — Shanghai International Energy Exchange'
    ),
    '**SHFE** 上期所——上海期货交易所': '**SHFE** SHFE — Shanghai Futures Exchange',
    '**SSE** 上交所——上海证券交易所': '**SSE** SSE — Shanghai Stock Exchange',
    '**SZSE** 深交所——深圳股票交易所': '**SZSE** SZSE — Shenzhen Stock Exchange',
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
    '`d`表示日频数据，`w`表示周频数据，`m`表示月频数据，`q`表示季频数据，`y`表示年频数据，'
    '`none`表示无频率数据': (
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
        "`DataTable` is qteasy's unified built-in storage table definition. It includes:"
    ),
    '`DataTables`——上市公司基本面数据': (
        '`DataTables` — Listed-company fundamental data'
    ),
    '`DataTables`——上市公司技术面指标及市场趋势': (
        '`DataTables` — Listed-company technical indicators and market trends'
    ),
    '`DataTables`——价格行情表': '`DataTables` — Price / OHLCV tables',
    '`DataTables`——基本信息表': '`DataTables` — Basics tables',
    '`fund_basic` -- 基金基本信息表，包含了所有基金的基本信息，包括基金代码、基金名称、基金类型、'
    '基金规模等信息。这张表是很多其他数据表的基础，例如基金日K线数据表、基金净值数据表等，'
    '因此，这也是您应该**优先**填充的数据表。': (
        '`fund_basic` — Fund basics table with code, name, type, size, etc. Foundation for '
        'fund daily K-line and NAV tables; **prioritize** filling this table.'
    ),
    '`index_basic` -- 指数基本信息表，包含了所有指数的基本信息，包括指数代码、指数名称、发布日期、'
    '退市日期等信息。这张表是很多其他数据表的基础，例如指数日K线数据表、指数成分股表等，'
    '因此，这也是您应该**优先**填充的数据表。': (
        '`index_basic` — Index basics table with code, name, publish/delisting dates, etc. '
        'Foundation for index daily K-line and constituent tables; **prioritize** filling '
        'this table.'
    ),
    '`index_daily`数据表的数据定义中包含11列，而上面的数据只有6列，不过`DataFrame`中的所有列都包含在'
    '`index_daily`数据表的`schema`中': (
        'The `index_daily` table schema defines 11 columns while the sample `DataFrame` '
        'above has only 6; all `DataFrame` columns are still within the `index_daily` '
        '`schema`.'
    ),
    '`index_daily`数据表目前是空的，没有填充任何数据': (
        'The `index_daily` table is currently empty with no data filled.'
    ),
    '`qteasy`内置大量的行情数据表，包含股票、基金、指数、期货、期权等不同资产类型的不同频率的K线行情数据。'
    '大部分行情数据都包含从1分钟到1小时的中高频K线数据，以及日K线、周、月等低频K线数据。': (
        'qteasy ships many OHLCV tables for stocks, funds, indices, futures, and options at '
        'various frequencies—from 1-minute to hourly intraday bars plus daily, weekly, and '
        'monthly bars.'
    ),
    '`qteasy`提供了上市公司的财务报表数据，包括利润表、资产负债表、现金流量表等。'
    '数据来源于tushare，数据频率为季度频率。': (
        'qteasy provides listed-company financial statements (income, balance sheet, cash '
        'flow, etc.) sourced from Tushare at quarterly frequency.'
    ),
    '`qteasy`的`DataSource`对象提供了一个删除数据表的方法: `drop_table_data()`,'
    '这个方法将删除整个数据表，而且**删除后无法恢复**！': (
        'The `DataSource` method `drop_table_data()` deletes an entire table and '
        '**cannot be undone**!'
    ),
    '`stock_basic` -- 股票基本信息表，包含了所有上市股票的基本信息，包括股票代码、股票名称、上市日期、'
    '退市日期、所属行业、地域等信息。这张表是很多其他数据表的基础，例如股票日K线数据表、股票财务数据表等，'
    '因此，这也是您应该**优先**填充的数据表。': (
        '`stock_basic` — Stock basics table with code, name, listing/delisting dates, '
        'industry, region, etc. Foundation for stock daily K-line and financial tables; '
        '**prioritize** filling this table.'
    ),
    '`sys_op_live_accounts` -- 实盘交易账户信息表，包含了所有实盘交易账户的基本信息，'
    '包括账户ID、账户名称、账户类型、账户状态等信息。': (
        '`sys_op_live_accounts` — Live trading account master table with account ID, name, '
        'type, status, etc.'
    ),
    '`sys_op_positions` -- 实盘持仓信息表，包括所有实盘交易账户的持仓信息，'
    '包括账户ID、证券代码、证券名称、持仓数量、持仓成本等信息。': (
        '`sys_op_positions` — Live positions table with account ID, security code/name, '
        'quantity, cost, etc.'
    ),
    '`sys_op_trade_orders` -- 实盘交易委托表，包括所有实盘交易账户的交易委托信息，'
    '包括账户ID、委托时间、委托类型、证券代码、委托数量、委托价格等信息。': (
        '`sys_op_trade_orders` — Live order table with account ID, order time/type, '
        'security code, quantity, price, etc.'
    ),
    '`sys_op_trade_results` -- 实盘交易成交表，包括所有实盘交易账户的交易成交信息，'
    '包括账户ID、成交时间、证券代码、成交数量、成交价格等信息。': (
        '`sys_op_trade_results` — Live fill table with account ID, fill time, security '
        'code, quantity, price, etc.'
    ),
    '`trade_calendar` -- 交易日历表，包含了所有交易所的交易日历信息，包括交易日、交易所代码、'
    '交易所名称等信息。可以说这是`qteasy`运行的基础，如果缺了这张表，`qteasy`的很多功能都将无法运行或者将降低效率。 '
    '`qteasy`使用这张表中的数据来判断交易日，如果要下载其他的数据表，通常也必须通过交易日数据表来确定下载的起止日期，'
    '因此，这是您应该**绝对优先**填充的数据表。': (
        '`trade_calendar` — Trading calendar for all exchanges (trading day, exchange '
        'code/name). Core to qteasy: many features fail or slow without it. Used to '
        'determine trading days and download date ranges — **fill this table first**.'
    ),
    '上市公司利润表: `income`': 'Listed-company income statement: `income`',
    '上市公司基本信息: `stock_company`': 'Listed-company basic information: `stock_company`',
    '上市公司基本信息表包含了所有上市公司的基本信息，包括公司代码、公司名称、法人代表、总经理、董秘、'
    '注册资本、注册日期、所在省份、所在城市、公司介绍、公司主页、电子邮件、办公室地址、员工人数、'
    '主要业务及产品、经营范围等信息。': (
        'Listed-company basics table with company code/name, legal rep, GM, board secretary, '
        'registered capital/date, province/city, introduction, website, email, office address, '
        'headcount, main business/products, business scope, etc.'
    ),
    '上市公司现金流量表: `cashflow`': 'Listed-company cash flow statement: `cashflow`',
    '上市公司管理层: `stk_managers`': 'Listed-company management: `stk_managers`',
    '上市公司管理层表包含了上市公司的高管信息，包括公司管理层姓名、性别、学历、简历以及任职期限等': (
        'Management table with executive name, gender, education, resume, and tenure.'
    ),
    '上市公司财务报表数据': 'Listed-company financial statement data',
    '上市公司财务指标: `financial`': 'Listed-company financial indicators: `financial`',
    '上市公司财报快报: `express`': 'Listed-company earnings express: `express`',
    '上市公司财报预测: `forecast`': 'Listed-company earnings forecast: `forecast`',
    '上市公司资产负债表: `balance`': 'Listed-company balance sheet: `balance`',
    '上面四张表是qteasy实盘交易功能的基础，这几张表中的数据不需要人为填充，而是系统自动生成，'
    '您不需要查看、填充或删除这些表': (
        'These four system tables underpin live trading; data is auto-generated — do not '
        'manually fill, view, or delete them.'
    ),
    '上面的`DataFrame`中保存了一些示例数据，我们下面将把这个`DataFrame`的数据写入数据源中的'
    '`index_daily`数据表。 目前我们可以看到，`index_daily`数据表是空的，'
    '而且这个数据表的`schema`与上面的`DataFrame`并不完全相同：': (
        'The sample `DataFrame` above will be written to `index_daily`. Currently '
        '`index_daily` is empty and its `schema` differs slightly from the `DataFrame`:'
    ),
    '上面的信息显示了数据源中有3张数据表已经有了数据，包括`trade_calendar`、`stock_basic`和`stock_daily`，'
    '并显示了这些数据表的数据量、占用磁盘空间、数据的起始日期\ufffd\ufffd结束日期等信息。'
    '如果想查看所有数据表的信息，可以将返回的`DataFrame`打印出来：': (
        'The summary shows three populated tables — `trade_calendar`, `stock_basic`, '
        '`stock_daily` — with row counts, disk usage, and start/end dates. Print the '
        'returned `DataFrame` to see all tables:'
    ),
    '下面代码删除了`index_daily`表，然后就会发现，无法从该表读取数据了：': (
        'The code below drops `index_daily`; afterwards reads from that table fail:'
    ),
    '下面列出`qteasy`中所有的内置预定义数据表，包括交易日历表、股票基本信息表、指数基本信息表、'
    '基金基本信息表、期货基本信息表、期权基本信息表、同花顺指数基本信息表、申万行业分类表等。': (
        'Below are all built-in predefined tables: trading calendar, stock/index/fund/futures/'
        'option basics, THS index basics, SW industry classification, etc.'
    ),
    '下面将一些示例数据写入数据源(写入的数据仅为演示效果)': (
        'Sample data is written below for demonstration only.'
    ),
    '业绩报表表 -- 这类数据表包含了上市公司的业绩报表数据，包括业绩快报、业绩预告、业绩预测等': (
        'Earnings report tables — express reports, earnings guidance, forecasts, etc.'
    ),
    '个股资金流向: `money_flow`': 'Stock money flow: `money_flow`',
    '个股资金流向表包含了个股的资金流向数据，包括小单、中单、大单、特大单等资金流向数据。': (
        'Stock money-flow table with small/medium/large/extra-large order flow data.'
    ),
    '中国交易日历: `trade_calendar`': 'China trading calendar: `trade_calendar`',
    '中国交易日历包括上海、深圳股票交易所的交易日历，也包括各大期货商品交易所的交易日历': (
        'Covers SSE/SZSE and major futures exchanges.'
    ),
    '中证指数日线行情: `ci_index_daily`': 'CSI index daily quotes: `ci_index_daily`',
    '中证指数日线行情表包含了中证指数的日线行情数据，包括指数代码、交易日期、开盘价、最高价、'
    '最低价、收盘价、涨跌幅、成交量、成交额等信息。': (
        'CSI index daily OHLCV table with code, trade date, open/high/low/close, '
        'change (%), volume, turnover.'
    ),
    '为了避免在代码中误删除数据表，默认情况下`drop_table_data()`会导致错误，'
    '例如我们想删除之前写入临时数据的`index_daily`表：': (
        'To prevent accidental drops, `drop_table_data()` errors by default — e.g. when '
        'dropping temporary `index_daily` data:'
    ),
    '为了避免读取的数据量过大，建议在读取数据时一定要同时给出某些筛选条件。'
    '对于`read_table_data()`方法来说，用户总是可以通过证券代码和起止日期来筛选数据:': (
        'To avoid huge reads, always pass filters. With `read_table_data()` you can filter '
        'by security code and date range:'
    ),
    '亚太主要指数：日经225指数、恒生指数、澳大利亚标普200指数': (
        'Major Asia-Pacific indices: Nikkei 225, Hang Seng, S&P/ASX 200'
    ),
    '交易所代码对照如下：': 'Exchange code reference:',
    '交易所：SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源': (
        'Exchanges: SSE Shanghai, SZSE Shenzhen, CFFEX, SHFE, CZCE, DCE, INE'
    ),
    '交易日历表: `trade_calendar`': 'Trading calendar: `trade_calendar`',
    '交易日历表的定义：': 'Trading calendar table definition:',
    '交易日历：': 'Trading calendar:',
    '什么是`DataSource`，如何创建一个数据源': 'What is `DataSource` and how to create one',
    '从`stock_daily`表中读取一只股票（`000651.SZ`）从2024年1月1日到2024年1月15日之间的股票日K线数据：': (
        'Read daily K-line data for `000651.SZ` from `stock_daily` between 2024-01-01 and '
        '2024-01-15:'
    ),
    '从数据表中获取数据': 'Reading data from tables',
    '以最重要的交易日历表为例，它的属性及SCHEMA定义如下：': (
        'Using the trading calendar as an example, its attributes and SCHEMA are:'
    ),
    '使用`update_table_data()`方法，用户不需要保证写入的数据格式与数据表完全一致，'
    '只要数据格式与数据表大致一致，`qteasy`就会自动整理数据格式、删除重复数据，'
    '确保写入数据表中的数据符合要求。': (
        'With `update_table_data()`, exact schema match is not required — qteasy '
        'normalizes format and deduplicates before writing.'
    ),
    '俄罗斯RTS指数': 'Russia RTS Index',
    '停复牌信息: `stock_suspend`': 'Suspension/resumption: `stock_suspend`',
    '停复牌信息表包含了股票的停复牌信息，包括停复牌日期、停复牌时间段、停复牌类型等信息。': (
        'Suspension/resumption table with date, time range, and type.'
    ),
    '全球主要指数主要包括：': 'Major global indices include:',
    '全球指数日线行情: `global_index_daily`': 'Global index daily quotes: `global_index_daily`',
    '全球指数日线行情表包含了全球主要指数的日线行情数据，包括指数代码、交易日期、开盘价、最高价、'
    '最低价、收盘价、涨跌幅、成交量、成交额等信息。': (
        'Global index daily OHLCV with code, trade date, OHLC, change (%), volume, turnover.'
    ),
    '关于`read_table_data()`方法的更多信息，请参阅`DataSource`对象的参考信息。': (
        'See `DataSource` reference for more on `read_table_data()`.'
    ),
    '其他主要指数：巴西IBOVESPA指数、俄罗斯RTS指数、印度SENSEX指数等等 上述指数代码对照表如下：': (
        'Other major indices: Bovespa, RTS, SENSEX, etc. Code reference:'
    ),
    '其他指数行情数据表：': 'Other index quote tables:',
    '其他的数据表': 'Other tables',
    '分红交易数据表 -- 这类数据表包含了上市公司的分红数据，以及股票大宗交易、股东交易等信息表': (
        'Dividend & block-trade tables — dividends, block trades, shareholder trades, etc.'
    ),
    '删除数据表 —— 请尽量小心，删除后无法恢复！！': (
        'Drop table — be careful; deletion is irreversible!!'
    ),
    '利润表是上市公司的财务报表之一，主要包括营业总收入、营业收入、营业总成本、营业成本、'
    '营业税金及附加、销售费用、管理费用、财务费用、资产减值损失、营业利润、利润总额、'
    '所得税费用、净利润等信息。': (
        'Income statement fields include total revenue, operating revenue/costs, taxes, '
        'selling/admin/financial expenses, impairment, operating/total profit, tax, net '
        'profit, etc.'
    ),
    '加拿大S&P/TSX指数': 'S&P/TSX Composite Index (Canada)',
    '印度孟买SENSEX指数': 'BSE SENSEX (India)',
    '参考数据表 -- 这类数据表包含了各种参考数据，例如宏观经济数据、行业数据、交易所数据等': (
        'Reference tables — macro, industry, exchange, and other reference data'
    ),
    '古董交易表包含了股票的股东交易信息，包括股东交易日期、股东交易价格、股东交易量、'
    '股东交易金额、股东名称、股东类型、增减持类型、变动数量、占流通比例、变动后持股、'
    '变动后占流通比例、平均价格、持股总数、增减持开始日期、增减持结束日期等\ufffd\ufffd息。': (
        'Shareholder trade table with trade date/price/volume/amount, shareholder name/type, '
        'change type, quantity, float share, post-change holdings, average price, total '
        'holdings, increase/decrease period, etc.'
    ),
    '另外，`qteasy`还在数据源中定义了几张系统数据表，这些表一共四张，用于存储跟实盘交易相关的信息：': (
        'qteasy also defines four system tables for live-trading records:'
    ),
    '台湾加权指数': 'TAIEX (Taiwan Weighted Index)',
    '同花顺指数基本信息: `ths_index_basic`': 'THS index basics: `ths_index_basic`',
    '同花顺指数基本信息表包含了所有同花顺指数的基本信息，包括指数代码、名称、成分个数、交易所、'
    '上市日期、N概念指数S特色指数等信息。': (
        'THS index basics with code, name, constituent count, exchange, listing date, '
        'N concept / S specialty flags, etc.'
    ),
    '同花顺行业指数成份数据表包含了同花顺行业指数的成份股数据，包括成份股代码、成份股权重等信息。': (
        'THS industry index constituents with code and weight.'
    ),
    '同花顺行业指数成分股权重: `ths_index_weight`': (
        'THS industry index constituent weights: `ths_index_weight`'
    ),
    '同花顺行业指数日线行情: `ths_index_daily`': 'THS industry index daily quotes: `ths_index_daily`',
    '同花顺行业指数行情表包含了同花顺行业指数的日线行情数据，包括指数代码、交易日期、开盘价、'
    '最高价、最低价、收盘价、涨跌幅、成交量、成交额等信息。': 'THS industry index daily OHLCV table.',
    '向数据表中填充数据可以使用数据源的`update_table_data()`方法。'
    '使用这个API，用户可以将保存在一个`DataFrame`中的数据写入到相应的数据表中。'
    '这个API只需要给出三个参数：': (
        'Fill tables via `update_table_data()`, writing a `DataFrame` with three parameters:'
    ),
    '向数据表中添加数据': 'Adding data to tables',
    '在`qteasy`中，每一张数据表都有以下几个基本属性：': (
        'Each table in qteasy has these basic attributes:'
    ),
    '在后面的章节中，您将会了解更多的内容：': 'Later chapters cover more:',
    '在统计过程中，`qteasy`会显示一根进度条显示统计的进度，最终统计分析完成后，'
    '`qteasy`会将数据源中所有数据表的信息以DataFrame的形式返回，并打印出关键的信息。': (
        'During overview, qteasy shows a progress bar, then returns a `DataFrame` of all '
        'tables and prints key stats.'
    ),
    '场内基金15分钟K线行情: `fund_15min`': 'On-exchange fund 15-min K-line: `fund_15min`',
    '场内基金30分钟K线行情: `fund_30min`': 'On-exchange fund 30-min K-line: `fund_30min`',
    '场内基金5分钟K线行情: `fund_5min`': 'On-exchange fund 5-min K-line: `fund_5min`',
    '场内基金60分钟K线行情: `fund_hourly`': 'On-exchange fund 60-min K-line: `fund_hourly`',
    '场内基金分钟K线行情: `fund_1min`': 'On-exchange fund 1-min K-line: `fund_1min`',
    '场内基金周K线行情: `fund_weekly`': 'On-exchange fund weekly K-line: `fund_weekly`',
    '场内基金月K线行情: `fund_monthly`': 'On-exchange fund monthly K-line: `fund_monthly`',
    '场内基金每日K线行情: `fund_daily`': 'On-exchange fund daily K-line: `fund_daily`',
    '场外基金每日净值: `fund_nav`': 'Off-exchange fund daily NAV: `fund_nav`',
    '场外基金每日净值表包含了所有场外基金的每日净值数据，包括基金代码、交易日期、单位净值、'
    '累计净值、日增长率、申购状态、赎回状态等信息。': (
        'Off-exchange fund daily NAV with code, date, unit/accumulated NAV, daily growth, '
        'subscription/redemption status.'
    ),
    '基本上，如果您能够填充了上面这几张数据表的数据，那么您就可以开始比较顺畅使用'
    '`qteasy`的大部分数据相关的功能了。': (
        'Once these key tables are filled, most qteasy data features work smoothly.'
    ),
    '基本信息表 -- 这类数据表包含了股票、基金、指数、期货、期权等各种金融产品的基本信息': (
        'Basics tables — stocks, funds, indices, futures, options, etc.'
    ),
    '基本信息表包括了股票、指数、基金、期货、期权等各种金融产品的基本信息。': (
        'Basics tables cover stocks, indices, funds, futures, options, etc.'
    ),
    '基金价格复权系数: `fund_adj_factor`': 'Fund adjustment factor: `fund_adj_factor`',
    '基金价格复权系数用于计算基金的前后复权价格。复权价格是指将基金的价格和成交量等指标调整为'
    '除权除息前的价格，以便于比较不同时间段的基金价格。复权因子是指除权除息后的价格与除权除息前的价格的比值。': (
        'Fund adjustment factors compute forward/backward adjusted prices and volumes for '
        'comparable historical analysis.'
    ),
    '基金份额: `fund_share`': 'Fund shares: `fund_share`',
    '基金份额表包含': 'Fund share table contains',
    '基金和指数技术指标数据：': 'Fund and index technical indicator data:',
    '基金基本信息: `fund_basic`': 'Fund basics: `fund_basic`',
    '基金基本信息表': 'Fund basics table',
    '基金基本信息表包含了所有基金的基本信息，包括基金代码、基金名称、管理人、托管人、投资类型、'
    '成立日期、到期日期、上市时间、发行日期、退市日期、发行份额、管理费、托管费、存续期、面值、'
    '起点金额、预期收益率、业绩比较基准、存续状态、投资风格、基金类型、受托人、日常申购起始日、'
    '日常赎回起始日、场内场外等信息。': (
        'Fund basics with code, name, manager, custodian, investment type, dates, fees, '
        'duration, par value, min investment, expected return, benchmark, status, style, '
        'type, trustee, subscription/redemption dates, on/off exchange flag, etc.'
    ),
    '基金经理: `fund_manager`': 'Fund manager: `fund_manager`',
    '基金经理表包含基金经理的详细信息，包括姓名、性别、出生年月和简历等信息': (
        'Fund manager details: name, gender, birth date, resume.'
    ),
    '基金行情数据表：': 'Fund quote tables:',
    '大宗交易: `block_trade`': 'Block trade: `block_trade`',
    '大宗交易表包含了股票的大宗交易信息，包括大宗交易日期、大宗交易价格、大宗交易量、'
    '大宗交易金额、买方营业部、卖方营业部等信息。': (
        'Block trade table with date, price, volume, amount, buyer/seller brokerage.'
    ),
    '如何从数据源中提取数据': 'Extracting data from DataSource',
    '如何从数据源中更有效地提取信息？': 'Extracting information from DataSource more effectively?',
    '如何批量下载数据并填充到数据源中？': 'How to batch-download and fill DataSource?',
    '如何操作数据源': 'Working with DataSource',
    '如果您是第一次使用`qteasy`，很可能数据源中的数据表都是空的，没有任何数据。'
    '通常这没有任何问题，因为`qteasy`的设计初衷就是极大地简化金融数据的获取和使用过程。': (
        'On first use, tables are often empty — by design, qteasy simplifies acquiring and '
        'using financial data.'
    ),
    '如果数据表中尚未填充数据，或者数据表中填充的数据不足以满足我们的需求，那么读取数据就会不成功。'
    '为了避免这种情况，我们需要向数据表中填充数据。': (
        'Reads fail if tables are empty or insufficient — fill tables first.'
    ),
    '如果数据表中已经填充了数据，那么现在就可以从中读取数据了。`DataSource`提供了`read_table_data()`方法，'
    '从数据源中直接读取某个数据表中的数据，同时，用户可以筛选数据的起止日期以及证券代码，'
    '同时不用考虑数据表的具体结构、存储方式、存储位置等具体的实现方式。': (
        'Once filled, use `read_table_data()` to read with date/code filters without '
        'worrying about storage details.'
    ),
    '富时100指数': 'FTSE 100',
    '富时中国A50指数 (富时A50)': 'FTSE China A50 Index (FTSE A50)',
    '将数据写入数据表之后，我们可以尝试一下从数据表中读取数据，现在我们已经可以读出刚才写入的数据了。': (
        'After writing, we can read back the data just inserted.'
    ),
    '巴西IBOVESPA指数': 'Brazil IBOVESPA Index',
    '市场技术面趋势数据：': 'Market technical trend data:',
    '德国DAX指数': 'DAX Index',
    '总结': 'Summary',
    '恒生AH股H指数': 'Hang Seng AH Premium Index (H-shares)',
    '恒生指数': 'Hang Seng Index',
    '恒生科技指数': 'Hang Seng Tech Index',
    '您可以非常容易地从网络数据提供商处获取最基本的数据。不过，虽然数据表中的数据可以是空的，'
    '但是有几张数据表却比其他的数据表更加重要，您应该优先将这几张数据表的数据填充完整，'
    '因为这几张数据表中的数据是很多其他数据表的基础，甚至是`qteasy`的运行基础：': (
        'Basic data is easy to download, but some tables are more critical — fill them first '
        'because others depend on them and on qteasy itself:'
    ),
    '我们除了可以向数据表中写入数据，从数据表中读取数据之外，当然也可以删除数据，不过请注意，'
    '在`qteasy`中操作`DataSource`删除数据时，您务必非常小心：因为`qteasy`不支持从数据表中删除部分数据，'
    '您只能删除整张数据表。': (
        'You can also drop entire tables — qteasy does not support partial deletes; be very '
        'careful.'
    ),
    '指数15分钟K线行情: `index_15min`': 'Index 15-min K-line: `index_15min`',
    '指数30分钟K线行情: `index_30min`': 'Index 30-min K-line: `index_30min`',
    '指数5分钟K线行情: `index_5min`': 'Index 5-min K-line: `index_5min`',
    '指数60分钟K线行情: `index_hourly`': 'Index 60-min K-line: `index_hourly`',
    '指数关键指标: `index_indicator`': 'Index key indicators: `index_indicator`',
    '指数关键指标数据表包含了指数的关键指标数据，例如市盈率、市净率、市销率、股息率、换手率等。': (
        'Index key indicators: P/E, P/B, P/S, dividend yield, turnover rate, etc.'
    ),
    '指数分钟K线行情: `index_1min`': 'Index 1-min K-line: `index_1min`',
    '指数周线行情: `index_weekly`': 'Index weekly K-line: `index_weekly`',
    '指数基本信息: `index_basic`': 'Index basics: `index_basic`',
    '指数基本信息表': 'Index basics table',
    '指数基本信息表包含了所有指数的基本信息，包括指数代码、指数名称、发布日期、退市日期等信息。': (
        'Index basics with code, name, publish/delisting dates.'
    ),
    '指数成份数据表包含了指数的成份股数据，包括成份股代码、成份股权重等信息。': (
        'Index constituents with code and weight.'
    ),
    '指数成分: `index_weight`': 'Index constituents: `index_weight`',
    '指数日线行情: `index_daily`': 'Index daily K-line: `index_daily`',
    '指数月度行情: `index_monthly`': 'Index monthly K-line: `index_monthly`',
    '指标信息表 -- 这类数据表包含了各种指标的信息，例如技术指标、基本面指标、宏观经济指标等': (
        'Indicator tables — technical, fundamental, macro indicators, etc.'
    ),
    '接下来我们可以将数据写入数据表，如果方法执行正确，它将返回写入数据表中的数据的行数，如下所示：': (
        'Next we write data; on success the method returns rows written:'
    ),
    '数据源中有哪些有用的金融数据？': 'What useful financial data is in DataSource?',
    '数据表的`SCHEMA`定义了数据表的所有字段和数据类型，`SCHEMA`各个字段的含义如下：': (
        'Table `SCHEMA` defines all columns and types; field meanings:'
    ),
    '数据表的`schema`信息可以通过`DataSource`对象的`get_table_info()`方法获取:': (
        'Table `schema` is available via `DataSource.get_table_info()`:'
    ),
    '数据表的定义': 'Table definitions',
    '日期: 格式YYYYMMDD': 'Date: format YYYYMMDD',
    '日期（格式YYYYMMDD）': 'Date (format YYYYMMDD)',
    '日经225指数': 'Nikkei 225',
    '是否交易：是：1，否：0': 'Is trading day: yes = 1, no = 0',
    '期权15分钟K线行情: `options_15min`': 'Option 15-min K-line: `options_15min`',
    '期权30分钟K线行情: `options_30min`': 'Option 30-min K-line: `options_30min`',
    '期权5分钟K线行情: `options_5min`': 'Option 5-min K-line: `options_5min`',
    '期权60分钟K线行情: `options_hourly`': 'Option 60-min K-line: `options_hourly`',
    '期权分钟K线行情: `options_1min`': 'Option 1-min K-line: `options_1min`',
    '期权基本信息: `opt_basic`': 'Option basics: `opt_basic`',
    '期权基本信息表包含了所有期权的基本信息，包括证券代码、交易市场、合约名称、合约单位、'
    '标准合约代码、合约类型、期权类型、行权方式、行权价格、结算月、到期日、挂牌基准价、'
    '开始交易日期、最后交易日期、最后行权日期、最后交割日期、报价单位、最小价格波幅等信息。': (
        'Option basics with security code, market, contract name/unit, standard code, '
        'contract/option type, exercise method/price, settlement month, expiry, listing '
        'reference price, trading/exercise/delivery dates, quote unit, min tick, etc.'
    ),
    '期权每日行情: `options_daily`': 'Option daily quotes: `options_daily`',
    '期权每日行情数据表字段说明：': 'Option daily quote field descriptions:',
    '期权行情数据表：': 'Option quote tables:',
    '期货15分钟K线行情: `future_15min`': 'Futures 15-min K-line: `future_15min`',
    '期货30分钟K线行情: `future_30min`': 'Futures 30-min K-line: `future_30min`',
    '期货5分钟K线行情: `future_5min`': 'Futures 5-min K-line: `future_5min`',
    '期货60分钟K线行情: `future_hourly`': 'Futures 60-min K-line: `future_hourly`',
    '期货分钟K线行情: `future_1min`': 'Futures 1-min K-line: `future_1min`',
    '期货合约映射表: `future_mapping`': 'Futures contract mapping: `future_mapping`',
    '期货合约映射表包含了所有期货合约的映射关系，包括连续合约代码、起始日期、期货合约代码等信息。': (
        'Futures mapping with continuous contract code, start date, contract code.'
    ),
    '期货周线行情: `future_weekly`': 'Futures weekly K-line: `future_weekly`',
    '期货和期权基本信息': 'Futures and option basics',
    '期货基本信息: `future_basic`': 'Futures basics: `future_basic`',
    '期货基本信息表包含了所有期货的基本信息，包括合约代码、交易标识、交易市场、中文简称、'
    '合约产品代码、合约乘数、交易计量单位、交易单位(每手)、报价单位、最小报价单位说明、'
    '交割方式说明、上市日期、最后交易日期、交割月份、最后交割日、交易时间说明等信息。': (
        'Futures basics with contract code, trading ID/market, short name, product code, '
        'multiplier, units, quote unit, min tick, delivery method, listing/last trading '
        'dates, delivery month/last delivery day, trading hours, etc.'
    ),
    '期货月线行情: `future_monthly`': 'Futures monthly K-line: `future_monthly`',
    '期货每日行情: `future_daily`': 'Futures daily quotes: `future_daily`',
    '期货行情数据表：': 'Futures quote tables:',
    '权重': 'Weight',
    '欧洲主要指数：英国富时100指数、德国DAX指数、法国CAC40指数': (
        'Major European indices: FTSE 100, DAX, CAC 40'
    ),
    '每股技术指标数据表包含了美股的各种技术指标数据，例如市盈率、市净率、市销率、股息率、换手率等。': (
        'US stock technical indicators: P/E, P/B, P/S, dividend yield, turnover rate, etc.'
    ),
    '沪深指数行情数据表：': 'CSI index quote tables:',
    '沪深股票停复牌和大宗交易：': 'A-share suspension/resumption and block trades:',
    '沪深股票技术指标数据：': 'A-share technical indicator data:',
    '沪深股通十大成交股: `hs_top10_stock`': 'Stock Connect top 10 trades: `hs_top10_stock`',
    '沪深股通十大成交股数据表包含了沪深股通的十大成交股数据，包括成交股票代码、成交股票名称、'
    '成交金额、净成交金额等信息。': (
        'Stock Connect top-10 table with code, name, turnover, net turnover.'
    ),
    '沪深股通资金流向: `hs_money_flow`': 'Stock Connect money flow: `hs_money_flow`',
    '沪深股通资金流向表包含了沪深股通的资金流向数据，包括港股通（沪）和港股通（深）的资金流向数据。': (
        'Stock Connect money flow for Shanghai and Shenzhen links.'
    ),
    '法国CAC40指数': 'CAC 40 Index',
    '涨跌停价格: `stock_limit`': 'Limit up/down prices: `stock_limit`',
    '涨跌停价格表包含了股票的涨停价和跌停价数据。': 'Limit up/down price table.',
    '港股交易日历: `hk_trade_calendar`': 'HK trading calendar: `hk_trade_calendar`',
    '港股交易日历表保存了香港股票交易所的交易日历': 'HKEX trading calendar table.',
    '港股基本信息: `hk_stock_basic`': 'HK stock basics: `hk_stock_basic`',
    '港股基本信息包括港交所股票的代码、名称、公司名称等基本信息': (
        'HK stock code, name, company name, etc.'
    ),
    '港股技术指标: `hk_stock_indicator`': 'HK stock indicators: `hk_stock_indicator`',
    '港股技术指标数据表包含了港股的各种技术指标数据，例如市盈率、市净率、市销率、股息率、换手率等。': (
        'HK technical indicators: P/E, P/B, P/S, dividend yield, turnover rate, etc.'
    ),
    '港股日线行情: `hk_stock_daily`': 'HK stock daily quotes: `hk_stock_daily`',
    '港股日线行情表包含了所有港股的日线行情数据，包括股票代码、交易日期、开盘价、最高价、最低价、'
    '收盘价、昨收盘价、涨跌额、涨跌幅、成交量、成交额等信息。': (
        'HK daily OHLCV with previous close, change amount/rate, volume, turnover.'
    ),
    '港股通十大成交股: `hk_top10_stock`': 'HK Stock Connect top 10: `hk_top10_stock`',
    '港股通十大成交股数据表包含了港股通的十大成交股数据，包括成交股票代码、成交股票名称、'
    '成交金额、净成交金额等信息。': (
        'HK Stock Connect top-10 with code, name, turnover, net turnover.'
    ),
    '澳大利亚标普200指数': 'S&P/ASX 200',
    '现金流量表是上市公司的财务报表之一，主要包括经营活动、投资活动、筹资活动等现金流量信息。': (
        'Cash flow statement — operating, investing, and financing cash flows.'
    ),
    '申万指数日线行情: `sw_index_daily`': 'SW index daily quotes: `sw_index_daily`',
    '申万指数日线行情表包含了申万指数的日线行情数据，包括指数代码、交易日期、开盘价、最高价、'
    '最低价、收盘价、涨跌幅、成交量、成交额等信息。': 'SW index daily OHLCV table.',
    '申万行业分类: `sw_industry_basic`': 'SW industry classification: `sw_industry_basic`',
    '申万行业分类指数表包含了所有申万行业分类指数的基本信息，包括指数代码、行业名称、父级代码、'
    '行业级别、行业代码、是否发布了指数、行业分类（SW申万）等信息。': (
        'SW industry index basics with code, industry name, parent code, level, industry '
        'code, index published flag, SW classification.'
    ),
    '申万行业分类明细: `sw_industry_detail`': (
        'SW industry classification detail: `sw_industry_detail`'
    ),
    '纳斯达克指数': 'NASDAQ Composite',
    '统一定义的金融历史数据表': 'Uniformly defined financial history tables',
    '罗素2000指数': 'Russell 2000 Index',
    '美国主要指数：道琼斯工业平均指数、标准普尔500指数、纳斯达克综合指数': (
        'Major US indices: Dow Jones, S&P 500, NASDAQ Composite'
    ),
    '美股交易日历: `us_trade_calendar`': 'US trading calendar: `us_trade_calendar`',
    '美股交易日历保存了美股的交易日历表': 'US trading calendar table.',
    '美股和港股基本信息': 'US and HK stock basics',
    '美股和港股行情数据': 'US and HK quote data',
    '美股基本信息: `us_stock_basic`': 'US stock basics: `us_stock_basic`',
    '美股基本信息包括美国股票的基本信息如名称、上市日期等': (
        'US stock name, listing date, etc.'
    ),
    '美股技术指标: `us_stock_indicator`': 'US stock indicators: `us_stock_indicator`',
    '美股日线行情: `us_stock_daily`': 'US stock daily quotes: `us_stock_daily`',
    '美股日线行情表包含了所有美股的日线行情数据，包括股票代码、交易日期、开盘价、最高价、最低价、'
    '收盘价、昨收盘价、涨跌额、涨跌幅、成交量、成交额、平均价、换手率、总市值、市盈率、市净率等信息。': (
        'US daily OHLCV with previous close, change, volume, turnover, average price, '
        'turnover rate, market cap, P/E, P/B, etc.'
    ),
    '股东交易: `stock_holder_trade`': 'Shareholder trades: `stock_holder_trade`',
    '股票15分钟K线行情: `stock_15min`': 'Stock 15-min K-line: `stock_15min`',
    '股票30分钟K线行情: `stock_30min`': 'Stock 30-min K-line: `stock_30min`',
    '股票5分钟K线行情: `stock_5min`': 'Stock 5-min K-line: `stock_5min`',
    '股票60分钟K线行情: `stock_hourly`': 'Stock 60-min K-line: `stock_hourly`',
    '股票价格复权系数: `stock_adj_factor`': 'Stock adjustment factor: `stock_adj_factor`',
    '股票价格复权系数用于计算股票的前后复权价格。复权价格是指将股票的价格和成交量等指标调整为'
    '除权除息前的价格，以便于比较不同时间段的股票价格。复权因子是指除权除息后的价格与除权除息前的价格的比值。': (
        'Stock adjustment factors compute forward/backward adjusted prices and volumes for '
        'comparable historical analysis.'
    ),
    '股票分钟K线行情: `stock_1min`': 'Stock 1-min K-line: `stock_1min`',
    '股票名称变更: `stock_names`': 'Stock name changes: `stock_names`',
    '股票名称变更表包含了所有股票名称变更的信息，包括股票代码、开始日期、证券名称、结束日期、'
    '公告日期、变更原因等信息。': (
        'Stock name change table with code, start/end dates, security name, announcement '
        'date, reason.'
    ),
    '股票周线行情: `stock_weekly`': 'Stock weekly K-line: `stock_weekly`',
    '股票基本信息: `stock_basic`': 'Stock basics: `stock_basic`',
    '股票基本信息表包含了所有上市股票的基本信息，包括股票代码、股票名称、上市日期、退市日期、'
    '所属行业、地域等信息。': (
        'Stock basics with code, name, listing/delisting dates, industry, region.'
    ),
    '股票基本信息表：': 'Stock basics table:',
    '股票成份和价格复权因子：': 'Stock constituents and price adjustment factors:',
    '股票技术指标: `stock_indicator`': 'Stock indicators: `stock_indicator`',
    '股票技术指标数据表包含了股票的各种技术指标数据，例如市盈率、市净率、市销率、股息率、换手率等。': (
        'Stock technical indicators: P/E, P/B, P/S, dividend yield, turnover rate, etc.'
    ),
    '股票技术指标表2: `stock_indicator2`': 'Stock indicators table 2: `stock_indicator2`',
    '股票技术指标表2包含了股票的各种技术指标数据，例如市盈率、市净率、市销率、股息率、换手率等。': (
        'Stock technical indicators (table 2): P/E, P/B, P/S, dividend yield, turnover rate, etc.'
    ),
    '股票日线行情: `stock_daily`': 'Stock daily K-line: `stock_daily`',
    '股票月线行情: `stock_monthly`': 'Stock monthly K-line: `stock_monthly`',
    '股票行情数据表：': 'Stock quote tables:',
    '至此，我们已经了解了`DataSource`对象，`qteasy`中金融历史数据管理的最重要的核心类的基本工作方式，'
    '了解了下面内容：': (
        "We now understand `DataSource`, qteasy's core class for financial history data "
        'management, including:'
    ),
    '融资融券交易明细: `margin_detail`': 'Margin trading detail: `margin_detail`',
    '融资融券交易明细数据表包含了融资融券交易的明细数据，包括证券代码、交易日期、融资余额、'
    '融资买入额、融资偿还额、融券余额、融券卖出量、融资融券余额、融券余量等信息。': (
        'Margin detail with security code, date, margin balance/buy/repay, securities '
        'lending balance/sell volume, total margin balance, lending volume.'
    ),
    '融资融券交易概况: `margin`': 'Margin trading summary: `margin`',
    '融资融券交易概况数据表包含了融资融券交易的概况数据，包括交易日期、交易所代码、融资余额、'
    '融资买入额、融资偿还额、融券余额、融券卖出量、融资融券余额、融券余量等信息。': (
        'Margin summary by trade date and exchange with balance, buy, repay, lending sell '
        'volume, etc.'
    ),
    '行情数据表 -- 这类数据表包含了股票、基金、指数各个不同频率的K线行情数据': (
        'Market data tables — OHLCV at various frequencies for stocks, funds, indices'
    ),
    '请注意，读出来的数据有许多列都是`NaN`值，这表明这些列没有写入数据，原因就是我们写入的`df`'
    '并不包含这些数据，因此读出的数据为`NaN`值。': (
        'Many columns read as `NaN` because the written `df` did not include those fields.'
    ),
    '请注意：': 'Note:',
    '财务指标表是上市公司的财务报表之一，主要包括每股指标、盈利能力指标、成长能力指标、'
    '偿债能力指标、现金流量指标等。': (
        'Financial indicators — per-share, profitability, growth, solvency, cash flow metrics.'
    ),
    '财务数据表 -- 这类数据表包含了上市公司的财务报表数据，包括资产负债表、利润表、现金流量表等': (
        'Financial statement tables — balance sheet, income statement, cash flow, etc.'
    ),
    '财报快报表是上市公司的财务报表之一，主要包括业绩快报、业绩预告、业绩预测等。': (
        'Earnings express reports — express, guidance, forecasts.'
    ),
    '财报预测表是上市公司的财务报表之一，主要包括业绩预告、业绩快报、业绩预测等。': (
        'Earnings forecast reports — guidance, express, forecasts.'
    ),
    '资产负债表是上市公司的财务报表之一，主要包括资产、负债、所有者权益等信息。': (
        "Balance sheet — assets, liabilities, shareholders' equity."
    ),
    '这些数据表的具体定义和数据类型，可以通过`get_table_info()`方法查看，或者通过本文档的下一章节查询。': (
        'See `get_table_info()` or the next chapter for table definitions and data types.'
    ),
    '这时候我们需要修改数据源的`allow_drop_table`属性，将其修改为`True`，这样就可以删除数据表了，'
    '请记住删除后将`allow_drop_table`改为`False`。': (
        'Set `allow_drop_table` to `True` to allow drops; set it back to `False` afterwards.'
    ),
    '这是因为`qteasy`的数据源被设计为高效地存储和读取数据，但它并不是一个通常的数据库，'
    '我们并不需要经常操作其中的数据，这个数据仓库的作用是为了存储巨量的数据，因此，'
    '它的重点在于保存和提取数据，而不是删除操作。': (
        'DataSource is optimized for storage and reads, not frequent deletes — it is a data '
        'warehouse, not a general database.'
    ),
    '这里介绍的仅仅是向数据表中手动添加数据的基本方法。`qteasy`还提供了全自动数据下载、数据清洗、'
    '数据填充等功能，可以帮助用户自动从网络数据源中下载数据，并将数据整理、清洗、更新到数据表中。'
    '这些功能将在后续章节中介绍。': (
        'This covers manual writes only; automatic download, cleaning, and refill are covered '
        'later.'
    ),
    '通过上面的方法，我们可以查看每一张数据表的具体定义和已经填充的数据信息。'
    '同样，通过`overview()`方法，我们可以检查所有的数据表，并汇总出整个数据源的整体信息：': (
        'Use the methods above to inspect each table; `overview()` summarizes the whole '
        'DataSource:'
    ),
    '道琼斯工业指数': 'Dow Jones Industrial Average',
    '除了上面提到的几张重要的数据表之外，数据源中还定义了大量的数据表，这些数据表包含了各种各样的'
    '金融数据，包括股票、指数、基金、期货、期权等各种金融产品的基本信息、日K线数据、财务数据、'
    '分红数据、业绩报表、宏观经济数据等等，主要分类如下：': (
        'Besides key tables, DataSource defines many more covering basics, daily K-line, '
        'financials, dividends, earnings reports, macro data, etc.:'
    ),
    '除了行情数据表之外，还包含了一些特殊的行情数据表，例如股票复权因子表、特殊指数的日K线行情表等。': (
        'Besides standard quote tables, special tables include adjustment factors and special '
        'index daily bars.'
    ),
    '韩国综合指数': 'Korea Composite Index (KOSPI)',
    '马来西亚指数': 'Malaysia Index',
    '龙虎榜交易明细: `top_list`': 'Top list trade detail: `top_list`',
    '龙虎榜交易明细数据表包含了龙虎榜的交易明细数据，包括证券代码、交易日期、名称、收盘价、涨跌幅、'
    '换手率、总成交额、龙虎榜卖出额、龙虎榜买入额、龙虎榜成交额、龙虎榜净买入额、龙虎榜净买额占比、'
    '龙虎榜成交额占比、当日流通市值、上榜理由等信息。': (
        'Top list detail with security code, date, name, close, change (%), turnover rate, '
        'total turnover, top-list buy/sell/turnover/net buy and shares, float market cap, '
        'listing reason.'
    ),
    '龙虎榜机构交易明细: `top_inst`': 'Top list institutional detail: `top_inst`',
    '龙虎榜机构交易明细数据表包含了龙虎榜的机构交易明细数据，包括证券代码、交易日期、机构名称、'
    '买入额、卖出额、净买入额、净买额占比、买入占总成交比例、卖出占总成交比例、净买占总成交比例、'
    '上榜理由等信息。': (
        'Top list institutional detail with security code, date, institution name, buy/sell/'
        'net amounts and shares of turnover, listing reason.'
    ),
}


def main() -> None:
    """生成 manage_data_docs_en.json。"""
    non_schema = json.loads((SCRIPTS.parent / 'scripts/manage_data_missing_after_fill.json').read_text(encoding='utf-8'))
    # rebuild non_schema list
    import sys
    sys.path.insert(0, str(SCRIPTS.parent.parent))
    from qteasy.datatables import TABLE_SCHEMA  # noqa: WPS433

    remarks = set()
    for schema in TABLE_SCHEMA.values():
        remarks.update(schema.get('remarks', []))
    missing = json.loads((SCRIPTS / 'manage_data_missing_after_fill.json').read_text(encoding='utf-8'))
    non_schema_list = [m for m in missing if m not in remarks]

    seeds = _load_seeds()
    need = [m for m in non_schema_list if m not in seeds]

    out: dict[str, str] = {}
    rules = (
        translate_table_use,
        translate_kline,
        translate_lowfreq_kline,
        translate_hourly_table,
        translate_daily_table,
        translate_weekly_monthly_kline,
        translate_futures_ohlcv,
    )
    missing_final: list[str] = []
    for msgid in need:
        if msgid in DOCS:
            out[msgid] = DOCS[msgid]
            continue
        translated = None
        for fn in rules:
            translated = fn(msgid)
            if translated:
                break
        if translated:
            out[msgid] = translated
        else:
            missing_final.append(msgid)

    path = SCRIPTS / 'manage_data_docs_en.json'
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {path.name}: {len(out)} keys, missing: {len(missing_final)}')
    for m in missing_final[:10]:
        print('  MISSING:', m[:120])


if __name__ == '__main__':
    main()
