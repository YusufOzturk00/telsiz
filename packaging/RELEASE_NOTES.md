[🇹🇷 Türkçe](#turkce) | [🇬🇧 English](#english)

<a id="turkce"></a>

## 🇹🇷 Türkçe

Telsiz, CS2 oynarken takım arkadaşlarının **sesli sohbetini** dinler, konuşulan dili tespit eder ve Türkçeye çevirip **yazı olarak** gösterir. Çevirileri **telefonunda** veya **ikinci ekrandaki tarayıcıda** izlersin.

### Kurulum

1. Aşağıdan `Telsiz-…-windows-x64.zip` dosyasını indir ve bir klasöre çıkar.
2. **Telsiz.exe**'ye çift tıkla. CS2'yi dinlemeye başlar ve çeviriler bu bilgisayarın tarayıcısında açılır.
3. Telefonda görmek için onun yerine **Telsiz - Telefon**'u çalıştır ve konsoldaki QR kodu okut. Telefon aynı Wi‑Fi ağında olmalı.

Bilmen gerekenler:

- İlk açılışta modeller bir kez indirilir: bilgisayarının RAM'ine göre ~1–2 GB.
- Program imzalı olmadığı için Windows "Bilgisayarınız korundu" uyarısı verebilir: **Ek bilgi → Yine de çalıştır**.
- Windows 10 2004 veya üstü, 64-bit gerekir. En tutarlı sonuç için CS2'yi **Tam Ekran Pencereli** modda oyna.
- Ayarları değiştirmek için `config.example.toml` dosyasını aynı klasörde `config.toml` adıyla kopyalayıp düzenle.

Kurulum, SSS ve "Neden güvenli?" bölümü için README'ye bak.

### Lisans

Telsiz MIT lisanslıdır. NLLB çeviri modelinin lisansı CC-BY-NC-4.0'dır (yalnızca ticari olmayan kullanım); paketle gelmez, ilk kullanımda indirilir. Paketteki açık kaynak bileşenler `THIRD_PARTY_NOTICES.txt` dosyasında listelenir.

<a id="english"></a>

## 🇬🇧 English

Telsiz listens to your teammates' **voice chat** while you play CS2, detects the spoken language, translates it into Turkish and shows it **as text**. You read the translations **on your phone** or **in a browser on a second screen**.

### Installation

1. Download `Telsiz-…-windows-x64.zip` below and extract it to a folder.
2. Double-click **Telsiz.exe**. It starts listening to CS2, and the translations open in a browser on this PC.
3. To see them on your phone, run **Telsiz - Telefon** instead and scan the QR code in the console. The phone must be on the same Wi‑Fi network.

Things to know:

- The models are downloaded once, on first start: ~1–2 GB depending on your PC's RAM.
- The program is not signed, so Windows may show "Windows protected your PC": **More info → Run anyway**.
- Requires Windows 10 2004 or later, 64-bit. For the most consistent results, play CS2 in **Fullscreen Windowed** mode.
- To change settings, copy `config.example.toml` to `config.toml` in the same folder and edit it.

See the README for installation, the FAQ and the "Why is this safe?" section.

### License

Telsiz is MIT-licensed. The NLLB translation model is licensed CC-BY-NC-4.0 (non-commercial use only); it is not part of the package and is downloaded on first use. The open source components in the package are listed in `THIRD_PARTY_NOTICES.txt`.
