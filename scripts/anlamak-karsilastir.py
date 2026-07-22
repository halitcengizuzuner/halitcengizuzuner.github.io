#!/usr/bin/env python3
"""anlamak ailesi restorasyon karşılaştırıcısı (O313).

Mod 1 (özet):  python3 anlamak-karsilastir.py <dil>
    TR ↔ dil: TÜM bölüm/alt-bölüm çiftleri, eşiksiz (araç eşiği süzülmüş
    alt kümeydi; restorasyon tam listeye bakar — O312 devir talimatı).
Mod 2 (detay): python3 anlamak-karsilastir.py <dil> <romen>
    O bölümün TR ve çeviri paragraflarını tam metin, numaralı döker.
"""
import sys
from pathlib import Path

REPO = Path.home() / "halitcengizuzuner.github.io"
sys.path.insert(0, str(REPO / "scripts"))
et = __import__("eksik-icerik-tara")

DOSYALAR = {
    "tr": REPO / "turkce/raporlar/anlamak.html",
    "es": REPO / "espanol/raporlar/comprender.html",
    "en": REPO / "english/raporlar/understanding.html",
    "zh": REPO / "zhongwen/raporlar/understanding.html",
    "fr": REPO / "francais/raporlar/comprendre.html",
    "de": REPO / "deutsch/raporlar/verstehen.html",
}


def alt_bolumler_tam(yol):
    """et.alt_bolumler ile aynı gezinme; başlık TAM + paragraf metinleri."""
    from bs4 import BeautifulSoup
    s = BeautifulSoup(yol.read_text(encoding="utf-8"), "lxml")
    kap, _ = et._kapsayici(s)
    out, cur, alt = {}, None, None
    onsoz = []  # h2 öncesi + bölüm içi h3 öncesi paragraflar da görünsün
    for el in kap.find_all(["h2", "h3", "p", "li", "blockquote"]):
        if not et._sayimda(el):
            continue
        if el.name == "h2":
            cur = et.bolum_no(el.get_text(strip=True))
            alt = None
            if cur:
                out[cur] = {"_baslik": el.get_text(" ", strip=True),
                            "_serbest": [], "altlar": []}
        elif cur is None:
            continue
        elif el.name == "h3":
            alt = {"baslik": el.get_text(" ", strip=True), "p": []}
            out[cur]["altlar"].append(alt)
        else:
            txt = el.get_text(" ", strip=True)
            if alt is not None:
                alt["p"].append((el.name, txt))
            else:
                out[cur]["_serbest"].append((el.name, txt))
    return out


def ozet(dil):
    tr = alt_bolumler_tam(DOSYALAR["tr"])
    cv = alt_bolumler_tam(DOSYALAR[dil])
    print(f"TR ↔ {dil.upper()} — bölüm/alt-bölüm tam listesi (eşiksiz)")
    for b, tb in tr.items():
        cb = cv.get(b)
        if cb is None:
            print(f"\n■ {b}. BÖLÜM — {dil.upper()}'DE YOK: «{tb['_baslik']}»")
            continue
        ts = sum(len(t) for _, t in tb["_serbest"])
        cs = sum(len(t) for _, t in cb["_serbest"])
        so = f" · serbest p {len(tb['_serbest'])}→{len(cb['_serbest'])} kütle {cs}/{ts}={cs/ts:.2f}" if ts else ""
        print(f"\n■ {b}. «{tb['_baslik'][:60]}»{so}")
        if len(tb["altlar"]) != len(cb["altlar"]):
            print(f"  ⚠ h3 sayısı farklı: TR {len(tb['altlar'])} ↔ {len(cb['altlar'])}")
        for i, ta in enumerate(tb["altlar"]):
            ca = cb["altlar"][i] if i < len(cb["altlar"]) else None
            tk = sum(len(t) for _, t in ta["p"])
            if ca is None:
                print(f"  · «{ta['baslik'][:48]}» TR p={len(ta['p'])} ↔ YOK")
                continue
            ck = sum(len(t) for _, t in ca["p"])
            oran = ck / tk if tk else 0
            isaret = " ◄◄" if (oran < 0.60 or len(ta["p"]) - len(ca["p"]) >= 2) else ""
            print(f"  · «{ta['baslik'][:48]}» p {len(ta['p'])}→{len(ca['p'])} kütle {oran:.2f}{isaret}")


def detay(dil, romen):
    tr = alt_bolumler_tam(DOSYALAR["tr"])[romen]
    cv = alt_bolumler_tam(DOSYALAR[dil]).get(romen)
    for ad, blok in (("TR", tr), (dil.upper(), cv)):
        print(f"\n{'='*70}\n{ad} — {romen}. «{blok['_baslik']}»\n{'='*70}")
        for tag, txt in blok["_serbest"]:
            print(f"  [serbest/{tag}] {txt}\n")
        for a in blok["altlar"]:
            print(f"--- h3: {a['baslik']} ({len(a['p'])} öğe) ---")
            for j, (tag, txt) in enumerate(a["p"], 1):
                print(f"  [{j}/{tag}] {txt}\n")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        ozet(sys.argv[1])
    elif len(sys.argv) == 3:
        detay(sys.argv[1], sys.argv[2])
    else:
        print(__doc__)
