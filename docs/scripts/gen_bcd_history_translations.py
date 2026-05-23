# coding=utf-8
"""生成 translations_bcd_history.py（一次性脚本）。"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'translations_bcd_history.py'

HISTORICAL_DATA_TYPES: dict[str, str] = {}
GET_HISTORY_DATA: dict[str, str] = {}


def _load_pairs(name: str) -> dict[str, str]:
    """从同目录 JSON 加载 msgid->msgstr。"""
    path = Path(__file__).resolve().parent / name
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> None:
    """写入 translations_bcd_history.py。"""
    hdt = _load_pairs('bcd_historical_data_types_en.json')
    ghd = _load_pairs('bcd_get_history_data_en.json')
    lines = [
        '# coding=utf-8',
        '"""references 历史数据章节翻译条目（msgid 精确匹配）。"""',
        '',
        f'HISTORICAL_DATA_TYPES = {repr(hdt)}',
        '',
        f'GET_HISTORY_DATA = {repr(ghd)}',
        '',
    ]
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'wrote {OUT} ({len(hdt)} + {len(ghd)} entries)')


if __name__ == '__main__':
    main()
