"""Tests for audio sources and resampling."""

import numpy as np
import pytest

from helpers import sine, write_wav
from telsiz.audio.base import AudioChunk
from telsiz.audio.file_source import FileSource
from telsiz.audio.resample import Resampler, to_mono


def _read_all(source: FileSource) -> tuple[np.ndarray, int]:
    chunks = list(source.chunks())
    rates = {c.sample_rate for c in chunks}
    assert len(rates) == 1
    return np.concatenate([c.samples for c in chunks]), rates.pop()


@pytest.mark.parametrize("sampwidth", [1, 2, 3, 4])
def test_file_source_reads_pcm_wav_as_float32(tmp_path, sampwidth):
    original = sine(440, 0.5, 16000)
    path = write_wav(tmp_path / "a.wav", original, 16000, sampwidth=sampwidth)

    samples, rate = _read_all(FileSource(path))

    assert rate == 16000
    assert samples.dtype == np.float32
    assert samples.shape == (8000, 1)
    tolerance = 0.02 if sampwidth == 1 else 1e-3
    np.testing.assert_allclose(samples[:, 0], original, atol=tolerance)


def test_file_source_keeps_channels(tmp_path):
    stereo = np.stack([sine(440, 0.2, 48000), sine(880, 0.2, 48000)], axis=1)
    path = write_wav(tmp_path / "s.wav", stereo, 48000)

    samples, rate = _read_all(FileSource(path))

    assert rate == 48000
    assert samples.shape == (9600, 2)


def test_file_source_splits_into_chunks_of_requested_length(tmp_path):
    path = write_wav(tmp_path / "a.wav", sine(440, 1.25, 16000), 16000)

    chunks = list(FileSource(path, chunk_seconds=0.5).chunks())

    assert [len(c.samples) for c in chunks] == [8000, 8000, 4000]


def test_file_source_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(FileSource(tmp_path / "nope.wav").chunks())


def test_to_mono_averages_channels():
    chunk = AudioChunk(np.array([[1.0, 0.0], [0.5, 0.5]], dtype=np.float32), 16000)

    np.testing.assert_allclose(to_mono(chunk), [0.5, 0.5])


def test_to_mono_accepts_1d_samples():
    chunk = AudioChunk(np.array([0.1, 0.2], dtype=np.float32), 16000)

    np.testing.assert_allclose(to_mono(chunk), [0.1, 0.2])


def _dominant_frequency(x: np.ndarray, rate: int) -> float:
    spectrum = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    return float(np.fft.rfftfreq(len(x), 1 / rate)[np.argmax(spectrum)])


@pytest.mark.parametrize("in_rate", [8000, 16000, 22050, 44100, 48000])
def test_resampler_converts_to_16k_and_keeps_pitch(in_rate):
    out = Resampler(in_rate).process(sine(440, 1.0, in_rate))

    assert out.dtype == np.float32
    assert abs(len(out) - 16000) <= 2
    assert abs(_dominant_frequency(out, 16000) - 440) < 3


def test_resampler_chunked_output_matches_single_call():
    signal = sine(300, 2.0, 44100) + sine(1700, 2.0, 44100, amplitude=0.2)
    whole = Resampler(44100).process(signal)

    resampler = Resampler(44100)
    pieces = [resampler.process(part) for part in np.array_split(signal, 37)]
    chunked = np.concatenate(pieces)

    assert len(chunked) == len(whole)
    np.testing.assert_allclose(chunked, whole, atol=1e-5)


def test_resampler_removes_frequencies_above_new_nyquist():
    # A 12 kHz tone cannot exist at 16 kHz; without filtering it would alias to 4 kHz.
    out = Resampler(48000).process(sine(12000, 1.0, 48000))

    assert np.sqrt(np.mean(out[200:] ** 2)) < 0.01
