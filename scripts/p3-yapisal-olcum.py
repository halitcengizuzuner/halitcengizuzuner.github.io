#!/usr/bin/env python3
"""P3 rollout ÖN-ÖLÇÜM (O491 'aynı şablon varsayma' + E469). Betik YAZMADAN önce
her makalenin gerçek yapısını çıkar: aksan değişkeni, token varlığı, kendi-font, P3-yapıldı mı."""
import re, glob, os, json
from collections import defaultdict

ROOT = os.path.expanduser('~/halitcengizuzuner.github.io')
DILLER = ['turkce','english','espanol','francais','deutsch','zhongwen','nihongo']

def h2_aksan(css):
    # h2 { ... color: var(--X) ... }
    m = re.search(r'\bh2\s*\{([^}]*)\}', css)
    if not m: return None
    cm = re.search(r'color:\s*var\((--[\w-]+)\)', m.group(1))
    return cm.group(1) if cm else None

def body_block(css):
    m = re.search(r'\bbody\s*\{([^}]*)\}', css)
    return m.group(1) if m else ''

def display_fonts(css):
    # Google font link family=X
    links = re.findall(r'family=([A-Za-z0-9+]+)', css)
    return links

rows = []
by_article = defaultdict(list)
for d in DILLER:
    for path in sorted(glob.glob(f'{ROOT}/{d}/raporlar/*.html')):
        base = os.path.basename(path)
        if '-dinle' in base or base == 'index.html': continue
        css = open(path, encoding='utf-8').read()
        bb = body_block(css)
        row = {
            'dil': d, 'makale': base,
            'has_read': '--read' in css,
            'has_book': '.book {' in css or '.book{' in css,
            'has_serif_tok': bool(re.search(r'--serif:', css)),
            'aksan': h2_aksan(css),
            'body_color': (re.search(r'color:\s*var\((--[\w-]+)\)', bb) or [None, None])[1] if re.search(r'color:\s*var\((--[\w-]+)\)', bb) else None,
            'body_font': (re.search(r'font-family:\s*var\((--[\w-]+)\)', bb).group(1) if re.search(r'font-family:\s*var\((--[\w-]+)\)', bb) else None),
            'body_lh': (re.search(r'line-height:\s*([\d.]+)', bb).group(1) if re.search(r'line-height:\s*([\d.]+)', bb) else None),
            'src_serif_link': 'Source+Serif+4' in css,
            'fonts': display_fonts(css),
            'has_pq': '.pull-quote' in css,
            'has_h3': bool(re.search(r'\bh3\s*\{', css)),
            'has_subtitle': '.subtitle' in css,
            'has_title': '.title' in css,
        }
        rows.append(row)
        by_article[base].append(row)

# ÖZET
print("=== MAKALE BAZLI (aksan + font + anomali; dil-içi tutarlılık) ===")
for art in sorted(by_article):
    rs = by_article[art]
    aksanlar = set(r['aksan'] for r in rs)
    fonts = set(tuple(sorted(set(f for f in r['fonts']))) for r in rs)
    body_c = set(r['body_color'] for r in rs)
    body_f = set(r['body_font'] for r in rs)
    body_l = set(r['body_lh'] for r in rs)
    has_book = set(r['has_book'] for r in rs)
    has_serif = set(r['has_serif_tok'] for r in rs)
    has_read = set(r['has_read'] for r in rs)
    has_pq = set(r['has_pq'] for r in rs)
    kendi_font = any('Instrument' not in ''.join(r['fonts']) for r in rs)
    flags = []
    if len(aksanlar)>1: flags.append(f"AKSAN-FARKLI:{aksanlar}")
    if len(fonts)>1: flags.append("FONT-DIL-FARKLI")
    if len(body_c)>1: flags.append(f"body_color-farkli:{body_c}")
    if len(body_f)>1: flags.append(f"body_font-farkli:{body_f}")
    if len(body_l)>1: flags.append(f"body_lh-farkli:{body_l}")
    if False in has_book: flags.append("BOOK-YOK-dil-var")
    if False in has_serif: flags.append("SERIF-TOK-YOK")
    if True in has_read: flags.append(f"ZATEN-P3:{sum(1 for r in rs if r['has_read'])}/{len(rs)}")
    print(f"  {art:34s} aksan={str(list(aksanlar)):18s} body(c={list(body_c)},f={list(body_f)},lh={list(body_l)}) book={list(has_book)} serifTok={list(has_serif)} pq={list(has_pq)} fonts={list(fonts)[0] if len(fonts)==1 else fonts} {'| KENDI-FONT' if kendi_font else ''} {'| '+' '.join(flags) if flags else ''}")

print(f"\n=== TOPLAM: {len(rows)} dosya, {len(by_article)} makale × {len(DILLER)} dil ===")
# Aksan dağılımı
aks = defaultdict(int)
for r in rows: aks[r['aksan']] += 1
print("Aksan değişkeni dağılımı:", dict(aks))
# Kendi-font makaleler
print("Kendi-font (Instrument DIŞI) makaleler:", sorted(set(r['makale'] for r in rows if 'Instrument' not in ''.join(r['fonts']))))
# .book olmayan
print(".book OLMAYAN:", sorted(set((r['dil'],r['makale']) for r in rows if not r['has_book'])))
# --serif token olmayan
print("--serif token YOK:", sorted(set(r['makale'] for r in rows if not r['has_serif_tok'])))
# zaten P3
print("Zaten --read (P3):", sorted(set((r['dil'],r['makale']) for r in rows if r['has_read'])))
