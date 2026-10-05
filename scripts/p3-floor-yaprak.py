#!/usr/bin/env python3
"""P3 okuma-yüzü rollout (STRATEJİ 1, O499 Halit onaylı; referans anlamak.html O498-O499).

İKİ KOL (O491 'aynı şablon varsayma' + E469 ham-ölç + İçi-Hayal):
  - .book aileleri (anlamak/görünmez-boşluk/yüzsüz/çay-masası): FLOOR + YAPRAK
  - .content aileleri (Instrument-tabanlı, kendi aksanı): yalnız FLOOR
  - ATLA: Nefret (Cormorant+Inter, kendi font sistemi) + eski-nesil (--serif token YOK)

FLOOR = gövde okunurluğu (Source Serif 4 Latin gövde + --ink + rahat lh + px→rem + color-scheme)
        + display-pin (başlık/h2/h3/pull-quote Instrument KARAKTER korunur).
YAPRAK = .book bg --sheet + kenar + aksan border-top (AKSAN-AGNOSTİK) + radius + margin/padding.

CJK (zhongwen/nihongo): Source Serif 4 CJK'yı KAPSAMAZ → gövde fontu (--jp) + lh DOKUNULMAZ;
        yalnız color→--ink + token + yaprak (Fable: CJK kimliği yüzey+ölçü+aksana asılır).

İDEMPOTENT (--read token varsa floor skip). Uygulayıcı+KIRICI (FAZ1 doğrula → FAZ2 yaz).
Kullanım: python3 scripts/p3-floor-yaprak.py --scope book|content|all [--apply]
"""
import re, glob, os, sys, argparse

ROOT = os.path.expanduser('~/halitcengizuzuner.github.io')
DILLER = ['turkce','english','espanol','francais','deutsch','zhongwen','nihongo']
CJK = {'zhongwen','nihongo'}
# ATLA: kendi-font (Nefret) — Cormorant; eski-nesil --serif token yok (ölçümle tespit edilir)
# Betik --serif token + Instrument şartıyla zaten eler; yine de ad bazlı emniyet:
NEFRET = {'de-la-haine','nefret-uzerine','on-hatred','sobre-el-odio','ueber-den-hass'}

SHEET, SHEET_EDGE, INK = '#171512', '#302a22', '#e9e3d7'
READ_DECL = "'Source Serif 4', Georgia, serif"
SRC_LINK = '&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400'
PIN_SELECTORS = ['.title', '.subtitle', 'h2', 'h3', '.pull-quote']

def find_style(html):
    """Asıl <style> bloğunu döndür (noscript içindeki fail-open DEĞİL).
    Asıl stil :root içerir; noscript override içermez."""
    styles = [(m.start(1), m.end(1), m.group(1)) for m in re.finditer(r'<style>(.*?)</style>', html, re.S)]
    for s, e, css in styles:
        if ':root' in css:
            return s, e, css
    return None, None, None

def h2_aksan(css):
    m = re.search(r'(?<![.\w-])h2\s*\{([^}]*)\}', css)
    if not m: return None
    cm = re.search(r'color:\s*var\((--[\w-]+)\)', m.group(1))
    return cm.group(1) if cm else None

def book_aksan(css):
    """Yaprak border-top aksanı: h2 rengi; yoksa makalenin kendi :root tokenı
    (--void/--bone*/--serif/--read/--sheet*/--ink/--jp HARİÇ ilk --X); yoksa --bone-bright."""
    a = h2_aksan(css)
    if a: return a
    STD = {'--void','--bone','--bone-bright','--bone-dim','--bone-ghost','--bone-read',
           '--serif','--read','--sheet','--sheet-edge','--ink','--jp',
           '--c-text','--c-quiet','--c-link','--c-label','--c-rule'}
    for m in re.finditer(r'(--[\w-]+):', css):
        tok = m.group(1)
        if tok not in STD and not tok.endswith(('-dim','-ghost','-bright')):
            return tok
    return '--bone-bright'

def transform(html, dil, has_book):
    is_cjk = dil in CJK
    s, e, css = find_style(html)
    if css is None:
        return html, ['NO-STYLE'], False
    orig_css = css
    ch = []
    aksan = book_aksan(css) if has_book else None

    # 1) FONT LINK — Source Serif 4 ekle (Instrument+Serif:ital@0;1 ardına)
    if 'Source+Serif+4' not in html:
        html, n = re.subn(r'(family=Instrument\+Serif:ital@0;1)', r'\1' + SRC_LINK.replace('\\', '\\\\'), html, count=1)
        if n: ch.append('fontlink')
    # style yeniden-konumlan (html değişti) — css'i tazele
    s, e, css = find_style(html)

    # 2) :root token — --serif: satırından sonra
    if '--read:' not in css:
        toks = f"    --read: {READ_DECL};\n"
        if has_book:
            toks += f"    --sheet: {SHEET};\n    --sheet-edge: {SHEET_EDGE};\n"
        toks += f"    --ink: {INK};\n"
        css2, n = re.subn(r'(--serif:[^\n]*\n)', r'\1' + toks.replace('\\', '\\\\'), css, count=1)
        if n: css = css2; ch.append('roottoken')

    # 3) html: px→rem + color-scheme:dark
    def px2rem(m):
        a, vw, b = int(m.group(1)), m.group(2).strip(), int(m.group(3))
        ar = f'{a/16:.4f}'.rstrip('0').rstrip('.')
        br = f'{b/16:.4f}'.rstrip('0').rstrip('.')
        return f'font-size: clamp({ar}rem, {vw}, {br}rem)'
    css2, n = re.subn(r'font-size:\s*clamp\((\d+)px,\s*([^,]+),\s*(\d+)px\)', px2rem, css, count=1)
    if n: css = css2; ch.append('htmlrem')
    if 'color-scheme' not in css:
        css2, n = re.subn(r'(html\s*\{[^}]*?scroll-behavior:\s*smooth;)', r'\1 color-scheme: dark;', css, count=1, flags=re.S)
        if n: css = css2; ch.append('colorscheme')

    # 4) body (asıl: background: var(--void) içeren)
    bm = re.search(r'(body\s*\{)([^}]*?background:\s*var\(--void\)[^}]*?)(\})', css, re.S)
    if bm:
        body = bm.group(2)
        nb = body
        # color → --ink
        nb = re.sub(r'color:\s*var\(--bone\)', f'color: var(--ink)', nb, count=1)
        if not is_cjk:
            # font-family → --read (yalnız --serif ise; CJK --jp dokunulmaz)
            nb = re.sub(r'font-family:\s*var\(--serif\)', 'font-family: var(--read)', nb, count=1)
            # line-height > 1.7 → 1.65 (floor); ≤1.7 koru
            lhm = re.search(r'line-height:\s*([\d.]+)', nb)
            if lhm and float(lhm.group(1)) > 1.7:
                nb = re.sub(r'line-height:\s*[\d.]+', 'line-height: 1.65', nb, count=1)
        if nb != body:
            css = css[:bm.start(2)] + nb + css[bm.end(2):]
            ch.append('body')

    # 5) display-pin: var olan seçicilere font-family: var(--serif) (yoksa)
    pinned = 0
    for sel in PIN_SELECTORS:
        pat = re.compile(r'(?<![.\w-])(' + re.escape(sel) + r')\s*\{([^}]*)\}')
        m = pat.search(css)
        if m and 'font-family' not in m.group(2):
            blk = m.group(0)
            newblk = blk.replace('{', '{\n    font-family: var(--serif);', 1)
            css = css[:m.start()] + newblk + css[m.end():]
            pinned += 1
    if pinned: ch.append(f'pin{pinned}')

    # 6) YAPRAK (.book) — bg/kenar/border-top aksan/radius + margin/padding (floor+yaprak)
    if has_book:
        bkm = re.search(r'(\.book\s*\{)([^}]*)(\})', css)
        if bkm and 'var(--sheet)' not in bkm.group(2):
            blk = bkm.group(2)
            # margin & padding (anlamak deseni): mevcut margin/padding'i değiştir
            blk = re.sub(r'margin:\s*[^;]+;', 'margin: 4vh auto 6rem;', blk, count=1)
            blk = re.sub(r'padding:\s*[^;]+;', 'padding: 7vh 2.75rem 5rem;', blk, count=1)
            yaprak = (f"\n    background: var(--sheet);"
                      f"\n    border: 1px solid var(--sheet-edge);"
                      f"\n    border-top: 2px solid var({aksan});"
                      f"\n    border-radius: 2px;")
            css = css[:bkm.start(2)] + blk + yaprak + '\n' + css[bkm.end(2):]
            ch.append(f'yaprak[{aksan}]')
            # mobil .book padding/margin (varsa daralt)
            mob = re.search(r'(@media[^{]*max-width:\s*600px[^{]*\{[^@]*?\.book\s*\{)([^}]*)(\})', css, re.S)
            if mob and 'margin' not in mob.group(2):
                css = css[:mob.end(2)] + ' margin: 2vh auto 4rem;' + css[mob.end(2):]

    # style bloğunu geri-yaz
    if css != orig_css:
        html = html[:s] + css + html[e:]
    changed = css != orig_css or ('fontlink' in ch)
    return html, ch, changed

def kirici(html, dil, has_book):
    """Bağımsız doğrulama — yazılmış dosyada beklenen imzalar."""
    s, e, css = find_style(html)
    is_cjk = dil in CJK
    fails = []
    if 'Source+Serif+4' not in html: fails.append('fontlink-yok')
    if '--read:' not in css: fails.append('read-token-yok')
    if 'color-scheme' not in css: fails.append('color-scheme-yok')
    bm = re.search(r'body\s*\{[^}]*?background:\s*var\(--void\)[^}]*?\}', css, re.S)
    if bm:
        body = bm.group(0)
        if 'color: var(--ink)' not in body: fails.append('body-ink-yok')
        if not is_cjk and 'font-family: var(--read)' not in body: fails.append('body-read-yok')
    else:
        fails.append('body-bulunamadi')
    if has_book:
        bk = re.search(r'\.book\s*\{[^}]*\}', css)
        if not bk or 'var(--sheet)' not in bk.group(0): fails.append('yaprak-yok')
        if bk and 'border-top: 2px solid var(--' not in bk.group(0): fails.append('border-top-yok')
    # display-pin: en az bir başlık seçicide var(--serif)
    if 'font-family: var(--serif)' not in css: fails.append('pin-yok')
    return fails

def dosyalar(scope):
    out = []
    for d in DILLER:
        for p in sorted(glob.glob(f'{ROOT}/{d}/raporlar/*.html')):
            base = os.path.basename(p)
            if '-dinle' in base or base == 'index.html': continue
            html = open(p, encoding='utf-8').read()
            s, e, css = find_style(html)
            if css is None: continue
            has_book = '.book {' in css or '.book{' in css
            has_serif = '--serif:' in css
            is_cormorant = 'Cormorant' in html
            if not has_serif or is_cormorant or base.replace('.html','') in NEFRET:
                continue  # eski-nesil / Nefret → ATLA
            if scope == 'book' and not has_book: continue
            if scope == 'content' and has_book: continue
            out.append((d, p, base, has_book, html))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scope', choices=['book','content','all'], default='book')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    files = dosyalar(args.scope)
    print(f"=== SCOPE={args.scope} · {len(files)} dosya ===\n")

    # FAZ 1: transform + doğrula (yazma yok)
    plan = []
    skip = 0
    for d, p, base, has_book, html in files:
        if '--read:' in find_style(html)[2]:
            skip += 1
            print(f"  SKIP (zaten floor): {d}/{base}")
            continue
        new, ch, changed = transform(html, d, has_book)
        fails = kirici(new, d, has_book) if changed else ['DEGISMEDI']
        status = 'OK' if not fails else 'FAIL:' + ','.join(fails)
        kind = 'BOOK' if has_book else 'content'
        print(f"  [{kind:7s}] {d}/{base:38s} {','.join(ch):40s} {status}")
        if fails and fails != ['DEGISMEDI']:
            print(f"      ⚠ KIRICI FAIL — bu dosya YAZILMAYACAK")
        else:
            plan.append((p, new, base))
    print(f"\n  {len(plan)} yazılacak, {skip} skip, {len(files)-len(plan)-skip} fail/değişmedi")

    if args.apply:
        for p, new, base in plan:
            open(p, 'w', encoding='utf-8').write(new)
        print(f"\n✓ YAZILDI: {len(plan)} dosya")
    else:
        print("\n(dry-run — yazmak için --apply)")

if __name__ == '__main__':
    main()
