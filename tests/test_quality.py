"""Tests for evaluation helpers: WER, chrF and the voice-chat degradation."""

import numpy as np
import pytest

from helpers import sine
from telsiz.quality.degrade import VoiceChatProfile, simulate_voice_chat
from telsiz.quality.metrics import chrf, corpus_chrf, word_error_rate

# --- WER -------------------------------------------------------------------------


def test_wer_is_zero_for_identical_text_ignoring_case_and_punctuation():
    assert word_error_rate("They're rushing B!", "they're rushing b") == 0.0


def test_wer_counts_substitutions_insertions_and_deletions():
    # ref: 4 words; hyp: one substitution (two->three), one deletion (of)
    assert word_error_rate("two of them mid", "three them mid") == pytest.approx(2 / 4)


def test_wer_of_empty_hypothesis_is_one():
    assert word_error_rate("rush b", "") == 1.0


def test_wer_requires_a_reference():
    with pytest.raises(ValueError):
        word_error_rate("", "something")


def test_wer_english_treats_spelled_and_written_numbers_alike():
    assert word_error_rate("And sixty cents of it", "And 60 cents of it", language="en") == 0.0


def test_wer_english_understands_dollar_amounts():
    wer = word_error_rate("One dollar and eighty-seven cents.", "$1.87", language="en")

    assert wer == pytest.approx(1 / 5)  # only the "and" is missing


def test_wer_without_language_compares_words_literally():
    assert word_error_rate("sixty cents", "60 cents") == pytest.approx(1 / 2)


# --- chrF ------------------------------------------------------------------------


def test_chrf_identical_is_100():
    assert chrf("B'ye geliyorlar", "B'ye geliyorlar") == pytest.approx(100.0)


def test_chrf_unrelated_is_0():
    assert chrf("xyz", "abc") == pytest.approx(0.0)


def test_chrf_partial_overlap_is_between():
    score = chrf("B'ye geliyorlar, beş kişiler", "B'ye geliyorlar")
    assert 0.0 < score < 100.0


def test_chrf_rewards_closer_translations():
    reference = "Biri A long'da, elinde AWP var."
    close = chrf("Biri A long'da, AWP var.", reference)
    far = chrf("Bir tane uzun A, o AWP sahip.", reference)
    assert close > far


def test_corpus_chrf_pools_statistics():
    pairs = [("aaaa", "aaaa"), ("bbbb", "cccc")]
    assert 0.0 < corpus_chrf(pairs) < 100.0


# --- voice chat simulation -------------------------------------------------------------


def _band_energy(x, lo, hi, rate=16000):
    spectrum = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(len(x), 1 / rate)
    return spectrum[(freqs >= lo) & (freqs < hi)].sum()


def test_degradation_keeps_length_and_dtype():
    audio = sine(440, 2.0, 16000, amplitude=0.3)

    out = simulate_voice_chat(audio, VoiceChatProfile(), seed=1)

    assert out.shape == audio.shape
    assert out.dtype == np.float32
    assert np.max(np.abs(out)) <= 1.0


def test_degradation_is_deterministic_for_a_seed():
    audio = sine(440, 1.0, 16000, amplitude=0.3)
    profile = VoiceChatProfile()

    np.testing.assert_array_equal(
        simulate_voice_chat(audio, profile, seed=3), simulate_voice_chat(audio, profile, seed=3)
    )


def test_band_limit_removes_high_frequencies():
    audio = sine(500, 1.0, 16000, 0.2) + sine(6000, 1.0, 16000, 0.2)
    profile = VoiceChatProfile(snr_db=None, drive=0.0, packet_loss=0.0)

    out = simulate_voice_chat(audio, profile, seed=0)

    assert _band_energy(out, 5500, 6500) < 0.01 * _band_energy(audio, 5500, 6500)
    assert _band_energy(out, 400, 600) > 0.5 * _band_energy(audio, 400, 600)


def test_noise_is_added_at_requested_snr():
    audio = sine(500, 2.0, 16000, 0.3)
    profile = VoiceChatProfile(band=None, snr_db=10.0, drive=0.0, packet_loss=0.0)

    out = simulate_voice_chat(audio, profile, seed=0)

    noise = out - audio
    snr = 10 * np.log10(np.mean(audio**2) / np.mean(noise**2))
    assert snr == pytest.approx(10.0, abs=0.5)


def test_packet_loss_drops_whole_frames():
    audio = np.full(16000 * 4, 0.1, dtype=np.float32)
    profile = VoiceChatProfile(band=None, snr_db=None, drive=0.0, packet_loss=0.1)

    out = simulate_voice_chat(audio, profile, seed=0)

    frames = out.reshape(-1, 320)  # 20 ms frames
    dropped = np.all(frames == 0.0, axis=1).mean()
    assert dropped == pytest.approx(0.1, abs=0.05)
