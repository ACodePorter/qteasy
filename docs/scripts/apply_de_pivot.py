# coding=utf-8
"""Phase 2：以 en msgstr 为 pivot 填充 de .po（技术条目 + 机器翻译正文 + 内链）。"""

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

from fill_de_po import DE_ROOT, EN_ROOT, apply_file, is_technical, localize_links

CACHE_PATH = _SCRIPTS / 'de_prose_cache.json'
CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')

# 品牌/API 名在机翻后保持不破坏（小写匹配替换回英文）
KEEP_TERMS = (
    'qteasy', 'QTEASY', 'Operator', 'HistoryPanel', 'DataSource', 'DataType',
    'Backtester', 'BaseStrategy', 'RiskManager', 'Broker', 'Trader',
    'Tushare', 'Poedit', 'Python', 'NumPy', 'pandas', 'Plotly',
)


def load_cache() -> dict[str, str]:
    """加载 en→de 正文翻译缓存。"""
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding='utf-8'))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    """保存缓存。"""
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')


def protect_terms(text: str) -> tuple[str, dict[str, str]]:
    """用占位符保护不宜翻译的术语。"""
    placeholders: dict[str, str] = {}
    out = text
    for i, term in enumerate(KEEP_TERMS):
        if term in out:
            key = f'__QT{i}__'
            placeholders[key] = term
            out = out.replace(term, key)
    return out, placeholders


def restore_terms(text: str, placeholders: dict[str, str]) -> str:
    """恢复术语占位符。"""
    out = text
    for key, term in placeholders.items():
        out = out.replace(key, term)
    return out


def translate_en_to_de(text: str, translator) -> str:
    """将英文正文译为德语（带术语保护）。"""
    if not text or not text.strip():
        return text
    protected, ph = protect_terms(text)
    try:
        result = translator.translate(protected)
    except Exception as exc:  # noqa: BLE001
        print(f'  [warn] translate failed: {exc!s:.80}')
        return text
    if not result:
        return text
    return restore_terms(result, ph)


def translate_zh_to_de(text: str, translator) -> str:
    """将中文译为德语（无 en pivot 的条目）。"""
    if not text or not text.strip():
        return text
    protected, ph = protect_terms(text)
    try:
        result = translator.translate(protected)
    except Exception as exc:  # noqa: BLE001
        print(f'  [warn] zh translate failed: {exc!s:.80}')
        return text
    if not result:
        return text
    return restore_terms(result, ph)


def collect_prose_keys() -> tuple[list[str], list[str]]:
    """收集待译的 en 正文键与 zh-only 键。"""
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
            if entry.obsolete or not entry.msgid:
                continue
            if entry.msgstr and 'fuzzy' not in entry.flags:
                continue
            if entry.msgstr and 'fuzzy' in entry.flags:
                continue
            mid = entry.msgid
            en = en_map.get(mid, '')
            if is_technical(mid, msgid=mid) or (en and is_technical(en, msgid=mid)):
                continue
            if en:
                en_keys.append(en)
            elif CHINESE_RE.search(mid):
                zh_keys.append(mid)
    return list(dict.fromkeys(en_keys)), list(dict.fromkeys(zh_keys))


def build_cache(en_keys: list[str], zh_keys: list[str], sleep_s: float = 0.15) -> dict[str, str]:
    """批量翻译并写入缓存。"""
    from deep_translator import GoogleTranslator

    en_de = GoogleTranslator(source='en', target='de')
    zh_de = GoogleTranslator(source='zh-CN', target='de')
    cache = load_cache()
    total = len(en_keys) + len(zh_keys)
    done = 0
    for en in en_keys:
        if en in cache:
            continue
        cache[en] = localize_links(translate_en_to_de(en, en_de))
        done += 1
        if done % 50 == 0:
            save_cache(cache)
            print(f'  en->de: {done}/{total} ...')
        time.sleep(sleep_s)
    for zh in zh_keys:
        key = f'__zh__{zh}'
        if key in cache:
            continue
        cache[key] = localize_links(translate_zh_to_de(zh, zh_de))
        done += 1
        if done % 50 == 0:
            save_cache(cache)
            print(f'  zh->de: {done}/{total} ...')
        time.sleep(sleep_s)
    save_cache(cache)
    return cache


def apply_all(cache: dict[str, str]) -> None:
    """将缓存应用到全部 de po。"""
    for de_path in sorted(DE_ROOT.rglob('*.po')):
        if de_path.name.endswith('~'):
            continue
        en_path = EN_ROOT / de_path.relative_to(DE_ROOT)
        apply_file(de_path, en_path if en_path.exists() else None)

    filled_prose = 0
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
            if entry.obsolete or not entry.msgid:
                continue
            if entry.msgstr and 'fuzzy' not in entry.flags:
                continue
            if entry.msgstr and 'fuzzy' in entry.flags:
                entry.msgstr = localize_links(entry.msgstr)
                entry.flags.remove('fuzzy')
                changed = True
                continue
            if entry.msgstr:
                continue
            mid = entry.msgid
            en = en_map.get(mid, '')
            if is_technical(mid, msgid=mid):
                continue
            if en and is_technical(en, msgid=mid):
                continue
            if en and en in cache:
                entry.msgstr = cache[en]
                filled_prose += 1
                changed = True
            elif not en and CHINESE_RE.search(mid):
                key = f'__zh__{mid}'
                if key in cache:
                    entry.msgstr = cache[key]
                    filled_prose += 1
                    changed = True
        if changed:
            po.metadata['PO-Revision-Date'] = '2026-05-23 22:00+0800'
            po.save(str(de_path))
    print(f'applied prose from cache: {filled_prose}')


def main() -> int:
    """入口：--build-cache 仅建缓存；默认建缓存并应用。"""
    build_only = '--build-cache' in sys.argv
    skip_cache = '--skip-cache' in sys.argv

    print('[de] pass 1: technical + fuzzy ...')
    total_m = total_e = total_f = 0
    for de_path in sorted(DE_ROOT.rglob('*.po')):
        if de_path.name.endswith('~'):
            continue
        en_path = EN_ROOT / de_path.relative_to(DE_ROOT)
        fm, fe, ff = apply_file(de_path, en_path if en_path.exists() else None)
        total_m += fm
        total_e += fe
        total_f += ff
    print(f'  msgid={total_m} en_tech={total_e} unfuzzy={total_f}')

    if not skip_cache:
        en_keys, zh_keys = collect_prose_keys()
        cache = load_cache()
        missing_en = [k for k in en_keys if k not in cache]
        missing_zh = [k for k in zh_keys if f'__zh__{k}' not in cache]
        print(f'[de] prose to translate: en={len(missing_en)} zh={len(missing_zh)} (cached {len(cache)})')
        if missing_en or missing_zh:
            cache = build_cache(missing_en, missing_zh)
        if not build_only:
            apply_all(cache)
    elif not build_only:
        apply_all(load_cache())

    # 清除文件头 fuzzy
    cleared = 0
    for de_path in DE_ROOT.rglob('*.po'):
        if de_path.name.endswith('~'):
            continue
        text = de_path.read_text(encoding='utf-8')
        if '\n#, fuzzy\n' in text:
            de_path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
            cleared += 1
    print(f'[de] cleared header fuzzy in {cleared} files')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
