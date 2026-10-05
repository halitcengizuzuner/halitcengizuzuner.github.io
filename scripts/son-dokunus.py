#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""son-dokunus.py — dürüstlük damgası (Portal O491, site dönüşümü P0).

dateModified + görünür "son dokunuş" tarihini git/çalışma-ağacından TÜRETİR
(elle yazılmaz; O430 bayatlama-karşıtı ilke). İdempotent + deploy-kapısı.

Tarih mantığı (her dosya ayrı):
  - Çalışma ağacında değişikse  -> bugün (henüz commit edilmemiş düzenleme).
  - Değilse                      -> o dosyanın son commit tarihi (%cs, ISO).
Böylece tarih sistem saati + git durumundan türer, hiçbir yere elle yazılmaz.

Yaptığı iki iş:
  1. JSON-LD WebSite düğümüne "dateModified": "YYYY-AA-GG" ekler/günceller.
  2. Bakım paragrafından sonra görünür <p data-son-dokunus> ekler/günceller
     (her dilde kendi etiketiyle; kök landing'de bakım paragrafı yok -> atlanır).

Kullanım: python3 scripts/son-dokunus.py [--kontrol]
  --kontrol: hiçbir şey yazmaz; eksik/bayat damga varsa EXIT 1 (deploy-kapısı).
"""
import re
import sys
import subprocess
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# dosya -> (bakım-p kapanış imzası | None, görünür etiket)
# Kök (index.html) bakım paragrafı taşımaz -> imza None (yalnız dateModified).
DOSYALAR = {
    "index.html":          (None,                  None),
    "turkce/index.html":   (">Atölye</a>.</p>",    "Son dokunuş"),
    "english/index.html":  (">The Workshop</a>.</p>", "Last updated"),
    "espanol/index.html":  (">El Taller</a>.</p>",  "Última actualización"),
    "francais/index.html": ("Atelier</a>.</p>",     "Dernière mise à jour"),
    "deutsch/index.html":  (">Die Werkstatt</a>.</p>", "Zuletzt aktualisiert"),
    "zhongwen/index.html": (">工坊</a>。</p>",       "最后更新"),
    "nihongo/index.html":  (">工房</a>。</p>",       "最終更新"),
}

STIL = ("font-size: clamp(0.72rem, 0.85vw, 0.8rem); color: var(--bone-dim); "
        "letter-spacing: 0.04em; margin-top: 1.4rem; opacity: 0.85;")


def git_tarih(rel: str) -> str:
    """Çalışma ağacında değişikse bugün, değilse son commit tarihi (ISO)."""
    degisik = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", rel], cwd=BASE
    ).returncode != 0
    if degisik:
        return date.today().isoformat()
    r = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", rel],
        cwd=BASE, capture_output=True, text=True,
    )
    return (r.stdout.strip() or date.today().isoformat())


def isle(rel, imza, etiket, kontrol):
    p = BASE / rel
    metin = p.read_text(encoding="utf-8")
    orig = metin
    tarih = git_tarih(rel)

    # --- 1) JSON-LD dateModified (WebSite düğümü) ---
    if re.search(r'"dateModified"\s*:\s*"[^"]*"', metin):
        metin = re.sub(r'"dateModified"\s*:\s*"[^"]*"',
                       f'"dateModified": "{tarih}"', metin, count=1)
    else:
        m = re.search(r'([ \t]*)"@type":\s*"WebSite",', metin)
        if not m:
            return None, f"{rel}: JSON-LD WebSite düğümü bulunamadı"
        girinti = m.group(1)
        metin = metin.replace(
            m.group(0),
            f'{m.group(0)}\n{girinti}"dateModified": "{tarih}",', 1)

    # --- 2) Görünür son-dokunuş satırı (bakım paragrafı olan diller) ---
    if imza is not None:
        if "data-son-dokunus" in metin:
            metin = re.sub(
                r'(<p[^>]*data-son-dokunus[^>]*>)[^<]*(</p>)',
                rf'\g<1>{etiket}: {tarih}\g<2>', metin, count=1)
        else:
            if metin.count(imza) != 1:
                return None, f"{rel}: bakım imzası «{imza}» {metin.count(imza)}× (1 olmalı)"
            yeni = (f'{imza}\n    <p class="son-dokunus" data-son-dokunus '
                    f'style="{STIL}">{etiket}: {tarih}</p>')
            metin = metin.replace(imza, yeni, 1)

    degisti = metin != orig
    if kontrol:
        # deploy-kapısı: dateModified tarihi bugünün çalışma-ağacı tarihiyle uyumsuzsa bayat
        return degisti, None  # çağıran yorumlar
    if degisti:
        p.write_text(metin, encoding="utf-8")
    return degisti, None


def main():
    kontrol = "--kontrol" in sys.argv
    hata, yazildi = [], []
    for rel, (imza, etiket) in DOSYALAR.items():
        degisti, err = isle(rel, imza, etiket, kontrol)
        if err:
            hata.append(err)
        elif degisti:
            yazildi.append(rel)

    if hata:
        print("✗ son-dokunus HATA:")
        for h in hata:
            print("   ", h)
        return 1

    if kontrol:
        if yazildi:
            print("✗ Bayat/eksik son-dokunuş damgası:", ", ".join(yazildi))
            return 1
        print("✓ son-dokunuş damgaları güncel.")
        return 0

    if yazildi:
        print(f"✓ son-dokunuş damgalandı ({len(yazildi)} dosya):")
        for r in yazildi:
            print("   ", r, "→", git_tarih(r))
    else:
        print("✓ değişiklik yok (zaten güncel).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
