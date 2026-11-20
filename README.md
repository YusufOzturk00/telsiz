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

🚧 **Erken geliştirme aşamasında.** Şu an yalnızca proje iskeleti hazır (M0). Çeviri hattı henüz yok; kullanılabilir bir sürüm yayınlandığında kurulum adımları burada olacak.

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

Gerçek modelle çalışan yavaş testler `@pytest.mark.slow` ile işaretlidir. Bunları atlamak için `pytest -m "not slow"` kullanabilirsin.

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

🚧 **In early development.** Only the project skeleton is ready right now (M0). The translation pipeline does not exist yet; installation steps will be here once a usable release is published.

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

Slow tests that run real models are marked with `@pytest.mark.slow`. You can skip them with `pytest -m "not slow"`.

### License

[MIT](LICENSE)

### Trademark notice

Counter-Strike and CS2 are trademarks of Valve Corporation. Telsiz is not affiliated with or endorsed by Valve in any way.
