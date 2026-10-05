#!/usr/bin/env python3
"""P2-A: render-bagimsiz erisim katmani (6 dil + kok; TR elle yapildi, idempotent-skip).
Enjekte edilen: --bone-read token + :visited, :lang(zh/ja) CJK font, @media print, lang-bar
lang/hreflang/aria-current, fail-open IO. FAZ1 tum dosyalarda anchor+idempotent dogrula,
FAZ2 atomik yaz, sonra count-assert kirici. 7-dil-atomik (O336)."""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANGS = {'turkce':'tr','english':'en','espanol':'es','francais':'fr','deutsch':'de','zhongwen':'zh','nihongo':'ja'}
HREF2LANG = {'/english/':'en','/zhongwen/':'zh','/nihongo/':'ja','/francais/':'fr','/deutsch/':'de','/espanol/':'es','/turkce/':'tr'}

P2A_CSS = """        /* === P2 erisim katmani (render-bagimsiz: :visited + print + CJK lang) === */
        :root { --bone-read: #8a7a66; }
        .lang-link:lang(zh) { font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif; }
        .lang-link:lang(ja) { font-family: 'Hiragino Mincho ProN', 'Yu Mincho', 'Noto Serif JP', serif; }
        .aphorism-link:visited { color: var(--bone-read); }
        @media print {
            body { background: #fff; color: #000; opacity: 1 !important; animation: none !important; }
            body::before { display: none !important; }
            .lang-bar { display: none; }
            .stance, .welcome, .limbs, .seal, .upkeep { opacity: 1 !important; transform: none !important; }
            .stance p, .welcome p, .aphorism-link, .upkeep p, .limb-name, .limb-what, .seal a { color: #000 !important; }
            a { text-decoration: underline; }
            @page { margin: 2cm; }
        }
"""

NEW_IO = """const reveals = document.querySelectorAll('.stance, .welcome, .limbs, .seal');
if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
        entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('seen'); });
    }, { threshold: 0, rootMargin: '0px 0px -60px 0px' });
    reveals.forEach(el => io.observe(el));
} else {
    reveals.forEach(el => el.classList.add('seen'));
}"""

IO_PAT = re.compile(
    r"const io = new IntersectionObserver\(entries => \{.*?\}\);\s*"
    r"document\.querySelectorAll\('\.stance, \.welcome, \.limbs, \.seal'\)\.forEach\(el => io\.observe\(el\)\);",
    re.DOTALL)

LANGBAR_PAT = re.compile(r'<a href="(/[a-z]+/)" class="(lang-link(?: lang-active)?)">')

def transform_dil(content, langdir):
    """6 dil icin. (yeni_content, [degisimler]) doner. Idempotent."""
    ch = []
    # 1. CSS blok (ana </style> oncesi)
    if '--bone-read' not in content:
        pos = content.rfind('</style>')
        if pos == -1: raise RuntimeError(f"{langdir}: </style> yok")
        line_start = content.rfind('\n', 0, pos) + 1
        content = content[:line_start] + P2A_CSS + content[line_start:]
        ch.append('css')
    # 2. lang-bar oznitelik
    if 'class="lang-link" lang=' not in content and 'class="lang-link lang-active" lang=' not in content:
        def repl(m):
            href, cls = m.group(1), m.group(2)
            lc = HREF2LANG.get(href)
            if not lc: return m.group(0)
            a = f' lang="{lc}" hreflang="{lc}"'
            if 'lang-active' in cls: a += ' aria-current="page"'
            return f'<a href="{href}" class="{cls}"{a}>'
        new, n = LANGBAR_PAT.subn(repl, content)
        if n == 0: raise RuntimeError(f"{langdir}: lang-bar link bulunamadi")
        content = new; ch.append(f'langbar({n})')
    # 3. fail-open
    if "'IntersectionObserver' in window" not in content:
        new, n = IO_PAT.subn(NEW_IO, content, count=1)
        if n == 0: raise RuntimeError(f"{langdir}: IO script bulunamadi")
        content = new; ch.append('failopen')
    return content, ch

def transform_kok(content):
    ch = []
    if 'lang="en" hreflang="en"' not in content:
        def repl(m):
            href, rest = m.group(1), m.group(2) or ''
            lc = HREF2LANG.get(href)
            if not lc: return m.group(0)
            return f'<a href="{href}"{rest} lang="{lc}" hreflang="{lc}">'
        # <a href="/X/"[ class="primary"]>
        new, n = re.subn(r'<a href="(/[a-z]+/)"( class="primary")?>', repl, content)
        if n == 0: raise RuntimeError("kok: nav link bulunamadi")
        content = new; ch.append(f'koknav({n})')
    return content, ch

# ---- FAZ1: dogrula (bellekte) ----
plan = {}
for d in LANGS:
    f = ROOT / d / 'index.html'
    c = f.read_text(encoding='utf-8')
    nc, ch = transform_dil(c, d)
    plan[f] = nc
    print(f"FAZ1 {d:9s}: {ch if ch else 'zaten tam (skip)'}")
fk = ROOT / 'index.html'
ck = fk.read_text(encoding='utf-8')
nck, chk = transform_kok(ck)
plan[fk] = nck
print(f"FAZ1 {'kok':9s}: {chk if chk else 'zaten tam (skip)'}")

if '--dogrula' in sys.argv:
    print("--dogrula: FAZ2 atlandi"); sys.exit(0)

# ---- FAZ2: atomik yaz ----
for f, nc in plan.items():
    f.write_text(nc, encoding='utf-8')
print("FAZ2: yazildi")

# ---- KIRICI: count-assert (7 dil) ----
print("\n=== KIRICI (7 dil count-assert) ===")
fail = 0
for d in LANGS:
    c = (ROOT / d / 'index.html').read_text(encoding='utf-8')
    vis_sel = '.thought a:visited' if d == 'turkce' else '.aphorism-link:visited'
    checks = {
        'bone-read': c.count('--bone-read: #8a7a66') == 1,
        'lang(zh)': c.count('.lang-link:lang(zh)') == 1,
        'lang(ja)': c.count('.lang-link:lang(ja)') == 1,
        'visited': c.count(vis_sel) == 1,
        'print': c.count('@media print') == 1,
        'aria-current': c.count('aria-current="page"') == 1,
        'hreflang-attr': c.count('class="lang-link" lang=') == 6,  # 6 non-active
        'failopen': c.count("'IntersectionObserver' in window") == 1,
    }
    bad = [k for k,v in checks.items() if not v]
    status = 'OK' if not bad else f'HATA {bad}'
    if bad: fail += 1
    print(f"  {d:9s}: {status}")
# kok
ck = (ROOT / 'index.html').read_text(encoding='utf-8')
kbad = []
if ck.count('lang="en" hreflang="en"') != 1: kbad.append('en-lang')
if ck.count(' hreflang="') < 6: kbad.append('hreflang<6')
print(f"  {'kok':9s}: {'OK' if not kbad else f'HATA {kbad}'}")
if kbad: fail += 1
print(f"\nSONUC: {'TUM GECTI' if fail==0 else f'{fail} DOSYA HATALI'}")
sys.exit(1 if fail else 0)
