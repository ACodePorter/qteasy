# coding=utf-8
"""Phase 3：以 OpenCC s2t 将 zh_TW .po 的 msgstr 从简体 msgid 转为繁体，并套用两岸术语与 RTD 链接。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import polib
from opencc import OpenCC

_SCRIPTS = Path(__file__).resolve().parent
ZH_TW_ROOT = _SCRIPTS.parent / 'source' / 'locale' / 'zh_TW' / 'LC_MESSAGES'

# 简体 -> 台湾常用（在 OpenCC 之后按长短序替换，避免短词误伤）
TW_TERMS: list[tuple[str, str]] = [
    ('默认', '預設'),
    ('数据库', '資料庫'),
    ('内存', '記憶體'),
    ('磁盘', '磁碟'),
    ('软件', '軟體'),
    ('程序', '程式'),
    ('服务器', '伺服器'),
    ('网络', '網路'),
    ('信息', '資訊'),
    ('视频', '影片'),
    ('代码', '程式碼'),
    ('文档', '文件'),
    ('鼠标', '滑鼠'),
    ('打印', '列印'),
    ('屏幕', '螢幕'),
    ('操作系统', '作業系統'),
    ('线程', '執行緒'),
    ('缓存', '快取'),
    ('链接', '連結'),
    ('账户', '帳戶'),
    ('账户', '帳戶'),
    ('回测', '回測'),
    ('实盘', '實盤'),
    ('持仓', '持倉'),
    ('标的', '標的'),
    ('复权', '復權'),
    ('优化', '最佳化'),
]

RTD_ZHCN = re.compile(r'https://qteasy\.readthedocs\.io/zh-cn/latest/', re.I)
ASCII_ONLY = re.compile(r'^[\x00-\x7f\s\d\W]+$')
CHINESE = re.compile(r'[\u4e00-\u9fff]')


def is_copy_as_is(msgid: str) -> bool:
    """英文/代码类 msgid 直接复制。"""
    if not msgid.strip():
        return False
    if not CHINESE.search(msgid):
        return True
    if msgid.count('`') >= 2 and len(CHINESE.findall(msgid)) <= 2:
        return True
    return False


def apply_tw_terms(text: str) -> str:
    """在 OpenCC 结果上套用术语表。"""
    for simp, trad in sorted(TW_TERMS, key=lambda x: -len(x[0])):
        text = text.replace(simp, trad)
    return text


def convert_text(converter: OpenCC, msgid: str) -> str:
    """将 msgid 转为繁中 msgstr。"""
    if is_copy_as_is(msgid):
        return msgid
    out = converter.convert(msgid)
    out = apply_tw_terms(out)
    out = RTD_ZHCN.sub('https://qteasy.readthedocs.io/zh-tw/latest/', out)
    return out


def process_po(po_path: Path, converter: OpenCC) -> int:
    """填充单个 po 文件。"""
    po = polib.pofile(str(po_path))
    filled = 0
    for entry in po:
        if entry.obsolete or not entry.msgid:
            continue
        if entry.msgstr and 'fuzzy' not in entry.flags:
            continue
        new = convert_text(converter, entry.msgid)
        if entry.msgstr != new:
            entry.msgstr = new
            filled += 1
        if 'fuzzy' in entry.flags:
            entry.flags.remove('fuzzy')
    if filled:
        po.metadata['PO-Revision-Date'] = '2026-05-24 16:00+0800'
        po.metadata['Last-Translator'] = 'Jackie PENG (zh_tw_fill_opencc)'
        po.save(str(po_path))
    return filled


def clear_header_fuzzy() -> int:
    """清除文件头 #, fuzzy。"""
    count = 0
    for path in ZH_TW_ROOT.rglob('*.po'):
        if path.name.endswith('~'):
            continue
        text = path.read_text(encoding='utf-8')
        if '\n#, fuzzy\n' in text:
            path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
            count += 1
    return count


def main() -> int:
    """遍历全部 zh_TW po 并填充 msgstr。"""
    converter = OpenCC('s2t')
    total = 0
    files = sorted(p for p in ZH_TW_ROOT.rglob('*.po') if not p.name.endswith('~'))
    for i, po_path in enumerate(files, 1):
        n = process_po(po_path, converter)
        if n:
            print(f'  [{i}/{len(files)}] {po_path.relative_to(ZH_TW_ROOT)}: +{n}')
            total += n
    hdr = clear_header_fuzzy()
    print(f'zh_tw_fill_opencc: filled={total} header_fuzzy_cleared={hdr}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
