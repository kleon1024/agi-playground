"""Measure the LSH duplicate-threshold S-curve that the release-policy
chapter tabulates analytically.

The chapter's table is computed from the band and row counts. This run
measures the same curve empirically: random shingle-set pairs at declared
Jaccard levels, MinHash signatures (64 permutations), and the fraction of
pairs where any band matches, against the analytic formula
1 - (1 - J^4)^16 for 16 bands of 4 rows, and the shifted curve for 32
bands of 4 rows. The threshold move is the release decision the chapter
names: change the band count and you have moved the duplicate threshold
whether or not you meant to.

Deterministic (single seed), stdlib only, CPU-only.
"""

from __future__ import annotations

import random


def shingle_set(rng: random.Random, size: int, lo: int, hi: int) -> set[tuple[int, int]]:
    """A set of `size` distinct shingles drawn from [lo, hi)."""
    return {(rng.randrange(lo, hi), i) for i in range(size)}


def pair_at_jaccard(rng: random.Random, m: int, j: float) -> tuple[set, set]:
    """Two shingle sets of size m whose Jaccard is as close to j as the
    integer intersection allows. J = |A&B| / |A|B| = j/(2m-j) with
    |A&B| = j."""
    inter = round(2 * m * j / (1 + j))
    base = shingle_set(rng, inter, 0, 1_000_000)
    extra_a = shingle_set(rng, m - inter, 1_000_000, 2_000_000)
    extra_b = shingle_set(rng, m - inter, 2_000_000, 3_000_000)
    return base | extra_a, base | extra_b


def minhash_bands(sh: set, perms: list[list[int]], bands: int) -> list[list[int]]:
    sig: list[int] = []
    for perm in perms:
        m = None
        for s in sh:
            h = (s[0] * perm[s[1] % len(perm)] + perm[s[0] % len(perm)]) & 0xFFFFFFFF
            if m is None or h < m:
                m = h
        sig.append(m if m is not None else 0)
    rows = len(perms) // bands
    return [sig[b * rows : (b + 1) * rows] for b in range(bands)]


def any_band_matches(a: list[list[int]], b: list[list[int]]) -> bool:
    return any(x == y for x, y in zip(a, b))


def measure(seed: int = 42, trials: int = 600, m: int = 48) -> None:
    rng = random.Random(seed)
    perms16 = [
        [random.Random(seed + p).randrange(1, 1 << 31) for _ in range(8)]
        for p in range(64)
    ]
    perms32 = [
        [random.Random(seed + 1000 + p).randrange(1, 1 << 31) for _ in range(8)]
        for p in range(128)
    ]

    levels = (0.1, 0.3, 0.5, 0.7, 0.9)
    print("release policy, measured (LSH duplicate-threshold S-curve):")
    print(f"  trials {trials} per Jaccard level, shingle-set size {m}, "
          f"64-permutation signatures")
    print(f"  {'J':>5}  {'16x4 measured':>13} {'16x4 formula':>12} "
          f"{'32x4 measured':>13} {'32x4 formula':>12}")
    for j in levels:
        hit16 = 0
        hit32 = 0
        for _ in range(trials):
            a, b = pair_at_jaccard(rng, m, j)
            sa, sb = minhash_bands(a, perms16, 16), minhash_bands(b, perms16, 16)
            if any_band_matches(sa, sb):
                hit16 += 1
            sa32, sb32 = minhash_bands(a, perms32, 32), minhash_bands(b, perms32, 32)
            if any_band_matches(sa32, sb32):
                hit32 += 1
        f16 = 1 - (1 - j**4) ** 16
        f32 = 1 - (1 - j**4) ** 32
        print(f"  {j:>5.1f}  {hit16/trials:>13.3f} {f16:>12.3f} "
              f"{hit32/trials:>13.3f} {f32:>12.3f}")

    # The threshold move: half-way points (1/bands)^(1/rows).
    half16 = (1 / 16) ** 0.25
    half32 = (1 / 32) ** 0.25
    print()
    print(f"  implied threshold: 16 bands of 4 rows -> {half16:.2f}; "
          f"32 bands of 4 rows -> {half32:.2f}")


if __name__ == "__main__":
    measure()
