#!/usr/bin/env python3
# FAZ 0 — Senkron denetimini SAĞLAMLAŞTIR (Portal O337, TAM-SENKRON programı)
# Amaç: her makale × 7 dil → gerçek versiyon (surum-kunye) + bölüm sayısı (h2)
#       + hreflang eşleştirme → kesin borç tablosu (kör üretimi önler, O291/O293/O336)
#
# O352 EK — İÇERİK-KALEM ekseni: "VERSİYON farklı" sinyalini RAFİNE eder (susturmaz).
#   Kök (O351 yanlış alarmı): sürüm no ≠ içerik senkronu. Dile-özgü tur (aksan
#   restorasyonu / noktalama / çeviri künyesi) sürümü yükseltir ama içeriği değiştirmez;
#   araç sürüm farkını "içerik açığı" sanıp elle-ayrım gürültüsü üretiyordu (15 kümenin
#   14'ü "versiyon farklı" → sinyal boğuldu).
#   Çözüm: gövdenin dile-İNVARYANT kalemini (çok-basamaklı SAYILAR: yıl/istatistik/tarih)
#   her dilde say; sürüm farklı AMA kalem örtüşmesi yüksekse "dil-turu (~senkron OK)",
#   düşükse "İÇERİK açığı şüphesi" + somut TR-fazlası kalem. İki alt-sınıfa böler.
#   TASARIM notu: SAYI seçildi, özel-ad DEĞİL — soyadları ZH/JA'da fonetik çevrilir
#   (Taleb→塔勒布) → yanlış-pozitif; sayı tam-genişlik normalize edilince 7 dilde de tutar.
#   Format-riski (ondalık/binlik ayraç EN 3.14 / DE 3,14) ayraç silinerek nötrlenir.
import re, glob, os, html as _html
from collections import defaultdict, Counter

ROOT = os.path.expanduser("~/halitcengizuzuner.github.io")
# dizin -> dil kodu; sıra çıktı sütun sırası
LANGS = [("turkce","tr"),("english","en"),("zhongwen","zh"),
         ("deutsch","de"),("francais","fr"),("espanol","es"),("nihongo","ja")]
CODES = [c for _,c in LANGS]

# gövde bu bölgelerden ÖNCE biter (hepsi sistem class'ı, her dilde sabit; kaynakça =
#   yazar-soyadı+yıl yoğun → gövde-kalem sayımını zehirler, ÇIKAR). references = olası EN varyantı.
_GOVDE_BITIS = re.compile(r'class="(?:kaynakca|references|diger-yazilar|surum-kunye|surum-notu|doi-kunye)')
_FULLWIDTH = {ord(c): chr(ord(c) - 0xFEE0) for c in "０１２３４５６７８９"}  # ZH/JA tam-genişlik → ASCII
KALEM_ESIK = 0.85  # örtüşme < eşik → içerik açığı şüphesi (O352 kalibrasyonu)

def govde_kalemleri(html):
    """Gövdenin (künye/nav/kaynakça HARİÇ) dile-invaryant SAYI kalemleri → Counter."""
    m = _GOVDE_BITIS.search(html)
    govde = html[:m.start()] if m else html
    govde = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', govde, flags=re.S)
    govde = re.sub(r'<[^>]+>', ' ', govde)
    govde = _html.unescape(govde).translate(_FULLWIDTH)
    kal = Counter()
    for tok in re.findall(r'\d[\d.,]*\d', govde):
        r = re.sub(r'[.,]', '', tok)   # ayraç sil → EN/DE/TR sayı formatı farkını nötrle
        # 4-6 basamak: yıl (1979/2026) + büyük süre/istatistik (2500 yıl, 10000).
        #   2-3 basamak KASTEN elenir: sayfa-no ("s. 199") dile-özgü baskıya bağlı,
        #   akademik atıfta yanlış-pozitif üretir (O289: her dil kendi baskısını anar).
        if 4 <= len(r) <= 6:
            kal[r] += 1
    return kal

def parse(fp):
    with open(fp, encoding="utf-8", errors="replace") as f:
        html = f.read()
    # versiyon: surum-kunye <p> İÇERİĞİ (style attribute'ündeki 0.78rem vb. sayıları AT)
    ver = "?"
    mk = re.search(r'class="surum-kunye"[^>]*>([^<]*)', html)
    if mk:
        mv = re.search(r'(\d+\.\d+)', mk.group(1))
        if mv: ver = mv.group(1)
    # ham h2 sayısı
    h2 = len(re.findall(r'<h2', html))
    # içerik h2 tahmini: surum-notu (version note) + diger-yazilar h2'lerini düş
    #   (ikisi de her dilde 1, simetrik; düşünce mutlak sayı içerik-bölüm'e yaklaşır)
    icerik_h2 = h2
    if re.search(r'class="surum-notu', html): icerik_h2 -= 1
    if re.search(r'class="diger-yazilar', html): icerik_h2 -= 1
    # noindex?
    noindex = bool(re.search(r'noindex', html))
    # hreflang kümesi
    hrefs = dict(re.findall(r'hreflang="([a-z-]+)"\s+href="([^"]+)"', html))
    kalem = govde_kalemleri(html)
    return ver, h2, icerik_h2, noindex, hrefs, kalem

def ident_key(hrefs, fp):
    # aynı makalenin tüm dilleri aynı x-default (yoksa en) URL'sine işaret eder
    for k in ("x-default","en"):
        if k in hrefs:
            return re.sub(r'.*halitcengizuzuner\.com','',hrefs[k])
    # hreflang yoksa / tek-dilse: kendi dosya adı
    return "SOLO:"+os.path.basename(fp)

records = {}
for d, code in LANGS:
    for fp in sorted(glob.glob(f"{ROOT}/{d}/raporlar/*.html")):
        base = os.path.basename(fp)
        if "-dinle" in base or base.endswith("-dinle.html"): continue
        records[fp] = (code,)+parse(fp)

groups = defaultdict(dict)   # kimlik -> {kod: (ver,h2,icerik_h2,noindex,base,kalem)}
ident_name = {}
for fp,(code,ver,h2,ic,ni,hrefs,kalem) in records.items():
    key = ident_key(hrefs, fp)
    ident_name.setdefault(key, os.path.basename(key) or os.path.basename(fp))
    groups[key][code] = (ver,h2,ic,ni,os.path.basename(fp),kalem)

def icerik_kalem_ayrimi(row):
    """VERSİYON farklı kümede: her dilin gövde-sayı örtüşmesini TR (içerik lideri) ile ölç.
       Döner: [(kod, oran, en_cok_eksik_kalemler)] — sadece TR dışı, kalemi olan diller."""
    if 'tr' in row and sum(row['tr'][5].values()) >= 3:
        ref = 'tr'
    else:  # TR yok/kalemsiz → en dolu kalem-kümeli dili referans al
        adaylar = [(c, sum(row[c][5].values())) for c in row]
        ref = max(adaylar, key=lambda x: x[1])[0] if adaylar else None
    if ref is None: return ref, []
    ref_kalem = row[ref][5]
    toplam = sum(ref_kalem.values())
    if toplam < 3: return ref, []   # kalem çok az → örtüşme oranı kırılgan, ölçme
    rapor = []
    for c in CODES:
        if c not in row or c == ref: continue
        dk = row[c][5]
        ortak = sum((ref_kalem & dk).values())
        oran = ortak / toplam
        eksik = ref_kalem - dk            # ref'te olup dilde eksik (dil geride izi)
        eksik_liste = [k for k,_ in eksik.most_common(4)]
        rapor.append((c, oran, eksik_liste))
    return ref, rapor

# çıktı
print(f"{'MAKALE (en-slug)':<34} | " + " | ".join(f"{c:^11}" for c in CODES))
print("-"*34 + "-+-" + "-+-".join("-"*11 for _ in CODES))
borc = []
for key in sorted(groups, key=lambda k: ident_name[k]):
    row = groups[key]
    name = ident_name[key].replace(".html","")
    cells=[]
    vers=set(); ich2=[]
    for c in CODES:
        if c in row:
            ver,h2,ic,ni,base,kalem = row[c]
            tag = "N" if ni else ""   # N = noindex
            cells.append(f"{ver}/{ic}{tag:>1}")
            vers.add(ver); ich2.append(ic)
        else:
            cells.append("—")
    print(f"{name:<34} | " + " | ".join(f"{x:^11}" for x in cells))
    # borç sinyalleri
    diller_var = [c for c in CODES if c in row]
    eksik = [c for c in CODES if c not in row]
    # içerik h2 sapması (max'tan >=2 sapan)
    if ich2:
        mx = max(ich2)
        sapan = [c for c in CODES if c in row and mx-row[c][2] >= 2]
    else:
        sapan=[]
    ver_farkli = len(vers) > 1
    if eksik or sapan or ver_farkli:
        # sürüm farklıysa içerik-kalem ayrımını hesapla (gürültüyü iki alt-sınıfa böl)
        ref, kalem_rapor = icerik_kalem_ayrimi(row) if ver_farkli else (None, [])
        borc.append((name, eksik, sapan, sorted(vers), diller_var, ref, kalem_rapor))

print("\n" + "="*70)
print("BORÇ SİNYALLERİ (elle meşru/eksik ayrımı için):")
print("="*70)
for name, eksik, sapan, vers, var, ref, kalem_rapor in borc:
    print(f"\n▸ {name}")
    if eksik:  print(f"   TAM-EKSİK dil (dosya yok): {', '.join(eksik)}")
    if sapan:  print(f"   İÇERİK-H2 ≥2 düşük (borç şüphesi): {', '.join(sapan)}")
    if len(vers)>1:
        print(f"   VERSİYON farklı: {vers}")
        if kalem_rapor:
            # O352: sürüm farkını "dil-turu" vs "içerik açığı" diye böl (ref=içerik lideri).
            #   ZH/JA sayı-kör (kanji rakam 二千五百 yakalanmaz) → eşik-altı olsa da "açık"
            #   İLAN ETME, ayrı "güvenilmez" not düş. Latin dil eşik-altı = elle-bak tetiği.
            LATIN = {"en","de","fr","es"}
            dil_turu = [f"{c} %{o*100:.0f}" for c,o,_ in kalem_rapor if o >= KALEM_ESIK]
            latin_acik = [(c,o,ek) for c,o,ek in kalem_rapor if o < KALEM_ESIK and c in LATIN]
            cjk_dusuk = [f"{c} %{o*100:.0f}" for c,o,ek in kalem_rapor if o < KALEM_ESIK and c not in LATIN]
            if dil_turu:
                print(f"     → içerik-kalem OK (ref={ref}, ~dil-turu, senkron muhtemel): {' · '.join(dil_turu)}")
            for c,o,ek in latin_acik:
                ekstr = (" TR-fazlası:"+",".join(ek)) if ek else ""
                print(f"     → ⚠ {c} açığı şüphesi %{o*100:.0f} (<%{KALEM_ESIK*100:.0f}) — ELLE BAK: atıf baskı-yılı farkı mı, gerçek borç mu{ekstr}")
            if cjk_dusuk:
                print(f"     → (zh/ja sayı-kör {' · '.join(cjk_dusuk)}: kanji rakam ölçülemez → senkronu h2+elle doğrula, açık SAYMA)")
        elif ref is None:
            print(f"     → (içerik-kalem: küme kalemsiz, ölçülemedi)")
        else:
            print(f"     → (içerik-kalem: ref={ref} kalemi <3, oran kırılgan, ölçülmedi)")

print(f"\n(Format: versiyon/içerik-h2 · N=noindex · —=dosya yok · toplam {len(groups)} makale-kümesi)")
print(f"(İçerik-kalem: gövde dile-invaryant SAYI örtüşmesi; eşik %{KALEM_ESIK*100:.0f}; "
      f"%eşik altı=içerik açığı şüphesi, üstü=dile-özgü tur/senkron OK)")
