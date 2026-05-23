# coding=utf-8
"""批量填充 en .po 中空 msgstr：代码/英文 msgid 直接复制，其余使用传入的翻译表。"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List

import polib

LOCALE_EN = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'en' / 'LC_MESSAGES'

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')


def is_copy_as_is(msgid: str) -> bool:
    """判断 msgid 是否可直接作为英文 msgstr（代码、API 名、纯英文）。"""
    if not msgid.strip():
        return False
    if not CHINESE_RE.search(msgid):
        return True
    # 以反引号为主的混合行（中文说明很少）
    if msgid.count('`') >= 2 and len(CHINESE_RE.findall(msgid)) <= 2:
        return True
    return False


def apply_po(path: Path, extra: Dict[str, str] | None = None) -> tuple[int, int, int]:
    """填充单个 po 文件。

    Returns
    -------
    tuple[int, int, int]
        (filled_copy, filled_dict, cleared_fuzzy)
    """
    extra = extra or {}
    po = polib.pofile(str(path))
    filled_copy = filled_dict = cleared_fuzzy = 0

    if 'fuzzy' in po.metadata:
        del po.metadata['fuzzy']

    for entry in po:
        if entry.obsolete or not entry.msgid:
            continue
        if entry.msgstr and 'fuzzy' not in entry.flags:
            continue
        if entry.msgid in extra:
            entry.msgstr = extra[entry.msgid]
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
            filled_dict += 1
        elif not entry.msgstr and is_copy_as_is(entry.msgid):
            entry.msgstr = entry.msgid
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
            filled_copy += 1
        elif entry.msgstr and 'fuzzy' in entry.flags:
            entry.flags.remove('fuzzy')
            cleared_fuzzy += 1

    po.metadata['PO-Revision-Date'] = '2026-05-23 15:00+0800'
    po.metadata['Last-Translator'] = 'Jackie PENG'
    po.save(str(path))
    return filled_copy, filled_dict, cleared_fuzzy


def stats(path: Path) -> str:
    """返回 msgfmt 风格统计摘要。"""
    import subprocess
    r = subprocess.run(
        ['msgfmt', '--statistics', '-o', '/dev/null', str(path)],
        capture_output=True,
        text=True,
    )
    return r.stderr.strip()


def process_files(rel_paths: Iterable[str], extra_map: Dict[str, Dict[str, str]] | None = None) -> None:
    """处理多个相对 LC_MESSAGES 的 po 路径。"""
    extra_map = extra_map or {}
    for rel in rel_paths:
        path = LOCALE_EN / rel
        fc, fd, cf = apply_po(path, extra_map.get(rel, {}))
        print(f'{rel}: copy={fc} dict={fd} unfuzzy={cf} | {stats(path)}')
