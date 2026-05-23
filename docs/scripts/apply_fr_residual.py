# coding=utf-8
"""补译 fr 中与 en 相同但应为法语的残留条目（短词、指数名等）。"""

from __future__ import annotations

import sys
from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'fr' / 'LC_MESSAGES'

# msgid -> msgstr（法语）
RESIDUAL: dict[str, str] = {
    '贡献代码': 'Contribuer au code',
    '备注': 'Remarque',
    '说明：': 'Note :',
    '说明': 'Remarque',
    'FT   : 期货': 'FT   : contrats à terme',
    '回测': 'Backtest',
    '生成器': 'Générateur',
    '维度': 'Dimension',
    '参数名': 'Nom du paramètre',
    '中': 'Milieu',
    '元素': 'Élément',
    '策略名称': 'Nom de la stratégie',
    '5. 跳转导航': '5. Navigation',
    '插图': 'Figure',
    '地域': 'Région',
    '姓名': 'Nom',
    '岗位': 'Poste',
    '名称': 'Nom',
    '代码': 'Code',
    '管理人': 'Gestionnaire',
    '拼音': 'Pinyin',
    '振幅': 'Amplitude',
    '未完待续': 'À suivre',
    'Properties': 'Propriétés',
    '方向': 'Direction',
    '概念': 'Concept',
    '常见问题': 'FAQ',
    '**注意**：': '**Remarque** :',
    '富时中国A50指数 (富时A50)': 'Indice FTSE China A50 (FTSE A50)',
    '恒生科技指数': 'Hang Seng Tech Index',
    '道琼斯工业指数': 'Dow Jones Industrial Average',
    '纳斯达克指数': 'NASDAQ Composite',
    '富时100指数': 'FTSE 100',
    '日经225指数': 'Nikkei 225',
    '韩国综合指数': 'KOSPI Composite',
    '澳大利亚标普200指数': 'S&P/ASX 200',
    'STOXX欧洲50指数': 'STOXX Europe 50',
    '港股通（上海）': 'Stock Connect (Shanghai)',
    '港股通（深圳）': 'Stock Connect (Shenzhen)',
    '息税前利润': 'EBIT',
    '息税折旧摊销前利润': 'EBITDA',
    '**空**': '**vide**',
    'HistoryPanel（历史数据面板）': 'HistoryPanel (panneau de données historiques)',
}


def main() -> int:
    """应用到所有 fr po 文件。"""
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
            po.metadata['PO-Revision-Date'] = '2026-05-24 12:00+0800'
            po.save(str(po_path))
    print(f'apply_fr_residual: filled {filled} entries')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
