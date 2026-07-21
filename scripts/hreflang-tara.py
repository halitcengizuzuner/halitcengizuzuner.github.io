#!/usr/bin/env python3
"""hreflang bütünlük taraması — dil eşleştirmesinin SESSİZ kırılmasını yakalar.

Neden ayrı bir kapı (O308'de ölçülerek kuruldu):
Portal'ın mevcut kapıları hreflang'in VARLIĞINI sayıyordu ("7/sayfa simetri"),
HEDEFİNİ değil. Bu yüzden iki makale ailesi aylarca şu kusuru taşıdı:

    <link rel="alternate" hreflang="en" href="https://.../english/">

Yani "bu makalenin İngilizcesi" olarak İngilizce ANA SAYFA gösteriliyordu —
oysa çeviri sayfalarının hepsi mevcuttu. Satır sayısı 7'ydi, sayan her kapı
temiz diyordu.

Neden ağır: hreflang KARŞILIKLILIK ister. A sayfası B'yi gösterip B sayfası
A'yı göstermezse Google çift yönlü doğrulamayı yapamaz ve kümeyi TÜMDEN yok
sayabilir. Yani kayıp tek sayfayla sınırlı kalmaz; ailenin tamamı dil
eşleştirmesini kaybeder. Sessiz, çünkü sayfa 200 döner ve içerik yerindedir.

DÖRT SINIF, dördü ayrı şey söyler:
  · hedef DİZİN        → çeviri yerine ana sayfa gösteriliyor (O308 kusuru)
  · hedef YOK          → dosya adı yanlış yazılmış (kırık küme)
  · KARŞILIKSIZ        → A→B var, B→A yok (Google kümeyi düşürebilir)
  · KENDİNE REFERANS YOK → sayfa kendi dilini bildirmiyor (Google şartı)

⚠ NOINDEX AYRIMI — aracın kendi ilk sürümünün kusuruydu, aynı turda onarıldı:
İlk koşuda 66 "karşılıksız" çıktı ve HEPSİ Japonca sayfalardandı. Kusur değil,
BİLİNÇLİ ARA DURUM: JA sayfaları noindex ile duruyor (geyşa kararı O265 —
16 makale bitmeden vitrin açılmaz), öbür diller onlara henüz işaret etmiyor,
çünkü `ja` hreflang'inin 18 sayfaya eklenmesi sona saklanan TEK ATOMİK iştir.

Yayına kapalı sayfa hreflang kümesine katılmaz; ondan karşılıklılık beklemek
aracın kusurudur (O306: üç hâli ayırmayan rapor, aracın körlüğünü metnin
yapısı gibi gösterir). Ama TERS YÖN kusur olarak kalır: YAYINDAKİ bir sayfa
noindex bir sayfayı gösteriyorsa, okuru yayımlanmamış içeriğe yollar.

Kullanım:  python3 scripts/hreflang-tara.py [--sessiz]
Çıkış kodu 1 = kusur var (deploy öncesi kapı olarak kullanılabilir).
"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup

KOK = Path(__file__).resolve().parent.parent
SITE = "https://halitcengizuzuner.com/"
DILLER = ["turkce", "english", "deutsch", "francais", "espanol", "zhongwen", "nihongo"]


def coz(p: Path):
    """(hreflang kümesi, yayında_mı) — tek okumada ikisi.

    Yayında değil = robots meta'sında noindex. O sayfa Google'ın hreflang
    kümesine girmez; ondan karşılıklılık beklenmez.
    """
    s = BeautifulSoup(p.read_text(encoding="utf-8"), "lxml")
    out = {}
    for l in s.find_all("link", rel="alternate"):
        hl, href = l.get("hreflang"), l.get("href", "")
        if hl and href.startswith(SITE):
            out[hl] = href[len(SITE):]
    robots = s.find("meta", attrs={"name": "robots"})
    yayinda = not (robots and "noindex" in (robots.get("content") or "").lower())
    return out, yayinda


def sayfalar():
    for d in DILLER:
        kok = KOK / d / "raporlar"
        if not kok.exists():
            continue
        for p in sorted(kok.glob("*.html")):
            if p.name != "index.html" and "dinle" not in p.name:
                yield p


def kalibre():
    """Bilinen-bozuk sınaması. SIFIR, başarının değil ölçümsüzlüğün işareti
    olabilir (O306) — bu yüzden kaç birim sınandığı yazdırılır."""
    ornekler = [
        ("hedef dizin", {"en": "english/"}, "dizin"),
        ("hedef yok", {"en": "english/raporlar/yok-boyle-dosya.html"}, "yok"),
        ("temiz", {"en": "english/raporlar/research-constitution.html"}, None),
    ]
    gecen = 0
    for ad, kume, beklenen in ornekler:
        bulunan = None
        for hl, yol in kume.items():
            t = KOK / yol
            if t.is_dir() or yol.endswith("/"):
                bulunan = "dizin"
            elif not t.is_file():
                bulunan = "yok"
        ok = bulunan == beklenen
        gecen += ok
        print(f"  {'✓' if ok else '✗'} [kalibrasyon] {ad}: {bulunan or 'temiz'} "
              f"(beklenen {beklenen or 'temiz'})")

    # KARŞILIKLILIK AYAĞI — ilk sürümde YOKTU ve tam o eksende yanlış pozitif
    # ürettim (66 JA satırı). Sentetik değil, GERÇEK sayfa çiftiyle sınanır:
    # kanonik doğru bilinen bir aile (O308'de elle doğrulandı, 12/12 simetri).
    a = KOK / "english/raporlar/research-constitution.html"
    b = KOK / "turkce/raporlar/arastirma-anayasasi.html"
    ka, ya = coz(a)
    kb, yb = coz(b)
    cift_ok = ("turkce/raporlar/arastirma-anayasasi.html" in ka.values()
               and "english/raporlar/research-constitution.html" in kb.values())
    gecen += cift_ok
    print(f"  {'✓' if cift_ok else '✗'} [kalibrasyon] karşılıklılık (gerçek çift): "
          f"{'A↔B çift yönlü' if cift_ok else 'ÇİFT YÖN YOK'}")

    # NOINDEX ayrımı gerçekten okunuyor mu (yanlış pozitifin kaynağı buydu)
    ja = KOK / "nihongo/raporlar/tea-table.html"
    noindex_ok = ja.is_file() and not coz(ja)[1] and ya
    gecen += noindex_ok
    print(f"  {'✓' if noindex_ok else '✗'} [kalibrasyon] noindex ayrımı: "
          f"{'JA kapalı / EN yayında' if noindex_ok else 'AYRIM OKUNAMADI'}")

    toplam = len(ornekler) + 2
    print(f"  → {gecen}/{toplam} kalibrasyon örneği sınandı.")
    return gecen == toplam


def main():
    sessiz = "--sessiz" in sys.argv
    print("KALİBRASYON:")
    if not kalibre():
        print("✗ KALİBRASYON BAŞARISIZ — tarama İPTAL.")
        sys.exit(1)
    print("✓ Kalibrasyon geçti.\n")

    tum, yayinda = {}, {}
    for p in sayfalar():
        yol = str(p.relative_to(KOK))
        tum[yol], yayinda[yol] = coz(p)

    dizin, kirik, karsiliksiz, kendisiz, blokusuz = [], [], [], [], []
    kapali_atlandi = 0

    for yol, kume in tum.items():
        if not kume:
            blokusuz.append(yol)
            continue
        # kendine referans: sayfanın kendi yolu kümede olmalı
        if yol not in kume.values():
            kendisiz.append(yol)
        for hl, hedef in kume.items():
            t = KOK / hedef
            if hedef.endswith("/") or t.is_dir():
                dizin.append(f"{yol}  [{hl} → {hedef or '/'}]")
            elif not t.is_file():
                kirik.append(f"{yol}  [{hl} → {hedef}]")
            elif hl != "x-default" and hedef in tum:
                if yol not in tum[hedef].values():
                    # Yayına kapalı sayfadan karşılıklılık BEKLENMEZ: o sayfa
                    # Google'ın kümesine girmiyor. Ters yön kusurdur.
                    if not yayinda[yol]:
                        kapali_atlandi += 1
                    elif not yayinda[hedef]:
                        karsiliksiz.append(
                            f"{yol} → {hedef}  ([{hl}] hedef YAYINA KAPALI)")
                    else:
                        karsiliksiz.append(
                            f"{yol} → {hedef}  ([{hl}] geri dönmüyor)")

    print(f"{len(tum)} makale sayfası tarandı.\n")
    kusur = 0
    for baslik, liste, aciklama in [
        ("HEDEF DİZİN — çeviri yerine ana sayfa gösteriliyor", dizin,
         "Makalenin o dildeki karşılığı ana sayfa DEĞİLDİR. Gerçek çeviri "
         "sayfası varsa oraya bağla; yoksa o hreflang satırını KALDIR."),
        ("HEDEF YOK — kırık küme", kirik,
         "Dosya adı yanlış yazılmış ya da sayfa taşınmış."),
        ("KARŞILIKSIZ — tek yönlü hreflang", karsiliksiz,
         "Google çift yönlü doğrulama ister; karşılıksız küme yok sayılabilir."),
        ("KENDİNE REFERANS YOK", kendisiz,
         "Her sayfa kendi dilini de bildirmeli (Google şartı)."),
    ]:
        if liste:
            kusur += len(liste)
            print(f"⚠ {baslik} — {len(liste)}:")
            for x in liste:
                print(f"    {x}")
            print(f"  → {aciklama}\n")

    # Bilinçli ara durumlar SAYILARAK bildirilir — sessiz muafiyet, muafiyet
    # değil körlüktür; okur neyin sınanmadığını görmeli (O306).
    if kapali_atlandi:
        print(f"○ YAYINA KAPALI SAYFADAN çıkan {kapali_atlandi} hreflang "
              f"karşılıklılık taramasından muaf tutuldu.\n"
              f"  Bu sayfalar noindex; Google'ın kümesine girmiyorlar. Görünür\n"
              f"  yapıldıkları turda öbür dillere karşılık satırı eklenmeli —\n"
              f"  muafiyet o ana kadar geçerlidir, kalıcı değildir.\n")

    if blokusuz and not sessiz:
        print(f"○ hreflang bloğu YOK — {len(blokusuz)} sayfa (tek dilli olabilir, "
              f"kusur değil):\n    " + ", ".join(blokusuz) + "\n")

    if kusur == 0:
        print("✓ hreflang bütünlüğü TEMİZ.")
    else:
        print(f"✗ {kusur} kusur bulundu.")
    sys.exit(1 if kusur else 0)


if __name__ == "__main__":
    main()
