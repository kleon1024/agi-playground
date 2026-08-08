"""Does stage 03's codec/LM result hold when speaker diversity increases from
stage 03's narrow baseline to 10?

Reuses every low-level building block from
[`03-real-speech-and-network/core/speech_data.py`](../../03-real-speech-and-network/core/speech_data.py)
unchanged (the LibriSpeech download/cache, FLAC->WAV decode via `ffmpeg`, and
per-clip chunking/normalization) -- the only new logic here is *balanced*
per-speaker extraction. Stage 03's own `build_dataset` extracts all requested
speakers' utterances into one speaker-major list and only then takes the
first `max_utterances`, which silently biases toward whichever speaker's
directory sorts first (a mix audit shows the bias already bites at the
2-speaker request stage 03 made). That bias is exactly wrong for a mission
whose entire point is speaker diversity,
so this stage extracts a bounded number of utterances *per speaker* before
combining and shuffling, guaranteeing every requested speaker actually
contributes clips to both the train and eval split.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

STAGE03_DIR = Path(__file__).resolve().parents[2] / "03-real-speech-and-network" / "core"
sys.path.insert(0, str(STAGE03_DIR))
import speech_data as sd

SAMPLE_RATE = sd.SAMPLE_RATE
CLIP_LEN = sd.CLIP_LEN
SpeechClip = sd.SpeechClip

# 10 dev-clean speakers with at least 80 archive entries each (well above
# per_speaker_utterances below), chosen for volume, not curated for any
# acoustic property. Includes stage 03's own 2035/2277 (dropping to a single
# stage-03 speaker was deliberately avoided to keep the comparison honest:
# this is 8 *additional* speakers on top of, not instead of, stage 03's two).
TEN_SPEAKERS = (
    "2277", "1462", "2035", "3752", "6313", "3081", "2428", "5694", "5895", "7976",
)


def build_balanced_dataset(
    n_train: int,
    n_eval: int,
    seed: int,
    speakers: tuple[str, ...] = TEN_SPEAKERS,
    per_speaker_utterances: int = 10,
) -> tuple[list, list]:
    """Balanced version of `speech_data.build_dataset`: bounds utterances
    *per speaker* before combining, so a 10-speaker request cannot silently
    collapse into "mostly speaker 1's data". Returns (train_clips, eval_clips)
    in `speech_data.SpeechClip` shape -- every downstream consumer (`Codec`,
    `audio_lm`) needs zero changes."""
    sd._download_archive()

    all_clips: list = []
    per_speaker_counts: dict[str, int] = {}
    for spk in speakers:
        flac_files = sd._extract_speakers((spk,))[:per_speaker_utterances]
        speaker_clips: list = []
        for flac_path in flac_files:
            wav_path = sd._decode_flac_to_wav(flac_path)
            waveform = sd._load_wav_as_tensor(wav_path)
            speaker_clips.extend(sd._chunk(waveform, speaker_id=spk, utterance_id=flac_path.stem))
        per_speaker_counts[spk] = len(speaker_clips)
        all_clips.extend(speaker_clips)

    generator = torch.Generator().manual_seed(seed)
    perm = torch.randperm(len(all_clips), generator=generator).tolist()
    shuffled = [all_clips[i] for i in perm]

    total_needed = n_train + n_eval
    if len(shuffled) < total_needed:
        raise RuntimeError(
            f"only {len(shuffled)} balanced clips available across {speakers} "
            f"(per-speaker counts: {per_speaker_counts}); need {total_needed}. "
            "Raise per_speaker_utterances or add a speaker."
        )
    train, eval_ = shuffled[:n_train], shuffled[n_train : n_train + n_eval]
    eval_speakers = sorted({c.speaker_id for c in eval_})
    if len(eval_speakers) < len(speakers):
        raise RuntimeError(
            f"eval split only covers speakers {eval_speakers}, missing "
            f"{set(speakers) - set(eval_speakers)} -- raise n_eval or "
            "per_speaker_utterances so every requested speaker is actually tested."
        )
    return train, eval_
