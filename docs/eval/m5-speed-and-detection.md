# Speed and speech detection in game (M5)

Measured on 2026-11-21 on a Ryzen 5 7500F (6 cores) with an RTX 4060, Windows 11,
Game Mode on. CPU inference uses int8 and 4 threads, as the live app does.

## What players saw

- Lines arrived only after alt-tab. CS2 was in front on the only monitor, so the
  console and the browser page were behind it. The pipeline itself was live. Fix:
  read the translations on the phone or on a second screen (there is no overlay).
- Lines took 5-6 s now and then: Whisper decoded unsure clips again.
- Most of the talking was not translated: the speech detector dropped it (below).

## In-game measurements (numbers only; no audio was written to disk)

| Setup | Recognition per 4 s clip, CS2 in front |
|---|---|
| Whisper large-v3-turbo on the GPU (any CPU or GPU priority) | 26-28 s |
| Whisper small on the CPU | ~2.9 s |

During a match CS2 keeps the graphics card busy, so live game mode recognizes on the CPU.

| Silero VAD peak per second | Bot match (game sound only, 154 s) | Real matches (teammates talking, 514 s) |
|---|---|---|
| >= 0.5 | 1 % of seconds | 44-60 % of seconds |
| >= 0.35 | 8 % | 50-71 % |

Game sound alone almost never reaches 0.5, but in real matches only about half of the
seconds that did became clips: a voice starts clearly, then scores 0.3-0.5 under game
sound, and the clip was cut short or dropped as under 250 ms of speech.
Now an utterance still starts at 0.5, but frames down to 0.35 count as speech.

CS2 mutes itself when it is not in front (-100 dBFS), so nothing can be translated
during alt-tab. Speech was caught in every display mode (Fullscreen Windowed, Windowed,
Fullscreen) in the same match; some earlier Fullscreen sessions caught very little.

## Test clips

Two English and two Russian public-domain clips (tests/fixtures), cut by the live VAD,
language detected per clip; clean and with simulated voice chat (codec band, noise,
clipping, packet loss), down to 0 dB SNR.

### Whisper encoder window (CPU)

Whisper pads every clip to 30 s; live clips are at most ~6 s.

| Model | Window | WER | Time per clip |
|---|---|---|---|
| small | 30 s | 39 % | 1573 ms |
| small | **10 s** | **38 %** | **386 ms** |
| small | clip + 1 s | 44 % | 248 ms |
| large-v3-turbo | 30 s | 26 % | 6440 ms |
| large-v3-turbo | **15 s** | **26 %** | **2180 ms** |
| large-v3-turbo | 10 s | 39 % | 1279 ms |

### Whisper temperature fallback (CPU, small)

| | Mean WER | Median time | Slowest clip |
|---|---|---|---|
| Single pass | 42 % | 2.07 s | 2.9 s |
| With retries | 42 % | 2.08 s | 10.0 s |

Same WER in 19 of 20 conditions; in the 20th (Russian at -5 dB) both were unusable.
In matches 27 % of lines were retried (~4.7 s instead of ~2.2 s).

### Old vs new settings, end to end through Telsiz's code (small, CPU)

| | WER | Clips | Time per clip |
|---|---|---|---|
| Before (VAD 0.5, 30 s window) | 41 % | 43 | 1710 ms |
| **Now (VAD start 0.5 / continue 0.35, 10 s window)** | **38 %** | 39 | **446 ms** |

Noisy voice chat improved most (59 % -> 49 %). Neither setting made a single clip from
a minute of white, pink, rumble or gunshot-like noise. In the live app the time from the
end of speech to the screen went from ~3.2 s to ~2.2 s.

### Translation beam size (NLLB, CPU, glossary on; chrF over 70 phrases)

| Model | Beam | chrF (all) | chrF (ru->tr) | Median time |
|---|---|---|---|---|
| NLLB-1.3B | **4** | **57.0** | **42.1** | 752 ms |
| NLLB-1.3B | 1 | 53.1 | 32.8 | 614 ms |
| NLLB-600M | 4 | 53.5 | 36.5 | 366 ms |

A smaller beam saves little time and costs Russian quality, so the beam stays at 4.
These timings were taken while another measurement ran; compare them with each other.
