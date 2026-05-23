# coding=utf-8
"""Phase 1 批次 E：应用 manage_data 英文翻译。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polib

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from fill_en_po import apply_po
from strip_po_obsolete import strip_file

ROOT = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'en' / 'LC_MESSAGES'
MANAGE_DATA = ROOT / 'manage_data'

PO_FILES = [
    'manage_data/01. overview.po',
    'manage_data/02. datatypes.po',
    'manage_data/02.5. historypanel.po',
    'manage_data/02.6. historypanel_visual.po',
    'manage_data/03. datasource.po',
    'manage_data/04. data_tables_10.po',
    'manage_data/05. data_tables_20.po',
    'manage_data/06. data_tables_30.po',
    'manage_data/07. data_tables_35.po',
    'manage_data/08. data_tables_40.po',
    'manage_data/09. data_tables_50.po',
    'manage_data/10. data_channels.po',
]


def load_translations() -> dict[str, str]:
    """加载 msgid→msgstr 主翻译表。"""
    path = _SCRIPTS / 'manage_data_en_translations.json'
    return json.loads(path.read_text(encoding='utf-8'))


def apply_translations(rel_path: str, mapping: dict[str, str]) -> tuple[int, int]:
    """将 mapping 应用到 po 文件。

    Returns
    -------
    tuple[int, int]
        (filled, remaining)
    """
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
    po.metadata['PO-Revision-Date'] = '2026-05-23 18:00+0800'
    po.metadata['Last-Translator'] = 'Jackie PENG'
    po.save(str(path))
    text = path.read_text(encoding='utf-8')
    if '\n#, fuzzy\n' in text:
        path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
    remaining = sum(1 for e in po if e.msgid and not e.msgstr and not e.obsolete)
    return filled, remaining


def main() -> int:
    """入口。"""
    mapping = load_translations()

    # 1. 移除 #~ 过时条目
    for po_path in sorted(MANAGE_DATA.glob('*.po')):
        if po_path.name.endswith('~'):
            continue
        n = strip_file(po_path)
        if n:
            print(f'strip: {po_path.name}: {n} blocks')

    # 2. 复制英文/代码 msgid
    for rel in PO_FILES:
        apply_po(ROOT / rel, mapping)

    # 3. 应用中文译文
    total_filled = 0
    for rel in PO_FILES:
        filled, remaining = apply_translations(rel, mapping)
        print(f'{rel}: dict={filled}, remaining={remaining}')
        total_filled += filled

    print(f'total dict filled this pass: {total_filled}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
