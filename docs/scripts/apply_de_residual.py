# coding=utf-8
"""补译 de 中与 en 相同但应为德语的残留条目（短词、指数名等）。"""

from __future__ import annotations

import sys
from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'de' / 'LC_MESSAGES'

# msgid -> msgstr（德语）
RESIDUAL: dict[str, str] = {
    '生成器': 'Generator',
    '维度': 'Dimension',
    '`Broker`：提交、取消、回报、连接语义': (
        '`Broker`: Übermittlung, Stornierung, Ausführungsmeldungen, Verbindungssemantik'
    ),
    '回测': 'Backtest',
    '**空**': '**leer**',
    'HistoryPanel（历史数据面板）': 'HistoryPanel (historisches Datenpanel)',
    '地域': 'Region',
    '姓名': 'Name',
    '岗位': 'Position',
    '名称': 'Name',
    '代码': 'Code',
    '管理人': 'Fondsverwalter',
    '拼音': 'Pinyin',
    '富时中国A50指数 (富时A50)': 'FTSE China A50 Index (FTSE A50)',
    '恒生科技指数': 'Hang Seng Tech Index',
    '道琼斯工业指数': 'Dow Jones Industrial Average',
    '纳斯达克指数': 'NASDAQ Composite',
    '富时100指数': 'FTSE 100',
    '日经225指数': 'Nikkei 225',
    '韩国综合指数': 'KOSPI Composite',
    '澳大利亚标普200指数': 'S&P/ASX 200',
    'STOXX欧洲50指数': 'STOXX Europe 50',
    '振幅': 'Schwankungsbreite',
    '港股通（上海）': 'Stock Connect (Shanghai)',
    '港股通（深圳）': 'Stock Connect (Shenzhen)',
    '息税前利润': 'EBIT',
    '息税折旧摊销前利润': 'EBITDA',
    '上海银行间行业拆放利率(SHIBOR): `shibor`': (
        'Shanghaier Interbank-Angebotszins (SHIBOR): `shibor`'
    ),
    '伦敦银行间行业拆放利率(LIBOR): `libor`': (
        'Londoner Interbank-Angebotszins (LIBOR): `libor`'
    ),
    '香港银行间行业拆放利率(HIBOR): `hibor`': (
        'Hongkonger Interbank-Angebotszins (HIBOR): `hibor`'
    ),
    '温州民间借贷指数: `wz_index`': 'Wenzhou-Index für privates Lending: `wz_index`',
    '参数名': 'Parametername',
    '中': 'Mitte',
    '`submit_trade_order` 前': 'Vor `submit_trade_order`',
    'HistoryPanel 与 `get_history_data`': 'HistoryPanel und `get_history_data`',
    '元素': 'Element',
    '策略名称': 'Strategiename',
    '5. 跳转导航': '5. Navigation',
    '插图': 'Abbildung',
}


def main() -> int:
    """应用到所有 de po 文件。"""
    filled = 0
    for po_path in sorted(ROOT.rglob('*.po')):
        if po_path.name.endswith('~'):
            continue
        po = polib.pofile(str(po_path))
        changed = False
        for entry in po:
            if entry.obsolete or not entry.msgid:
                continue
            if entry.msgid in RESIDUAL:
                entry.msgstr = RESIDUAL[entry.msgid]
                if 'fuzzy' in entry.flags:
                    entry.flags.remove('fuzzy')
                filled += 1
                changed = True
        if changed:
            po.metadata['PO-Revision-Date'] = '2026-05-23 22:30+0800'
            po.save(str(po_path))
    print(f'apply_de_residual: filled {filled} entries')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
