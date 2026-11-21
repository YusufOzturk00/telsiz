// telsiz-loopback: capture the audio one process tree plays and write it to stdout.
//
// Based on Microsoft's ApplicationLoopback sample
// (https://github.com/microsoft/Windows-classic-samples, MIT License).
//
// The capture goes through the Windows audio engine only (process loopback, the same
// API OBS and Discord use). The target process is never opened, read, written or
// injected into: its process ID is just a filter for the audio engine.
//
// Usage:   telsiz-loopback --pid <PID>
//          telsiz-loopback --version
//
// Output (stdout, binary):
//   16-byte header: "TLSZ" | uint32 sample rate | uint16 channels | uint16 bits per sample
//                   | uint32 reserved (0), all little-endian
//   then interleaved signed 16-bit PCM frames, in step with the wall clock: while the
//   process is silent (the audio engine then delivers nothing), silence is written so
//   the reader always sees a continuous stream.
//
// Exit codes: 0 = the reader closed the pipe, 1 = bad arguments,
//             3 = process loopback is not available on this system,
//             4 = capture failed after it started.

#include <windows.h>

#include <audioclient.h>
#include <audioclientactivationparams.h>
#include <avrt.h>
#include <mmdeviceapi.h>
#include <propidl.h>
#include <wrl/client.h>
#include <wrl/implements.h>

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cwchar>
#include <vector>

using Microsoft::WRL::ComPtr;

namespace {

constexpr char kVersion[] = "telsiz-loopback 2";

constexpr int kExitOk = 0;
constexpr int kExitUsage = 1;
constexpr int kExitUnavailable = 3;
constexpr int kExitFailed = 4;

constexpr REFERENCE_TIME kBufferDuration = 2000000;  // 200 ms, in 100-ns units
constexpr DWORD kFillMs = 50;                        // silence block while nothing plays
constexpr DWORD kActivationTimeoutMs = 10000;
constexpr WORD kChannels = 2;
constexpr WORD kBitsPerSample = 16;
constexpr DWORD kSampleRates[] = {48000, 44100};

// Receives the result of ActivateAudioInterfaceAsync. FtmBase makes it agile, which
// the audio engine requires.
class ActivationHandler
    : public Microsoft::WRL::RuntimeClass<
          Microsoft::WRL::RuntimeClassFlags<Microsoft::WRL::ClassicCom>, Microsoft::WRL::FtmBase,
          IActivateAudioInterfaceCompletionHandler> {
   public:
    ActivationHandler() : done_(CreateEventW(nullptr, TRUE, FALSE, nullptr)) {}
    ~ActivationHandler() {
        if (done_ != nullptr) CloseHandle(done_);
    }

    STDMETHOD(ActivateCompleted)(IActivateAudioInterfaceAsyncOperation* operation) override {
        HRESULT activate_hr = E_FAIL;
        ComPtr<IUnknown> unknown;
        HRESULT hr = operation->GetActivateResult(&activate_hr, &unknown);
        if (SUCCEEDED(hr)) hr = activate_hr;
        if (SUCCEEDED(hr)) hr = unknown.As(&client_);
        result_ = hr;
        SetEvent(done_);
        return S_OK;
    }

    HRESULT Wait(ComPtr<IAudioClient>* client) {
        if (done_ == nullptr) return HRESULT_FROM_WIN32(GetLastError());
        if (WaitForSingleObject(done_, kActivationTimeoutMs) != WAIT_OBJECT_0) {
            return HRESULT_FROM_WIN32(ERROR_TIMEOUT);
        }
        if (SUCCEEDED(result_)) *client = client_;
        return result_;
    }

   private:
    HANDLE done_;
    HRESULT result_ = E_FAIL;
    ComPtr<IAudioClient> client_;
};

HRESULT ActivateProcessLoopback(DWORD pid, ComPtr<IAudioClient>* client) {
    AUDIOCLIENT_ACTIVATION_PARAMS params = {};
    params.ActivationType = AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK;
    params.ProcessLoopbackParams.TargetProcessId = pid;
    params.ProcessLoopbackParams.ProcessLoopbackMode =
        PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE;

    PROPVARIANT activation = {};
    activation.vt = VT_BLOB;
    activation.blob.cbSize = sizeof(params);
    activation.blob.pBlobData = reinterpret_cast<BYTE*>(&params);

    ComPtr<ActivationHandler> handler = Microsoft::WRL::Make<ActivationHandler>();
    if (!handler) return E_OUTOFMEMORY;
    ComPtr<IActivateAudioInterfaceAsyncOperation> operation;
    HRESULT hr = ActivateAudioInterfaceAsync(VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK,
                                             __uuidof(IAudioClient), &activation,
                                             handler.Get(), &operation);
    if (FAILED(hr)) return hr;
    return handler->Wait(client);
}

WAVEFORMATEX MakeFormat(DWORD sample_rate) {
    WAVEFORMATEX format = {};
    format.wFormatTag = WAVE_FORMAT_PCM;
    format.nChannels = kChannels;
    format.nSamplesPerSec = sample_rate;
    format.wBitsPerSample = kBitsPerSample;
    format.nBlockAlign = static_cast<WORD>(format.nChannels * format.wBitsPerSample / 8);
    format.nAvgBytesPerSec = format.nSamplesPerSec * format.nBlockAlign;
    return format;
}

bool WriteAll(HANDLE out, const void* data, size_t size) {
    const BYTE* cursor = static_cast<const BYTE*>(data);
    while (size > 0) {
        DWORD chunk = size > 0x10000000 ? 0x10000000 : static_cast<DWORD>(size);
        DWORD written = 0;
        if (!WriteFile(out, cursor, chunk, &written, nullptr) || written == 0) return false;
        cursor += written;
        size -= written;
    }
    return true;
}

class Writer {
   public:
    Writer(HANDLE out, WORD block_align, UINT32 fill_frames)
        : out_(out), block_align_(block_align), zeros_(size_t{fill_frames} * block_align, 0) {}

    bool Audio(const BYTE* data, UINT32 frames) {
        return WriteAll(out_, data, size_t{frames} * block_align_);
    }

    bool Silence(UINT32 frames) {
        size_t remaining = size_t{frames} * block_align_;
        while (remaining > 0) {
            size_t part = remaining < zeros_.size() ? remaining : zeros_.size();
            if (!WriteAll(out_, zeros_.data(), part)) return false;
            remaining -= part;
        }
        return true;
    }

   private:
    HANDLE out_;
    WORD block_align_;
    std::vector<BYTE> zeros_;
};

void PutLe32(BYTE* at, uint32_t value) {
    for (int i = 0; i < 4; ++i) at[i] = static_cast<BYTE>(value >> (8 * i));
}

void PutLe16(BYTE* at, uint16_t value) {
    at[0] = static_cast<BYTE>(value);
    at[1] = static_cast<BYTE>(value >> 8);
}

bool WriteHeader(HANDLE out, const WAVEFORMATEX& format) {
    BYTE header[16] = {'T', 'L', 'S', 'Z'};
    PutLe32(header + 4, format.nSamplesPerSec);
    PutLe16(header + 8, format.nChannels);
    PutLe16(header + 10, format.wBitsPerSample);
    PutLe32(header + 12, 0);
    return WriteAll(out, header, sizeof(header));
}

int Capture(DWORD pid) {
    ComPtr<IAudioClient> client;
    HRESULT hr = ActivateProcessLoopback(pid, &client);
    if (FAILED(hr)) {
        std::fprintf(stderr, "process loopback activation failed: 0x%08lx\n", static_cast<unsigned long>(hr));
        return kExitUnavailable;
    }

    WAVEFORMATEX format = {};
    hr = E_FAIL;
    for (DWORD rate : kSampleRates) {
        format = MakeFormat(rate);
        hr = client->Initialize(AUDCLNT_SHAREMODE_SHARED,
                                AUDCLNT_STREAMFLAGS_LOOPBACK | AUDCLNT_STREAMFLAGS_EVENTCALLBACK,
                                kBufferDuration, 0, &format, nullptr);
        if (SUCCEEDED(hr)) break;
    }
    if (FAILED(hr)) {
        std::fprintf(stderr, "process loopback initialization failed: 0x%08lx\n", static_cast<unsigned long>(hr));
        return kExitUnavailable;
    }

    HANDLE ready = CreateEventW(nullptr, FALSE, FALSE, nullptr);
    if (ready == nullptr) {
        std::fprintf(stderr, "CreateEvent failed: %lu\n", GetLastError());
        return kExitFailed;
    }
    ComPtr<IAudioCaptureClient> capture;
    hr = client->SetEventHandle(ready);
    if (SUCCEEDED(hr)) hr = client->GetService(IID_PPV_ARGS(&capture));
    if (SUCCEEDED(hr)) hr = client->Start();
    if (FAILED(hr)) {
        std::fprintf(stderr, "process loopback start failed: 0x%08lx\n", static_cast<unsigned long>(hr));
        CloseHandle(ready);
        return kExitUnavailable;
    }

    HANDLE out = GetStdHandle(STD_OUTPUT_HANDLE);
    const UINT32 fill_frames = format.nSamplesPerSec * kFillMs / 1000;
    Writer writer(out, format.nBlockAlign, fill_frames);
    int exit_code = kExitOk;
    if (!WriteHeader(out, format)) {
        client->Stop();
        CloseHandle(ready);
        return kExitOk;
    }

    LARGE_INTEGER frequency, started, now;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&started);
    uint64_t emitted = 0;  // frames written so far

    for (;;) {
        if (WaitForSingleObject(ready, kFillMs) == WAIT_FAILED) {
            std::fprintf(stderr, "wait failed: %lu\n", GetLastError());
            exit_code = kExitFailed;
            break;
        }

        bool reader_gone = false;
        UINT32 packet = 0;
        for (hr = capture->GetNextPacketSize(&packet); SUCCEEDED(hr) && packet > 0;
             hr = capture->GetNextPacketSize(&packet)) {
            BYTE* data = nullptr;
            UINT32 frames = 0;
            DWORD flags = 0;
            hr = capture->GetBuffer(&data, &frames, &flags, nullptr, nullptr);
            if (FAILED(hr)) break;
            bool ok = (flags & AUDCLNT_BUFFERFLAGS_SILENT) ? writer.Silence(frames)
                                                           : writer.Audio(data, frames);
            capture->ReleaseBuffer(frames);
            if (!ok) {
                reader_gone = true;
                break;
            }
            emitted += frames;
        }
        if (reader_gone) break;
        if (FAILED(hr)) {
            std::fprintf(stderr, "capture failed: 0x%08lx\n", static_cast<unsigned long>(hr));
            exit_code = kExitFailed;
            break;
        }

        // Nothing is playing: keep the stream in step with the clock.
        QueryPerformanceCounter(&now);
        const uint64_t due = static_cast<uint64_t>(now.QuadPart - started.QuadPart) *
                             format.nSamplesPerSec / static_cast<uint64_t>(frequency.QuadPart);
        while (due >= emitted + 2ull * fill_frames) {
            if (!writer.Silence(fill_frames)) {
                reader_gone = true;
                break;
            }
            emitted += fill_frames;
        }
        if (reader_gone) break;
    }

    client->Stop();
    CloseHandle(ready);
    return exit_code;
}

int Usage() {
    std::fprintf(stderr, "usage: telsiz-loopback --pid <PID>\n       telsiz-loopback --version\n");
    return kExitUsage;
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
    if (argc == 2 && std::wcscmp(argv[1], L"--version") == 0) {
        std::printf("%s\n", kVersion);
        return kExitOk;
    }
    if (argc != 3 || std::wcscmp(argv[1], L"--pid") != 0) return Usage();

    wchar_t* end = nullptr;
    errno = 0;
    const unsigned long pid = std::wcstoul(argv[2], &end, 10);
    if (end == argv[2] || *end != L'\0' || errno == ERANGE || pid == 0) return Usage();

    // Register the capture thread with the Multimedia Class Scheduler ("Audio"), as audio
    // apps do: it only copies a few kilobytes per buffer, but if a busy game delays it, the
    // audio engine's buffer overflows and speech is lost. Failure is not fatal.
    DWORD mmcss_task = 0;
    HANDLE mmcss = AvSetMmThreadCharacteristicsW(L"Audio", &mmcss_task);

    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (FAILED(hr)) {
        std::fprintf(stderr, "CoInitializeEx failed: 0x%08lx\n", static_cast<unsigned long>(hr));
        if (mmcss != nullptr) AvRevertMmThreadCharacteristics(mmcss);
        return kExitFailed;
    }
    const int code = Capture(static_cast<DWORD>(pid));
    CoUninitialize();
    if (mmcss != nullptr) AvRevertMmThreadCharacteristics(mmcss);
    return code;
}
