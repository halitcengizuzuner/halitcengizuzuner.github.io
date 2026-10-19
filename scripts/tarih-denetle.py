#!/usr/bin/env python3
"""Yapılandırılmış tarih = görünür künye denetimi (salt-okuma, deploy kapısı).

Kural (Google yayım-tarihi rehberi: yapılandırılmış tarih görünür tarihle eşleşmeli):
  - JSON-LD datePublished ve meta article:published_time = sayfanın kendi künyesindeki
    ilk-yayım etiketi (TR İlk yayım · EN First published · ES Primera publicación ·
    FR Première publication · ZH 首次发表/首次發表 · JA 初版).
    EN/ES/FR/DE/ZH künyesi eser düzeyidir (TR ilk yayımı); JA künyesi sayfa düzeyidir.
  - JSON-LD dateModified = künyedeki en geç tarih (JA'da "トルコ語原文" sonrası aslın
    tarihleri sayılmaz).
  - Alt bilgi satırı (footer-inner'ın ilk <p>'si) ilk yayım / son revizyon etiketi taşıyorsa
    görünür künyenin İKİNCİ yeridir (Araştırma Anayasası: sürüm künyesi yok, tarih alt satırda;
    JA'da alt satırdaki 初版 eserin tarihidir, sayfa künyesindeki 初版 yanında geçerli sayılır).
  - Başlık ekseni: hero-eyebrow sürüm numarası taşıyorsa alt satırdaki sürümle aynı olmalı;
    ay-yıl taşıyorsa dateModified'ın ayıyla aynı olmalı.
Görünür künyesi (sürüm künyesi ya da etiketli alt satır) olmayan sayfa kıyaslanmaz (sayılır, raporlanır).
Çıkış: 0 = temiz, 1 = uyuşmazlık var.
"""
import html
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
DILLER = ["turkce", "english", "espanol", "francais", "deutsch", "zhongwen", "nihongo"]
AYLAR = {
    "turkce": "ocak şubat mart nisan mayıs haziran temmuz ağustos eylül ekim kasım aralık",
    "english": "january february march april may june july august september october november december",
    "espanol": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre",
    "francais": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre",
    "deutsch": "januar februar märz april mai juni juli august september oktober november dezember",
}
ETIKET = {
    "turkce": r"İlk yayım\s*:",
    "english": r"First published\s*:",
    "espanol": r"Primera publicación\s*:",
    "francais": r"Première publication\s*:",
    "deutsch": r"Erst(?:veröffentlichung|veröffentlicht|publikation)\s*:?",
    "zhongwen": r"首次(?:[发發]表|[发發]布)\s*[：:]",
    "nihongo": r"初版\s*[：:]",
}
REVIZYON = r"(Son revizyon|Last revised|Última revisión|Dernière révision|Zuletzt überarbeitet|Letzte Überarbeitung|最[后後]修[订訂]|最終改訂)"


def tarih_cevir(dil, s):
    s = s.strip()
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", s)
    if m:
        return f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}"
    m = re.match(r"(\d{1,2})(?:er)?\.?\s+(?:de\s+)?([A-Za-zÀ-ÿçğıöşüÇĞİÖŞÜäÄ]+)\s+(?:de\s+)?(\d{4})", s)
    if m:
        ay = m[2].lower().replace("İ", "i")
        for liste in (AYLAR.get(dil, ""), AYLAR["english"]):
            aylar = liste.split()
            if ay in aylar:
                return f"{m[3]}-{aylar.index(ay) + 1:02d}-{int(m[1]):02d}"
    return None


def tarihler(dil, k):
    out = [tarih_cevir(dil, m[0]) for m in re.finditer(r"\d{4}年\d{1,2}月\d{1,2}日", k)]
    out += [tarih_cevir(dil, m[0]) for m in re.finditer(
        r"\d{1,2}(?:er)?\.?\s+(?:de\s+)?[A-Za-zÀ-ÿçğıöşüÇĞİÖŞÜäÄ]+\s+(?:de\s+)?\d{4}", k)]
    return [d for d in out if d]


def ay_yil(dil, s):
    m = re.search(r"(\d{4})年(\d{1,2})月(?!\s*\d)", s)
    if m:
        return f"{m[1]}-{int(m[2]):02d}"
    for liste in (AYLAR.get(dil, ""), AYLAR["english"]):
        for i, ay in enumerate(liste.split()):
            m = re.search(r"(?<![\wÀ-ÿ])" + ay + r"\s+(\d{4})", s.lower())
            if m:
                return f"{m[1]}-{i + 1:02d}"
    return None


def main():
    sayfa = kunyesiz = ilk_kiyas = mod_kiyas = alt_satir = baslik_kiyas = 0
    hatalar = []
    for dil in DILLER:
        for f in sorted((SITE / dil / "raporlar").glob("*.html")):
            if "dinle" in f.name or f.name == "index.html":
                continue
            sayfa += 1
            t = f.read_text(encoding="utf-8")
            dp = re.findall(r'"datePublished"\s*:\s*"([^"]+)"', t)
            dm = re.findall(r'"dateModified"\s*:\s*"([^"]+)"', t)
            apt = re.findall(r'property="article:published_time"\s+content="([^"]+)"', t)
            yol = f"{dil}/raporlar/{f.name}"
            for x in apt:
                if dp and x != dp[0]:
                    hatalar.append(f"{yol}: article:published_time {x} ≠ datePublished {dp[0]}")
            m = re.search(r'<p class="surum-kunye"[^>]*>(.*?)</p>', t, re.S)
            ma = re.search(r'<div class="footer-inner">\s*<p>(.*?)</p>', t, re.S)
            alt = html.unescape(re.sub(r"<[^>]+>", " ", ma[1])) if ma else ""
            if not (re.search(ETIKET[dil], alt) or re.search(REVIZYON, alt)):
                alt = ""
            if not m and not alt:
                kunyesiz += 1
                continue
            if alt:
                alt_satir += 1
            k = html.unescape(re.sub(r"<[^>]+>", "", m[1])) if m else ""
            asil = []
            if dil == "nihongo":
                # JA künyesi iki tarih taşır: 初版 (JA sayfası) + 初出 (TR aslı). Başlık çoğunlukla eserin
                # tarihini gösterir; datePublished ikisinden biri olur ve başlıkla (p.meta) tutarlı olmalı.
                asil = [tarih_cevir(dil, x) for x in re.findall(r"初出\s*(\d{4}年\d{1,2}月\d{1,2}日)", k)]
                k = k.split("トルコ語原文")[0]
            mi = re.search(ETIKET[dil] + r"\s*(.{4,40})", k)
            ilk = tarih_cevir(dil, mi[1]) if mi else None
            mia = re.search(ETIKET[dil] + r"\s*(.{4,40})", alt) if alt else None
            ilk_alt = tarih_cevir(dil, mia[1]) if mia else None
            if ilk_alt:
                if dil == "nihongo" and ilk:
                    asil.append(ilk_alt)  # alt satırdaki 初版 = eserin ilk yayımı
                elif ilk and ilk != ilk_alt:
                    hatalar.append(f"{yol}: künye ilk yayım {ilk} ≠ alt satır ilk yayım {ilk_alt}")
                else:
                    ilk = ilk or ilk_alt
            if ilk and dp:
                ilk_kiyas += 1
                gecerli = {ilk, *asil}
                if dp[0][:10] not in gecerli:
                    hatalar.append(f"{yol}: datePublished {dp[0]} ∉ künye ilk yayım {sorted(gecerli)}")
            mb = re.search(r'<p class="meta">(.*?)</p>', t, re.S)
            if mb and dp:
                b = re.search(r"(\d{4})年(\d{1,2})月(?:(\d{1,2})日)?", mb[1])
                if b:
                    beklenen = f"{b[1]}-{int(b[2]):02d}" + (f"-{int(b[3]):02d}" if b[3] else "")
                    if not dp[0].startswith(beklenen):
                        hatalar.append(f"{yol}: datePublished {dp[0]} başlık tarihiyle ({beklenen}) uyuşmuyor")
            ds = tarihler(dil, k) + (tarihler(dil, alt) if alt else [])
            me = re.search(r'<p class="hero-eyebrow">(.*?)</p>', t, re.S)
            if me and alt:
                e = html.unescape(me[1])
                ve = re.search(r"v(\d+\.\d+)", e)
                va = re.search(r"v(\d+\.\d+)", alt)
                ay = ay_yil(dil, e)
                if ve or ay:
                    baslik_kiyas += 1
                if ve and va and ve[1] != va[1]:
                    hatalar.append(f"{yol}: başlık sürümü v{ve[1]} ≠ alt satır sürümü v{va[1]}")
                if ay and dm and not dm[0].startswith(ay):
                    hatalar.append(f"{yol}: başlık ayı {ay} ≠ dateModified {dm[0]}")
            if ds and dm:
                mod_kiyas += 1
                if dm[0][:10] != max(ds):
                    hatalar.append(f"{yol}: dateModified {dm[0]} ≠ künyedeki en geç tarih {max(ds)}")
            if dp and dm and dm[0][:10] < dp[0][:10]:
                hatalar.append(f"{yol}: dateModified {dm[0]} < datePublished {dp[0]}")
    print(f"sayfa {sayfa} · görünür künyesiz {kunyesiz} · alt satırdan okunan {alt_satir} · "
          f"datePublished kıyası {ilk_kiyas} · dateModified kıyası {mod_kiyas} · başlık kıyası {baslik_kiyas}")
    if hatalar:
        print("\n".join(hatalar))
        print(f"✗ {len(hatalar)} uyuşmazlık")
        return 1
    print("✓ Yapılandırılmış tarihler görünür künyeyle TUTARLI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
