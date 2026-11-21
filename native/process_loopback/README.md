# telsiz-loopback

A small Windows helper that captures the audio **one application** plays (for Telsiz:
`cs2.exe` and its child processes) and writes it to stdout as raw PCM.

It uses Windows **process loopback** (`ActivateAudioInterfaceAsync` with
`AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`), an audio-engine API that OBS and
Discord also use. The target process is only a filter for the audio engine: the helper
never opens, reads, writes or injects into it.

Based on Microsoft's
[ApplicationLoopback sample](https://github.com/microsoft/Windows-classic-samples/tree/main/Samples/ApplicationLoopback)
(MIT License).

## Build

The exe is built from this source by CI (`.github/workflows/ci.yml`, artifact
`telsiz-loopback`). No prebuilt binary is kept in the repository.

To build it yourself you need CMake and the Visual Studio Build Tools (C++ workload,
Windows SDK 10.0.20348 or newer):

```powershell
cmake -S native/process_loopback -B native/process_loopback/build -A x64
cmake --build native/process_loopback/build --config Release
```

Telsiz finds `native/process_loopback/build/Release/telsiz-loopback.exe` automatically.

## Protocol

```
telsiz-loopback --pid <PID>
telsiz-loopback --version
```

stdout: a 16-byte header (`"TLSZ"`, uint32 sample rate, uint16 channels, uint16 bits per
sample, uint32 reserved; little-endian), then interleaved signed 16-bit PCM. While the
application is silent the helper writes silence, so the stream stays in step with the
clock.

Exit codes: `0` the reader closed the pipe, `1` bad arguments, `3` process loopback is not
available on this Windows version, `4` capture failed after it started.
