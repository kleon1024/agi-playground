"""A character-level SMILES vocabulary: one token per character, built from
the training split only, with an explicit UNK for any character stage 01's
test set contains that training never did.

SMILES's own alphabet is small (atoms, bond symbols, ring-closure digits,
brackets) -- character-level tokenization needs no subword algorithm to reach
full coverage, unlike free-text language, which is the entire reason mission
01's tokenizer stage exists as its own chapter. This is why that stage is not
reused here: the tokenization *problem* SMILES poses is not the one that
stage solves.
"""

from __future__ import annotations

import csv
from pathlib import Path

PAD, UNK = 0, 1


class SmilesVocab:
    def __init__(self, chars: list[str]):
        self.itos = ["<pad>", "<unk>"] + chars
        self.stoi = {c: i for i, c in enumerate(self.itos)}

    @property
    def size(self) -> int:
        return len(self.itos)

    def encode(self, smiles: str, max_len: int) -> tuple[list[int], int]:
        ids = [self.stoi.get(ch, UNK) for ch in smiles[:max_len]]
        real_len = len(ids)
        ids = ids + [PAD] * (max_len - real_len)
        return ids, real_len


def build_vocab(train_csv: Path) -> SmilesVocab:
    chars: set[str] = set()
    with Path(train_csv).open() as f:
        for row in csv.DictReader(f):
            chars.update(row["smiles"])
    return SmilesVocab(sorted(chars))


def load_split(csv_path: Path, vocab: SmilesVocab, max_len: int):
    ids_list, len_list, labels, n_truncated = [], [], [], 0
    with Path(csv_path).open() as f:
        for row in csv.DictReader(f):
            if len(row["smiles"]) > max_len:
                n_truncated += 1
            ids, real_len = vocab.encode(row["smiles"], max_len)
            ids_list.append(ids)
            len_list.append(real_len)
            labels.append(int(row["label"]))
    return ids_list, len_list, labels, n_truncated
