# coding=utf-8
"""de .po 填充：技术条目复制 msgid/en，正文由 apply_de_pivot 处理。"""

from __future__ import annotations

import re
from pathlib import Path

import polib

DE_ROOT = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'de' / 'LC_MESSAGES'
EN_ROOT = Path(__file__).resolve().parent.parent / 'source' / 'locale' / 'en' / 'LC_MESSAGES'

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')


def is_technical(s: str, *, msgid: str = '') -> bool:
    """判断字符串是否应原样进入德文 msgstr（代码、字段名、短标签）。

    当 ``msgid`` 含中文而 ``s`` 为英文 pivot 时，仅极短标签可原样复制，正文须译为德语。
    """
    if not s or not s.strip():
        return False
    if CHINESE_RE.search(s):
        if s.count('`') >= 2 and len(CHINESE_RE.findall(s)) <= 2:
            return True
        return False
    if msgid and CHINESE_RE.search(msgid):
        stripped = s.strip()
        if len(stripped) <= 35 and stripped.count(' ') <= 4 and '. ' not in stripped:
            return True
        if '`' in stripped and len(stripped) < 60 and '. ' not in stripped:
            return True
        return False
    if len(s) <= 60 and s.count('. ') < 2:
        return True
    if '`' in s and len(s) < 120:
        return True
    return False


def localize_links(text: str) -> str:
    """RTD 内链改为德语路径。"""
    return (
        text.replace('https://qteasy.readthedocs.io/zh-cn/latest/', 'https://qteasy.readthedocs.io/de/latest/')
        .replace('https://qteasy.readthedocs.io/zh/latest/', 'https://qteasy.readthedocs.io/de/latest/')
        .replace('https://qteasy.readthedocs.io/en/latest/', 'https://qteasy.readthedocs.io/de/latest/')
    )


def apply_file(de_path: Path, en_path: Path | None) -> tuple[int, int, int]:
    """填充单个 de po 的技术条目。

    Returns
    -------
    tuple[int, int, int]
        (filled_msgid, filled_en, cleared_fuzzy)
    """
    po = polib.pofile(str(de_path))
    en_map: dict[str, str] = {}
    if en_path and en_path.exists():
        en_po = polib.pofile(str(en_path))
        en_map = {e.msgid: e.msgstr for e in en_po if e.msgid and not e.obsolete}

    filled_msgid = filled_en = cleared_fuzzy = 0
    for entry in po:
        if entry.obsolete or not entry.msgid:
            continue
        if entry.msgstr and 'fuzzy' not in entry.flags:
            continue
        en_str = en_map.get(entry.msgid, '')
        if entry.msgstr and 'fuzzy' in entry.flags:
            entry.msgstr = localize_links(entry.msgstr)
            entry.flags.remove('fuzzy')
            cleared_fuzzy += 1
            continue
        if is_technical(entry.msgid, msgid=entry.msgid):
            entry.msgstr = localize_links(entry.msgid)
            filled_msgid += 1
        elif en_str and is_technical(en_str, msgid=entry.msgid):
            entry.msgstr = localize_links(en_str)
            filled_en += 1

    po.metadata['PO-Revision-Date'] = '2026-05-23 22:00+0800'
    po.metadata['Last-Translator'] = 'Jackie PENG'
    po.save(str(de_path))
    text = de_path.read_text(encoding='utf-8')
    if '\n#, fuzzy\n' in text:
        de_path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
    return filled_msgid, filled_en, cleared_fuzzy
