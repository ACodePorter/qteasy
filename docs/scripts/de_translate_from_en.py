# coding=utf-8
"""Phase 2：以 en msgstr 为 pivot，将 de .po 中仍为英文的条目译为德语。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import polib
from deep_translator import GoogleTranslator

_SCRIPTS = Path(__file__).resolve().parent
LOCALE = _SCRIPTS.parent / 'source' / 'locale'
DE_ROOT = LOCALE / 'de' / 'LC_MESSAGES'
EN_ROOT = LOCALE / 'en' / 'LC_MESSAGES'
CACHE_PATH = _SCRIPTS / 'de_translation_cache.json'

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')
# 不送入翻译器的占位符（术语表：品牌、类名、信号缩写）
PROTECT_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r'`[^`]+`'), 'CODE'),
    (re.compile(r'\b(?:qteasy|QTEASY|QtEasy)\b'), 'QTEASY'),
    (re.compile(r'\b(?:Operator|HistoryPanel|DataType|DataSource|BaseStrategy|Backtester|Trader|RiskManager|BrokerFacade|SimulatorBroker)\b'), 'CLS'),
    (re.compile(r'\b(?:PT|PS|VS)\b'), 'SIG'),
    (re.compile(r'https?://[^\s\])>]+'), 'URL'),
]

URL_EN_TO_DE = re.compile(
    r'https://qteasy\.readthedocs\.io/en/latest/',
    re.IGNORECASE,
)


def load_cache() -> Dict[str, str]:
    """加载翻译缓存。"""
    if CACHE_PATH.is_file():
        return json.loads(CACHE_PATH.read_text(encoding='utf-8'))
    return {}


def save_cache(cache: Dict[str, str]) -> None:
    """保存翻译缓存。"""
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=0),
        encoding='utf-8',
    )


def protect(text: str) -> Tuple[str, List[str]]:
    """将代码/术语替换为占位符。"""
    tokens: List[str] = []

    def repl_factory(tag: str):
        def _repl(m: re.Match[str]) -> str:
            tokens.append(m.group(0))
            return f'⟦{tag}{len(tokens) - 1}⟧'
        return _repl

    out = text
    for pat, tag in PROTECT_PATTERNS:
        out = pat.sub(repl_factory(tag), out)
    return out, tokens


def unprotect(text: str, tokens: List[str]) -> str:
    """还原占位符。"""
    for i, tok in enumerate(tokens):
        for tag in ('CODE', 'QTEASY', 'CLS', 'SIG', 'URL'):
            placeholder = f'⟦{tag}{i}⟧'
            if placeholder in text:
                text = text.replace(placeholder, tok, 1)
    return text


def postprocess_de(text: str) -> str:
    """RTD 内链与常见后处理。"""
    text = URL_EN_TO_DE.sub('https://qteasy.readthedocs.io/de/latest/', text)
    # 翻译器有时破坏反引号，简单修复空反引号对
    text = re.sub(r'``\s*``', '', text)
    return text


def needs_german_translation(msgid: str, msgstr_de: str, msgstr_en: str) -> bool:
    """判断是否需要从 en 译为 de。"""
    if not CHINESE_RE.search(msgid):
        return False
    if not msgstr_en.strip():
        return False
    if not msgstr_de.strip() or msgstr_de.strip() == msgstr_en.strip():
        return True
    return False


def translate_text(text: str, translator: GoogleTranslator, cache: Dict[str, str]) -> str:
    """翻译单段文本（带缓存与保护）。"""
    key = text.strip()
    if key in cache:
        return cache[key]
    protected, tokens = protect(key)
    # Google 单次长度限制，过长则分块
    if len(protected) > 4500:
        parts = []
        chunk_size = 4000
        for i in range(0, len(protected), chunk_size):
            chunk = protected[i : i + chunk_size]
            parts.append(translator.translate(chunk))
            time.sleep(0.15)
        result = ''.join(parts)
    else:
        result = translator.translate(protected)
        time.sleep(0.12)
    result = unprotect(result, tokens)
    result = postprocess_de(result)
    cache[key] = result
    return result


def iter_po_files(sections: Iterable[str] | None) -> List[Path]:
    """按章节过滤 de po 文件列表。"""
    files = sorted(p for p in DE_ROOT.rglob('*.po') if not p.name.endswith('~'))
    if not sections:
        return files
    sec_set = set(sections)
    out: List[Path] = []
    for p in files:
        rel = p.relative_to(DE_ROOT)
        top = rel.parts[0] if len(rel.parts) > 1 else '(root)'
        if top in sec_set:
            out.append(p)
    return out


def process_file(
    de_path: Path,
    translator: GoogleTranslator,
    cache: Dict[str, str],
    dry_run: bool,
) -> Tuple[int, int]:
    """处理单个 de po 文件。

    Returns
    -------
    tuple[int, int]
        (translated_count, skipped_count)
    """
    rel = de_path.relative_to(DE_ROOT)
    en_path = EN_ROOT / rel
    if not en_path.is_file():
        return 0, 0

    de_po = polib.pofile(str(de_path))
    en_po = polib.pofile(str(en_path))
    en_map = {e.msgid: e.msgstr for e in en_po if e.msgid and not e.obsolete}

    translated = skipped = 0
    for entry in de_po:
        if entry.obsolete or not entry.msgid:
            continue
        en_s = en_map.get(entry.msgid, '')
        if not needs_german_translation(entry.msgid, entry.msgstr, en_s):
            skipped += 1
            continue
        if dry_run:
            translated += 1
            continue
        try:
            entry.msgstr = translate_text(en_s, translator, cache)
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
            translated += 1
        except Exception as exc:  # noqa: BLE001 — 批量翻译需记录单条失败
            print(f'  WARN {rel}: {exc!s} :: {entry.msgid[:60]!r}')

    if not dry_run and translated:
        de_po.metadata['PO-Revision-Date'] = '2026-05-23 22:00+0800'
        de_po.metadata['Last-Translator'] = 'Jackie PENG (de_translate_from_en)'
        de_po.save(str(de_path))
        text = de_path.read_text(encoding='utf-8')
        if '\n#, fuzzy\n' in text:
            de_path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')

    return translated, skipped


def main(argv: List[str] | None = None) -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description='Translate de .po from en pivot')
    parser.add_argument(
        '--sections',
        nargs='*',
        default=None,
        help='Top-level dirs e.g. optimization manage_strategies (omit = all)',
    )
    parser.add_argument('--dry-run', action='store_true', help='Count only, no writes')
    parser.add_argument('--limit-files', type=int, default=0, help='Max po files (0=all)')
    args = parser.parse_args(argv)

    files = iter_po_files(args.sections)
    if args.limit_files:
        files = files[: args.limit_files]

    cache = load_cache()
    translator = GoogleTranslator(source='en', target='de')

    total_tr = 0
    print(f'[de_translate] files={len(files)} dry_run={args.dry_run}')
    for i, de_path in enumerate(files, 1):
        tr, sk = process_file(de_path, translator, cache, args.dry_run)
        if tr:
            print(f'  [{i}/{len(files)}] {de_path.relative_to(DE_ROOT)}: +{tr}')
        total_tr += tr
        if i % 10 == 0 and not args.dry_run:
            save_cache(cache)

    if not args.dry_run:
        save_cache(cache)
    print(f'[de_translate] done translated={total_tr} cache_size={len(cache)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
