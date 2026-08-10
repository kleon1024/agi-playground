"""Benchmark contamination: detection methods vs a leaked eval set, and
the answer-inflation a leak causes.

The scenario mirrors production: a "benchmark" of question-answer items
is collated, and a slice of those items ends up inside the training
corpus -- scraped from a site that published them, drawn from the same
crawl the eval set sampled, or pasted into a dataset by mistake. The
checks are the ones real pipelines run before release:

  - exact hash: the same normalized text appears in both sets (cheap,
    catches only verbatim copies);
  - 13-gram overlap: any 13-token sequence shared with a benchmark item
    flags the document (the GPT-3 heuristic, Brown et al. 2020);
  - MinHash near-duplicate: shingle signatures plus LSH banding with a
    verified Jaccard threshold (the dedup family from Lee et al. 2022),
    read at two thresholds to show the recall dial.

The leak is injected at three edit levels: verbatim copies, near copies
(high token overlap, what dedup is built for), and paraphrases (the same
fact with a mostly different token stream). The inflation read then asks
how many benchmark answers a model could learn from the corpus at all --
the memorization measure of Carlini et al. 2021: an answer is recoverable
when the corpus contains the subject and its property in one document.

Deterministic (single seed), stdlib only, CPU-only.
"""

from __future__ import annotations

import hashlib
import random
from collections import Counter

SUBJECTS = [
    "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf",
    "hotel", "india", "juliet", "kilo", "lima", "mike", "november",
    "oscar", "papa", "quebec", "romeo", "sierra", "tango",
]
PROPERTIES = [
    "amber", "cobalt", "crimson", "emerald", "ivory", "lavender",
    "maroon", "ochre", "pearl", "scarlet", "teal", "violet",
]
FILLER = [
    "common", "people", "ask", "known", "color", "usually", "seems",
    "popular", "telling", "quite", "often", "observed", "describe",
]


def benchmark_item(seed: int, i: int) -> tuple[str, str, str, str]:
    """One benchmark item: subject, property, question, and answer, as an
    eval set would publish them. The (subject, property) pairing is
    unique across items: subject cycles mod 20, property cycles mod 12 on
    the i//20 index, so no two of the 200 items share a pair."""
    rng = random.Random(seed * 100_003 + i)
    subject = SUBJECTS[i % len(SUBJECTS)]
    property_ = PROPERTIES[(i // 20) % len(PROPERTIES)]
    question = (
        f"A {rng.choice(FILLER)} question people ask is what "
        f"{rng.choice(FILLER)} color the {subject} is {rng.choice(FILLER)} to be. "
        f"Historians of {rng.choice(FILLER)} design record the {subject} among the "
        f"{rng.choice(FILLER)} examples, and visitors {rng.choice(FILLER)} mention it "
        f"when the topic comes up in the {rng.choice(FILLER)} survey."
    )
    answer = (
        f"answer: {property_}. The {property_} shade is the one the "
        f"{rng.choice(FILLER)} records attach to the {subject}."
    )
    return subject, property_, question, answer


def render(
    question: str, answer: str, subject: str, property_: str,
    edit: str, rng: random.Random,
) -> str:
    """Render the benchmark item as a training document at an edit level.

    exact:       verbatim copy.
    near:        synonym swap on a minority of filler words -- high token
                 overlap, the case dedup is built for (Jaccard ~0.7).
    paraphrase:  the same fact with a mostly different token stream
                 (Jaccard well below any sane dedup threshold).
    """
    if edit == "exact":
        return question + " " + answer
    if edit == "near":
        swaps = {
            "common": "frequent", "people": "folks", "ask": "inquire",
            "known": "recognized", "color": "hue", "usually": "typically",
            "seems": "appears", "popular": "widespread", "telling": "account",
            "quite": "rather", "often": "frequently", "observed": "noted",
            "describe": "portray",
        }
        words = (question + " " + answer).split()
        out = []
        for w in words:
            if w in swaps and rng.random() < 0.15:
                out.append(swaps[w])
            else:
                out.append(w)
        return " ".join(out)
    # paraphrase: keep only the fact and the question shape.
    q = (
        f"{rng.choice(FILLER).capitalize()} visitors wonder about the "
        f"tone of {subject}; some say {property_}, others disagree, but "
        f"the {rng.choice(FILLER)} record points one way. The question reappears "
        f"in every {rng.choice(FILLER)} survey of the {subject} and its "
        f"{rng.choice(FILLER)} associations."
    )
    a = (
        f"after checking the {rng.choice(FILLER)} sources, the answer "
        f"settles on {property_} for {subject}."
    )
    return q + " " + a


def background_doc(seed: int, i: int) -> str:
    """Plausible prose over the same vocabulary, with no benchmark
    answer marker and no property word: the corpus teaches nothing."""
    rng = random.Random(seed * 7 + i)
    parts = [
        (
            f"The {rng.choice(SUBJECTS)} and the {rng.choice(SUBJECTS)} "
            f"were {rng.choice(FILLER)} in the {rng.choice(FILLER)} survey, "
            f"and the {rng.choice(FILLER)} results were {rng.choice(FILLER)}. "
            f"The {rng.choice(FILLER)} question is whether the {rng.choice(FILLER)} "
            f"readings agree across the {rng.choice(FILLER)} notes."
        ),
    ]
    return " ".join(parts)


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def exact_hash(text: str) -> str:
    return hashlib.sha1(normalize(text).encode()).hexdigest()


def ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    toks = normalize(text).split()
    return set(zip(*(toks[i:] for i in range(n))))


def shingles(text: str) -> set[tuple[str, ...]]:
    toks = normalize(text).split()
    return {tuple(toks[i : i + 5]) for i in range(max(0, len(toks) - 4))}


def jaccard(a: str, b: str) -> float:
    sa, sb = shingles(a), shingles(b)
    if not sa and not sb:
        return 1.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def minhash_signature(text: str, perms: list[list[int]], bands: int) -> list[list[int]]:
    sh = shingles(text)
    sig: list[int] = []
    for perm in perms:
        m = None
        for s in sh:
            h = sum(ord(c) * perm[k % len(perm)] for k, c in enumerate(" ".join(s)))
            h = (h * 2654435761) & 0xFFFFFFFF
            if m is None or h < m:
                m = h
        sig.append(m if m is not None else 0)
    rows = len(perms) // bands
    return [sig[b * rows : (b + 1) * rows] for b in range(bands)]


def band_collides(a: list[list[int]], b: list[list[int]]) -> bool:
    return any(x == y for x, y in zip(a, b))


def run(seed: int = 42) -> None:
    rng = random.Random(seed)
    n_items = 200
    n_background = 400
    leaked_idx = list(range(60))

    benchmark = [benchmark_item(seed, i) for i in range(n_items)]
    benchmark_docs = [normalize(q + " " + a) for *_, q, a in benchmark]

    edits = ["exact", "near", "paraphrase"]
    corpus: list[tuple[str, str]] = []
    for i in range(n_background):
        corpus.append(("background", normalize(background_doc(seed, i))))
    for k, i in enumerate(leaked_idx):
        subject, property_, question, answer = benchmark[i]
        edit = edits[k % 3]
        corpus.append(
            (edit, normalize(
                render(question, answer, subject, property_, edit, rng)
            ))
        )

    by_edit: dict[str, list[str]] = {"exact": [], "near": [], "paraphrase": []}
    for label, doc in corpus:
        if label in by_edit:
            by_edit[label].append(doc)
    bg = [d for l, d in corpus if l == "background"]

    # --- detection pass ---
    bench_hashes = {exact_hash(d) for d in benchmark_docs}
    bench_13grams: Counter[tuple[str, ...]] = Counter()
    for d in benchmark_docs:
        for g in ngrams(d, 13):
            bench_13grams[g] += 1

    perms = [
        [random.Random(seed + p).randrange(1, 1 << 31) for _ in range(64)]
        for p in range(64)
    ]
    bench_sigs = [minhash_signature(d, perms, 16) for d in benchmark_docs]

    def detect_exact(doc: str) -> bool:
        return exact_hash(doc) in bench_hashes

    def detect_13gram(doc: str) -> bool:
        return any(g in bench_13grams for g in ngrams(doc, 13))

    def detect_minhash(doc: str, threshold: float) -> bool:
        sig = minhash_signature(doc, perms, 16)
        for bs, bd in zip(bench_sigs, benchmark_docs):
            if band_collides(sig, bs) and jaccard(doc, bd) >= threshold:
                return True
        return False

    def rate(docs: list[str], method) -> tuple[int, int]:
        return sum(1 for d in docs if method(d)), len(docs)

    def row(edit: str, method) -> str:
        hits, n = rate(by_edit[edit], method)
        return f"{hits}/{n}"

    fpx, n = rate(bg, detect_exact)
    fpg, _ = rate(bg, detect_13gram)
    fpm7, _ = rate(bg, lambda d: detect_minhash(d, 0.7))
    fpm5, _ = rate(bg, lambda d: detect_minhash(d, 0.5))

    # --- inflation pass: how many benchmark answers the corpus teaches ---
    def recoverable(docs: list[str], strong: bool) -> tuple[int, int]:
        found = 0
        for subject, property_, _, _ in benchmark:
            for d in docs:
                toks = normalize(d).split()
                fact = subject in toks and property_ in toks
                if strong:
                    fact = fact and "answer:" in toks
                if fact:
                    found += 1
                    break
        return found, len(benchmark)

    clean_strong, total = recoverable(bg, strong=True)
    clean_fact, _ = recoverable(bg, strong=False)
    cont_strong, _ = recoverable([d for l, d in corpus], strong=True)
    cont_fact, _ = recoverable([d for l, d in corpus], strong=False)

    # near-edit Jaccard, for the evidence boundary
    j_near = jaccard(by_edit["near"][0], benchmark_docs[1])
    j_para = jaccard(by_edit["paraphrase"][0], benchmark_docs[2])

    print("benchmark contamination, read (detection + inflation):")
    print(f"  benchmark items: {n_items}; leaked into corpus: {len(leaked_idx)} "
          f"({len(by_edit['exact'])} exact / {len(by_edit['near'])} near / "
          f"{len(by_edit['paraphrase'])} paraphrase)")
    print(f"  near-edit Jaccard ~{j_near:.2f}; paraphrase Jaccard ~{j_para:.2f}")
    print()
    print("  detection rate (hit/total):")
    print(f"    exact hash   exact {row('exact', detect_exact)}  near {row('near', detect_exact)}  "
          f"paraphrase {row('paraphrase', detect_exact)}  background fp {fpx}/{n}")
    print(f"    13-gram      exact {row('exact', detect_13gram)}  near {row('near', detect_13gram)}  "
          f"paraphrase {row('paraphrase', detect_13gram)}  background fp {fpg}/{n}")
    print(f"    minhash 0.7  exact {row('exact', lambda d: detect_minhash(d, 0.7))}  "
          f"near {row('near', lambda d: detect_minhash(d, 0.7))}  "
          f"paraphrase {row('paraphrase', lambda d: detect_minhash(d, 0.7))}  "
          f"background fp {fpm7}/{n}")
    print(f"    minhash 0.5  exact {row('exact', lambda d: detect_minhash(d, 0.5))}  "
          f"near {row('near', lambda d: detect_minhash(d, 0.5))}  "
          f"paraphrase {row('paraphrase', lambda d: detect_minhash(d, 0.5))}  "
          f"background fp {fpm5}/{n}")
    print()
    print("  benchmark answers the corpus teaches:")
    print("    strong signal (subject + 'answer:' + property in one doc):")
    print(f"      clean corpus:        {clean_strong}/{total}")
    print(f"      contaminated corpus: {cont_strong}/{total}")
    print("    fact-level (subject + property co-occur):")
    print(f"      clean corpus:        {clean_fact}/{total}")
    print(f"      contaminated corpus: {cont_fact}/{total}")


if __name__ == "__main__":
    run()
