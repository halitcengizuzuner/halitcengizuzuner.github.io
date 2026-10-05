#!/usr/bin/env python3
"""P2-B1: landmark + baslik semantigi (iskelet, render-nötr yarisi).
- .gate-words div -> <h1> (+ CSS reset: margin 0, font-weight 400)
- <main id="icerik"> sarma (nav sonrasi -> footer.seal oncesi)
- sr-only h2 (duvar/kadro/bakim) + .sr-only CSS
- translate="no" (kadro limb-name 5x + metin-ici HCU)
7 dil ortak kol; yalniz h2-duvar yerlesimi TR (.mind-ici) != 6 dil (ilk .first-wall oncesi).
Uygulayici+kirici: assert'ler = count-assert (sessiz hata yok). FAZ1 bellekte dogrula, FAZ2 atomik yaz.
Kullanim: python3 scripts/p2b1-iskelet.py [--only turkce] [--yaz]   (--yaz yoksa FAZ1 kuru calisma)
"""
import re, sys, pathlib

ROOT = pathlib.Path.home() / "halitcengizuzuner.github.io"
DILLER = ["turkce", "english", "espanol", "francais", "deutsch", "zhongwen", "nihongo"]

# sr-only h2 cevirileri (duvar, kadro, bakim) - DeepSeek native-check sonrasi guncellenebilir
H2 = {
    "turkce":   ("Düşünceler", "Kadro", "Bakım"),
    "english":  ("Thoughts", "Collaborators", "Upkeep"),
    "espanol":  ("Pensamientos", "Colaboradores", "Mantenimiento"),
    "francais": ("Pensées", "Collaborateurs", "Entretien"),
    "deutsch":  ("Gedanken", "Mitwirkende", "Pflege"),
    "zhongwen": ("思考", "团队", "维护"),
    "nihongo":  ("思考", "チーム", "保守"),
}

SRONLY_CSS = ('.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; '
              'margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }\n        ')


def transform(dil, html):
    rapor = []

    # --- 0. idempotent guard: zaten uygulanmissa dur ---
    if '<h1 class="gate-words">' in html or 'id="icerik"' in html:
        return None, ["zaten uygulanmis (idempotent skip)"]

    # --- 1. .gate-words div -> h1 ---
    html, n = re.subn(r'<div class="gate-words">(.*?)</div>',
                      r'<h1 class="gate-words">\1</h1>', html, flags=re.S)
    assert n == 1, f"{dil}: gate-words div->h1 beklenen 1, bulunan {n}"
    rapor.append("h1 (gate-words)")

    # CSS reset: h1 default margin+bold ez (blok-ici, format-bagimsiz)
    html, n = re.subn(r'(\.gate-words\s*\{[^}]*?)\}',
                      r'\1 margin: 0; font-weight: 400; }', html, count=1)
    assert n == 1, f"{dil}: gate-words CSS reset beklenen 1, bulunan {n}"
    rapor.append("h1 CSS reset")

    # --- 2. .sr-only CSS (ilk `.gate {` kurali oncesi; .gate-words'e eslesmez) ---
    html, n = re.subn(r'(\.gate\s*\{)', SRONLY_CSS + r'\1', html, count=1)
    assert n == 1, f"{dil}: sr-only CSS yerlesimi beklenen 1, bulunan {n}"
    rapor.append("sr-only CSS")

    # --- 3. main#icerik sarma (nav sonrasi, footer.seal oncesi) ---
    html, n = re.subn(r'(</nav>)', r'\1\n\n<main id="icerik">', html, count=1)
    assert n == 1, f"{dil}: main acilis (</nav>) beklenen 1, bulunan {n}"
    html, n = re.subn(r'(<footer class="seal">)', r'</main>\n\n\1', html, count=1)
    assert n == 1, f"{dil}: main kapanis (footer.seal) beklenen 1, bulunan {n}"
    rapor.append("main#icerik")

    duvar, kadro, bakim = H2[dil]

    # --- 4a. h2 kadro (limbs section) ---
    html, n = re.subn(r'(<section class="limbs">)',
                      rf'\1\n    <h2 class="sr-only">{kadro}</h2>', html, count=1)
    assert n == 1, f"{dil}: h2 kadro (limbs) beklenen 1, bulunan {n}"

    # --- 4b. h2 bakim (upkeep section, style tasir) ---
    html, n = re.subn(r'(<section class="upkeep"[^>]*>)',
                      rf'\1\n    <h2 class="sr-only">{bakim}</h2>', html, count=1)
    assert n == 1, f"{dil}: h2 bakim (upkeep) beklenen 1, bulunan {n}"

    # --- 4c. h2 duvar: TR .mind-ici / 6 dil ilk .first-wall oncesi ---
    if dil == "turkce":
        html, n = re.subn(r'(<div class="mind">)',
                          rf'\1\n    <h2 class="sr-only">{duvar}</h2>', html, count=1)
    else:
        html, n = re.subn(r'(<section class="first-wall">)',
                          rf'<h2 class="sr-only">{duvar}</h2>\n\1', html, count=1)
    assert n == 1, f"{dil}: h2 duvar beklenen 1, bulunan {n}"
    rapor.append("h2 x3 (duvar/kadro/bakim)")

    # --- 5a. translate="no" kadro limb-name (5x) ---
    html, n = re.subn(r'<span class="limb-name">',
                      r'<span class="limb-name" translate="no">', html)
    assert n == 5, f"{dil}: limb-name translate=no beklenen 5, bulunan {n}"
    rapor.append("translate=no limb-name (5)")

    # --- 5b. translate="no" metin-ici HCU (buyuk harf, sarilmamis: oncesi >, sonrasi < degil) ---
    html, n = re.subn(r'(?<!>)Halit Cengiz Uzuner(?!<)',
                      r'<span translate="no">Halit Cengiz Uzuner</span>', html)
    assert n >= 1, f"{dil}: HCU translate=no beklenen >=1, bulunan {n}"
    rapor.append(f"translate=no HCU ({n})")

    return html, rapor


def main():
    only = None
    yaz = "--yaz" in sys.argv
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    hedef = [only] if only else DILLER
    sonuc = {}  # dil -> (yeni_html, path, rapor)

    # FAZ1: bellekte donustur + dogrula
    for dil in hedef:
        p = ROOT / dil / "index.html"
        html = p.read_text(encoding="utf-8")
        yeni, rapor = transform(dil, html)
        if yeni is None:
            print(f"  {dil}: {rapor[0]}")
            continue
        sonuc[dil] = (yeni, p, rapor)
        print(f"  {dil}: FAZ1 OK — {', '.join(rapor)}")

    if not sonuc:
        print("Yazilacak dil yok (hepsi idempotent skip?).")
        return

    # FAZ2: atomik yaz
    if yaz:
        for dil, (yeni, p, _) in sonuc.items():
            p.write_text(yeni, encoding="utf-8")
        print(f"\nFAZ2: {len(sonuc)} dosya YAZILDI.")
    else:
        print(f"\n(kuru calisma; yazmak icin --yaz) — {len(sonuc)} dosya hazir.")


if __name__ == "__main__":
    main()
