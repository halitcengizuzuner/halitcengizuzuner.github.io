#!/usr/bin/env python3
"""P1 okunurluk tabani (site donusumu, O492).

Anlamsal rol-token katmani: metin rolleri asla ghost almaz (min bone-dim=4.68:1 AA),
yalniz --c-rule (cizgi/ayrac/dekoratif) ghost kalir. Aforizma duvari (baglantisiz
dusunceler, site ilkesi "sus olugu belli") DOKUNULMAZ.

Desen: O491 count-assert. --c-text global guard (P1 atomik: hep birlikte).
FAZ1 tum diller + tum degisiklikler bellekte dogrular; herhangi assert patlarsa HIC yazmaz.
FAZ2 hepsi gecince topluca yazar. Blok-ici regex (\\.class\\s*\\{[^}]*?ghost) CSS
format-bagimsiz (nihongo tek-satir CSS'i de yakalar).
"""
import re, sys
from pathlib import Path

ROOT = Path.home() / "halitcengizuzuner.github.io"
LANGS = ["turkce", "english", "espanol", "francais", "deutsch", "zhongwen", "nihongo"]

ROLE_TOKENS = """--ember: #a08060;
            /* anlamsal rol katmani (P1 okunurluk: metin asla ghost; yalniz --c-rule dekoratif) */
            --c-text: var(--bone);
            --c-quiet: var(--bone-dim);
            --c-link: var(--bone-dim);
            --c-label: var(--bone-dim);
            --c-rule: var(--bone-ghost);"""

A11Y_BLOCK = """        /* === P1 erisilebilirlik tabani === */
        html { color-scheme: dark; }
        :focus-visible { outline: 2px solid var(--ember); outline-offset: 3px; }
        a:focus-visible { outline: 2px solid var(--ember); outline-offset: 3px; border-radius: 2px; }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
            body { opacity: 1 !important; }
            .stance, .thought, .limbs, .seal { opacity: 1 !important; transform: none !important; }
        }

        ::selection {"""

# (ad, old_regex, new_repl, beklenen_sayi)
CHANGES = [
    # --- rol-token tanimi ---
    ("token-ekle",
     re.escape("--ember: #a08060;"),
     ROLE_TOKENS.replace("\\", "\\\\"), 1),
    # --- METIN ghost -> rol-token (okunurluk; blok-ici, format-bagimsiz) ---
    ("limb-what->c-label",
     r'(\.limb-what\s*\{[^}]*?)var\(--bone-ghost\)', r'\1var(--c-label)', 1),
    ("seal-a->c-link",
     r'(\.seal a \{[^}]*?)var\(--bone-ghost\)', r'\1var(--c-link)', 1),
    ("bakim-p->c-quiet",
     r'(font-size: clamp\(0\.9rem, 1\.1vw, 1rem\); line-height: [\d.]+; )color: var\(--bone-ghost\)',
     r'\1color: var(--c-quiet)', 1),
    ("imza->c-quiet",
     r'(class="upkeep-sign"[^>]*?)color: var\(--bone-ghost\)', r'\1color: var(--c-quiet)', 1),
    # --- DEKORATIF ghost -> c-rule (gorsel-notr, rol sistemi tamligi; ESNEK: dile gore var/yok) ---
    ("lang-sep->c-rule",
     r'(\.lang-sep\s*\{[^}]*?)var\(--bone-ghost\)', r'\1var(--c-rule)', "esnek"),
    ("limb-border-bottom->c-rule",
     r'(\.limb\s*\{[^}]*?border-bottom: 1px solid )var\(--bone-ghost\)', r'\1var(--c-rule)', "esnek"),
    ("limb-first-border-top->c-rule",
     r'(\.limb:first-child\s*\{[^}]*?border-top: 1px solid )var\(--bone-ghost\)', r'\1var(--c-rule)', "esnek"),
    ("seal-sep->c-rule",
     r'(\.seal-sep\s*\{[^}]*?)var\(--bone-ghost\)', r'\1var(--c-rule)', "esnek"),
    ("text-decoration->c-rule",
     r'text-decoration-color: var\(--bone-ghost\)', r'text-decoration-color: var(--c-rule)', "esnek"),
    # --- kok punto px -> rem (kullanici font tercihi korunur) ---
    ("font-px->rem",
     re.escape("font-size: clamp(17px, 1.2vw, 21px);"),
     "font-size: clamp(1.0625rem, 1.2vw, 1.3125rem);", 1),
    # --- erisilebilirlik blogu (::selection anchor, blok ONUNE) ---
    ("a11y-blok",
     r'        ::selection \{',
     A11Y_BLOCK.replace("\\", "\\\\"), 1),
    # --- theme-color meta (viewport anchor) ---
    ("theme-color",
     r'(<meta name="viewport"[^>]*>)',
     r'\1\n    <meta name="theme-color" content="#060604">', 1),
]


def process(content, lang):
    log = []
    for name, old_re, new_re, expected in CHANGES:
        matches = re.findall(old_re, content)
        if expected == "esnek":
            n = len(matches)
            content = re.sub(old_re, new_re, content)
            log.append(f"  {name}: OK (esnek, {n})")
            continue
        if len(matches) != expected:
            raise SystemExit(f"[{lang}] ASSERT FAIL '{name}': {len(matches)} bulundu, {expected} beklendi")
        content = re.sub(old_re, new_re, content, count=expected)
        log.append(f"  {name}: OK")
    return content, log


def main():
    paths = {d: ROOT / d / "index.html" for d in LANGS}
    for d, p in paths.items():
        if not p.exists():
            raise SystemExit(f"YOK: {p}")

    # global guard: --c-text P1 isaretcisi (atomik)
    applied = [d for d in LANGS if "--c-text" in paths[d].read_text(encoding="utf-8")]
    if len(applied) == 7:
        print("P1 zaten uygulanmis (7/7 --c-text var); cikiliyor.")
        return
    if applied:
        raise SystemExit(f"YARIM DURUM: {applied} uygulanmis, digerleri degil. Elle incele.")

    # FAZ1: hepsini bellekte isle + dogrula
    results = {}
    for d in LANGS:
        c = paths[d].read_text(encoding="utf-8")
        c2, log = process(c, d)
        results[d] = c2
        print(f"[{d}] FAZ1 gecti:")
        for line in log:
            print(line)

    # FAZ2: hepsi gecti, topluca yaz
    for d in LANGS:
        paths[d].write_text(results[d], encoding="utf-8")
    print(f"\nFAZ2: {len(LANGS)} dosya yazildi (atomik).")


if __name__ == "__main__":
    main()
