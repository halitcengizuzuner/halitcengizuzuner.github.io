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
# Arap rakamıyla numaralanan makaleler (O308: mahremiyet-paradoksu ailesi 6 dilde
# "1. Giriş / 2. ..." kullanıyor). Romen/CJK aranıyordu, bu aile bu yüzden
# "numarasız" sayılıp HİÇ taranmıyordu — 7 dilde canlı, en büyük makalelerden.
#
# ⚠ TARİH TUZAĞI, ölçülerek bulundu: `deutsch/bild-des-gluecks.html` başlığı
# "3. Juni 1963" — Almanca tarih yazımı noktalıdır ve bu desene UYAR. Türkçesi
# "3 Haziran 1963" (noktasız) uymuyordu, yani tuzak dile özgü doğuyor. Tek
# başına regex yetmez; korunma makale düzeyindeki NUMARALI-ORAN eşiğidir
# (aşağıda ORAN_ESIK): bir başlık numara sanılabilir, on başlığın sekizi
# sanılamaz.
ARAP_RAKAM = re.compile(r"^\s*(\d{1,2})\s*[\.\)]\s")
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
    """h2 metninden bölüm numarasını romen olarak döndür (Romen, CJK veya Arap)."""
    m = ROMEN.match(baslik)
    if m:
        return m.group(1)
    m = CJK_RAKAM.match(baslik)
    if m:
        return _cjk_romene(m.group(1))
    m = ARAP_RAKAM.match(baslik)
    if m:
        n = int(m.group(1))
        return _ROMEN_TABLO[n] if 0 < n < len(_ROMEN_TABLO) else None
    return None


# Bir makale "numaralı" sayılsın diye h2'lerinin bu oranı numaralı olmalı.
# Tek başlığın numara sanılması kaçınılmaz (tarih, liste, yıl); belirleyici
# olan çoğunluktur. mahremiyet ailesi 8/10 = 0.80 geçer; bild-des-gluecks
# 1/10 = 0.10 geçmez ve numarasız kalır (doğru sonuç).
ORAN_ESIK = 0.6
# Latin diller Türkçeden UZUN olur (TR sondan eklemeli, kompakt).
# EN/DE ölçüldü: 1.08-1.09. Bu eşiğin altı eksiklik şüphesidir.
ESIK_ALT = 0.90
CJK = {"zh", "ja"}

# ── GÖVDE-GENELİ EKSENİN TABANI: DİL NORMU (O308) ────────────────────────────
# Sabit eşik (0.90) bu eksende KÖRDÜR ve körlüğü ölçüldü: Latin çevirilerin
# gerçek oran bandı 1.05-1.33 (site geneli medyan 1.19), çünkü Türkçe sondan
# eklemeli ve kompakttır. Normal oranı 1.19 olan bir makalede %20 içerik kaybı
# 0.95 verir — sabit eşiğin ÜSTÜNDE kalır, araç susar.
#
# Taban bu yüzden her dilin KENDİ site-geneli medyanıdır (de 1.21 · en 1.12 ·
# es 1.18 · fr 1.22 · zh 0.41). Kazanç iki katlı:
#   · duyarlılık: sabit eşik yalnız anlamak/ES'i görüyordu; dil normu aynı
#     makaleyi DE/ES/FR/ZH dördünde birden gösterdi (bilinen kusur, O305-307).
#   · CJK artık dışlanmıyor: zh kendi normuna göre ölçülüyor, ayrı eşik
#     gerekmiyor. Öncesinde ZH bu eksende hiç ölçülemiyordu.
#
# ⚠ SINIR (O306'nın medyan dersinin aynısı, burada da geçerli): norm site
# genelinden gelir. Bütün çeviriler sistematik olarak kısaysa norm onlarla
# birlikte düşer ve eksen susar. Bu eksen AZINLIK sapmasını yakalar; toptan
# kısaltmayı yakalayamaz. Yedeği yoktur, bilerek kabul edilmiştir.
NORM_ESIK = 0.80


# Sitede bilinen gövde kapsayıcıları. Sıra ÖNEMLİ: dar olan önce denenir,
# `main`/`article` en sonda kalır (onlar nav/footer'ı da içerebilir).
#
# O306: liste üç aileden sekize çıktı. Öncesinde tarayıcı 16 makalenin
# 7'sinde kapsayıcı BULAMIYOR, bulamadığını da `--tam` verilmedikçe
# SÖYLEMİYORDU — "16 TR makale · 1'inde şüphe" satırı hepsi taranmış gibi
# okunuyordu. En pahalısı `bunu-kim-yazdi`ydı: 13 numaralı bölüm, yedi dil,
# tam taranabilir bir makale, hiç bakılmadan geçiyordu.
AILELER = [
    ("main", "content"), ("main", "book"), ("div", "book"),
    ("div", "wrap"), ("div", "content"), ("div", "container"),
    ("article", None), ("main", None), ("body", None),
]
# Gövde sayımına girmeyen bölgeler: kapsayıcı geniş seçilirse (article/main)
# site iskeleti sayıma sızar ve kütle oranını sahte şişirir.
SAYIM_DISI = {"nav", "footer", "header"}


def _kapsayici(s):
    for etiket, sinif in AILELER:
        b = s.find(etiket, class_=sinif) if sinif else s.find(etiket)
        # h2 taşımayan kap gövde değildir (ör. yalnız başlık saran div).
        if b is not None and b.find("h2") is not None:
            return b, f"{etiket}.{sinif}" if sinif else etiket
    return None, None


def _sayimda(el):
    """Eleman gövdeye mi ait? nav/footer/header içindekiler sayılmaz."""
    for ata in el.parents:
        if ata.name in SAYIM_DISI:
            return False
    return True


def govde_bolumleri(yol: Path):
    """{romen: (h3_sayisi, karakter)} — yalnız numaralı gövde bölümleri."""
    s = BeautifulSoup(yol.read_text(encoding="utf-8"), "lxml")
    kap, aile = _kapsayici(s)
    if kap is None:
        return None, None
    out, cur = {}, None
    h2_toplam = 0
    for el in kap.find_all(["h2", "h3", "p", "li", "blockquote"]):
        if not _sayimda(el):
            continue
        if el.name == "h2":
            h2_toplam += 1
            cur = bolum_no(el.get_text(strip=True))
            if cur:
                out[cur] = [0, 0]
        elif cur:
            if el.name == "h3":
                out[cur][0] += 1
            else:
                out[cur][1] += len(el.get_text(" ", strip=True))
    # NUMARALI-ORAN EŞİĞİ (O308): birkaç başlık tesadüfen numara desenine
    # uyabilir (Almanca tarih "3. Juni 1963"). Azınlık eşleşmesiyle hizalama
    # kurmak, hizalamanın kaymasından daha kötüdür — sahte bulgu üretir ve
    # gerçek sinyali gölgeler. Çoğunluk yoksa makale numarasız sayılır.
    if h2_toplam and len(out) / h2_toplam < ORAN_ESIK:
        return {}, aile
    return out, aile


def alt_bolumler(yol: Path):
    """{romen: [(h3_başlığı, paragraf_sayısı, karakter), ...]}

    İKİNCİ EKSEN (O305). Birinci eksen (govde_bolumleri) bir alt bölümün
    VARLIĞINI sınar; bu, İÇİNİ sınar. Aradaki fark canlı bir kusurla ölçüldü:
    `anlamak`/ES h3 sayısı 39/39 TAM görünüyordu, ama VI. bölümde 23 paragraf
    eksikti — O303'ün onardığı üç alt bölüm doluydu, dokunulmayan altısı
    yarı boştu. Başlık duruyor, altındaki metin yok: h3 ekseni buna kördür.
    """
    s = BeautifulSoup(yol.read_text(encoding="utf-8"), "lxml")
    kap, _ = _kapsayici(s)
    if kap is None:
        return {}
    out, cur, alt = {}, None, None
    for el in kap.find_all(["h2", "h3", "p", "li", "blockquote"]):
        if not _sayimda(el):
            continue
        if el.name == "h2":
            cur = bolum_no(el.get_text(strip=True))
            alt = None
            if cur:
                out[cur] = []
        elif cur is None:
            continue
        elif el.name == "h3":
            alt = [el.get_text(" ", strip=True)[:44], 0, 0]
            out[cur].append(alt)
        elif alt is not None:
            if el.name == "p":
                alt[1] += 1
            alt[2] += len(el.get_text(" ", strip=True))
    return out


def alt_bolum_kutlesi(ref_alt, c_alt):
    """Alt bölüm bazında kütle kaybı → [(bölüm, başlık, TR_p, dil_p, oran)].

    İKİ TUZAK, ikisi de bu ekseni kurarken düşünüldü:

    1. İNDEKS HİZALAMASI YALNIZ h3 SAYISI EŞİTKEN GÜVENLİ. Sayı farklıysa
       zaten birinci eksen konuşuyor; orada indeksle hizalamak kaymış
       eşleştirme üretir (tuzak #2'nin alt bölüm hâli).
    2. AZ PARAGRAF ≠ EKSİK İÇERİK. Çeviri paragrafları birleştirebilir.
       Ayırt eden: karakter oranı. Paragraf düşmüş ama karakter oranı o
       makalenin MEDYANI kadarsa birleştirmedir, meşrudur. Medyan taban
       alınır (genel ortalama değil): eksik alt bölümler azınlıkken medyan
       sağlam kalır, ortalama onlarla birlikte çöker ve kusuru normalleştirir.
       Medyan CJK/Latin ayrımını da kendiliğinden çözer — her dil kendi
       ölçeğine göre normalize olur, sabit eşiğe gerek kalmaz.
    """
    ciftler = []
    for b, ref_list in ref_alt.items():
        c_list = c_alt.get(b, [])
        if len(c_list) != len(ref_list) or not ref_list:
            continue  # sayı farklı → birinci eksenin işi
        for (rb, rp, rk), (_, cp, ck) in zip(ref_list, c_list):
            if rk:
                ciftler.append((b, rb, rp, cp, ck / rk))
    if not ciftler:
        return []
    oranlar = sorted(x[4] for x in ciftler)
    medyan = oranlar[len(oranlar) // 2]
    if medyan <= 0:
        return []
    return [(b, rb, rp, cp, o) for (b, rb, rp, cp, o) in ciftler
            if o < medyan * 0.72 and rp - cp >= 2]


def _kapsayici_genis(s):
    """h2 şartı ARAMAYAN kapsayıcı — üçüncü eksenin gövde ölçümü için.

    `_kapsayici` h2 taşımayan kabı gövde saymaz, çünkü bölüm-bazlı eksenler
    h2'siz sayfada zaten çalışamaz. Ama gövde-geneli kütle ölçümü h2
    gerektirmez: `cay-masasi` ve `kulaga-yazmak` hiç h2 kullanmıyor ve altı
    dilde canlı oldukları hâlde bugüne dek HİÇ ölçülmediler.

    En çok metin taşıyan aile seçilir (nav/footer/header düşülerek) — dar
    kaplar (yalnız başlık saran div) böylece elenir.
    """
    en_iyi, en_ad, en_kutle = None, None, 0
    for etiket, sinif in AILELER:
        b = s.find(etiket, class_=sinif) if sinif else s.find(etiket)
        if b is None:
            continue
        k = len(b.get_text(" ", strip=True))
        if k > en_kutle:
            en_iyi, en_ad, en_kutle = b, f"{etiket}.{sinif or ''}", k
    return en_iyi, en_ad


# Çeviri notu bloklarının sınıf adları. Bu bölüm ÇEVİRİDE VAR, ASILDA YOK →
# kütle karşılaştırmasında düşülmezse çeviriyi olduğundan uzun gösterir.
CEVIRI_NOTU = ("transcreation", "ceviri-not", "translation-not")


def _temiz_govde(yol: Path):
    """(kapsayıcı, aile) — iskelet ve çeviri notları AYIKLANMIŞ hâlde."""
    s = BeautifulSoup(yol.read_text(encoding="utf-8"), "lxml")
    for t in s(["script", "style", "nav", "footer", "header"]):
        t.decompose()
    for n in s.find_all(class_=lambda c: c and any(
            k in x for x in (c if isinstance(c, list) else [c])
            for k in CEVIRI_NOTU)):
        n.decompose()
    return _kapsayici_genis(s)


def govde_kutlesi(yol: Path):
    """Gövdenin toplam karakter kütlesi — h2/numara GEREKTİRMEZ.

    ÜÇÜNCÜ EKSENİN BİRİNCİ KATMANI (O308). Numaralı-bölüm ekseni 16 makalenin
    yalnız 5'ini görebiliyordu; 9'u numarasız, 2'si h2'siz olduğu için 11
    makale düşürülmüş içerik açısından HİÇ ölçülmemişti — aralarında 7 dilde
    canlı olanlar var.

    Bu en kaba eksendir ve bilinçli olarak öyle: bölüm hizalaması kurulamayan
    yerde bile "çeviri asıldan belirgin kısa mı?" sorusu sorulabilir. O303'te
    ölçülen taban geçerli: Latin diller Türkçeden UZUNDUR (EN/DE 1.08-1.09),
    çünkü Türkçe sondan eklemeli ve kompakttır. Belirgin altı şüphedir.

    ⚠ TAM METİN, p/li/blockquote DEĞİL — ilk sürümde yapı-bazlı saydım ve
    ARAÇ YANLIŞ POZİTİF ÜRETTİ: `cay-masasi` diyalog biçiminde ve metninin
    %93'ü paragraf etiketi dışında duruyor (TR tam metin 8821, paragraf
    sayımı 629). Araç üç dilde "kütle 0.59×" dedi; gerçek oranlar 1.35-1.50,
    yani çeviriler asıldan UZUN, eksiklik yok. Yapı-bazlı sayım yapının
    kendisi değişince kör olur (O305: ölçüm aracının kusuru sağlam metni
    bozuk gösterir).

    ⚠ ÇEVİRİ NOTLARI DÜŞÜLÜR, ölçülmüş zorunluluk: notlar gövdenin %5-23'ünü
    tutuyor (cay-masasi/zh %23, mutlulugun-resmi/zh %17). Düşülmezse %20
    eksik bir çeviriyi %20'lik çeviri notu maskeler ve araç susar. Paragraf
    bazında ölçtüğümde bu risk SIFIR görünmüştü — doğru ölçümdü ama yanlış
    sorunun cevabıydı; notlar paragraf etiketi kullanmıyor.
    """
    kap, aile = _temiz_govde(yol)
    if kap is None:
        return 0, None
    return len(kap.get_text(" ", strip=True)), aile


def baslik_bolumleri(yol: Path):
    """[(h2 başlığı, paragraf, karakter), ...] — SIRAYLA, numara aranmadan.

    ÜÇÜNCÜ EKSENİN İKİNCİ KATMANI: numarasız ama h2'li makaleler (9 tane).
    """
    s = BeautifulSoup(yol.read_text(encoding="utf-8"), "lxml")
    kap, _ = _kapsayici(s)
    if kap is None:
        return []
    out, cur = [], None
    for el in kap.find_all(["h2", "p", "li", "blockquote"]):
        if not _sayimda(el):
            continue
        if el.name == "h2":
            cur = [el.get_text(" ", strip=True)[:44], 0, 0]
            out.append(cur)
        elif cur is not None:
            if el.name == "p":
                cur[1] += 1
            cur[2] += len(el.get_text(" ", strip=True))
    return out


def baslik_sirasi_kutlesi(ref, cev):
    """Başlık SIRASIYLA hizala → kütlesi çöken bölümler.

    ⚠ Hizalama yalnız h2 SAYILARI EŞİTKEN kurulur. Bu, O303 tuzak #2'nin
    (indeks-bazlı hizalama yanlış-pozitif üretir) doğrudan uygulaması:
    çevirilerde Kaynakça ayrı h2 olabilir, TR'de bölüm içinde durur; sayı
    farklıyken indeksle hizalamak her bölümü bir kaydırır ve makalenin
    TAMAMINI sahte bulgu olarak raporlar.

    Sayı farklıysa bu eksen SUSAR — ama gövde-geneli eksen (govde_kutlesi)
    yine konuşur, yani makale ölçümsüz kalmaz.

    Eşik mantığı alt-bölüm ekseniyle aynı ve aynı gerekçeyle MEDYAN tabanlı:
    her dil kendi ölçeğine normalize olur, CJK için ayrı eşik gerekmez.
    """
    if len(ref) != len(cev) or not ref:
        return []
    ciftler = [(rb, rp, cp, ck / rk)
               for (rb, rp, rk), (_, cp, ck) in zip(ref, cev) if rk]
    if not ciftler:
        return []
    oranlar = sorted(x[3] for x in ciftler)
    medyan = oranlar[len(oranlar) // 2]
    if medyan <= 0:
        return []
    return [(rb, rp, cp, o) for (rb, rp, cp, o) in ciftler
            if o < medyan * 0.72 and rp - cp >= 2]


def kardesler(yol: Path):
    """hreflang'dan kardeşler — canlı yapıdan, ikincil kayıttan değil (E459)."""
    s = BeautifulSoup(yol.read_text(encoding="utf-8"), "lxml")
    out = {}
    for link in s.find_all("link", rel="alternate"):
        hl, href = link.get("hreflang"), link.get("href", "")
        if not hl or hl in ("x-default", "tr") or not href.startswith(SITE):
            continue
        p = KOK / href[len(SITE):]
        # is_file, exists DEĞİL (O308): bazı hreflang'ler DİZİNE işaret ediyordu
        # (`.../english/` — makale yerine ana sayfa). exists() dizinde de True
        # döner, sonra read_text IsADirectoryError ile çöker. Kusur onarıldı ama
        # kapı kalıyor: hedef dosya değilse kardeş sayılmaz.
        if p.is_file():
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
    # BOŞ KALİBRASYON GEÇMİŞ SAYILMAZ (O306). Silinecek h3 yoksa eski kod
    # `(t-b) == silinen` → `0 == 0` ile "✓ geçti" diyordu: hiçbir şey sınamadan
    # onay. Aynı desen aynı turda test betiğimde de çıktı (boş küme "yakaladı"
    # raporladı) — sıfır, başarının değil ölçümsüzlüğün işaretidir.
    if not aday:
        print(f"  ○ [{aile}] {ornek.name}: numaralı bölümde h3 YOK — "
              f"ikinci eksen bu ailede SINANAMADI (birinci eksen çalışır)")
        return True
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


def kalibre_alt_eksen():
    """İkinci eksenin kalibrasyonu — sentetik, üç ayaklı.

    Kalibre edilmemiş tarayıcı sessizliğini "temiz" diye satar (O303: tek
    dosyada kalibre edilen tarayıcı 16 makalenin 14'ünü atlayıp "geçti" dedi).
    Üç ayak ayrı şeyi sınar: yakalıyor mu · susması gerekende susuyor mu ·
    CJK ölçeğinde de çalışıyor mu.
    """
    ref = {"I": [("A", 10, 1000), ("B", 10, 1000), ("C", 10, 1000), ("D", 10, 1000)]}
    testler = [
        ("yakalama", ref,
         {"I": [("a", 10, 1100), ("b", 10, 1100), ("c", 4, 300), ("d", 10, 1100)]},
         ["C"]),
        # Latin norm 1.1× — hiçbiri eksik değil, susmalı.
        ("yanlış pozitif yok", ref,
         {"I": [("a", 10, 1100), ("b", 9, 1050), ("c", 10, 1120), ("d", 10, 1100)]},
         []),
        # CJK ~0.26× — kütle Latin ölçüsünde "düşük" ama dilin normu bu.
        # Sabit eşik burada yanlış alarm verirdi; medyan normalizasyonu
        # yalnız gerçek sapmayı (C) yakalamalı.
        ("CJK ölçeği", ref,
         {"I": [("a", 10, 260), ("b", 10, 255), ("c", 3, 45), ("d", 10, 262)]},
         ["C"]),
    ]
    hepsi = True
    for ad, r, c, beklenen in testler:
        bulunan = [x[1] for x in alt_bolum_kutlesi(r, c)]
        ok = bulunan == beklenen
        hepsi &= ok
        print(f"  {'✓' if ok else '✗'} [alt-eksen] {ad}: "
              f"{bulunan or '—'} (beklenen {beklenen or '—'})")
    return hepsi


def kalibre_ucuncu_eksen():
    """Üçüncü eksenin kalibrasyonu — dört ayak, ikisi GERÇEK girdiyle.

    O306 dersi burada bağlayıcı: sentetik ayak mantığı sınar, aracın kendisini
    değil. Numara tanıma ayağı bu yüzden gerçek sayfa başlıklarıyla çalışır —
    tarih tuzağı ancak orada görünür.
    """
    hepsi = True

    # (1) Arap rakamı tanıma + TARİH TUZAĞI. Tuzak ölçülerek bulundu, sentetik
    # değil: Almanca tarih yazımı noktalıdır ve numara desenine uyar.
    ornekler = [("1. Giriş: Söyleyen ile yapan", "I"),
                ("2. Mahremiyet paradoksu", "II"),
                ("3. Juni 1963", "III"),          # tarih — desene UYAR
                ("1930 İki paşa torunu", None),   # yıl, noktasız — uymaz
                ("Obje Sorunu", None)]
    for baslik, beklenen in ornekler:
        bulunan = bolum_no(baslik)
        ok = bulunan == beklenen
        hepsi &= ok
        print(f"  {'✓' if ok else '✗'} [3. eksen] numara tanıma «{baslik[:26]}»: "
              f"{bulunan or '—'} (beklenen {beklenen or '—'})")

    # (2) ORAN EŞİĞİ tarih tuzağını gerçekten savuşturuyor mu? Tek başına
    # regex yetmiyordu; koruma makale düzeyinde. Gerçek sayfayla sınanır.
    dg = KOK / "deutsch/raporlar/bild-des-gluecks.html"
    if dg.is_file():
        b, _ = govde_bolumleri(dg)
        ok = not b   # "3. Juni 1963" tek başına makaleyi numaralı yapmamalı
        hepsi &= ok
        print(f"  {'✓' if ok else '✗'} [3. eksen] oran eşiği (gerçek sayfa, "
              f"tarih başlığı): {'numarasız sayıldı' if ok else 'TUZAĞA DÜŞTÜ'}")

    # (3) Başlık-sırası ekseni: yakalıyor mu, susması gerekende susuyor mu.
    ref = [("A", 10, 1000), ("B", 10, 1000), ("C", 10, 1000), ("D", 10, 1000)]
    for ad, cev, beklenen in [
        ("yakalama", [("a", 10, 1100), ("b", 10, 1100),
                      ("c", 4, 300), ("d", 10, 1100)], ["A"]),
        ("yanlış pozitif yok", [("a", 10, 1100), ("b", 9, 1050),
                                ("c", 10, 1120), ("d", 10, 1100)], []),
        # Sayı farklı → hizalama kurulamaz, SUSMALI (O303 tuzak #2).
        ("sayı farklıysa susar", [("a", 10, 1100), ("c", 4, 300)], []),
    ]:
        bulunan = [x[0] for x in baslik_sirasi_kutlesi(ref, cev)]
        # yakalama ayağında dönen başlık REFERANSIN başlığıdır (indeks 2 → "C")
        bekle = ["C"] if beklenen == ["A"] else beklenen
        ok = bulunan == bekle
        hepsi &= ok
        print(f"  {'✓' if ok else '✗'} [3. eksen] başlık-sırası {ad}: "
              f"{bulunan or '—'} (beklenen {bekle or '—'})")
    return hepsi


def kalibre_govde_geneli():
    """Gövde-geneli eksen GERÇEK sayfada çalışıyor mu (dördüncü ayak deseni).

    Bugüne dek hiç ölçülmemiş bir makale seçilir, gövdesinin yarısı silinir;
    oran belirgin düşmüyorsa zincir kopuktur.
    """
    tr = KOK / "turkce/raporlar/kulaga-yazmak.html"
    if not tr.is_file():
        print("  ○ [3. eksen] gövde-geneli: örnek sayfa yok — SINANAMADI")
        return True
    kar = kardesler(tr)
    if not kar:
        print("  ○ [3. eksen] gövde-geneli: kardeş yok — SINANAMADI")
        return True
    dil, cev = sorted(kar.items())[0]
    ref_k, _ = govde_kutlesi(tr)
    tam_k, _ = govde_kutlesi(cev)
    if not ref_k or not tam_k:
        print("  ○ [3. eksen] gövde-geneli: kütle ölçülemedi — SINANAMADI")
        return True

    s = BeautifulSoup(cev.read_text(encoding="utf-8"), "lxml")
    kap, _ = _kapsayici_genis(s)
    pler = [el for el in kap.find_all("p") if _sayimda(el)]
    for p in pler[:len(pler) // 2]:
        p.decompose()
    tmp = KOK / "_kalibrasyon_govde_gecici.html"
    tmp.write_text(str(s), encoding="utf-8")
    bozuk_k, _ = govde_kutlesi(tmp)
    tmp.unlink()

    tam_o, bozuk_o = tam_k / ref_k, bozuk_k / ref_k
    # Ölçüt ÜRETİMDEKİYLE aynı yapıda olmalı (ölçüm/norm < eşik), yoksa
    # kalibrasyon başka bir mantığı sınar (O306). Burada sağlam hâlin oranı
    # normun yerini tutar: aynı sayfa, tek değişken silinen içerik.
    ok = (bozuk_o / tam_o) < NORM_ESIK
    print(f"  {'✓' if ok else '✗'} [3. eksen] gövde-geneli (gerçek sayfa "
          f"{tr.name}↔{dil}): oran {tam_o:.2f} → {bozuk_o:.2f} "
          f"(norma göre {bozuk_o/tam_o:.2f}, eşik {NORM_ESIK}; "
          f"{len(pler)//2}/{len(pler)} paragraf silindi)"
          + ("" if ok else "  ← ZİNCİR KOPUK"))

    # ÇEVİRİ NOTU DÜŞME AYAĞI — ölçülmüş risk (%5-23) kapıyla kapatıldı mı?
    # Notu olan gerçek bir sayfada, ayıklanmış kütle ham kütleden KÜÇÜK olmalı.
    notlu = KOK / "deutsch/raporlar/teetisch.html"
    not_ok = True
    if notlu.is_file():
        ham = BeautifulSoup(notlu.read_text(encoding="utf-8"), "lxml")
        for t in ham(["script", "style", "nav", "footer", "header"]):
            t.decompose()
        ham_k = len(_kapsayici_genis(ham)[0].get_text(" ", strip=True))
        ayik_k, _ = govde_kutlesi(notlu)
        not_ok = ayik_k < ham_k
        print(f"  {'✓' if not_ok else '✗'} [3. eksen] çeviri notu düşülüyor "
              f"(teetisch.html): {ham_k} → {ayik_k} "
              f"(−%{100*(ham_k-ayik_k)/ham_k:.0f})"
              + ("" if not_ok else "  ← NOT DÜŞÜLMÜYOR, maskeleme riski açık"))
    return ok and not_ok


def kalibre_gercek_sayfa(tr_yol):
    """DÖRDÜNCÜ AYAK — sentetik değil, GERÇEK sayfayı bozarak sına (O306).

    Öbür üç ayak `alt_bolum_kutlesi`'ni elle yazılmış dict'lerle sınar; HTML'den
    veri üretimi zincirini (_kapsayici → _sayimda → alt_bolumler) hiç kullanmaz.
    O zincir koptuğunda üç ayak da yeşil yanar ve tarayıcı sessizce körleşir —
    O306'da tam bu oldu: 16 makalenin 12'si hiç taranmıyordu, kalibrasyon
    "✓ geçti" diyordu.

    Burada gerçek çeviri sayfasının bir alt bölümü boşaltılır; tarayıcı bunu
    görmüyorsa zincir kopuktur.

    ÖLÇÜLMÜŞ SINIR (O306): araç AZINLIK kusurunu yakalar. Aynı sayfada 27 alt
    bölümün 27'si birden boşaltıldığında yalnız 17'si yakalandı — taban MEDYAN
    olduğu için kusur çoğunluğa yayılınca medyan da düşer, eşik kusurla birlikte
    kayar. Yani bu araç SİSTEMATİK kısaltmaya kördür; onu birinci eksen
    (karakter oranı) yakalar. İki eksen bu yüzden birbirinin yedeği değildir.
    """
    kardes = next(iter(sorted(kardesler(tr_yol).items())), None)
    if kardes is None:
        print("  ○ [gerçek-sayfa] kardeş sayfa yok — SINANAMADI")
        return True
    dil, cev_yol = kardes
    ref = alt_bolumler(tr_yol)
    temiz = alt_bolumler(cev_yol)
    taban = len(alt_bolum_kutlesi(ref, temiz))

    s = BeautifulSoup(cev_yol.read_text(encoding="utf-8"), "lxml")
    kap, _ = _kapsayici(s)
    # En çok paragraflı alt bölümü boşalt (sinyal en güçlü orada).
    gruplar, cur, alt = [], None, None
    for el in kap.find_all(["h2", "h3", "p", "li", "blockquote"]):
        if not _sayimda(el):
            continue
        if el.name == "h2":
            cur, alt = bolum_no(el.get_text(strip=True)), None
        elif cur is None:
            continue
        elif el.name == "h3":
            alt = []
            gruplar.append(alt)
        elif alt is not None and el.name == "p":
            alt.append(el)
    hedef = max(gruplar, key=len, default=[])
    if len(hedef) < 4:
        print("  ○ [gerçek-sayfa] boşaltılacak alt bölüm yok — SINANAMADI")
        return True
    for p in hedef[:int(len(hedef) * 0.85) or 1]:
        p.decompose()

    tmp = KOK / "_kalibrasyon_gercek_gecici.html"
    tmp.write_text(str(s), encoding="utf-8")
    bozuk = len(alt_bolum_kutlesi(ref, alt_bolumler(tmp)))
    tmp.unlink()

    ok = bozuk > taban
    print(f"  {'✓' if ok else '✗'} [gerçek-sayfa] {tr_yol.name}↔{dil}: "
          f"alt bölüm boşaltıldı, bulgu {taban}→{bozuk}"
          + ("" if ok else "  ← ZİNCİR KOPUK"))
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
        if not (b and a):
            continue
        if a not in aileler:
            aileler[a] = p
        elif sum(v[0] for v in govde_bolumleri(aileler[a])[0].values()) == 0 \
                and sum(v[0] for v in b.values()) > 0:
            # Ailenin kayıtlı örneği h3 taşımıyorsa ikinci eksen sınanamaz;
            # h3 taşıyan kardeşi varsa örnek ONUNLA değiştirilir (O306).
            aileler[a] = p
    if not aileler or not all(kalibre_et(p) for p in aileler.values()):
        print("✗ KALİBRASYON BAŞARISIZ — tarama İPTAL.")
        sys.exit(1)
    if not kalibre_alt_eksen():
        print("✗ ALT-EKSEN KALİBRASYONU BAŞARISIZ — tarama İPTAL.")
        sys.exit(1)
    # h3 taşıyan bir aile örneğiyle gerçek-sayfa ayağı (O306).
    gercek_ornek = next((p for p in aileler.values()
                         if sum(v[0] for v in govde_bolumleri(p)[0].values()) > 0), None)
    if gercek_ornek is not None and not kalibre_gercek_sayfa(gercek_ornek):
        print("✗ GERÇEK-SAYFA KALİBRASYONU BAŞARISIZ — tarama İPTAL.")
        sys.exit(1)
    if not kalibre_ucuncu_eksen():
        print("✗ ÜÇÜNCÜ EKSEN KALİBRASYONU BAŞARISIZ — tarama İPTAL.")
        sys.exit(1)
    if not kalibre_govde_geneli():
        print("✗ GÖVDE-GENELİ KALİBRASYONU BAŞARISIZ — tarama İPTAL.")
        sys.exit(1)
    print("✓ Kalibrasyon geçti.\n")

    # ── BİRİNCİ GEÇİŞ: dil normlarını ölç (gövde-geneli eksenin tabanı) ──
    # İki geçiş şart: taban site genelinden gelir, tek sayfaya bakarak
    # kurulamaz. Norm hesabı bulgu üretmez, yalnız ölçek verir.
    ham_oranlar = {}
    for tr in sayfalar:
        ref_gk, _ = govde_kutlesi(tr)
        if not ref_gk:
            continue
        for dil, yol in sorted(kardesler(tr).items()):
            c_gk, _ = govde_kutlesi(yol)
            if c_gk:
                ham_oranlar.setdefault(dil, []).append((tr.name, c_gk / ref_gk))
    dil_normu = {}
    for dil, kayitlar in ham_oranlar.items():
        v = sorted(o for _, o in kayitlar)
        dil_normu[dil] = v[len(v) // 2]

    supheli = 0
    # KAPSAM DIŞI KALANLAR — sonda ZORUNLU raporlanır (O306).
    # Eskiden `--tam` bayrağına bağlıydı; bayraksız koşuda tarayıcı 16 makalenin
    # 12'sini sessizce atlıyor, sonra "16 TR makale · 1'inde şüphe" diyordu.
    # Sessiz kapsam kusuru gürültüden beterdir (O303): okur taranmayanı taranmış
    # sanır ve "temiz" raporu asılsız bir güven üretir.
    kapsam_disi = {"kapsayici": [], "numarasiz": [], "basliksiz": []}
    ucuncu_tarandi = 0
    for tr in sayfalar:
        ref, _ = govde_bolumleri(tr)
        if not ref:
            # ── ÜÇÜNCÜ EKSEN (O308): numara-bazlı hizalama kurulamayan
            # makaleler artık ölçümsüz KALMIYOR. Kapsam dışı bildirimi
            # duruyor (hangi eksende ölçülemediği bilgisi değerli), ama
            # yanına ölçülebilen ne varsa o konuluyor.
            satirlar = []
            ref_gk, _aile = govde_kutlesi(tr)
            ref_bas = baslik_bolumleri(tr)
            for dil, yol in sorted(kardesler(tr).items()):
                c_gk, _ = govde_kutlesi(yol)
                if ref_gk and c_gk:
                    oran = c_gk / ref_gk
                    norm = dil_normu.get(dil)
                    # CJK artık DIŞLANMIYOR: dil normu ölçeği kendisi çözüyor.
                    if norm and oran / norm < NORM_ESIK:
                        satirlar.append(
                            f"    {dil}: gövde kütlesi {c_gk}/{ref_gk} = {oran:.2f}× "
                            f"· {dil} normu {norm:.2f} → norma göre "
                            f"{oran/norm:.2f} (gövde-geneli eksen)")
                for baslik, rp, cp, o in baslik_sirasi_kutlesi(
                        ref_bas, baslik_bolumleri(yol)):
                    satirlar.append(
                        f"    {dil}: «{baslik}» paragraf {rp}→{cp}, "
                        f"kütle {o:.2f}× (başlık-sırası ekseni)")
            if ref_gk:
                ucuncu_tarandi += 1
            if satirlar:
                supheli += 1
                print(f"■ {tr.name}  [TR gövde={ref_gk} · üçüncü eksen]")
                print("\n".join(satirlar))

            s = BeautifulSoup(tr.read_text(encoding="utf-8"), "lxml")
            kap, _a = _kapsayici(s)
            # ÜÇ ayrı hâl, üçü ayrı şey söyler (O306 — ikisini birbirine
            # karıştırmak aracın kusurunu makalenin yapısı gibi gösterir):
            #   · h2 hiç yok        → makale bölüm başlığı kullanmıyor (yapı farkı)
            #   · h2 var, kap yok   → ARACIN körlüğü, AILELER genişletilmeli
            #   · kap var, numarasız→ numara-bazlı hizalama kurulamaz (meşru sınır)
            if not s.find_all("h2"):
                kapsam_disi["basliksiz"].append(tr.name)
            elif kap is None:
                kapsam_disi["kapsayici"].append(tr.name)
            else:
                kapsam_disi["numarasiz"].append(tr.name)
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
        # ── İKİNCİ EKSEN: alt bölümün İÇİ (O305) ──────────────────
        ref_alt = alt_bolumler(tr)
        for dil, yol in sorted(kardesler(tr).items()):
            kayip = alt_bolum_kutlesi(ref_alt, alt_bolumler(yol))
            for b, baslik, rp, cp, o in kayip:
                satirlar.append(
                    f"    {dil}: {b}. bölüm · «{baslik}» "
                    f"paragraf {rp}→{cp}, kütle {o:.2f}× (alt-bölüm ekseni)")

        # ── ÜÇÜNCÜ EKSENİN GÖVDE KATMANI — NUMARALILARDA DA (O312) ──
        # Kuru-koşla ölçülüp açıldı (O308 talimatı "önce ölç"): 6 numaralı
        # makale × 27 dil-çifti → 3 bulgu, üçü de bilinen gerçek kusur
        # (anlamak ES/FR/ZH), yanlış pozitif SIFIR. Kör bölge gerçekti:
        # numara ekseni yalnız numaralı bölümlerin İÇİNİ ölçer; anlamak'ta
        # gövdenin %22'si bölüm dışında (79156'nın 62042'si bölümlerde) ve
        # o kısım bu satırlar olmadan HİÇ ölçülmüyordu.
        #
        # BAŞLIK-SIRASI katmanı numaralılarda AÇILMADI: aynı kuru-koşta 0
        # bulgu; h2 hizalaması numara ekseninde zaten (daha sağlam anahtar
        # ile) var, indeks-bazlı ikinci hizalama mükerrerdir ve O303 tuzak
        # #2 sınıfı riski geri getirir.
        ref_gk, _gaile = govde_kutlesi(tr)
        if ref_gk:
            ucuncu_tarandi += 1
            for dil, yol in sorted(kardesler(tr).items()):
                c_gk, _ = govde_kutlesi(yol)
                if not c_gk:
                    continue
                oran = c_gk / ref_gk
                norm = dil_normu.get(dil)
                if norm and oran / norm < NORM_ESIK:
                    satirlar.append(
                        f"    {dil}: gövde kütlesi {c_gk}/{ref_gk} = {oran:.2f}× "
                        f"· {dil} normu {norm:.2f} → norma göre "
                        f"{oran/norm:.2f} (gövde-geneli eksen)")

        if satirlar:
            supheli += 1
            print(f"■ {tr.name}  [TR h3={ref_h3} karakter={ref_kar}]")
            print("\n".join(satirlar))

    tarandi = len(sayfalar) - sum(len(v) for v in kapsam_disi.values())
    # Gövde-geneli eksen O312'den beri numaralılarda DA çalışır → ucuncu_tarandi
    # artık evrensel kapsam sayacıdır; ondan eksik kalan makale ÖLÇÜMSÜZDÜR ve
    # sayısı gizlenmez (O306: sessiz kapsam kusuru gürültüden beterdir).
    print(f"\n{tarandi}/{len(sayfalar)} makale NUMARA ekseninde (h3 + alt bölüm) · "
          f"{ucuncu_tarandi}/{len(sayfalar)} makale GÖVDE-GENELİ eksende "
          f"(O312: numaralılar dahil) → ölçümsüz makale: "
          f"{len(sayfalar) - ucuncu_tarandi}.")
    print(f"{supheli} makalede eksiklik ŞÜPHESİ.")
    if kapsam_disi["kapsayici"]:
        print(f"\n⚠ ARACIN KÖRLÜĞÜ — kapsayıcı tanınmadı ({len(kapsam_disi['kapsayici'])}): "
              + ", ".join(kapsam_disi["kapsayici"])
              + "\n  Bu makaleler taranmadı. Yeni şablon ailesi → AILELER listesine eklenmeli.")
    if kapsam_disi["numarasiz"]:
        print(f"\n○ KAPSAM SINIRI — numaralı bölüm yok ({len(kapsam_disi['numarasiz'])}): "
              + ", ".join(kapsam_disi["numarasiz"])
              + "\n  Numara-bazlı hizalama kurulamaz (meşru sınır, kusur değil), ama"
                "\n  bu makaleler ÖLÇÜMSÜZ DEĞİL: üçüncü eksen (gövde kütlesi +"
                "\n  başlık sırası) yukarıda taradı. Kaçırdığı: bölüm içi ince kayıp.")
    if kapsam_disi["basliksiz"]:
        print(f"\n○ KAPSAM SINIRI — bölüm başlığı (h2) yok ({len(kapsam_disi['basliksiz'])}): "
              + ", ".join(kapsam_disi["basliksiz"])
              + "\n  Bölüm-bazlı karşılaştırma tanımsız; gövde-geneli eksenle ölçüldüler.")
    print("\nŞüphe bulgu değildir: çeviri notunda/künyede belgelenmiş kısaltma meşrudur;"
          "\nbelgelenmemiş olan üretim kusuru sayılır (O302)."
          "\n\nÜÇ EKSEN, üçü ayrı soru sorar — hiçbiri ötekinin yedeği değildir:"
          "\n  1. h3 sayısı      → alt bölüm VAR MI                     (O303)"
          "\n  2. alt bölüm      → İÇİ DOLU MU                           (O305)"
          "\n  3. gövde (+başlık)→ TOPLAM KÜTLE tutuyor mu (O308; gövde katmanı"
          "\n                      O312'den beri numaralılarda DA — bölüm dışı"
          "\n                      metni yalnız o görür. Başlık-sırası katmanı"
          "\n                      yalnız numarasızlarda: numara hizalaması"
          "\n                      varken mükerrer, kuru-koşta 0 bulgu.)"
          "\nİlk ikisi numara hizalaması ister; üçüncüsü istemez, o yüzden"
          "\nkabadır: bölüm içi ince kaybı göremez, toptan kısalmayı görür.")


if __name__ == "__main__":
    main()
