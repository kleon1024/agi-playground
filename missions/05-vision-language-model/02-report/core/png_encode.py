"""Encode a raw RGB pixel grid as a real PNG file, stdlib only.

Stages 00-01 never needed an actual image file -- the tokenizer and training
loop consume raw pixel tensors directly. This stage is the first one that
hands an image to something outside this repository (a hosted API), and
almost no vision API accepts a raw pixel array or the PPM format stage 00
already writes to disk. PNG is the lowest-friction real format: one required
compressed chunk, deflate via the stdlib `zlib` module, no external
dependency.

Encodes the minimum valid PNG: IHDR (8-bit RGB, no interlace), one IDAT chunk
holding a zlib stream of one "filter type 0" (no filter) byte plus the raw
row bytes for every scanline, and IEND. Correct but not optimized -- there is
no filter search or palette; a 32x32 fixture image does not need one.
"""

from __future__ import annotations

import struct
import zlib


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def encode_png(pixels: list[tuple[int, int, int]], width: int, height: int) -> bytes:
    """`pixels` is row-major, length `width * height`, each entry an (r, g, b) triple
    of 0-255 ints -- the exact shape `generate_dataset.py`'s `render()` produces."""
    assert len(pixels) == width * height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # color type 2 = RGB
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (none) for this scanline
        row = pixels[y * width : (y + 1) * width]
        for r, g, b in row:
            raw.extend((r, g, b))
    idat = zlib.compress(bytes(raw), level=9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )
