# Real speech codec retrain, KV-cache reuse check, and a real Tailscale round trip

## Commands

```bash
cd missions/07-realtime-voice/03-real-speech-and-network/core
uv run --group torch python train_real_speech.py --codec-steps 2000 --lm-steps 800 --seed 0
uv run --group torch python train_real_speech.py --codec-steps 2000 --lm-steps 800 --seed 1
uv run --group torch python train_real_speech.py --codec-steps 2000 --lm-steps 800 --seed 2

# on the remote host (~/latency_probe/, outside its git checkout):
python3 network_latency.py --role server --port 8765
# from this machine:
python3 network_latency.py --role client --host 100.74.20.55 --port 8765 --n-pings 200 --payload-tokens 8
```

Apple silicon laptop, macOS, CPU only (no CUDA GPU available in this
sandbox, same deviation from `mission.yaml`'s local-GPU-lane framing stage
01 already recorded). Per-seed wall-clock: data build under 1s (cached
after first download), codec training 620-630s, LM training 70-90s. Real
network measurement: <1s of actual pinging (200 round trips at ~10-40ms
each), plus one-time SSH setup. LibriSpeech `dev-clean` download (338MB,
one-time, $0, CC BY 4.0) cached under a git-ignored `core/.cache/`.

## Codec: collapses at 600 steps on real speech, escapes at 2000 -- same learning rate

Diagnostic sweep (2000 steps each, held-out eval):

```
lr=1e-3 (unchanged): escapes by step ~1400-1800, eval MSE 0.01306, 58/64 codes used
lr=3e-3 (higher):    never escapes, eval MSE 0.02722 (tied with silence), 3/64 codes used
```

Production runs at the corrected `--codec-steps 2000`, three seeds:

| seed | eval MSE | silence baseline | mean-signal baseline | codes used | entropy ratio |
|---|---|---|---|---|---|
| 0 | 0.013062 | 0.027220 | 0.027333 | 58/64 | 0.836 |
| 1 | 0.013690 | 0.028275 | 0.028396 | 51/64 | 0.787 |
| 2 | 0.013086 | 0.027664 | 0.027769 | 63/64 | 0.870 |

All three seeds beat both required naive baselines by roughly 2x, with
healthy (non-collapsed) codebook usage. Full per-step `codec_history` in
`real-speech-seed{0,1,2}.json`. Reference/reconstructed audio for three
held-out clips: `example_clips/` (from the most recently run seed).

## KV-cache correctness: holds on the real-speech token vocabulary

| seed | max logit gap | mean logit gap | token sequences matched |
|---|---|---|---|
| 0 | 2.84e-05 | 1.40e-05 | 60/60 |
| 1 | 2.34e-05 | 1.14e-05 | 60/60 |
| 2 | 3.10e-05 | 1.24e-05 | 60/60 |

Same order of magnitude as stage 01's text-vocabulary result (1.19e-05) and
this repository's established tolerance (`TOL=2e-5` in
`tests/test_decode_correctness.py`).

## Real network round trip: Mac client -> Tailscale (DERP-relayed) -> WSL2/RTX-4090 host

```
200 round trips, 8 int64 token ids each way (64 bytes):
  p50:  9.66ms
  p95:  42.46ms
  mean: 15.11ms
  min:  6.07ms   max: 85.25ms
```

Independently verified live before this measurement: `tailscale ping`
returned real round trips via DERP relay (no direct connection
established); non-interactive SSH confirmed the remote RTX 4090 reachable
and CUDA-visible. The echo-server script was copied to a separate directory
on the remote host (`~/latency_probe/`, outside its git checkout) and run
standalone with bare `python3` -- the remote host's actual project
checkout, including one real uncommitted local change there, was never
touched, synced, or reset. The server process exited on its own once the
client disconnected; nothing was left running on the remote host after the
measurement.

Full JSON: `network_latency.json`.
