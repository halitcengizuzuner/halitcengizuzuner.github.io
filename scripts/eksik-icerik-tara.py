#!/usr/bin/env python3
"""
Eksik-içerik taraması — çeviri sayfasında DÜŞÜRÜLMÜŞ içeriği yakalar.

Kaynak: Film oturumunun çeviri birikimi (`ceviri_ilkeleri.md` §16.8-16.10),
Portal O303'te ölçülüp uyarlandı. Film'in dersi:

  "Blok blok denetim yalnız VAR OLAN blokları sınar; düşürülmüş repliği
   yapısal olarak yakalayamaz. Ters yönde tara: kaynağın hangi birimleri
   hedefte hiç eşleşmedi? Bu kayıp OLMAYAN ŞEYİN İZİ OLMADIĞI İÇİN hiçbir
   blok denetiminde görünmez."

Portal'ın bütün kapıları (aksan yoğunluğu, entity, tırnak içeriği, künye,
sızıntı, urun-denetle) VAR OLAN metni sınar. Bu betik yokluğu sınar.

ÇIKTI BULGU DEĞİL, SORUDUR. Sapma meşru olabilir:
  · TR başlıkta dinle-katmanı tanıtımı (KATMAN MİMARİSİ: TR 2 katman)
  · çeviride "çeviri notları" başlığı
  · künye sayısı dillerde bilinçli farklı olabilir (O288)
Meşruluğu belgelenmemiş sapma üretim kusuru sayılır (O302 ZH dersi:
kaydedilmemiş tercih hatadan ayırt edilemez).

ÜÇ TUZAK — hepsi O303'te bizzat düşülüp kodlandı:
 1. KALİBRASYON AİLE BAŞINA. Tek dosyada kalibre edildi, tarayıcının kapsam
    kusuru (16 makalenin 14'ünü atlaması) kalibrasyonun dışında kaldı.
    Üç şablon ailesi var: main.content · main.book · div.book.
 2. İNDEKS-BAZLI HİZALAMA YANLIŞ-POZİTİF ÜRETİR. Çevirilerde Kaynakça ayrı
    h2, TR'de değil → indeksle hizalayınca "X. bölüm hiçbir dilde yok" gibi
    sahte bulgu çıkar. Hizalama BAŞLIK NUMARASIYLA yapılır (Film'in
    "num-bazlı vs timecode-bazlı hizalama" dersinin karşılığı).
 3. KAYNAKÇA BÖLÜMÜ SAYIMA GİRMEZ. TR'de kaynakça son bölümün içinde
    tematik h3 gruplarıyla durur; çevirilerde ayrı h2. Karşılaştırma yalnız
    romen-rakamlı gövde bölümlerinde anlamlıdır.

Kullanım:  python3 scripts/eksik-icerik-tara.py [--tam]
"""
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

KOK = Path(__file__).resolve().parent.parent
SITE = "https://halitcengizuzuner.com/"
ROMEN = re.compile(r"^\s*([IVX]+)[\.\s]")
# CJK sürümler bölümleri Çince rakamla numaralar (一、二、三…), Roma rakamıyla
# değil. Tanınmazsa "numaralı bölüm YOK" yanlış alarmı çıkar ve gerçek sinyali
# gölgeler (Portal O304: yuzsuz-iletisim ZH iki tur boyunca yanlış ⚠ verdi).
CJK_RAKAM = re.compile(r"^\s*([一二三四五六七八九十]+)\s*[、．.,\s]")
_CJK_BIR = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9}
_ROMEN_TABLO = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
                "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]


def _cjk_romene(im: str):
    """一 → I, 十二 → XII. Tanınmazsa None."""
    if "十" in im:
        on, _, birler = im.partition("十")
        n = (_CJK_BIR.get(on, 1) if on else 1) * 10 + (_CJK_BIR.get(birler, 0) if birler else 0)
    else:
        n = _CJK_BIR.get(im, 0)
    return _ROMEN_TABLO[n] if 0 < n < len(_ROMEN_TABLO) else None


def bolum_no(baslik: str):
    """h2 metninden bölüm numarasını romen olarak döndür (Latin veya CJK)."""
    m = ROMEN.match(baslik)
    if m:
        return m.group(1)
    m = CJK_RAKAM.match(baslik)
    return _cjk_romene(m.group(1)) if m else None
# Latin diller Türkçeden UZUN olur (TR sondan eklemeli, kompakt).
# EN/DE ölçüldü: 1.08-1.09. Bu eşiğin altı eksiklik şüphesidir.
ESIK_ALT = 0.90
CJK = {"zh", "ja"}


def _kapsayici(s):
    main = s.find("main", class_="content")
    if main is not None:
        return main, "main.content"
    for etiket in ("main", "div"):
        b = s.find(etiket, class_="book")
        if b is not None:
            return b, f"{etiket}.book"
    return None, None


def govde_bolumleri(yol: Path):
    """{romen: (h3_sayisi, karakter)} — yalnız numaralı gövde bölümleri."""
    s = BeautifulSoup(yol.read_text(encoding="utf-8"), "lxml")
    kap, aile = _kapsayici(s)
    if kap is None:
        return None, None
    out, cur = {}, None
    for el in kap.find_all(["h2", "h3", "p", "li", "blockquote"]):
        if el.name == "h2":
            cur = bolum_no(el.get_text(strip=True))
            if cur:
                out[cur] = [0, 0]
        elif cur:
            if el.name == "h3":
                out[cur][0] += 1
            else:
                out[cur][1] += len(el.get_text(" ", strip=True))
    return out, aile


def kardesler(yol: Path):
    """hreflang'dan kardeşler — canlı yapıdan, ikincil kayıttan değil (E459)."""
    s = BeautifulSoup(yol.read_text(encoding="utf-8"), "lxml")
    out = {}
    for link in s.find_all("link", rel="alternate"):
        hl, href = link.get("hreflang"), link.get("href", "")
        if not hl or hl in ("x-default", "tr") or not href.startswith(SITE):
            continue
        p = KOK / href[len(SITE):]
        if p.exists():
            out[hl] = p
    return out


def kalibre_et(ornek: Path):
    temiz, aile = govde_bolumleri(ornek)
    if not temiz:
        print(f"  ✗ {ornek.name}: numaralı bölüm yok")
        return False
    s = BeautifulSoup(ornek.read_text(encoding="utf-8"), "lxml")
    kap, _ = _kapsayici(s)
    # Silinecek h3 SAYIMA GİREN bölgeden seçilir: numaralı bir h2'den sonra
    # gelenler. Belge sırasındaki ilk h3'ler numaralı bölüm dışında olabilir
    # (kaynakça, giriş) — o zaman kalibrasyon kendi kusurundan patlar.
    aday, sayiliyor = [], False
    for el in kap.find_all(["h2", "h3"]):
        if el.name == "h2":
            sayiliyor = bolum_no(el.get_text(strip=True)) is not None
        elif sayiliyor:
            aday.append(el)
    silinen = 0
    for h3 in aday[:2]:
        h3.decompose()
        silinen += 1
    tmp = KOK / "_kalibrasyon_gecici.html"
    tmp.write_text(str(s), encoding="utf-8")
    bozuk, _ = govde_bolumleri(tmp)
    tmp.unlink()
    t = sum(v[0] for v in temiz.values())
    b = sum(v[0] for v in bozuk.values())
    ok = (t - b) == silinen
    print(f"  {'✓' if ok else '✗'} [{aile}] {ornek.name}: h3 {t}→{b} "
          f"(fark {t-b}, beklenen {silinen})")
    return ok


def main():
    tam = "--tam" in sys.argv
    sayfalar = sorted(p for p in (KOK / "turkce/raporlar").glob("*.html")
                      if "dinle" not in p.name and p.name != "index.html")

    print("KALİBRASYON (her şablon ailesinden bir örnek):")
    aileler = {}
    for p in sayfalar:
        b, a = govde_bolumleri(p)
        # Kalibrasyon örneği de kalibre seçilir: romen-rakamsız makale
        # (ör. aynen-oyle) örnek olursa kalibrasyon kendi kusurundan patlar.
        if b and a and a not in aileler:
            aileler[a] = p
    if not aileler or not all(kalibre_et(p) for p in aileler.values()):
        print("✗ KALİBRASYON BAŞARISIZ — tarama İPTAL.")
        sys.exit(1)
    print("✓ Kalibrasyon geçti.\n")

    supheli = 0
    for tr in sayfalar:
        ref, _ = govde_bolumleri(tr)
        if not ref:
            if tam:
                print(f"· {tr.name}: numaralı bölüm yok — karşılaştırma dışı")
            continue
        ref_h3 = ref_kar = 0  # yapısal bölümler düşülerek aşağıda hesaplanır
        # Her dilde AYNI olan sapma yapısal farktır, eksiklik değil.
        # Canlı vaka: TR'de kaynakça son numaralı bölümün içinde tematik h3
        # gruplarıyla durur, çevirilerde ayrı h2 → altı dilde birden "X:12→0".
        tum = {}
        for dil, yol in sorted(kardesler(tr).items()):
            c, _ = govde_bolumleri(yol)
            if c:
                tum[dil] = c
        yapisal = {b for b in ref
                   if tum and all(b in c and c[b][0] == 0 and ref[b][0] > 0
                                  for c in tum.values())}
        ref_h3 = sum(v[0] for b, v in ref.items() if b not in yapisal)
        ref_kar = sum(v[1] for b, v in ref.items() if b not in yapisal)

        satirlar = []
        for dil, yol in sorted(kardesler(tr).items()):
            c, _ = govde_bolumleri(yol)
            if not c:
                satirlar.append(f"    {dil}: ⚠ numaralı bölüm YOK ({yol.relative_to(KOK)})")
                continue
            c_h3 = sum(v[0] for b, v in c.items() if b not in yapisal)
            c_kar = sum(v[1] for b, v in c.items() if b not in yapisal)
            oran = c_kar / ref_kar if ref_kar else 1
            eksik_h3 = ref_h3 - c_h3
            # CJK'de karakter oranı doğrudan kıyaslanamaz (1 karakter ~2.5 Latin)
            supheli_oran = (dil not in CJK) and oran < ESIK_ALT
            if eksik_h3 > 0 or supheli_oran:
                bolum_farki = [f"{b}:{ref[b][0]}→{c[b][0]}" for b in ref
                               if b in c and c[b][0] < ref[b][0] and b not in yapisal]
                satirlar.append(
                    f"    {dil}: h3 {c_h3}/{ref_h3} (−{eksik_h3}) · "
                    f"karakter oranı {oran:.2f}"
                    + (f" · eksilen bölümler → {' '.join(bolum_farki)}" if bolum_farki else ""))
        if satirlar:
            supheli += 1
            print(f"■ {tr.name}  [TR h3={ref_h3} karakter={ref_kar}]")
            print("\n".join(satirlar))

    print(f"\n{len(sayfalar)} TR makale · {supheli} tanesinde eksiklik ŞÜPHESİ."
          "\nŞüphe bulgu değildir: çeviri notunda/künyede belgelenmiş kısaltma meşrudur;"
          "\nbelgelenmemiş olan üretim kusuru sayılır (O302).")


if __name__ == "__main__":
    main()
