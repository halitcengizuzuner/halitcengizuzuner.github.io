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

Kullanım:
  provenans-strip.py [dizin|dosya ...]        -> temizle (in-place); arg yoksa site kökü
  provenans-strip.py --check [dizin|dosya ...] -> rapor-only; sızıntı varsa EXIT 1 (deploy kapısı)
"""
import sys
import re
import pathlib

# <em>(...Samsung...)</em>: ascii () veya fullwidth （）; içerik parantez/tag içermez
# (newline serbest — em-notu satıra bölünebilir). Öndeki boşluk da yutulur.
PAT_EM = re.compile(r'\s*<em>[（(][^（）()<]*(?:Samsung|文献库|文献庫)[^（）()<]*[）)]</em>')
# bunu-kim-yazdi varyantı: <strong>[Samsung'da]</strong> (düz veya eğri apostrof)
PAT_STRONG = re.compile(r"\s*<strong>\[Samsung['’]da\]</strong>")

ROOT = pathlib.Path(__file__).resolve().parent.parent


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
    targets = [a for a in args if a != '--check'] or [str(ROOT)]

    total = 0
    for p in iter_html(targets):
        html = p.read_text(encoding='utf-8')
        hits = scan(html)
        if not hits:
            continue
        total += len(hits)
        rel = p.relative_to(ROOT)
        if check:
            print(f"[SIZ] {rel}: {len(hits)}")
        else:
            new = PAT_STRONG.sub('', PAT_EM.sub('', html))
            p.write_text(new, encoding='utf-8')
            print(f"[strip] {rel}: {len(hits)}")

    if check:
        if total:
            print(f"\nSIZINTI: {total} provenans notu — deploy engellendi.")
            sys.exit(1)
        print("TEMIZ: provenans sızıntısı yok.")
    else:
        print(f"\nstrip toplam: {total}")


if __name__ == '__main__':
    main()
