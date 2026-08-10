#!/usr/bin/env python3
"""duvar-denetle.py — ANA SAYFA DUVARI harita-simetri kapısı (Portal O388).

KÖK SORUN (Halit güven-krizi O388): harita PASİF kayıttı, duvarı ona zorlayan
kapı yoktu → who-wrote-this 5 dilde, kendisi-hakkında 4 dilde, JA tümüyle
duvardan düşmüş, hiçbiri alarm çalmamıştı (çalacak zil yoktu). Bu araç o zil.

harita-otorite: her CANLI makale, her dilin ana sayfa duvarında link taşıyor mu?
EXIT 1 = kusur (deploy kapısı, hreflang-tara.py kardeşi). JA harita-dışı (6-dil
harita) → nihongo canlı dosyaları ayrı sayılır.
"""
import json, pathlib, sys
SITE = pathlib.Path(__file__).resolve().parent.parent
HARITA = pathlib.Path.home() / "portal-worker" / "yayin_varlik_haritasi.jsonl"
LANGS = {"tr": "turkce", "en": "english", "de": "deutsch",
         "fr": "francais", "es": "espanol", "zh": "zhongwen"}
# duvar-DIŞI KASITLI (rapor DEĞİL / fikir yazısı / kök özel sayfa) — CLAUDE.md ayrımı
DUVAR_DISI = {"on-listening", "dinleme-ustune", "genesis", "workshop",
              "atolye", "werkstatt", "atelier", "taller", "index"}

def slug_kok(url_veya_dosya):
    return url_veya_dosya.split("/")[-1].replace(".html", "").replace("-dinle", "")

idx = {c: (SITE / d / "index.html").read_text(encoding="utf-8") for c, d in LANGS.items()}
makaleler = []
for l in HARITA.read_text(encoding="utf-8").splitlines():
    if not l.strip():
        continue
    o = json.loads(l)
    if o.get("diller"):
        makaleler.append(o)

kusur = []
for m in makaleler:
    ad = m.get("kanonik_baslik") or m.get("baslik") or "?"
    for c in LANGS:
        d = m["diller"].get(c)
        if not d:
            continue
        if "/raporlar/" not in d["url"]:
            continue  # kök sayfa / fikir yazısı (On Listening vb.) — rapor değil, duvar-dışı
        slug = d["url"].split("/raporlar/")[-1]
        if slug_kok(slug) in DUVAR_DISI:
            continue
        if slug not in idx[c]:
            kusur.append(f"{c}: {ad} → {slug} duvarda YOK")

# JA (nihongo) harita-dışı: canlı raporları ayrı denetle
ja_dir = SITE / "nihongo" / "raporlar"
if ja_dir.exists():
    ja_idx = (SITE / "nihongo" / "index.html").read_text(encoding="utf-8")
    ja_eksik = [p.name for p in ja_dir.glob("*.html")
                if "-dinle" not in p.name
                and slug_kok(p.name) not in DUVAR_DISI
                and p.name not in ja_idx]
    if ja_eksik:
        kusur.append(f"ja: {len(ja_eksik)}/{len(list(ja_dir.glob('*.html')))} makale duvarda YOK "
                     f"(örn: {', '.join(sorted(ja_eksik)[:4])} …)")

if kusur:
    print(f"✗ DUVAR SİMETRİ KUSURU — {len(kusur)} kalem:")
    for k in kusur:
        print(f"  {k}")
    print("\n→ harita-otorite: yukarıdaki makaleler CANLI ama o dilin ana sayfasında TIKLANAMAZ.")
    sys.exit(1)
print(f"✓ Duvar simetri TEMİZ — {len(makaleler)} makale × {len(LANGS)} dil + JA denetlendi.")
sys.exit(0)
