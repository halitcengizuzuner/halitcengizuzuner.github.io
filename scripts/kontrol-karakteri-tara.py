#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Site geneli kontrol-karakteri + bos-tirnak tarayicisi.

NEDEN VAR (Portal O301):
24 Haziran 2026'da bir noktalama turu (commit d145c35, "Ingilizce tirnak ->
Almanca") regex backreference yerine ham 0x01 bayti yazdi. Almanca
'wer-hat-das-geschrieben.html' sayfasinda 75 terim tek kontrol karakterine
coktu: „Kuenstliche Intelligenz“ -> „“. Okur bir ay boyunca bos tirnak gordu;
kavramin tanimlandigi cumlede kavram yoktu.

Hicbir mevcut kapi bunu yakalamadi: HTML gecerliydi, tirnak sayisi dengeliydi,
urun-denetle temiz donuyordu, dil-sizinti taramasi temiz donuyordu. Bozulmayi
kardes oturum (Temas) okurken fark etti.

DERS: bicimsel donusum turu (tirnak, tire, bosluk normallestirme) icerik turu
kadar tehlikelidir; tirnagin VARLIGINI degil ICERIGINI de denetlemek gerekir.

KULLANIM:
    python3 scripts/kontrol-karakteri-tara.py            # tum site
    python3 scripts/kontrol-karakteri-tara.py <yol>      # tek dosya/dizin
Cikis kodu: 0 temiz, 1 bulgu var (gece bakimi bunu okur).
"""
import os, re, sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UZANTI = (".html", ".xml", ".txt", ".json", ".md")

# C0 kontrol karakterleri; sekme/satirbasi/satirsonu mesru
YASAK = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Dile gore bos tirnak ciftleri: acilis hemen kapanisla bitiyorsa icerik yok.
# Yalnizca TIPOGRAFIK tirnaklar taranir; duz " ve ' kod icinde (content:'',
# var x="") mesru bos deger olarak gecer ve yanlis alarm uretir.
BOS_TIRNAK = [
    ("„“", "Almanca"), ("“”", "curly"),
    ("«»", "Fransizca"), ("« »", "Fransizca-bosluklu"),
    ("「」", "CJK-kose"), ("《》", "CJK-kitap"), ("‘’", "curly-tek"),
]

# <script> ve <style> bloklari metin degildir; kontrol karakteri disinda taranmaz
KOD_BLOGU = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)


def dosyalar(hedef):
    if os.path.isfile(hedef):
        yield hedef
        return
    for kok, dizinler, adlar in os.walk(hedef):
        dizinler[:] = [d for d in dizinler if d not in (".git", "node_modules", ".jekyll-cache")]
        for ad in adlar:
            if ad.endswith(UZANTI):
                yield os.path.join(kok, ad)


def main():
    hedef = sys.argv[1] if len(sys.argv) > 1 else KOK
    bulgular = []

    for yol in dosyalar(hedef):
        try:
            metin = open(yol, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        goreli = os.path.relpath(yol, KOK)

        # kontrol karakteri: kod bloklari dahil her yerde yasak
        for m in YASAK.finditer(metin):
            cevre = re.sub(r"\s+", " ", metin[max(0, m.start() - 45):m.start() + 45])
            bulgular.append((goreli, f"kontrol karakteri 0x{ord(m.group()):02x}", cevre))

        # bos tirnak: yalniz metin govdesinde anlamli
        govde = KOD_BLOGU.sub(" ", metin)
        for cift, etiket in BOS_TIRNAK:
            n = govde.count(cift)
            if n:
                bulgular.append((goreli, f"bos tirnak {cift} ({etiket}) x{n}", ""))

    if not bulgular:
        print("✓ TEMIZ — kontrol karakteri ve bos tirnak yok")
        return 0

    print(f"⚠ {len(bulgular)} BULGU\n")
    for yol, tur, cevre in bulgular:
        print(f"  {yol}\n    {tur}")
        if cevre:
            print(f"    ...{cevre}...")
    print("\nBir bicimsel donusum turu metni yemis olabilir (Portal O301 deseni).")
    print("Onarim: bozulma oncesi commit'i bul (git log -S), icerigi ORADAN al, uydurma.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
