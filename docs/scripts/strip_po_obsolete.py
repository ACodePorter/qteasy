# coding=utf-8
"""从 .po 文件中移除 #~ 过时条目，避免 msgfmt 重复 msgid 报错。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

OBS_BLOCK = re.compile(
    r'\n#~[^\n]*(?:\n(?!#~|\nmsgid)[^\n]*)*',
    re.MULTILINE,
)


def strip_file(path: Path) -> int:
    """移除单个 po 文件中的过时块。

    Returns
    -------
    int
        移除的块数量
    """
    text = path.read_text(encoding='utf-8')
    blocks = OBS_BLOCK.findall(text)
    if not blocks:
        return 0
    new_text = OBS_BLOCK.sub('', text)
    path.write_text(new_text, encoding='utf-8')
    return len(blocks)


def main(argv: list[str]) -> int:
    """入口：可传入相对 LC_MESSAGES 的路径，默认扫描 manage_data。"""
    root = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'en' / 'LC_MESSAGES'
    if len(argv) > 1:
        paths = [root / p for p in argv[1:]]
    else:
        paths = sorted((root / 'manage_data').glob('*.po'))
    total = 0
    for path in paths:
        if path.name.endswith('~'):
            continue
        n = strip_file(path)
        if n:
            print(f'{path.relative_to(root)}: removed {n} obsolete blocks')
            total += n
    print(f'total removed: {total}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
