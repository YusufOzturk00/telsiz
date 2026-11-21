# Telsiz — Proje Talimatları (Claude Code için)

**İsim kuralı:** Uygulamanın adı **Telsiz**. Repo adı `telsiz`, Python paket adı `telsiz`. "CS2" ve "Counter-Strike" Valve'ın markasıdır; uygulama adında, paket adında veya logoda kullanılmaz. Yalnızca açıklamada geçebilir: "Real-time voice chat translator for CS2".

Bu dosya projenin ana talimat dosyasıdır. Her oturumda önce bunu oku. Kod, yorumlar ve commit mesajları **İngilizce** olacak (açık kaynak, uluslararası kitle).

**README kuralı:** README iki dilli olacak: **önce Türkçe, sonra İngilizce.** İki bölüm **aynı metnin tam karşılığı** olmalı; İngilizce bölüm kısaltılmış bir özet değil, Türkçe bölümün eksiksiz çevirisi olacak. Uygulama Türkçeye çeviri yaptığı için ana hedef kitle Türk oyuncular, bu yüzden Türkçe bölüm önce gelir. Yapı:
1. En üstte dil bağlantıları: `🇹🇷 Türkçe | 🇬🇧 English` (sayfa içi bağlantılarla bölümlere gider)
2. `## 🇹🇷 Türkçe`: bölümün tamamı
3. `## 🇬🇧 English`: aynı başlıklar, aynı sıra, aynı içerik

README'de bir değişiklik yapıldığında **iki dil birlikte güncellenir**; biri güncellenip diğeri eski bırakılmaz.

## 1. Proje özeti

Counter-Strike 2 oynarken takım arkadaşlarının **sesli sohbetini** dinleyen, konuşulan dili (İngilizce, Rusça, Ukraynaca, Lehçe vb.) tespit eden ve kullanıcının seçtiği dile (varsayılan: Türkçe) çevirip **yazı olarak** gösteren bir masaüstü uygulaması.

Çeviri üç yerde gösterilebilmeli (kullanıcı seçer, aynı anda birden fazlası açık olabilir):
1. **Overlay**: Oyunun üstünde duran, şeffaf, tıklamaları geçiren pencere
2. **İkinci ekran**: Normal bir pencere veya tarayıcı sekmesi
3. **Telefon**: Aynı Wi‑Fi ağında, QR kod okutularak açılan bir web sayfası

**Kapsam dışı:** Yazılı (text) sohbet çevirisi **yapılmayacak**. Uygulama yalnızca sesli sohbetle ilgilenir. Konsol log dosyası okuma, `-condebug` / `con_logfile` gibi özellikler ekleme ve önerme.

Hedef platform: **Windows 10 2004 (build 19041) ve üstü, 64-bit.**
Lisans: **MIT.**

---

## 2. KIRMIZI ÇİZGİLER: Anti-cheat güvenliği (mutlak kurallar)

Bu uygulama VAC, FACEIT AC ve diğer anti-cheat sistemleri açısından **sıfır risk** taşımalı. Aşağıdaki kurallar hiçbir koşulda esnetilmez. Bir özellik bunlardan birini gerektiriyorsa **o özelliği yapma, bana sor.**

**YASAK:**
- `cs2.exe` (veya herhangi bir oyun süreci) üzerinde `OpenProcess`, `ReadProcessMemory`, `WriteProcessMemory`, `VirtualAllocEx`, `CreateRemoteThread` vb. çağırmak
- DLL enjeksiyonu, DirectX/Vulkan/DXGI hook'u, `SetWindowsHookEx` ile oyuna global hook
- Oyun dosyalarını, config'lerini (`.cfg`) veya `.vpk` dosyalarını değiştirmek
- Kernel sürücüsü yüklemek veya kullanmak
- Oyuna tuş/fare girdisi göndermek (`SendInput`, `keybd_event` vb.)
- Oyun belleğinden offset/pattern okuyan herhangi bir kütüphane eklemek
- Uygulamanın kendini gizlemesi (process gizleme, string şifreleme, "undetected" tarzı teknikler). Uygulama şeffaf ve masum görünmeli, çünkü masum.

**İZİNLİ (ve kullanılacak) yöntemler:**
- **Ses:** Windows WASAPI loopback capture (sistem geneli) ve **Application/Process Loopback** (`ActivateAudioInterfaceAsync` + `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`). Bu, OBS ve Discord'un kullandığı işletim sistemi seviyesindeki API'dir; oyun sürecine dokunmaz. Oyunun PID'sini bulmak için sadece süreç listesi (`psutil.process_iter`) okunabilir. Bu bir **liste okuma** işlemidir, süreç açılmaz.
- **Görüntü:** Ayrı, kendi sürecimizde çalışan, `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` stilli şeffaf pencere (DWM üzerinden çizilir).
- **(İleride, opsiyonel)** Valve'ın resmi **Game State Integration (GSI)** özelliği, örneğin raund durumuna göre overlay'i gizlemek için.

README'de Türkçe bölümde "Neden güvenli?", İngilizce bölümde "Why is this safe?" başlıklı bir bölüm olacak ve yukarıdaki listeyi açıkça anlatacak.

---

## 3. Teknoloji yığını (MVP)

| Katman | Seçim | Not |
|---|---|---|
| Dil | Python 3.11+ | Hızlı prototip için. İleride sıcak noktalar native'e taşınabilir |
| Ses yakalama (M1) | `PyAudioWPatch` (WASAPI sistem loopback) | Basit başlangıç |
| Ses yakalama (M3) | Process loopback | Microsoft `ApplicationLoopback` örneğinden (MIT) türetilmiş küçük bir C++ yardımcı exe/DLL, **CI'da kaynak koddan derlenecek**. Repoya hazır (prebuilt) binary konmaz |
| VAD | `silero-vad` | Sadece konuşma bölümlerini ayıklar |
| Konuşmayı yazıya çevirme ve dil tespiti | `faster-whisper` (CTranslate2) | Model seçilebilir: `small` / `medium` / `large-v3-turbo`. Varsayılan `auto`: NVIDIA (CUDA) varsa GPU'da `large-v3-turbo` (`int8_float16`), yoksa CPU'da `small` (int8). AMD/Intel ekran kartları CUDA desteklemediği için CPU'ya düşer. **Oyun dinlenirken (`--live`, capture `auto`) `auto` her zaman CPU'dur:** ölçümde CS2 maç sırasında GPU'yu doldurduğu için bir cümle GPU'da ~26 sn, CPU'da ~3 sn sürdü (öncelik fark etmedi) |
| Çeviri | Takılıp çıkarılabilir `Translator` arayüzü | Varsayılan: **`auto`**, kurulu RAM'e göre seçilir: 22 GB ve üstü **NLLB-200 distilled 1.3B**, 11 GB ve üstü **NLLB-200 distilled 600M**, altı **Argos Translate**. Hepsi yerel ve CPU'da çalışır. NLLB yüklenemezse otomatik olarak Argos'a düşülür. NLLB model ağırlıkları **CC-BY-NC-4.0** (ticari olmayan kullanım); ağırlıklar uygulamayla dağıtılmaz, ilk kullanımda indirilir; bu README'de belirtilir. Opsiyonel: **DeepL API** (kullanıcının kendi anahtarıyla) |
| Sunucu | `FastAPI` + `uvicorn` + WebSocket | Yalnızca yerel ağda çalışır, varsayılan `127.0.0.1`; telefon modu açıkça açıldığında LAN'a bağlanır |
| Web arayüzü | Düz HTML/CSS/JS, build adımı yok | İkinci ekran ve telefon bunu kullanır |
| Overlay | `PySide6` çerçevesiz, şeffaf pencere + ctypes ile extended style | Web arayüzüne değil, doğrudan iç event bus'a abone olur |
| QR kod | `qrcode` | Telefon bağlantısı için |
| Ayarlar | `config.toml` (`tomllib` + `tomli-w`) | |
| Test | `pytest` | |
| Paketleme (sonra) | PyInstaller | |

Bağımlılık eklerken lisansı kontrol et; GPL/AGPL bağımlılık ekleme, önce bana sor.

---

## 4. Mimari

```
[cs2.exe ses çıkışı]
      │  (WASAPI loopback / process loopback — oyuna dokunmaz)
      ▼
AudioCapture ──► Resampler (16 kHz mono float32)
      ▼
VAD (silero) ──► Utterance segmenter (konuşma parçaları, maks ~10 sn)
      ▼
ASR (faster-whisper) ──► dil tespiti (izinli diller listesiyle sınırlı) + yazıya çevirme
      ▼
GlossaryFilter (oyun terimleri: "eco", "flash", "A long"… çevrilmez)
      ▼
Translator (argos | nllb | deepl)
      ▼
EventBus (asyncio) ──┬──► Overlay (PySide6)
                     ├──► WebSocket ──► 2. ekran (tarayıcı/pencere)
                     └──► WebSocket ──► Telefon (LAN, QR)
```

Her pipeline aşaması ayrı bir modül olacak ve bir arayüzün (Protocol/ABC) arkasında duracak. Böylece testlerde sahte (mock) bileşenler kullanılabilir.

### Event şeması (WebSocket JSON)
```json
{
  "type": "voice",
  "id": "uuid",
  "ts": 1732100000.123,
  "source_lang": "ru",
  "source_lang_confidence": 0.93,
  "original": "Они идут на Б",
  "translated": "B'ye geliyorlar",
  "target_lang": "tr",
  "speaker": null,
  "latency_ms": 1450
}
```
`speaker` şimdilik `null` (konuşanı belirlemek ileriki bir iş). `type` alanı ileride başka event türleri (ör. durum bildirimleri) eklenebilsin diye duruyor.

---

## 5. Repo yapısı

```
telsiz/
├── CLAUDE.md
├── README.md                 # Önce TR, sonra EN (aynı metin), "Neden güvenli? / Why is this safe?"
├── LICENSE                   # MIT
├── pyproject.toml
├── config.example.toml
├── src/telsiz/
│   ├── __main__.py           # giriş noktası, CLI argümanları
│   ├── config.py
│   ├── bus.py                # asyncio event bus
│   ├── audio/
│   │   ├── base.py           # AudioSource protocol
│   │   ├── system_loopback.py
│   │   ├── process_loopback.py   # M3
│   │   └── file_source.py    # testler ve demo için .wav okuyucu
│   ├── vad.py
│   ├── asr.py
│   ├── glossary.py
│   ├── translate/
│   │   ├── base.py
│   │   ├── argos.py
│   │   ├── nllb.py
│   │   └── deepl.py
│   ├── server/
│   │   ├── app.py            # FastAPI + WS
│   │   └── static/           # index.html, overlay-style.css, app.js
│   ├── overlay/
│   │   ├── window.py         # PySide6 şeffaf pencere
│   │   └── win32.py          # ctypes: extended styles, DPI awareness
│   └── util/
│       └── qr.py
├── native/process_loopback/  # M3: C++ yardımcı (CMake), CI'da derlenir
├── data/glossary.toml        # oyun terimleri sözlüğü
├── tests/
│   ├── fixtures/             # yalnızca CC0/kamu malı ses örnekleri, gerçek oyuncu kaydı YOK
│   └── ...
└── .github/workflows/ci.yml  # windows-latest: lint (ruff), test (pytest), native build
```

---

## 6. Ekran, tam ekran modu ve çözünürlük kuralları

- Overlay konumu ve boyutu **yüzde** olarak saklanır (`x_pct`, `y_pct`, `width_pct`, `font_scale`). Piksel değeri saklanmaz.
- Uygulama başlarken `SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)` çağrılır.
- Overlay hangi monitörde olacağını config'den alır (varsayılan: birincil monitör). Monitör geometrisi değişirse (`QScreen.geometryChanged`) yeniden konumlanır.
- Overlay **tıklamaları geçirir** ve **odak çalmaz** (`WS_EX_NOACTIVATE`). Oyun asla alta inmemeli.
- Overlay yalnızca **Tam Ekran Pencereli (borderless)** modda garanti edilir. Uygulama ilk açılışta ve README'de bunu söyler. Exclusive fullscreen ve 4:3 stretched kullananlara **ikinci ekran veya telefon modu** önerilir.
- Overlay görünümü: yarı saydam koyu arka plan, beyaz yazı, son N mesaj (varsayılan 3), her mesaj X saniye sonra kaybolur (varsayılan 6). Dil kodu küçük bir etiket olarak gösterilir: `[RU]`.
- Ayarlar ve overlay konumu için **ayrı bir ayar penceresi** olur; overlay'in kendisi asla etkileşimli değildir. Konumlandırma için "düzenleme modu" sadece ayar penceresinden açılır.

---

## 7. Dil tespiti kuralları

- Config'de `allowed_source_langs = ["en", "ru", "uk", "pl", "de", "tr", ...]` bulunur.
- faster-whisper'ın dil olasılıkları alınır, **sadece izinli dillere** göre yeniden normalize edilir ve en yükseği seçilir.
- Kısa konuşmalarda (< 1.2 sn) veya güven < eşik (varsayılan 0.6) ise: aynı oturumda son 30 sn içinde baskın olan dil kullanılır (dil yapışkanlığı).
- Kaynak dil hedef dille aynıysa (ör. Türkçe konuşan bir takım arkadaşı) çeviri atlanır. Bu durumda orijinal metin gösterilir veya kullanıcı tercihine göre hiç gösterilmez.
- Whisper halüsinasyonlarını filtrele: sessiz ve gürültülü parçalarda çıkan tipik çıktılar ("Thank you.", "Продолжение следует...", tekrar eden token'lar) kara listeye alınır, `no_speech_prob` eşiği uygulanır.

---

## 8. Gizlilik

- Ses **asla diske yazılmaz** (debug modu dahil; debug için kullanıcı açıkça `--record-debug` vermeli ve bu README'de uyarıyla açıklanmalı).
- Varsayılan çeviri motoru yereldir. Bulut motoru (DeepL) seçilirse ayarlar ekranında "metin üçüncü tarafa gönderilecek" uyarısı gösterilir.
- Telemetri yok.
- Sunucu varsayılan olarak yalnızca `127.0.0.1`'de dinler. Telefon modu açılınca LAN'a açılır ve rastgele bir **erişim token'ı** üretilir; bu token QR koddaki URL'ye eklenir, token'ı olmayan bağlantılar reddedilir.

---

## 9. Kilometre taşları

Her kilometre taşı ayrı bir branch/PR olarak ilerlesin. Bir kilometre taşını bitirince durup bana özet ver.

### M0: İskelet
- `pyproject.toml`, paket yapısı, `ruff`, `pytest`, MIT lisansı, README taslağı (önce Türkçe, sonra İngilizce; "Neden güvenli? / Why is this safe?" bölümü dahil)
- GitHub Actions: `windows-latest` üzerinde lint ve test
- **Kabul kriteri:** `python -m telsiz --help` çalışır; CI yeşil.

### M1: Dosyadan çeviri hattı (oyunsuz)
- `FileSource` → VAD → ASR → Translator (argos) → konsola yazdırma
- `python -m telsiz --input sample.wav --target tr`
- **Kabul kriteri:** İngilizce ve Rusça örnek dosyalar doğru dilde tespit edilip Türkçeye çevrilir; testler sahte ASR ve sahte çevirmenle de çalışır.

### M2: Canlı sistem sesi ile web arayüzü
- `SystemLoopbackSource` (PyAudioWPatch)
- FastAPI + WebSocket + basit web arayüzü (2. ekran için)
- Telefon modu: LAN, token, QR kod
- **Kabul kriteri:** YouTube'da Rusça bir video oynatınca tarayıcıda ve telefonda Türkçe altyazı akar; uçtan uca gecikme loglanır.

### M3: Yalnızca CS2 sesi (process loopback)
- `native/process_loopback`: C++/CMake ile PCM'i stdout'a veya named pipe'a yazan küçük bir yardımcı; CI'da derlenir
- `ProcessLoopbackSource`: `cs2.exe` PID'sini süreç listesinden bulur; oyun kapanınca bekler, açılınca bağlanır
- Windows sürümü desteklemiyorsa sistem loopback'e otomatik düşer ve kullanıcıyı uyarır
- **Kabul kriteri:** Arka planda müzik çalarken yalnızca hedef uygulamanın sesi işlenir.

### M4: Overlay
- PySide6 şeffaf, tıklama geçiren, odak çalmayan pencere; yüzde tabanlı konumlandırma; DPI farkındalığı; çoklu monitör
- Ayarlar penceresi (dil seçimi, motor seçimi, overlay konumu/boyutu, gösterim modları)
- **Kabul kriteri:** CS2 Tam Ekran Pencereli modda 1080p, 1440p ve %150 ölçekte overlay doğru yerde görünür, oyun odağı kaybolmaz.

### M5: Cilalama ve dağıtım
- Oyun terimleri sözlüğü (`data/glossary.toml`)
- PyInstaller ile tek klasörlük dağıtım; GitHub Releases iş akışı
- README (TR + EN, aynı içerik): kurulum, ekran görüntüleri, SSS (exclusive fullscreen, stretched, FACEIT, gizlilik)
- **Kabul kriteri (README):** Türkçe ve İngilizce bölümler aynı başlıklara, aynı sıraya ve aynı içeriğe sahip

---

## 10. Çalışma kuralları

- Kod yazmadan önce ilgili kilometre taşı için kısa bir plan çıkar.
- Testleri önce veya kodla birlikte yaz. Ağır modelleri (Whisper, çeviri) birim testlerde **mock'la**. Gerçek modelle çalışan testleri `@pytest.mark.slow` ile işaretle.
- Gerçek oyuncu ses kayıtlarını repoya koyma. Test sesleri CC0/kamu malı kaynaklardan (ör. Mozilla Common Voice CC0) gelsin ve kaynakları `tests/fixtures/SOURCES.md`'de listelensin.
- Bölüm 2'deki kırmızı çizgilere değen herhangi bir öneri, kütüphane veya kod parçası görürsen **uygulama, bana sor.**
- Küçük ve anlamlı commit'ler at; commit mesajları İngilizce olsun.
- **Oyun performansı önce gelir:** Telsiz oyunun FPS'ini düşürmemeli. Telsiz CPU iş parçacıklarını sınırlar (varsayılan 4) ve RAM'e göre hafif modeller seçer. İşlem önceliği `normal` kalır: `below_normal`, CS2 sırasında tanımayı (GPU'da bile) aç bırakıyor ve çeviriler ancak alt-tab'da geliyordu. Yeni bir özellik CPU, GPU veya RAM yükünü artırıyorsa önce ölç, sonra varsayılan yap. Ağır işleri (ör. çeviri) GPU'ya ancak ölçüm GPU'nun daha iyi olduğunu gösterirse taşı.

---

## 11. Şimdi başla

**M0 ile başla.** Önce bu dosyaya göre kısa bir uygulama planı yaz, sonra iskeleti oluştur ve CI'ı ayarla. M0 bitince dur ve bana özet ver.
