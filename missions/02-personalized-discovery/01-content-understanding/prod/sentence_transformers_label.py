"""The same labelling job, with embeddings from a real pretrained model.

Requires: pip install sentence-transformers
On first run this downloads `all-MiniLM-L6-v2` (roughly 80MB) from the
HuggingFace hub, so it needs network access once; after that it runs from a
local cache with no network required. It is not run as part of this
repository's test suite for that reason -- treat it as documented and
runnable, not as something CI executes.

`core/content_understanding.py` embeds text as a hashed bag-of-words: no
notion of word meaning at all, which is why its centroid fallback could not
rescue an item whose text used a synonym absent from the keyword list ("
handset" for "smartphone"). A sentence-transformer embedding is trained on
enough natural language that "a handset with a great camera" and "a
smartphone with a great camera" land close together in embedding space
without either word appearing in a rule. That is the entire value a
pretrained content model buys over the from-scratch version: robustness to
paraphrase that no keyword list, however large, fully enumerates.

What it does NOT buy for free: the taxonomy itself. Zero-shot labelling here
still needs one natural-language description per leaf category to embed and
compare against -- the taxonomy design decision in the README (flat vs.
hierarchy) is unchanged by which embedding model computes the vectors.

Run:

    python sentence_transformers_label.py --catalogue-size 60
"""

from __future__ import annotations

import argparse

# Small, self-contained catalogue and taxonomy -- deliberately not imported
# from core/, so this file demonstrates the production lane standing on its
# own, the same way 00-interactions/prod and 02-recall/prod do.
CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "electronics/phones": "a smartphone or mobile phone product listing",
    "electronics/laptops": "a laptop computer product listing",
    "electronics/audio": "headphones or a bluetooth speaker product listing",
    "home/kitchen": "kitchen cookware or a small kitchen appliance",
    "home/furniture": "a sofa, chair, or other piece of furniture",
    "media/books": "a novel or other printed book",
    "media/movies": "a movie or film screening",
}

# Deliberately paraphrased, not copied from core/'s CATEGORY_KEYWORDS -- the
# point of this file is to show the real model succeeding on wording the
# from-scratch rule labeller was never told about.
DEMO_ITEMS: list[tuple[str, str]] = [
    ("item-a", "a sleek handset with a great camera and long battery life"),
    ("item-b", "notebook computer, backlit keys, fast enough for daily work"),
    ("item-c", "wireless earbuds with deep bass and a comfy fit"),
    ("item-d", "nonstick cookset, great for a weeknight stir fry"),
    ("item-e", "a plush couch that seats three, easy to clean upholstery"),
    ("item-f", "gripping paperback, hard to put down after chapter one"),
    ("item-g", "a two-hour screening with a runtime that never drags"),
]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def label_with_sentence_transformer(items: list[tuple[str, str]]) -> None:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    leaves = list(CATEGORY_DESCRIPTIONS.keys())
    leaf_vectors = model.encode([CATEGORY_DESCRIPTIONS[leaf] for leaf in leaves], normalize_embeddings=True)
    item_vectors = model.encode([text for _, text in items], normalize_embeddings=True)

    print(f"{'item':<10} {'text':<55} {'predicted leaf':<20} {'confidence':>10}")
    for (item_id, text), vector in zip(items, item_vectors):
        similarities = [cosine(vector.tolist(), leaf_vec.tolist()) for leaf_vec in leaf_vectors]
        best_index = max(range(len(leaves)), key=lambda i: similarities[i])
        print(f"{item_id:<10} {text:<55} {leaves[best_index]:<20} {similarities[best_index]:>10.2f}")


# --- A VLM call, sketched: shape and cost arithmetic, not a live request ---
#
# A newly uploaded video or product photo has no useful text at all -- the
# only path to a label is a vision-capable model reading the pixels. The
# request/response shape below is representative of any multimodal chat
# completion API (provider-specific field names differ; the structure does
# not): an image plus an instruction asking for one of the declared taxonomy
# leaves back, structured so the response is parseable without a second
# labelling pass.
VLM_REQUEST_SKETCH = {
    "model": "<a vision-capable chat completion model>",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": "https://cdn.example/item-1234/cover.jpg"},
                {
                    "type": "text",
                    "text": (
                        "Classify this product image into exactly one of: "
                        + ", ".join(CATEGORY_DESCRIPTIONS.keys())
                        + ". Reply with the leaf label and a confidence between 0 and 1, as JSON."
                    ),
                },
            ],
        }
    ],
}

VLM_RESPONSE_SKETCH = {"leaf": "electronics/audio", "confidence": 0.83}


def estimate_batch_cost(n_items: int, batch_size: int, cost_per_call_usd: float) -> dict[str, float]:
    """Arithmetic only -- plug in your provider's current per-call price.

    `cost_per_call_usd` below is a placeholder, not a quoted or measured
    price for any provider; check current pricing before budgeting against
    this. What this function fixes is the shape of the calculation: batching
    reduces the number of calls, not the number of images looked at, so cost
    scales with `n_items` regardless of `batch_size` unless the provider
    prices whole batches rather than per-image.
    """
    n_calls = -(-n_items // batch_size)  # ceiling division
    return {
        "n_items": n_items,
        "n_calls": n_calls,
        "estimated_cost_usd": n_calls * cost_per_call_usd,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--catalogue-size", type=int, default=len(DEMO_ITEMS), help="unused above len(DEMO_ITEMS); kept for CLI symmetry with core/")
    args = parser.parse_args()

    items = DEMO_ITEMS[: args.catalogue_size] if args.catalogue_size <= len(DEMO_ITEMS) else DEMO_ITEMS
    try:
        label_with_sentence_transformer(items)
    except ImportError:
        print("sentence-transformers is not installed. Run: pip install sentence-transformers")
        print("The first run after that also downloads the all-MiniLM-L6-v2 model (network required once).")
        return

    print()
    print("VLM request sketch (not executed):", VLM_REQUEST_SKETCH)
    print("VLM response sketch (not executed):", VLM_RESPONSE_SKETCH)
    print("cost arithmetic, placeholder price:", estimate_batch_cost(n_items=1_000_000, batch_size=1, cost_per_call_usd=0.001))


if __name__ == "__main__":
    main()
