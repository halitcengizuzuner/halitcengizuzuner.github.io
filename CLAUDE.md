# halitcengizuzuner.com — Site İlkeleri

## Bireysel Karakter İlkesi — KESİN
- **Ana sayfa:** Her düşünce girişi kendi punto boyutunu, satır yüksekliğini, rengini, konumunu taşır. Paylaşılan boyut sınıfları (t-small, t-medium, t-large) kullanılmaz. Her cümle kendi bedenini giyer.
- **Raporlar:** Her rapor sayfası kendi görsel karakterini taşır. Ortak şablon kopyalanmaz — her metin kendi tipografisini, ritmini, boşluklarını belirler. Renk paleti (void/bone) ortaktır ama kullanım biçimi farklılaşabilir.
- **İlke:** Tekrar eden kalıp = üniforma. Bu site üniforma giymez.

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
- Grain overlay: fractalNoise SVG, mix-blend-mode overlay (opaklık rapor bazında farklı)
- Responsive: clamp() ile akışkan tipografi
- Raporlar: /raporlar/ dizininde
- Görseller: /img/ dizininde
