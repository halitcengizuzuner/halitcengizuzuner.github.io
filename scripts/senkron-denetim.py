#!/usr/bin/env python3
# FAZ 0 — Senkron denetimini SAĞLAMLAŞTIR (Portal O337, TAM-SENKRON programı)
# Amaç: her makale × 7 dil → gerçek versiyon (surum-kunye) + bölüm sayısı (h2)
#       + hreflang eşleştirme → kesin borç tablosu (kör üretimi önler, O291/O293/O336)
import re, glob, os
from collections import defaultdict

ROOT = os.path.expanduser("~/halitcengizuzuner.github.io")
# dizin -> dil kodu; sıra çıktı sütun sırası
LANGS = [("turkce","tr"),("english","en"),("zhongwen","zh"),
         ("deutsch","de"),("francais","fr"),("espanol","es"),("nihongo","ja")]
CODES = [c for _,c in LANGS]

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
    return ver, h2, icerik_h2, noindex, hrefs

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

groups = defaultdict(dict)   # kimlik -> {kod: (ver,h2,icerik_h2,noindex,base)}
ident_name = {}
for fp,(code,ver,h2,ic,ni,hrefs) in records.items():
    key = ident_key(hrefs, fp)
    ident_name.setdefault(key, os.path.basename(key) or os.path.basename(fp))
    groups[key][code] = (ver,h2,ic,ni,os.path.basename(fp))

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
            ver,h2,ic,ni,base = row[c]
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
        borc.append((name, eksik, sapan, sorted(vers), diller_var))

print("\n" + "="*70)
print("BORÇ SİNYALLERİ (elle meşru/eksik ayrımı için):")
print("="*70)
for name, eksik, sapan, vers, var in borc:
    print(f"\n▸ {name}")
    if eksik:  print(f"   TAM-EKSİK dil (dosya yok): {', '.join(eksik)}")
    if sapan:  print(f"   İÇERİK-H2 ≥2 düşük (borç şüphesi): {', '.join(sapan)}")
    if len(vers)>1: print(f"   VERSİYON farklı (dile-özgü mü içerik mi?): {vers}")

print(f"\n(Format: versiyon/içerik-h2 · N=noindex · —=dosya yok · toplam {len(groups)} makale-kümesi)")
