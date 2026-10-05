#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2-B2: Liste semantiği — düşünce duvarı ul/li + kadro dl/dt/dd (7 dil ATOMİK).

İki kol (6 dil ≠ TR yapısı, O491/O493/O494 + E469 ham ölçüm):
  TR   : <div class="mind"> → <ul class="mind" role="list">; mind-içi <h2 sr-only> → ul DIŞINA;
         22 <div class="thought p-* gap-* style=..> → <li ...> (class+inline style KORUNUR);
         mind kapanış </div> → </ul>.
  6 dil: ardışık <section class="first-wall">İÇERİK</section> → tek <ul class="mind" role="list"> içinde
         <li class="first-wall">İÇERİK</li> (İÇERİK dokunulmaz: kapı/süs/note/2-link korunur);
         BOŞ first-wall (whitespace) ATILIR; welcome ul-DIŞI (dokunulmaz); h2 zaten ul-dışı.
Ortak (7 dil): <section class="limbs"> içine <dl>; her limb <span class="limb-name"> → <dt>,
         <span class="limb-what"> → <dd> (translate="no" KORUNUR); h2 "Kadro" dl-DIŞI.
CSS reset (ana <style>, idempotent marker): .mind list-style/margin/padding-left,
         .thought + .first-wall display:block (li list-item → .p-right margin-auto ÇALIŞSIN),
         .limbs dl margin:0, .limb dd margin:0.

Atomik: FAZ1 7 dil BELLEKTE dönüştür + assert (patlarsa HİÇ yazma), FAZ2 topluca yaz.
Idempotent: <ul class="mind" varsa skip. Kırıcı: count-assert (li = dolu duvar birimi, dt=dd=5).
"""
import re, sys, pathlib

BASE = pathlib.Path.home() / "halitcengizuzuner.github.io"
TR = "turkce"
DILLER6 = ["english", "espanol", "francais", "deutsch", "zhongwen", "nihongo"]
# Ölçümden (olc.py): dolu duvar birimi sayısı (boş first-wall hariç)
BEKLENEN_LI = {"turkce": 22, "english": 22, "espanol": 21, "francais": 21,
               "deutsch": 21, "zhongwen": 20, "nihongo": 22}

RESET_MARKER = "/* P2-B2 liste reset */"
RESET_CSS = (
    "\n        " + RESET_MARKER + "\n"
    "        .mind { list-style: none; margin: 0; padding-left: 0; }\n"
    "        .thought { display: block; }\n"
    "        .first-wall { display: block; }\n"
    "        .limbs dl { margin: 0; }\n"
    "        .limb dd { margin: 0; }\n"
)


def _reset_css_ekle(h):
    """Ana <style> (duvar kuralı içeren) </style>'ından önce reset ekle (idempotent)."""
    if RESET_MARKER in h:
        return h
    ana = None
    for s in re.finditer(r'<style[^>]*>.*?</style>', h, re.DOTALL):
        g = s.group()
        if '.thought' in g or '.first-wall' in g or '.aphorism' in g:
            ana = s
    if ana is None:
        raise RuntimeError("ana <style> bulunamadı (duvar kuralı yok)")
    ins = ana.end() - len('</style>')
    return h[:ins] + RESET_CSS + "        " + h[ins:]


def _limbs_dl(h):
    """7 dil ortak: limbs span→dt/dd + dl sarma. Idempotent (<dl yoksa)."""
    if '<dl' in h:
        return h, "limbs skip (dl var)"
    m = re.search(r'(<section class="limbs">)(.*?)(</section>)', h, re.DOTALL)
    if not m:
        raise RuntimeError("limbs section yok")
    ic = m.group(2)
    # span → dt/dd (translate="no" ve diğer öznitelikler korunur)
    ic2, n_name = re.subn(r'<span class="limb-name"([^>]*)>(.*?)</span>',
                          r'<dt class="limb-name"\1>\2</dt>', ic, flags=re.DOTALL)
    ic2, n_what = re.subn(r'<span class="limb-what"([^>]*)>(.*?)</span>',
                          r'<dd class="limb-what"\1>\2</dd>', ic2, flags=re.DOTALL)
    if n_name != 5 or n_what != 5:
        raise RuntimeError(f"limb dt/dd beklenen 5/5, bulunan {n_name}/{n_what}")
    # ilk <div class="limb öncesine <dl>, son </div>'den sonra </dl>
    ic2 = ic2.replace('<div class="limb', '<dl>\n    <div class="limb', 1)
    ic2 = re.sub(r'(</div>)(\s*)$', r'\1\n    </dl>\2', ic2, count=1)
    return h[:m.start()] + m.group(1) + ic2 + m.group(3) + h[m.end():], f"limbs dl + {n_name} dt/dd"


def donustur_tr(h):
    if '<ul class="mind"' in h:
        return h, "TR skip (ul var)"
    start = h.index('<div class="mind">')
    limbs_i = h.index('<section class="limbs">')
    blok = h[start:limbs_i]
    # mind-içi h2'yi çıkar (ul dışına alınacak)
    h2m = re.search(r'\s*<h2 class="sr-only">[^<]*</h2>\s*', blok)
    if not h2m:
        raise RuntimeError("TR mind-içi h2 sr-only yok")
    h2 = h2m.group(0).strip()
    blok = blok[:h2m.start()] + "\n    " + blok[h2m.end():]  # h2 yerine tek satır boşluk
    # <div class="mind"> → h2 (ul-dışı) + <ul>
    blok = blok.replace('<div class="mind">',
                        f'{h2}\n<ul class="mind" role="list">', 1)
    # thought div → li (class + style KORUNUR; nested div yok, .*? güvenli)
    blok, n = re.subn(r'<div class="(thought[^"]*)"([^>]*)>(.*?)</div>',
                      r'<li class="\1"\2>\3</li>', blok, flags=re.DOTALL)
    # kalan tek </div> = mind kapanış → </ul>
    kalan_div = blok.count('<div')
    kalan_close = blok.count('</div>')
    if kalan_div != 0 or kalan_close != 1:
        raise RuntimeError(f"TR mind blok kalıntı: <div={kalan_div} </div>={kalan_close} (beklenen 0/1)")
    blok = blok.replace('</div>', '</ul>', 1)
    h = h[:start] + blok + h[limbs_i:]
    h = _reset_css_ekle(h)
    h, lmsg = _limbs_dl(h)
    # kırıcı
    assert h.count('<ul class="mind" role="list">') == 1, "TR ul != 1"
    assert h.count('<li class="thought') == 22, f"TR li != 22 ({h.count(chr(60)+'li class=' + chr(34) + 'thought')})"
    mind_blok = h[h.index('<ul class="mind"'):h.index('</ul>')]
    assert '<h2' not in mind_blok, "TR h2 hâlâ ul-içi (geçersiz HTML)"
    assert h.count('<dt class="limb-name"') == 5 and h.count('<dd class="limb-what"') == 5, "TR dt/dd != 5"
    assert RESET_MARKER in h, "TR reset CSS yok"
    return h, f"TR: ul + {n} li + {lmsg}"


def donustur_6(h, dil):
    if '<ul class="mind"' in h:
        return h, f"{dil} skip (ul var)"
    fw_start = h.index('<section class="first-wall">')
    limbs_i = h.index('<section class="limbs">')
    bolge = h[fw_start:limbs_i]
    # bölge first-wall dışında içerik taşımamalı (welcome fw_start'tan önce/uzakta)
    kalan = re.sub(r'<section class="first-wall">.*?</section>', '', bolge, flags=re.DOTALL).strip()
    if kalan:
        raise RuntimeError(f"{dil} duvar bölgesinde beklenmedik içerik: {kalan[:120]!r}")
    fws = re.findall(r'<section class="first-wall">(.*?)</section>', bolge, re.DOTALL)
    lis = [f'    <li class="first-wall">{ic}</li>' for ic in fws if ic.strip()]
    atilan = len(fws) - len(lis)
    yeni = '<ul class="mind" role="list">\n' + '\n'.join(lis) + '\n</ul>\n\n'
    h = h[:fw_start] + yeni + h[limbs_i:]
    h = _reset_css_ekle(h)
    h, lmsg = _limbs_dl(h)
    # kırıcı
    assert h.count('<ul class="mind" role="list">') == 1, f"{dil} ul != 1"
    assert h.count('<li class="first-wall">') == BEKLENEN_LI[dil], \
        f"{dil} li {h.count(chr(60)+'li class=' + chr(34) + 'first-wall' + chr(34))} != {BEKLENEN_LI[dil]}"
    assert h.count('<section class="welcome">') == 1, f"{dil} welcome bozuldu"
    mind_blok = h[h.index('<ul class="mind"'):h.index('</ul>')]
    assert '<h2' not in mind_blok, f"{dil} h2 ul-içi (geçersiz)"
    assert h.count('<dt class="limb-name"') == 5 and h.count('<dd class="limb-what"') == 5, f"{dil} dt/dd != 5"
    assert RESET_MARKER in h, f"{dil} reset CSS yok"
    return h, f"{dil}: ul + {len(lis)} li (boş {atilan} atıldı) + {lmsg}"


def main():
    sonuc = {}  # dil -> yeni içerik
    rapor = []
    # FAZ1: bellekte dönüştür + assert
    for dil in [TR] + DILLER6:
        p = BASE / dil / "index.html"
        h = p.read_text(encoding="utf-8")
        yeni, msg = (donustur_tr(h) if dil == TR else donustur_6(h, dil))
        sonuc[dil] = (p, yeni, h != yeni)
        rapor.append(msg)
    print("FAZ1 (bellekte doğrulama) OK:")
    for r in rapor:
        print("  " + r)
    # FAZ2: atomik yaz
    yazildi = 0
    for dil, (p, yeni, degisti) in sonuc.items():
        if degisti:
            p.write_text(yeni, encoding="utf-8")
            yazildi += 1
    print(f"FAZ2: {yazildi} dosya yazıldı.")


if __name__ == "__main__":
    main()
