#!/usr/bin/env python3
"""Provenans-strip — kaynakça iç-provenans em-notlarını kamusal HTML'den çıkarır.

Evrim O757 kararı (Portal O460 tespiti → O462 uygulama). İç-not sızıntısı
tekrar-önleme: üretim oturumu kaynakçaya "tam metin okundu; Samsung kaynakça"
gibi iç-çalışma provenans notu koyar (KUTUPHANE disiplini gereği DEĞERLİ, ham
kaynakta KALIR) ama çeviri/deploy hattı strip etmezse kamusala sızar.

Hedef SADECE: parantezli <em>(...)</em> içinde 'Samsung / 文献库 / 文献庫'
GEÇEN provenans notu + <strong>[Samsung'da]</strong> varyantı.
DOKUNULMAZ (false-positive koruması, Evrim §3):
  - t-line output <div> içerik ('BMJ sayfası açıldı, tam metin okundu')
  - Samsung'suz içerik 全文 ('全文的最后一句' = metnin son cümlesi)
Desen <em> + parantez + Samsung üçlüsü ister; hiçbiri tek başına yeterli değil.

== COMMENT-EKSENİ (Evrim O764, Portal O506 uygulama; EK katman) ==
Üretim-iskeleti HTML-comment'leri (<!-- ... -->) kamusal artefakttan strip edilir.
Gerekçe (Evrim): deployed comment public okuyucuya sıfır değer taşır (üretim-navigasyonu
kaynak .md'de yaşar), buna karşılık view-source'ta iç üretim-mantığını (Savak↔Halit
diyalog yapısı), em-dash (yasak karakter) ve yapı-notlarını sızdırır (O102). Silme
deploy-nötr (görünmez, SEO/render etkisiz).
KORU (yanlış-pozitif freni, Evrim "gerçek teknik comment TR/iskelet taşımaz → dar tut"):
  teknik-yapısal comment DOKUNULMAZ — kapanış-div (/wrap, /character-grid),
  CSS selector (.book, #id), conditional ([if..., <![, ...endif]).
STRIP (üretim-iskeleti): geri kalan her comment — TR-iskelet (İlke/KÜME/Aktörler),
  dekoratif ayraç (═══), SVG konum/yapı-notu, karakter-grid etiketi, iç-oturum-adı (Tasvir).
Ayrım DİL-BAĞIMSIZ (ö/ü Almanca-Türkçe ortak olduğundan "TR-karakter" kriteri tek başına
hem fazla geniş hem fazla dar çıktı, O506 ölçümü): teknik-yapısal mı, üretim-içeriği mi.

Kullanım:
  provenans-strip.py [dizin|dosya ...]        -> temizle (in-place, prov + comment); arg yoksa site kökü
  provenans-strip.py --check [dizin|dosya ...] -> rapor-only; sızıntı varsa EXIT 1 (deploy kapısı)
  provenans-strip.py --no-comments [...]       -> yalnız provenans ekseni (comment-eksenini atla)
"""
import sys
import re
import pathlib

# <em>(...Samsung...)</em>: ascii () veya fullwidth （）; içerik parantez/tag içermez
# (newline serbest — em-notu satıra bölünebilir). Öndeki boşluk da yutulur.
PAT_EM = re.compile(r'\s*<em>[（(][^（）()<]*(?:Samsung|文献库|文献庫)[^（）()<]*[）)]</em>')
# bunu-kim-yazdi varyantı: <strong>[Samsung'da]</strong> (düz veya eğri apostrof)
PAT_STRONG = re.compile(r"\s*<strong>\[Samsung['’]da\]</strong>")

# comment-ekseni: <!-- ... --> + öndeki boşluk + arkadaki tek newline (tam-satır temiz)
COMMENT_PAT = re.compile(r"[ \t]*<!--(.*?)-->[ \t]*\n?", re.S)
# KORU: teknik-yapısal (dokunma) — / kapanış-div, . # selector, [if / <![ / endif conditional
COMMENT_KORU = re.compile(r"^\s*(?:/|[.#][A-Za-z]|\[if|<!\[|endif)")

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _comment_strip(html):
    """KORU olmayan (üretim-iskeleti) comment'leri çıkar; sayıyı döndür."""
    n = 0
    def repl(m):
        nonlocal n
        if COMMENT_KORU.match(m.group(1)):
            return m.group(0)   # teknik-yapısal: dokunma
        n += 1
        return ""               # üretim-iskeleti: strip
    new = COMMENT_PAT.sub(repl, html)
    return new, n


def _comment_count(html):
    return sum(1 for m in COMMENT_PAT.finditer(html)
               if not COMMENT_KORU.match(m.group(1)))


def scan(html):
    return PAT_EM.findall(html) + PAT_STRONG.findall(html)


def iter_html(args):
    seen = set()
    for a in args:
        p = pathlib.Path(a)
        if not p.is_absolute():
            p = ROOT / p
        if p.is_dir():
            for f in sorted(p.rglob('*.html')):
                if f not in seen:
                    seen.add(f)
                    yield f
        elif p.suffix == '.html' and p.exists():
            if p not in seen:
                seen.add(p)
                yield p


def main():
    args = sys.argv[1:]
    check = '--check' in args
    no_comments = '--no-comments' in args
    targets = [a for a in args if not a.startswith('--')] or [str(ROOT)]

    total_prov = 0
    total_cmt = 0
    for p in iter_html(targets):
        html = p.read_text(encoding='utf-8')
        prov = scan(html)
        cmt = 0 if no_comments else _comment_count(html)
        if not prov and not cmt:
            continue
        total_prov += len(prov)
        total_cmt += cmt
        rel = p.relative_to(ROOT)
        if check:
            print(f"[SIZ] {rel}: prov={len(prov)} comment={cmt}")
        else:
            new = PAT_STRONG.sub('', PAT_EM.sub('', html))
            if not no_comments:
                new, _ = _comment_strip(new)
            p.write_text(new, encoding='utf-8')
            print(f"[strip] {rel}: prov={len(prov)} comment={cmt}")

    if check:
        total = total_prov + total_cmt
        if total:
            print(f"\nSIZINTI: provenans={total_prov} comment={total_cmt} — deploy engellendi.")
            sys.exit(1)
        print("TEMIZ: provenans + comment sızıntısı yok.")
    else:
        print(f"\nstrip toplam: provenans={total_prov} comment={total_cmt}")


if __name__ == '__main__':
    main()
