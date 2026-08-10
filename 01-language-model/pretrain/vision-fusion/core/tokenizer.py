"""A minimal word-level tokenizer scoped to this stage's tiny, closed
vocabulary (colors, shapes, question words, digits).

Mission 01's BPE tokenizer (`01-tokenizer/`) was trained on general web text
and is the wrong tool here -- its merge table spends capacity discovering
subword structure that does not exist in a vocabulary this small and this
closed. A whitespace/regex word tokenizer is the right-sized instrument for a
few dozen fixed words, the same "match the tool to the task" judgment this
repository already applies elsewhere.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PAD, SEP, EOS = "<pad>", "<sep>", "<eos>"
SPECIALS = [PAD, SEP, EOS]

_TOKEN_RE = re.compile(r"[a-z]+|[0-9]+|\?")


def word_tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class Tokenizer:
    def __init__(self, vocab: list[str]):
        self.vocab = vocab
        self.stoi = {w: i for i, w in enumerate(vocab)}
        self.pad_id = self.stoi[PAD]
        self.sep_id = self.stoi[SEP]
        self.eos_id = self.stoi[EOS]

    @classmethod
    def build(cls, texts: list[str]) -> Tokenizer:
        words: set[str] = set()
        for t in texts:
            words.update(word_tokenize(t))
        vocab = list(SPECIALS) + sorted(words)
        return cls(vocab)

    def encode(self, text: str) -> list[int]:
        return [self.stoi[w] for w in word_tokenize(text)]

    def decode(self, ids: list[int]) -> str:
        words = [self.vocab[i] for i in ids if i != self.pad_id]
        return " ".join(w for w in words if w not in (SEP, EOS))

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.vocab, indent=2))

    @classmethod
    def load(cls, path: Path) -> Tokenizer:
        return cls(json.loads(path.read_text()))

    def __len__(self) -> int:
        return len(self.vocab)
