# Telsiz

[🇹🇷 Türkçe](#turkce) | [🇬🇧 English](#english)

---

<a id="turkce"></a>

## 🇹🇷 Türkçe

> Real-time voice chat translator for CS2

### Telsiz nedir?

Telsiz, Counter-Strike 2 oynarken takım arkadaşlarının **sesli sohbetini** dinleyen, konuşulan dili (İngilizce, Rusça, Ukraynaca, Lehçe vb.) tespit eden ve seçtiğin dile (varsayılan: Türkçe) çevirip **yazı olarak** gösteren bir masaüstü uygulamasıdır.

Çeviriyi üç yerde görebilirsin (aynı anda birden fazlası açık olabilir):

1. **Overlay:** Oyunun üstünde duran, şeffaf, tıklamaları geçiren bir pencere
2. **İkinci ekran:** Normal bir pencere veya tarayıcı sekmesi
3. **Telefon:** Aynı Wi‑Fi ağında, QR kod okutularak açılan bir web sayfası

Telsiz yalnızca sesli sohbetle ilgilenir; yazılı sohbeti çevirmez.

### Durum

🚧 **Erken geliştirme aşamasında.** Şu an bilgisayarında çalan sesi canlı olarak dinleyip konuşmaları Türkçeye çevirebiliyor ve çeviriyi tarayıcıda (ikinci ekran) ve telefonda gösterebiliyor (M2). Overlay ve yalnızca CS2 sesini dinleme henüz yok; kullanılabilir bir sürüm yayınlandığında kurulum adımları burada olacak.

Geliştiriciler şöyle deneyebilir (ilk çalıştırma modelleri indirir):

```powershell
pip install -e ".[all]"
python -m telsiz --live
```

Tarayıcıda `http://127.0.0.1:8765/` açılır ve çeviriler orada akar. Telefonda da görmek için:

```powershell
python -m telsiz --live --phone
```

Konsolda bir QR kod ve bağlantı çıkar; telefon aynı Wi‑Fi ağında olmalı. Bağlantıda bu oturuma özel rastgele bir erişim anahtarı vardır; anahtarı olmayan cihazlar reddedilir. Windows ilk seferde Python'un ağı kullanmasına izin isteyebilir: yalnızca **özel ağlar** için izin ver.

Bilmen gerekenler:

- Şimdilik bilgisayarında çalan **bütün sesi** dinler (müzik, videolar dahil). Yalnızca CS2'nin sesini dinlemek bir sonraki aşamada (M3) gelecek.
- Ses diske yazılmaz ve bilgisayarından dışarı çıkmaz. Çeviri yereldir; telefon modu yalnızca yerel ağda çalışır.
- Konsolda her satır için uçtan uca gecikme yazılır (konuşma bitişinden ekrana).
- Bir ses dosyasını çevirmek için: `python -m telsiz --input tests/fixtures/en_magi_1.wav --target tr`

Oyun terimleri (AWP, eco, A long…) çevrilmeden kalır ve kısaltmalar (nt, gg…) açılır; sözlük [data/glossary.toml](data/glossary.toml) dosyasında. Ölçüm raporları [docs/eval](docs/eval) klasöründe.

### Neden güvenli?

Telsiz, VAC, FACEIT AC ve diğer anti-cheat sistemleri açısından **sıfır risk** taşıyacak şekilde tasarlanmıştır. Oyuna hiçbir şekilde dokunmaz; yalnızca Windows'un, OBS ve Discord'un da kullandığı standart ses ve pencere API'lerini kullanır.

**Telsiz'in asla yapmadığı şeyler:**

- `cs2.exe` (veya herhangi bir oyun süreci) üzerinde `OpenProcess`, `ReadProcessMemory`, `WriteProcessMemory`, `VirtualAllocEx`, `CreateRemoteThread` vb. çağırmak
- DLL enjeksiyonu, DirectX/Vulkan/DXGI hook'u, `SetWindowsHookEx` ile oyuna global hook
- Oyun dosyalarını, config'lerini (`.cfg`) veya `.vpk` dosyalarını değiştirmek
- Kernel sürücüsü yüklemek veya kullanmak
- Oyuna tuş veya fare girdisi göndermek (`SendInput`, `keybd_event` vb.)
- Oyun belleğinden offset veya pattern okuyan herhangi bir kütüphane kullanmak
- Kendini gizlemek (süreç gizleme, string şifreleme, "undetected" tarzı teknikler). Telsiz şeffaf ve masum görünür, çünkü masumdur.

**Telsiz'in kullandığı yöntemler:**

- **Ses:** Windows WASAPI loopback capture (sistem geneli) ve **Application/Process Loopback** (`ActivateAudioInterfaceAsync` + `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`). Bu, OBS ve Discord'un kullandığı işletim sistemi seviyesindeki API'dir; oyun sürecine dokunmaz. Oyunun süreç kimliğini (PID) bulmak için yalnızca süreç listesi okunur. Bu bir **liste okuma** işlemidir, süreç açılmaz.
- **Görüntü:** Ayrı, kendi sürecinde çalışan, `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` stilli şeffaf bir pencere. Pencere, Windows'un masaüstü pencere yöneticisi (DWM) tarafından çizilir; oyunun çizim hattına girilmez.
- **(İleride, opsiyonel)** Valve'ın resmi **Game State Integration (GSI)** özelliği, örneğin raund durumuna göre overlay'i gizlemek için.

Kaynak kodun tamamı açıktır; bu iddiaları kendin doğrulayabilirsin.

### Gereksinimler

- Windows 10 2004 (build 19041) veya üstü, 64-bit
- Python 3.11 veya üstü (kaynak koddan çalıştırmak için)

### Geliştirme

```powershell
git clone https://github.com/YusufOzturk00/telsiz.git
cd telsiz
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Kontroller:

```powershell
ruff check .
ruff format --check .
pytest
python -m telsiz --help
```

Gerçek modelle çalışan yavaş testler `@pytest.mark.slow` ile işaretlidir ve varsayılan olarak atlanır. Çalıştırmak için önce `pip install -e ".[all,dev]"`, sonra `pytest -m slow` kullan; ilk çalıştırma modelleri indirir.

### Lisans

[MIT](LICENSE)

### Marka notu

Counter-Strike ve CS2, Valve Corporation'ın ticari markalarıdır. Telsiz'in Valve ile herhangi bir bağlantısı yoktur ve Valve tarafından onaylanmamıştır.

---

<a id="english"></a>

## 🇬🇧 English

> Real-time voice chat translator for CS2

### What is Telsiz?

Telsiz is a desktop application that listens to your teammates' **voice chat** while you play Counter-Strike 2, detects the spoken language (English, Russian, Ukrainian, Polish, etc.), translates it into the language you choose (default: Turkish) and shows it **as text**.

You can see the translation in three places (more than one can be open at the same time):

1. **Overlay:** A transparent, click-through window that sits on top of the game
2. **Second screen:** A normal window or browser tab
3. **Phone:** A web page on the same Wi‑Fi network, opened by scanning a QR code

Telsiz only deals with voice chat; it does not translate text chat.

### Status

🚧 **In early development.** Right now it can listen to the audio playing on your PC live, translate the speech into Turkish and show the translation in a browser (second screen) and on your phone (M2). The overlay and listening only to CS2's audio do not exist yet; installation steps will be here once a usable release is published.

Developers can try it like this (the first run downloads the models):

```powershell
pip install -e ".[all]"
python -m telsiz --live
```

`http://127.0.0.1:8765/` opens in the browser and the translations stream there. To see them on your phone too:

```powershell
python -m telsiz --live --phone
```

A QR code and a link appear in the console; the phone must be on the same Wi‑Fi network. The link contains a random access key for this session only; devices without the key are refused. The first time, Windows may ask whether Python may use the network: allow it for **private networks** only.

Things to know:

- For now it listens to **all audio** playing on your PC (including music and videos). Listening only to CS2's audio comes in the next stage (M3).
- Audio is never written to disk and never leaves your PC. Translation is local; phone mode only works on the local network.
- The console shows the end-to-end latency of every line (from the end of speech to the screen).
- To translate an audio file: `python -m telsiz --input tests/fixtures/en_magi_1.wav --target tr`

Game terms (AWP, eco, A long…) stay untranslated and abbreviations (nt, gg…) are expanded; the glossary is in [data/glossary.toml](data/glossary.toml). Measurement reports are in the [docs/eval](docs/eval) folder.

### Why is this safe?

Telsiz is designed to carry **zero risk** with respect to VAC, FACEIT AC and other anti-cheat systems. It never touches the game in any way; it only uses the standard Windows audio and window APIs that OBS and Discord also use.

**Things Telsiz never does:**

- Calling `OpenProcess`, `ReadProcessMemory`, `WriteProcessMemory`, `VirtualAllocEx`, `CreateRemoteThread`, etc. on `cs2.exe` (or any game process)
- DLL injection, DirectX/Vulkan/DXGI hooks, global hooks into the game with `SetWindowsHookEx`
- Modifying game files, configs (`.cfg`) or `.vpk` files
- Loading or using a kernel driver
- Sending keyboard or mouse input to the game (`SendInput`, `keybd_event`, etc.)
- Using any library that reads offsets or patterns from game memory
- Hiding itself (process hiding, string encryption, "undetected"-style techniques). Telsiz looks transparent and innocent, because it is innocent.

**Methods Telsiz uses:**

- **Audio:** Windows WASAPI loopback capture (system-wide) and **Application/Process Loopback** (`ActivateAudioInterfaceAsync` + `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`). This is the operating-system-level API that OBS and Discord use; it does not touch the game process. To find the game's process ID (PID), only the process list is read. This is a **list read**; no process is opened.
- **Display:** A separate transparent window running in its own process, with the `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` styles. The window is drawn by the Windows Desktop Window Manager (DWM); the game's rendering pipeline is never entered.
- **(Later, optional)** Valve's official **Game State Integration (GSI)** feature, for example to hide the overlay based on the round state.

All of the source code is open; you can verify these claims yourself.

### Requirements

- Windows 10 2004 (build 19041) or later, 64-bit
- Python 3.11 or later (to run from source)

### Development

```powershell
git clone https://github.com/YusufOzturk00/telsiz.git
cd telsiz
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Checks:

```powershell
ruff check .
ruff format --check .
pytest
python -m telsiz --help
```

Slow tests that run real models are marked with `@pytest.mark.slow` and are skipped by default. To run them, first `pip install -e ".[all,dev]"`, then use `pytest -m slow`; the first run downloads the models.

### License

[MIT](LICENSE)

### Trademark notice

Counter-Strike and CS2 are trademarks of Valve Corporation. Telsiz is not affiliated with or endorsed by Valve in any way.
