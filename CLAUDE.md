# halitcengizuzuner.com — Site İlkeleri

## İçi Hayal, Dışı Gerçek
- **Duvar (dış):** Gerçek. Ziyaretçi neyin kapı olduğunu sezgisel anlar. Bağlantılı girişler bone/bone-bright — tıklanabilir görünür, hover'da ince alt çizgi belirir. Bağlantısız aforizmalar bone-ghost — nefes verir ama dikkat çekmez, "süs" olduğu belli.
- **Yazılar (iç):** Hayal. Her rapor sayfası kendi görsel karakterini taşır. Ortak şablon kopyalanmaz — her metin kendi tipografisini, ritmini, boşluklarını belirler. Renk paleti (void/bone) ortaktır ama kullanım biçimi farklılaşabilir.
- **İlke:** Duvar okunabilir, yazılar keşfedilir. Kaos dışarıda değil içeride yaşar.

## Kronolojik Sıralama
- Ana sayfada en yeni düşünce en üstte, en eski en altta.
- Bağlantısız düşünceler (aforizmalar) aralarda nefes verir, konumları sabit değil.

## İçerik Sahipliği
- Başkasının metni taşınırken: metin dokunulmaz, atıf açık, "neden burada" bölümü ayrı.
- Başkasının sesinden konuşulmaz (Gemici hatası). Kendi sesimiz kendi bölümümüzde.

## Mahremiyet
- Kişisel detaylar (konum, sağlık, gelir, aile) kamusal sayfalara yazılmaz.
- "Bir adam tanıyorum" düzeyinde kalınır — kim olduğu açılmaz.

## Teknik
- Font: Instrument Serif
- Ortak renk paleti: --void (#060604), --bone (#d4ccc0), --bone-bright, --bone-dim, --bone-ghost
- Rapor vurgu renkleri (her rapor kendi rengini taşır):
  - Mutluluğun Resmi: --straw (#c8a055) — saman altını
  - İyi Yaşamak: --wine (#a07068) — şarap tozu
  - Halüsinasyon: --steel (#7890a0) — çelik mavisi
  - Araştırma Anayasası: --sage (#78a890) — adaçayı yeşili
  - Sturgeon Yasası: --rust (#b87050) — pas turuncusu
  - Aynen Öyle: --ash (#a098b0) — kül lavantası
  - Çay Masası: --cay (#b89060) — çay amberi
  - Nefret Üzerine: --accent (#c4785a) — yanık toprak (kendi font/CSS sistemi: Cormorant Garamond + Inter)
  - Yazıdan Sese: --yanki (#7068a0) — yankı indigo
  - Yüzsüz İletişim: --visage (#5a7a7a) — koyu teal
  - Görünmez Boşluk: --bosluk (#7a8a9a) — soğuk gri mavi
  - Yapay Zekâyı Kim Kullanıyor: --bicak (#b08838) — bıçak amberi
  - Anlamak: --anlam (#708050) — zeytin yeşili
- Grain overlay: fractalNoise SVG, mix-blend-mode overlay (opaklık rapor bazında farklı)
- Responsive: clamp() ile akışkan tipografi
- Raporlar: /raporlar/ dizininde
- Görseller: /img/ dizininde
- Genesis (/genesis.html, kök özel sayfa — rapor DEĞİL): ortaklığın doğuş tarihi; --kor (#c89a58) kor amberi + ısınan faz paleti (f1 #96684a → f4 #e2c478); ana sayfa bakım tabelasından bağlı; bilinçli görselsiz/tipografik (tarih belgesi sadeliği). İçerik Evrim'in (metin dokunulmaz), yayım/kap Portal'ın.
- Atölye (/atolye.html, kök özel sayfa): sitenin mutfağı/yöntemi; --tezgah (#b0a080) tezgâh ahşabı + kanıt-etiket renkleri (yeşil/amber/leylak); Genesis'in kardeşi, içerik+yayım Portal'ın (O183). Dil-bütünlüğü ilkesi (Halit): her dil ana sayfasından Atölye ve Genesis o dilde açılmalı — SAĞLANDI (O184, 3 Tem 2026): 5 çeviri çifti canlı (english/workshop+genesis, deutsch/werkstatt+genesis, francais/atelier+genesis, espanol/taller+genesis, zhongwen/workshop+genesis), 5 tabela kendi dilinde iki linkle, hreflang 7-satır tam simetri, dil-özgü noktalama (DE Gänsefüßchen, FR guillemets+boşluk, ES comillas+ters işaret, ZH tam-genişlik), em-dash 0/10.
- On Listening / Dinleme Üstüne (/english/on-listening.html + /turkce/dinleme-ustune.html, fikir yazısı — rapor DEĞİL, Okuma Halkası #7 ürünü): dinleme üstüne bağımsız deneme; --ses (#c9a06a) sıcak amber; v1.0 · 16 Tem 2026 (O240, EN+TR aynı gece). hreflang: tr + en + x-default→EN (DE/FR/ES/ZH gelince genişler). Sonda tek satır vesile: Faith Lawrence "The listening gift" (Aeon 2025) linki — özet YOK (O239 kararı: bağımsız fikir yazısı, reading-response değil). Rilke alıntısı EN'de Norton 1945 birebir, TR'de bu yazı için çevrildi (iki muhur footer'da künye). Duvar girişleri en üstte: EN "Listening is dead; what remains is hearing." / TR "Dinleme öldü, geriye işitme kaldı." Görsel: Tasvir'e istek bırakıldı (O240), gelince iki sayfaya v1.1.

## Teknik Altyapı ve Araştırma Kaynak Referansları (Evrim 74, 17 Nis 2026 dağıtım)

Aşağıdaki üç referans **tek gerçek kaynak** — bu oturum kendi kayıt tutmaz, buraya işaret eder:

1. **Dış platform veri çekme yöntemleri** (WhatsApp, Drive, Gmail, Messenger, Facebook, Evernote, Gemini geçmişi, DeepSeek, ChatGPT/Claude.ai): `~/Documents/Evrim/CLAUDE.md` → "Teknik Altyapı Referansı" bölümü. Yöntem sorusunda buraya bak, QR/login/session gereksiz yere tekrarlama.

2. **Akademik ve kütüphane altyapısı** (JSTOR, ACM, CiNii, NCPSSD, Trove API key, Semantic Scholar, paper-search-mcp + arxiv-mcp + simple-pubmed + dergipark-mcp, Turuz, ücretsiz açık erişim): `~/.claude/auto-memory/reference_akademik_kaynaklar.md`. Araştırma öncesi MCP + kayıtlı hesap + açık erişim sırası.

3. **VPN refleksi — engelli sitelerde otomatik deneme**: `~/.claude/auto-memory/reference_vpn.md`. Web erişim hatasında Türkiye engeli sor → Urban VPN → iş bitince KAPAT.

**Memory aktif kullanım refleksi** (`~/.claude/auto-memory/feedback_memory_aktif_kullanim.md`): Konu geldiğinde `MEMORY.md` indeksini değil detay memory dosyasını aç. Halit söylemesin diye — refleks Evrim'in kimliği gereği.
