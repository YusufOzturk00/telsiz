"""Tests for WASAPI system-loopback capture (with a fake PyAudioWPatch)."""

import numpy as np
import pytest

from telsiz.audio.system_loopback import SystemLoopbackSource

RATE = 48000
FRAMES = 4800  # 0.1 s


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeStream:
    """Delivers scripted blocks; ``None`` means nothing is playing for one poll."""

    def __init__(self, script, clock, source_ref):
        self.script = list(script)
        self.clock = clock
        self.source_ref = source_ref
        self.closed = False

    def get_read_available(self):
        if not self.script:
            self.source_ref[0].stop()  # end the test once the script is used up
            return 0
        if self.script[0] is None:
            self.script.pop(0)
            return 0
        return FRAMES

    def read(self, frames, exception_on_overflow=True):
        block = self.script.pop(0)
        self.clock.now += frames / RATE
        return block.astype(np.float32).tobytes()

    def stop_stream(self):
        pass

    def close(self):
        self.closed = True


class FakePyAudio:
    paFloat32 = 1
    paWASAPI = 13

    def __init__(self, script, clock, source_ref, device=True):
        self.script, self.clock, self.source_ref, self.device = script, clock, source_ref, device
        self.opened = None
        self.stream = None
        self.terminated = False

    # module-level constructor
    def PyAudio(self):  # noqa: N802 (mirrors the PyAudio API)
        return self

    def get_default_wasapi_loopback(self):
        if not self.device:
            raise OSError("no loopback")
        return {
            "index": 20,
            "name": "Speakers [Loopback]",
            "defaultSampleRate": 48000.0,
            "maxInputChannels": 2,
        }

    def open(self, **kwargs):
        self.opened = kwargs
        self.stream = FakeStream(self.script, self.clock, self.source_ref)
        return self.stream

    def terminate(self):
        self.terminated = True


def make(script, device=True):
    clock = FakeClock()
    ref = [None]
    fake = FakePyAudio(script, clock, ref, device=device)
    source = SystemLoopbackSource(
        chunk_seconds=0.1, pyaudio_module=fake, clock=clock, sleep=clock.sleep
    )
    ref[0] = source
    return source, fake


def stereo(value):
    return np.full((FRAMES, 2), value, dtype=np.float32)


def test_reads_float_chunks_from_the_default_loopback_device():
    source, fake = make([stereo(0.25), stereo(-0.5)])

    chunks = list(source.chunks())

    assert fake.opened["input_device_index"] == 20
    assert fake.opened["rate"] == 48000
    assert fake.opened["channels"] == 2
    assert fake.opened["input"] is True
    assert chunks[0].sample_rate == 48000
    assert chunks[0].samples.shape == (FRAMES, 2)
    assert chunks[0].samples.dtype == np.float32
    np.testing.assert_allclose(chunks[1].samples, -0.5)
    assert source.device_name == "Speakers [Loopback]"


def test_silence_is_generated_while_nothing_is_playing():
    # 0.1 s of sound, then the stream goes quiet for many polls.
    source, _ = make([stereo(0.25)] + [None] * 40)

    chunks = list(source.chunks())

    silent = [c for c in chunks[1:]]
    assert silent, "expected silence chunks while the device sent nothing"
    assert all(np.all(c.samples == 0) for c in silent)
    total = sum(len(c.samples) for c in chunks) / RATE
    assert total == pytest.approx(source.elapsed_seconds, abs=0.21)  # lags at most 2 chunks


def test_stop_closes_the_stream_and_audio_system():
    source, fake = make([stereo(0.1)])

    list(source.chunks())

    assert fake.stream.closed
    assert fake.terminated


def test_missing_loopback_device_gives_a_clear_error():
    source, fake = make([], device=False)

    with pytest.raises(RuntimeError, match="loopback"):
        list(source.chunks())
    assert fake.terminated
