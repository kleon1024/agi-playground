"""A synthetic waveform source this mission can generate, encode, and check
provenance on trivially -- the audio analogue of mission 05 stage 00's
synthetic shapes-and-captions image set. Real speech would need a dataset
license and a much larger codec to matter; a small set of procedurally
generated tone sequences is enough to test whether a codec can turn a
waveform into a useful discrete-token sequence at all, which is this
mission's actual question.

Each clip is 1-3 "notes" played back to back, each note a sine tone at one
of a small fixed set of frequencies with a linear attack/decay envelope (to
avoid the click a hard on/off would leave) plus a little noise. This gives
every clip real, non-trivial structure -- a short, checkable "which notes
played, in what order" identity -- without needing any external dataset.
"""

from __future__ import annotations

import math
import random
import wave
from dataclasses import dataclass
from pathlib import Path

import torch

SAMPLE_RATE = 8000
CLIP_LEN = 4096  # 0.512s at 8kHz -- long enough for 1-3 notes, short enough to train fast on CPU
NOTE_FREQS = [220.0, 277.0, 330.0, 392.0, 440.0, 523.0]  # a small fixed "vocabulary" of tones
NOISE_AMPLITUDE = 0.02


@dataclass
class Clip:
    waveform: torch.Tensor  # (CLIP_LEN,), float32 in [-1, 1]
    notes: list[float]


def _envelope(n: int) -> torch.Tensor:
    ramp = max(1, n // 8)
    env = torch.ones(n)
    env[:ramp] = torch.linspace(0.0, 1.0, ramp)
    env[-ramp:] = torch.linspace(1.0, 0.0, ramp)
    return env


def _render_note(freq: float, n: int, rng: random.Random) -> torch.Tensor:
    t = torch.arange(n, dtype=torch.float32) / SAMPLE_RATE
    tone = torch.sin(2 * math.pi * freq * t)
    noise = torch.tensor([rng.uniform(-1, 1) for _ in range(n)]) * NOISE_AMPLITUDE
    return (tone + noise) * _envelope(n)


def sample_clip(rng: random.Random) -> Clip:
    num_notes = rng.randint(1, 3)
    notes = [rng.choice(NOTE_FREQS) for _ in range(num_notes)]
    note_len = CLIP_LEN // num_notes
    pieces = []
    remaining = CLIP_LEN
    for i, freq in enumerate(notes):
        n = note_len if i < num_notes - 1 else remaining
        pieces.append(_render_note(freq, n, rng))
        remaining -= n
    waveform = torch.cat(pieces)
    waveform = waveform / (waveform.abs().max() + 1e-6) * 0.9
    return Clip(waveform=waveform, notes=notes)


def build_dataset(n_train: int, n_eval: int, seed: int) -> tuple[list[Clip], list[Clip]]:
    rng = random.Random(seed)
    train = [sample_clip(rng) for _ in range(n_train)]
    eval_ = [sample_clip(rng) for _ in range(n_eval)]
    return train, eval_


def write_wav(path: Path, waveform: torch.Tensor) -> None:
    """16-bit PCM mono WAV via the stdlib `wave` module -- no soundfile/scipy
    dependency, the same "write the real file format from scratch with
    stdlib only" choice mission 05's `png_encode.py` made."""
    samples = (waveform.clamp(-1, 1) * 32767).to(torch.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(samples.numpy().tobytes())
