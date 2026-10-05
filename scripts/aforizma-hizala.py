#!/usr/bin/env python3
"""
TR aforizma duvarı tutarlılık hizalama (O495, Halit O494 profesyonel-dokunuş talebi).
ASIL İŞ: durağan renk gürültüsü (Halit'in gözlemi: aforizma bağlantıları "farklı tonda").

18 bağlantılı KAPI (içinde <a>): durağan renk → tek-taban var(--bone), italik → düz.
  - Gerekçe: 6 dil deseni (.aphorism-link { color: var(--bone); font-style yok }) = referans.
  - 7-dil tam-senkron (O336): durağan renk + düz, tüm diller aynı.
  - O494 teşhisi: bone-bright serpiştirmesi sistemsiz birikim (punto/tema/kronoloji korelasyonu yok).
4 bağlantısız SÜS (bone-ghost): DOKUNULMAZ (site ilkesi "İçi Hayal Dışı Gerçek": bağlantısız aforizma ghost, "süs olduğu belli").
KORUNAN: punto/konum/gap asimetrisi (O8 ritim), hover ember (TR-içi tutarlı; TR↔6dil hover-mimari senkronu = P2-B).

İdempotent: ikinci koşu no-op (bone-bright=0, italic=0 → değişim 0, assert'ler geçer).
"""
import sys

F = "turkce/index.html"
s = open(F, encoding="utf-8").read()

lines = s.split("\n")
kapi = 0
sus = 0
renk_degisti = 0
italik_kaldirildi = 0
out = []
for ln in lines:
    if '<div class="thought' in ln and "style=" in ln:
        if "var(--bone-ghost)" in ln:
            sus += 1
            out.append(ln)          # SÜS dokunulmaz
            continue
        kapi += 1
        n = ln
        if "var(--bone-bright)" in n:
            n = n.replace("color: var(--bone-bright)", "color: var(--bone)")
            renk_degisti += 1
        if "font-style: italic;" in n:
            n = n.replace(" font-style: italic;", "")
            italik_kaldirildi += 1
        out.append(n)
    else:
        out.append(ln)

# --- FAZ1: bellekte doğrula (count-assert, kırıcı built-in) ---
assert kapi == 18, f"KIRICI: kapı sayısı {kapi} != 18 (yapı değişmiş, DUR)"
assert sus == 4, f"KIRICI: süs sayısı {sus} != 4 (yapı değişmiş, DUR)"

new_s = "\n".join(out)

# .mind bloğu içi son doğrulama (CSS kuralları dışarıda, sadece inline .thought)
m0 = new_s.index('<div class="mind">')
m1 = new_s.index('<section class="limbs"', m0)
mind = new_s[m0:m1]
bb = mind.count("var(--bone-bright)")
it = mind.count("font-style: italic")
gh = mind.count("var(--bone-ghost)")
assert bb == 0, f"KIRICI: kapılarda hâlâ bone-bright={bb}"
assert it == 0, f"KIRICI: kapılarda hâlâ italic={it}"
assert gh == 4, f"KIRICI: süs ghost={gh} != 4 (süse dokunulmuş)"

# --- FAZ2: atomik yaz ---
open(F, "w", encoding="utf-8").write(new_s)
print(f"OK kapı={kapi} süs={sus} | renk_değişti(bright→bone)={renk_degisti} italik_kaldırıldı={italik_kaldirildi}")
print(f"DOĞRULAMA .mind: bone-bright={bb} italic={it} ghost(süs)={gh}")
