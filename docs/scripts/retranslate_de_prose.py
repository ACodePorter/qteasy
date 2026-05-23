# coding=utf-8
"""将误复制为英文的 de 条目重新译为德语（中文 msgid + de 与 en 相同）。"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import polib

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from apply_de_pivot import (
    CACHE_PATH,
    build_cache,
    load_cache,
    localize_links,
    save_cache,
    translate_en_to_de,
    translate_zh_to_de,
)
from fill_de_po import DE_ROOT, EN_ROOT, is_technical

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')


def needs_retranslate(msgid: str, en: str, de: str) -> bool:
    """是否应将英文 pivot 重新译为德语。"""
    if not en or not de:
        return False
    if de.strip() != en.strip():
        return False
    if not CHINESE_RE.search(msgid):
        return False
    if is_technical(en, msgid=msgid):
        return False
    return True


def collect_retranslate_keys() -> tuple[list[str], list[str]]:
    """收集需重译的 en 与 zh 键。"""
    en_keys: list[str] = []
    zh_keys: list[str] = []
    for de_path in sorted(DE_ROOT.rglob('*.po')):
        if de_path.name.endswith('~'):
            continue
        en_path = EN_ROOT / de_path.relative_to(DE_ROOT)
        if not en_path.exists():
            continue
        de_po = polib.pofile(str(de_path))
        en_map = {e.msgid: e.msgstr for e in polib.pofile(str(en_path)) if e.msgid and not e.obsolete}
        for entry in de_po:
            if entry.obsolete or not entry.msgid or not entry.msgstr:
                continue
            mid, en, de = entry.msgid, en_map.get(entry.msgid, ''), entry.msgstr
            if needs_retranslate(mid, en, de):
                en_keys.append(en)
            elif not en and CHINESE_RE.search(mid) and mid == de:
                zh_keys.append(mid)
    return list(dict.fromkeys(en_keys)), list(dict.fromkeys(zh_keys))


def apply_retranslations(cache: dict[str, str]) -> int:
    """写回 de po。"""
    n = 0
    for de_path in sorted(DE_ROOT.rglob('*.po')):
        if de_path.name.endswith('~'):
            continue
        en_path = EN_ROOT / de_path.relative_to(DE_ROOT)
        if not en_path.exists():
            continue
        po = polib.pofile(str(de_path))
        en_map = {e.msgid: e.msgstr for e in polib.pofile(str(en_path)) if e.msgid and not e.obsolete}
        changed = False
        for entry in po:
            if entry.obsolete or not entry.msgid or not entry.msgstr:
                continue
            mid, en, de = entry.msgid, en_map.get(entry.msgid, ''), entry.msgstr
            new_str = ''
            if needs_retranslate(mid, en, de) and en in cache:
                new_str = cache[en]
            elif not en and CHINESE_RE.search(mid) and mid == de:
                new_str = cache.get(f'__zh__{mid}', '')
            if new_str and new_str.strip() != de.strip():
                entry.msgstr = new_str
                if 'fuzzy' in entry.flags:
                    entry.flags.remove('fuzzy')
                n += 1
                changed = True
        if changed:
            po.metadata['PO-Revision-Date'] = '2026-05-23 23:30+0800'
            po.save(str(de_path))
    return n


def main() -> int:
    """入口。"""
    en_keys, zh_keys = collect_retranslate_keys()
    print(f'retranslate candidates: en={len(en_keys)} zh={len(zh_keys)}')
    cache = load_cache()
    # 强制重译这些键
    for k in en_keys:
        cache.pop(k, None)
    for k in zh_keys:
        cache.pop(f'__zh__{k}', None)
    save_cache(cache)
    if en_keys or zh_keys:
        cache = build_cache(en_keys, zh_keys, sleep_s=0.12)
    updated = apply_retranslations(cache)
    print(f'updated {updated} entries')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
