# coding=utf-8
"""构建 bcd_*_en.json 翻译映射文件。"""

from __future__ import annotations

import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

HDT_EN = [
    'Data types are a core qteasy concept: information used in a trading strategy, such as historical market data or macroeconomic series. Information is not the same as raw data. In older versions, `qteasy` equated data types with DataSource table columns, which was inadequate because:',
    'Some raw fields alone carry little meaning and must be combined with other data',
    'Some fields encode multiple kinds of information extractable from different angles',
    'The meaning of information is dynamic—the same data can be interpreted differently',
    'Equating information with data is careless: logically, data is only a carrier of information.',
    'In the new qteasy definition, a data type is information extracted from complex stored data. Some can be read directly from tables, for example:',
    'Stock open price, read directly from the price table',
    'Some data must be assembled from multiple tables, for example:',
    'Adjusted stock price requires price data, adjustment factors, and computation',
    'Sometimes one column yields different information, for example:',
    'Previous close and daily change are different information from the same price table',
    'qteasy redefines data types as the information we need, with simple APIs to extract it quickly, support custom types, and chart, compare, and analyze results.',
    'Each data type is implemented as a class for easy customization. qteasy also ships extensive built-in types covering many tables so downloaded data is fully usable.',
    'Logically, defining a data type requires:',
    'Data source: which tables and columns provide this information?',
    'Acquisition: how is the information extracted?',
    'Many built-in types must be defined simply and parametrically; the class model stays small enough for parameter-driven definitions.',
    'Usage and output — data types expose two unified APIs:',
    'API1: `data_type.get(start, end, frequency)` — symbol-agnostic interval data at one frequency, Series-like output.',
    'API2: `data_type.get(shares, start, end, frequency)` — per-share interval data at one frequency.',
    'A third API: `data_type.get(shares, start, end, frequency, **kwargs)`',
    'Built-in and custom types share the same return format.',
    'Acquisition categories depend on how data is read and produced—direct reads vs composition tables, multi-table queries such as adjusted prices, etc. Distinct patterns need distinct handling.',
    'Ignoring pure multi-field math types (except adjusted price), acquisition types include:',
    '`acquisition_type` controls symbolised vs un-symbolised output and Period vs TimeStamp layouts:',
    'Supported output layouts are fixed at data-type definition time',
    '`basics` — time-independent reference data; kwargs: one table and column',
    '`direct` — read one table/column over an interval and frequency',
    '`adjustment` — read A and B from two tables and adjust A with B (e.g. adjusted price)',
    '`relations` — relational output between A and B (eq/ne/gt/or/nor, etc.)',
    '`operation` — arithmetic between A and B (+/-/*//)',
    '`event_status` — fill status over event impact windows (suspension, rename, etc.)',
    '`event_multi_stat` — multiple statuses over event windows (e.g. management roster)',
    '`event_signal` — signals at event dates (limit up/down, listings, dividends, etc.)',
    '`composition` — filter composition tables and pivot rows/columns; plus special procedural types',
    '`compound` — combine multiple fields at one timestamp (e.g. financial statements)',
    'Symbolised Period data: DataFrame-like, rows = time periods, columns = share codes',
    'Un-symbolised Period data: Series-like, rows = time periods, single column',
    'Class design is parametric: parameters fix acquisition method and target tables',
    'One public method dispatches by acquisition type, reads target tables, cleans, and returns data.',
    'Type metadata can encode field semantics, e.g. `open` usable in the latest cycle but `close` not',
    'A hook method may be overridden for custom acquisition logic',
    'Many built-in types are created via a mapping table from type IDs to key parameters.',
    '`DATA_TYPE_MAP` maps each data type ID to its storage table (unique ID and location per type).',
    'Data table mapping columns: `htype_name` (key): data type name',
    '`freq` (key): available frequency — min/d/w/m/q',
    '`asset_type` (key): E, IDX, FT, FD, OPT, THS, SW, etc.',
    '`description`: detailed description for search',
    '`acquisition_type`: acquisition method',
    '`table_name`: storage table name',
    '`column`: column name in the table',
]

GHD_EN = [
    'In qteasy 2.x, `qt.get_history_data()` is recommended to return a `HistoryPanel` directly:',
    '`HistoryPanel` is a 3-D container with axes:',
    '**axis 0 (shares)**: instrument list, e.g. stock or index codes',
    '**axis 1 (hdates)**: time axis — one row per timestamp',
    '**axis 2 (htypes)**: history data types such as `open`, `high`, `low`, `close`, `vol`',
    "Slicing with `hp[...]` returns a **sub-`HistoryPanel`** with correct axis labels, not a raw `ndarray`. Use `hp['close'].values` or `hp['close'].to_numpy(copy=True)` for arrays; see `hp.subpanel(..., copy=True)` for named slices and copy behavior.",
    'For research masks and APIs with `mask=`, use `hp.where(condition)` — a bool array matching `hp.values` without mutating `hp`. See [HistoryPanel API](../api/HistoryPanel.rst) and [HistoryPanel tutorial](../tutorials/2.5-historypanel-data-analysis.md).',
    'Since **2.2.8**: read-only column attributes (`hp.close` ≡ `hp[\'close\']`); comparisons (`hp.close > 100`) yield numpy bool arrays for `hp.where(...)`; time filtering via `hp.loc[key]` (≡ `hp[:, :, key]`). See API “column access, comparisons, and loc” and tutorial §6.1.',
    'Strategies and visualization share one structured object without repeated conversions.',
    'Adapt existing `DataFrame` or dict data with `qt.dataframe_to_hp()` and reuse the same API.',
    'From HistoryPanel to Visualization',
    '`HistoryPanel.plot()` picks chart types (candlestick, volume, MACD, line) from existing htypes and supports multi-instrument comparison:',
    'HistoryPanel.plot Interactive Visualization (Plotly)',
    '`hp.plot(interactive=True)` uses Plotly with zoom, pan, and hover. In notebooks, FigureWidget (needs `ipywidgets` and `anywidget`) is preferred; otherwise HTML fallback. Set `plotly_backend_app=\'auto\'|\'FigureWidget\'|\'html\' explicitly if needed.',
    'Dependencies and Installation',
    '**Basic interactivity (Plotly Figure)**:',
    '**Full notebook interactivity (FigureWidget + callbacks)**:',
    'If Plotly is missing, `interactive=True` raises an English error (e.g. “requires plotly”) so missing dependencies fail early instead of producing a non-interactive empty chart.',
    '`plotly_backend_app`: output mode and fallback',
    '`plotly_backend_app` applies only when `interactive=True`:',
    "`plotly_backend_app='auto'`: prefer FigureWidget in notebooks; else HTML wrapper; may return raw Plotly Figure in scripts.",
    "`plotly_backend_app='FigureWidget'`: force FigureWidget; error if not in notebook or deps missing.",
    "`plotly_backend_app='html'`: force HTML wrapper; error if not in notebook.",
    'Key Interactive Features (User View)',
    '**Zoom/pan consistency**: HTML and FigureWidget share x-axis constraints — minimum visible bars, pan back into data range when out of bounds.',
    '**Top OHLC summary**: shown when full OHLC candlestick main chart exists; starts at last bar, updates on click. Hidden for line-only charts (e.g. close only).',
    "`layout='overlay'` for two instruments: clicking a bar switches primary/secondary; opacity and line width update; `highlight` follows the primary instrument.",
    '**Selection crosshair**: shown on the main price chart after click; syncs on zoom/pan; hidden when the selected bar scrolls out of view.',
    'Examples: Two Common Interactive Calls',
    '**Example 1: single-instrument interactive candlestick**',
    '**Example 2: two-instrument overlay + highlight**',
    'Visualization follows “**plot what exists**”:',
    'Only columns already in the HistoryPanel — no new indicators computed in the plot layer',
    'Candlestick, volume, or MACD depends solely on corresponding htypes present',
    'Typical htype-to-chart mapping:',
    'Chart type',
    'Example htypes required',
    'Candlestick',
    'Volume',
    'Line chart',
    'Any 1-D series (e.g. `close`, `pe`)',
    'For MA/Bollinger/MACD, compute on HistoryPanel (`hp.kline.ma()`, `hp.kline.bbands()`, `hp.kline.macd()`), append columns, then `hp.plot()`.',
    'Relationship between `qt.candle` and HistoryPanel',
    '`qt.candle()` is a high-level shortcut to plot one instrument’s candlestick in one line:',
    'Parse `stock`, `start`, `end`, fetch from local DataSource',
    'Adapt prices to a single-instrument HistoryPanel',
    'Append requested indicators (MA, Bollinger, MACD) on HistoryPanel',
    'Call `hp.plot(...)` to render',
    'Keep existing `qt.candle` calls or control plotting directly on HistoryPanel.',
    'Common usage examples:',
    '`plot_type` values:',
    "`'candle'` / `'c'`: OHLC candlestick",
    "`'ohlc'` / `'o'`: lightweight alias near `'candle'`",
    "`'line'` / `'l'`: 1-D price line (usually `close`)",
    "`'none'` / `'n'`: **data only**, return `DataFrame` for external plotting",
    "Renko (`'renko'` / `'r'`) is no longer built in; use a dedicated TA/charting library.",
    '`qt.refill_data_source()` `tables` selects tables to refill — by name or by group:',
    '`cal`: trading calendars per exchange',
    '`basics`: basic info tables (stocks, funds, indices, futures, options)',
    '`adj`: adjustment factor tables for adjusted prices',
    '`data`: historical OHLCV tables (daily/weekly/monthly)',
    '`events`: corporate/event tables (renames, manager changes, fund shares, etc.)',
    '`report`: financial statements and reports',
    '`comp`: index composition and weights',
    '`all`: all tables — large download; refill in batches',
    'After download, use `qt.get_history_data()`; multiple shares return a `dict` keyed by code.',
    'Example: `stock_daily` ends at 2022-03-22 with ~12.1M rows',
    'Use `qt.refill_data_source()` to refill `stock_daily` from Mar 2022 through Oct 2022',
    'Refill shows progress, row counts, and elapsed time. Large jobs are slow; parallel threads speed downloads but may hit Tushare rate limits.',
    'After refill, `stock_daily` grows to ~12.8M rows (+700k) through 2022-10-31.',
    'Local Data Access and Visualization',
    'Once data is local, fetch it easily; OHLCV can be visualized as candlesticks or lines',
    'Basic security information',
    '`get_basic_info(code_or_name)` accepts code or name; global match lists all hits unless `asset_type` narrows scope; `match_full_name=True` fuzzy-matches full names',
    'Alias of `get_basic_info()`',
    'Filter stock codes',
    'Filter stocks by listing date, region, industry, size, index membership, etc., and print info',
    'Same filters, return full stock codes',
    'Extract historical financial data',
    'Reads from default `QT_DATA_SOURCE` by data type, codes, date range, and frequency; returns `DataFrame` or `HistoryPanel` objects in a dict keyed by code or type',
    'OHLCV visualization',
    'Fetch local price data and render a full dynamic advanced candlestick chart',
    'Example:',
    'Look up basic security information',
    'With data in `DataSource`, `qt.get_basic_info()` finds securities by six-digit code or name (fuzzy or wildcard search supported)',
    'Example: lookup by six-digit code',
    'Or search by name — fuzzy match may return multiple hits, e.g.:',
    'Wildcard search by name is supported',
    'By default full names are not matched; set full-name matching when needed, e.g.:',
    'Output:',
    '`qt.filter_stocks` filters stocks by criteria, e.g.:',
    'Result is a `dict` keyed by stock code; each value is a `DataFrame` of requested types',
    'Multiple shares and types at different frequencies are supported',
    'Local OHLCV can be shown as candlesticks — examples below',
    'Historical price visualization',
    'Dynamic candlesticks via `qt.candle()` without manual DataSource reads',
    '`qt.candle()` accepts start/end, frequency, adjustment, MA periods, MACD params — e.g. 60-minute post-adjusted chart:',
    '`qt.candle()` accepts names with fuzzy/wildcard lookup, e.g.:',
    'More candlestick examples: stocks, funds, indices, frequencies, MAs, chart types',
]


def _build(missing_name: str, en_list: list[str], out_name: str) -> None:
    """按顺序将英文列表与 missing JSON 对齐并写出映射。"""
    missing = json.loads((SCRIPTS / missing_name).read_text(encoding='utf-8'))
    if len(missing) != len(en_list):
        raise ValueError(f'{missing_name}: {len(missing)} msgids vs {len(en_list)} translations')
    mapping = dict(zip(missing, en_list))
    out = SCRIPTS / out_name
    out.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {out.name}: {len(mapping)} entries')


def main() -> None:
    """入口。"""
    _build(
        'references_2-historical_data_types_missing.json',
        HDT_EN,
        'bcd_historical_data_types_en.json',
    )
    _build(
        'references_2-get-history-data_missing.json',
        GHD_EN,
        'bcd_get_history_data_en.json',
    )


if __name__ == '__main__':
    main()
