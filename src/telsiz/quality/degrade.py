"""Make clean recordings sound like in-game voice chat, to test robustness."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, sosfiltfilt


@dataclass(frozen=True)
class VoiceChatProfile:
    band: tuple[float, float] | None = (300.0, 3400.0)  # codec / headset bandwidth
    snr_db: float | None = 15.0  # background noise (gunfire, footsteps, fans)
    drive: float = 2.0  # soft clipping from a hot microphone; 0 disables it
    packet_loss: float = 0.02  # fraction of 20 ms frames lost on the network
    sample_rate: int = 16_000


def simulate_voice_chat(audio: np.ndarray, profile: VoiceChatProfile, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = np.asarray(audio, dtype=np.float64).copy()

    if profile.drive > 0:
        x = np.tanh(profile.drive * x) / np.tanh(profile.drive)

    if profile.snr_db is not None:
        power = np.mean(x**2)
        if power > 0:
            noise_power = power / 10 ** (profile.snr_db / 10)
            x = x + rng.standard_normal(len(x)) * np.sqrt(noise_power)

    if profile.band is not None:
        sos = butter(6, profile.band, btype="bandpass", fs=profile.sample_rate, output="sos")
        x = sosfiltfilt(sos, x)

    if profile.packet_loss > 0:
        frame = profile.sample_rate // 50
        n_frames = len(x) // frame
        lost = np.flatnonzero(rng.random(n_frames) < profile.packet_loss)
        for index in lost:
            x[index * frame : (index + 1) * frame] = 0.0

    return np.clip(x, -1.0, 1.0).astype(np.float32)
