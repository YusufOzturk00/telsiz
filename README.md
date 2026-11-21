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

🚧 **Erken geliştirme aşamasında.** Şu an **yalnızca CS2'nin sesini** canlı olarak dinleyip konuşmaları Türkçeye çevirebiliyor ve çeviriyi tarayıcıda (ikinci ekran) ve telefonda gösterebiliyor (M3). Overlay henüz yok; kullanılabilir bir sürüm yayınlandığında kurulum adımları burada olacak.

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

**Yalnızca oyunun sesi:** Telsiz yalnızca `cs2.exe`'nin sesini dinler; arka planda çalan müzik, videolar ve Discord çevrilmez. Bunun için `telsiz-loopback.exe` adlı küçük bir yardımcı program gerekir. Bu program açık kaynak kodundan ([native/process_loopback](native/process_loopback)) GitHub Actions'ta derlenir; repoda hazır exe tutulmaz. Kaynak koddan çalıştırırken son derlenmiş halini şöyle indirebilirsin ([GitHub CLI](https://cli.github.com/) gerekir):

```powershell
$run = gh run list --repo YusufOzturk00/telsiz --workflow ci.yml --branch main --status success -L 1 --json databaseId -q ".[0].databaseId"
```

```powershell
gh run download $run --repo YusufOzturk00/telsiz -n telsiz-loopback -D native/process_loopback/build/Release
```

Ya da kendin derle (bkz. [native/process_loopback/README.md](native/process_loopback/README.md)). Oyun kapalıysa Telsiz açılmasını bekler; oyun kapanıp yeniden açılınca kendiliğinden yeniden bağlanır. Yardımcı program bulunamazsa ya da Windows sürümün bunu desteklemiyorsa Telsiz bunu konsolda söyler ve bilgisayarda çalan **bütün sesi** dinlemeye geçer. Bütün sesi kendin seçmek için `--capture system`, başka bir programla denemek için `--app` kullan (ör. tarayıcıda Rusça bir video açıp `python -m telsiz --live --app chrome.exe`).

Bilmen gerekenler:

- Ses diske yazılmaz ve bilgisayarından dışarı çıkmaz. Çeviri yereldir; telefon modu yalnızca yerel ağda çalışır.
- Konsolda her satır için uçtan uca gecikme yazılır (konuşma bitişinden ekrana).
- **Hep canlı kalır:** Ekran kartı oyunla meşgul olduğu için Telsiz 5 saniyeden fazla geride kalırsa birikmiş sesi atlar ve canlı sese döner; geç gelen bir uyarı oyunda işe yaramaz. Bu süre `config.toml` içinde `[performance]` bölümündeki `max_lag_s` ile değiştirilebilir (`0` = hiç atlama). Kapanışta kaç saniyenin atlandığı ve konuşma olmayan kaç ses parçasının (silah, adım sesi) elendiği yazılır.
- **Oyun önce gelir:** Telsiz en fazla 4 işlemci çekirdeği kullanır ve kimse konuşmazken neredeyse hiç kaynak kullanmaz. İşlem önceliği bilerek normal bırakılır: düşük öncelikte, CS2 bütün çekirdekleri kullanırken konuşma tanıma takılıyor ve çeviriler ancak alt-tab yapınca geliyordu (ekran kartı kullanılırken bile).
- **Donanıma göre otomatik ayar:** Telsiz açılırken bilgisayarını tanır ve neyi neden seçtiğini konsola yazar.
  - **Konuşmayı yazıya çevirme:** NVIDIA ekran kartı varsa ekran kartında `large-v3-turbo` (daha isabetli), yoksa işlemcide `small` çalışır. AMD ve Intel ekran kartları bu hızlandırmayı (CUDA) desteklemediği için işlemci kullanılır.
  - **Oyunu dinlerken tanıma işlemcide yapılır:** Maç sırasında CS2 ekran kartını o kadar doldurur ki, ekran kartında 4 saniyelik bir cümlenin tanınması ~26 saniye sürdü; Telsiz'e öncelik vermek de fark etmedi ve tanıma ancak alt-tab yapınca bitti. İşlemcide aynı cümle oyun öndeyken ~3 saniye sürdü (ölçüm: RTX 4060, Ryzen 5 7500F, Windows Oyun Modu açık). Bu yüzden Telsiz CS2'yi dinlerken tanımayı işlemcide `small` modeliyle yapar ve oyuna ekran kartı belleği bırakır. Ekran kartını yine de kullanmak için `--device cuda` ver.
  - **Çeviri:** Kurulu RAM'e göre seçilir: 24 GB ve üstü **NLLB-200 1.3B** (en iyi kalite), 12–16 GB **NLLB-200 600M**, daha azı **Argos Translate** (en hafif). Çeviri her zaman işlemcide çalışır; ekran kartı oyuna kalır. NLLB indirilemez ya da yüklenemezse Argos'a geçilir.
  - **Kaynak kullanımı (yaklaşık):** NLLB-1.3B ~1.6 GB RAM, NLLB-600M ~0.8 GB, Argos ~0.4 GB; konuşmayı yazıya çevirme ekran kartında ~1.2 GB ekran kartı belleği kullanır.
  - **İndirilenler (ilk kullanımda bir kez):** NVIDIA ve 32 GB RAM'li bir bilgisayarda toplam ~4.4 GB, NVIDIA ve 16 GB RAM'de ~3.7 GB, AMD/Intel ekran kartı ve 16 GB RAM'de ~1.3 GB.
  - **Elle seçmek için:** `config.toml` içinde `[translate]` bölümüne `engine = "nllb"` veya `engine = "argos"`, `[asr]` bölümüne `device = "cpu"` (ekran kartını hiç kullanmaz) yaz.
- **NLLB lisansı:** NLLB-200 model ağırlıklarının lisansı **CC-BY-NC-4.0**'dır, yani yalnızca ticari olmayan kullanıma izin verir. Telsiz'in kodu MIT lisanslıdır; NLLB modeli Telsiz ile dağıtılmaz, ilk kullanımda indirilir. NLLB Rusça ve Ukraynacayı İngilizceye uğramadan doğrudan Türkçeye çevirir.
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

- **Ses:** Windows WASAPI loopback capture (sistem geneli) ve **Application/Process Loopback** (`ActivateAudioInterfaceAsync` + `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`). Bu, OBS ve Discord'un kullandığı işletim sistemi seviyesindeki API'dir; oyun sürecine dokunmaz. Oyunun süreç kimliğini (PID) bulmak için yalnızca süreç listesi okunur (Windows Görev Yöneticisi'nin de gösterdiği liste, `CreateToolhelp32Snapshot`). Bu bir **liste okuma** işlemidir, süreç açılmaz. PID yalnızca Windows ses motoruna "bu programın sesini ver" demek için kullanılır. Bu işi yapan `telsiz-loopback.exe`, Microsoft'un açık kaynak ApplicationLoopback örneğine dayanır ve kaynak kodundan derlenir.
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

`telsiz-loopback.exe`'yi derlemek için CMake ve Visual Studio Build Tools (C++) gerekir; adımlar [native/process_loopback/README.md](native/process_loopback/README.md) dosyasında.

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

🚧 **In early development.** Right now it can listen live to **only CS2's audio**, translate the speech into Turkish and show the translation in a browser (second screen) and on your phone (M3). The overlay does not exist yet; installation steps will be here once a usable release is published.

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

**Only the game's audio:** Telsiz listens only to `cs2.exe`'s audio; music, videos and Discord playing in the background are not translated. This needs a small helper program called `telsiz-loopback.exe`. It is built from its open source code ([native/process_loopback](native/process_loopback)) on GitHub Actions; no prebuilt exe is kept in the repository. When running from source you can download the latest build like this ([GitHub CLI](https://cli.github.com/) required):

```powershell
$run = gh run list --repo YusufOzturk00/telsiz --workflow ci.yml --branch main --status success -L 1 --json databaseId -q ".[0].databaseId"
```

```powershell
gh run download $run --repo YusufOzturk00/telsiz -n telsiz-loopback -D native/process_loopback/build/Release
```

Or build it yourself (see [native/process_loopback/README.md](native/process_loopback/README.md)). If the game is closed, Telsiz waits for it to start; when the game closes and starts again, it reconnects by itself. If the helper cannot be found or your Windows version does not support this, Telsiz says so in the console and switches to listening to **all audio** playing on your PC. Use `--capture system` to choose all audio yourself, and `--app` to try it with another program (e.g. open a Russian video in the browser and run `python -m telsiz --live --app chrome.exe`).

Things to know:

- Audio is never written to disk and never leaves your PC. Translation is local; phone mode only works on the local network.
- The console shows the end-to-end latency of every line (from the end of speech to the screen).
- **Always live:** if Telsiz falls more than 5 seconds behind because the graphics card is busy with the game, it skips the backlog and returns to live audio; a late warning is useless in a game. Change this with `max_lag_s` in the `[performance]` section of `config.toml` (`0` = never skip). On exit it reports how many seconds were skipped and how many sound clips that were not speech (gunfire, footsteps) were dropped.
- **The game comes first:** Telsiz uses at most 4 CPU cores and almost no resources while nobody speaks. Its process priority is deliberately left at normal: at a lower priority, speech recognition stalled while CS2 used every core, and translations only arrived after alt-tab (even with the graphics card).
- **Automatic settings for your hardware:** At startup Telsiz looks at your PC and writes what it chose and why to the console.
  - **Speech recognition:** With an NVIDIA graphics card, `large-v3-turbo` (more accurate) runs on the card; otherwise `small` runs on the processor. AMD and Intel graphics cards do not support this acceleration (CUDA), so the processor is used.
  - **While listening to the game, recognition runs on the processor:** During a match CS2 keeps the graphics card so busy that recognizing a 4-second sentence on the card took ~26 seconds; giving Telsiz priority made no difference, and recognition only finished after alt-tab. On the processor the same sentence took ~3 seconds with the game in front (measured: RTX 4060, Ryzen 5 7500F, Windows Game Mode on). So while listening to CS2, Telsiz recognizes speech on the processor with the `small` model and leaves the graphics memory to the game. To use the graphics card anyway, pass `--device cuda`.
  - **Translation:** Chosen by installed RAM: 24 GB or more **NLLB-200 1.3B** (best quality), 12–16 GB **NLLB-200 600M**, less **Argos Translate** (lightest). Translation always runs on the processor; the graphics card is left to the game. If NLLB cannot be downloaded or loaded, Argos is used.
  - **Resource use (approximate):** NLLB-1.3B ~1.6 GB RAM, NLLB-600M ~0.8 GB, Argos ~0.4 GB; speech recognition on the graphics card uses ~1.2 GB of graphics memory.
  - **Downloads (once, on first use):** about 4.4 GB in total on a PC with NVIDIA and 32 GB RAM, ~3.7 GB with NVIDIA and 16 GB RAM, ~1.3 GB with an AMD/Intel graphics card and 16 GB RAM.
  - **To choose yourself:** in `config.toml` write `engine = "nllb"` or `engine = "argos"` in the `[translate]` section, and `device = "cpu"` in the `[asr]` section (never uses the graphics card).
- **NLLB license:** the NLLB-200 model weights are licensed **CC-BY-NC-4.0**, which allows non-commercial use only. Telsiz's code is MIT-licensed; the NLLB model is not distributed with Telsiz and is downloaded on first use. NLLB translates Russian and Ukrainian straight into Turkish without going through English.
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

- **Audio:** Windows WASAPI loopback capture (system-wide) and **Application/Process Loopback** (`ActivateAudioInterfaceAsync` + `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`). This is the operating-system-level API that OBS and Discord use; it does not touch the game process. To find the game's process ID (PID), only the process list is read (the list Windows Task Manager also shows, `CreateToolhelp32Snapshot`). This is a **list read**; no process is opened. The PID is only used to tell the Windows audio engine "give me this program's audio". `telsiz-loopback.exe`, which does this, is based on Microsoft's open-source ApplicationLoopback sample and is built from source.
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

Building `telsiz-loopback.exe` needs CMake and the Visual Studio Build Tools (C++); the steps are in [native/process_loopback/README.md](native/process_loopback/README.md).

### License

[MIT](LICENSE)

### Trademark notice

Counter-Strike and CS2 are trademarks of Valve Corporation. Telsiz is not affiliated with or endorsed by Valve in any way.
