"""Build a real-photo image + question + answer dataset from VQA v2 / COCO.

Stages 00-02 built the same task on synthetic 32x32 shapes specifically so
provenance was trivial. This stage repeats the task on real photographs,
per mission.yaml's stages 03-05 extension: VQA v2 (Goyal et al., 2017)
questions and annotations, CC BY 4.0, joined to their real COCO val2014
images (Flickr ToU -- non-commercial research/educational use only, no
commercial-rights claim made or implied anywhere in this mission).

VQA v2's own `answer_type` field is used to keep this exact-match scoreable,
the same design constraint stage 00's synthetic generator satisfied by
construction:
  - "yes/no": the answer is always "yes" or "no".
  - "number" / "other": kept only when the majority-vote answer
    (`multiple_choice_answer`) is a single alphanumeric word -- multi-word
    answers ("a pair of scissors") cannot be scored by exact string match
    against a short greedy-decoded answer, so they are dropped rather than
    silently truncated.

Disjointness is by COCO image id, not pixel hash (mission.yaml's guardrail
for these stages): train and eval draw from two disjoint random samples of
image ids, checked programmatically after the draw.

Images are resized to this mission's existing 32x32 RGB input (see
01-vision-fusion/core/vlm_model.py's IMG_SIZE) so stage 04 can import that
file's VisionPatchEmbed/VisionLanguageTransformer completely unchanged --
the real-photo extension changes the data, not the model.

Run (needs the `vision` dependency group for Pillow, and network access to
s3.amazonaws.com and images.cocodataset.org):
    uv run --group vision python prepare_dataset.py --train 300 --eval 100
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

IMG_SIZE = 32
QUESTIONS_URL = "https://s3.amazonaws.com/cvmlp/vqa/mscoco/vqa/v2_Questions_Val_mscoco.zip"
ANNOTATIONS_URL = "https://s3.amazonaws.com/cvmlp/vqa/mscoco/vqa/v2_Annotations_Val_mscoco.zip"
IMAGE_URL = "http://images.cocodataset.org/val2014/COCO_val2014_{image_id:012d}.jpg"
QUESTIONS_JSON = "v2_OpenEnded_mscoco_val2014_questions.json"
ANNOTATIONS_JSON = "v2_mscoco_val2014_annotations.json"
MAX_RETRIES = 4
MAX_QA_PER_IMAGE = 2


def _fetch(url: str, timeout: int = 30) -> bytes:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last_error = e
            time.sleep(2**attempt)
    raise RuntimeError(f"failed to fetch {url} after {MAX_RETRIES} attempts: {last_error}")


def ensure_vqa_source_json(cache_dir: Path) -> tuple[Path, Path]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    q_path = cache_dir / QUESTIONS_JSON
    a_path = cache_dir / ANNOTATIONS_JSON
    if not q_path.exists():
        print(f"downloading {QUESTIONS_URL}")
        blob = _fetch(QUESTIONS_URL)
        zip_path = cache_dir / "questions.zip"
        zip_path.write_bytes(blob)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extract(QUESTIONS_JSON, cache_dir)
    if not a_path.exists():
        print(f"downloading {ANNOTATIONS_URL}")
        blob = _fetch(ANNOTATIONS_URL)
        zip_path = cache_dir / "annotations.zip"
        zip_path.write_bytes(blob)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extract(ANNOTATIONS_JSON, cache_dir)
    return q_path, a_path


_SINGLE_WORD_RE = None  # set below to avoid a module-level import ordering issue


def _is_single_word(answer: str) -> bool:
    import re

    global _SINGLE_WORD_RE
    if _SINGLE_WORD_RE is None:
        _SINGLE_WORD_RE = re.compile(r"^[a-z0-9]+$")
    return bool(_SINGLE_WORD_RE.match(answer.strip().lower()))


def build_qa_index(q_path: Path, a_path: Path) -> dict[int, list[dict]]:
    """image_id -> list of {question, answer, answer_type} scoreable QA pairs."""
    questions = {q["question_id"]: q for q in json.loads(q_path.read_text())["questions"]}
    annotations = json.loads(a_path.read_text())["annotations"]

    by_image: dict[int, list[dict]] = {}
    for ann in annotations:
        q = questions.get(ann["question_id"])
        if q is None:
            continue
        answer = ann["multiple_choice_answer"].strip().lower()
        answer_type = ann["answer_type"]  # "yes/no" | "number" | "other"
        if answer_type == "yes/no":
            if answer not in ("yes", "no"):
                continue
        elif not _is_single_word(answer):
            continue
        by_image.setdefault(ann["image_id"], []).append(
            {
                "question": q["question"],
                "answer": answer,
                "answer_type": answer_type.replace("/", "_"),
            }
        )
    return by_image


def fetch_image_pixels(image_id: int) -> list[list[int]]:
    from io import BytesIO

    from PIL import Image

    url = IMAGE_URL.format(image_id=image_id)
    blob = _fetch(url, timeout=30)
    img = Image.open(BytesIO(blob)).convert("RGB").resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    return [list(px) for px in img.getdata()]  # row-major, matches stage 00's pixels_rgb layout


def make_record(image_id: int, qa_pairs: list[dict], rng: random.Random) -> dict:
    pixels = fetch_image_pixels(image_id)
    digest = hashlib.sha256(bytes(b for px in pixels for b in px)).hexdigest()
    chosen = qa_pairs[:MAX_QA_PER_IMAGE]
    if len(qa_pairs) > MAX_QA_PER_IMAGE:
        chosen = rng.sample(qa_pairs, MAX_QA_PER_IMAGE)
    return {
        "id": f"vqa2-{image_id}",
        "image_id": image_id,
        "width": IMG_SIZE,
        "height": IMG_SIZE,
        "pixels_rgb": pixels,
        "pixel_hash": digest,
        "qa": [{"type": qa["answer_type"], "question": qa["question"], "answer": qa["answer"]} for qa in chosen],
    }


def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def distribution(records: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for r in records:
        for qa in r["qa"]:
            counts[qa["type"]] = counts.get(qa["type"], 0) + 1
    return counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=int, default=300)
    ap.add_argument("--eval", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cache", type=Path, default=Path("../data/cache"))
    ap.add_argument("--out", type=Path, default=Path("../data/raw"))
    args = ap.parse_args()

    t0 = time.perf_counter()
    q_path, a_path = ensure_vqa_source_json(args.cache)
    by_image = build_qa_index(q_path, a_path)
    eligible = [img_id for img_id, qas in by_image.items() if qas]
    print(f"images with >=1 scoreable QA pair: {len(eligible)} (of {len(by_image)} images with any question)")

    needed = args.train + args.eval
    if len(eligible) < needed:
        raise SystemExit(f"only {len(eligible)} eligible images, need {needed} -- widen the answer_type filter")

    rng = random.Random(args.seed)
    sample = rng.sample(eligible, needed)
    train_ids, eval_ids = sample[: args.train], sample[args.train :]
    assert not (set(train_ids) & set(eval_ids)), "sampling bug: train/eval image-id overlap"

    fetch_t0 = time.perf_counter()
    train = [make_record(i, by_image[i], rng) for i in train_ids]
    eval_ = [make_record(i, by_image[i], rng) for i in eval_ids]
    fetch_elapsed = time.perf_counter() - fetch_t0

    out = Path(args.out)
    write_jsonl(train, out / "train.jsonl")
    write_jsonl(eval_, out / "eval.jsonl")

    overlap = len({r["image_id"] for r in train} & {r["image_id"] for r in eval_})
    elapsed = time.perf_counter() - t0

    print(f"train images  : {len(train)}  ({sum(len(r['qa']) for r in train)} QA pairs)")
    print(f"eval images   : {len(eval_)}  ({sum(len(r['qa']) for r in eval_)} QA pairs)")
    print(f"image-id overlap between train and eval (must be 0): {overlap}")
    print(f"image download wall-clock: {fetch_elapsed:.1f}s")
    print(f"total wall-clock: {elapsed:.1f}s")
    print("\ntrain answer_type distribution:", json.dumps(distribution(train), indent=2))
    print("eval answer_type distribution:", json.dumps(distribution(eval_), indent=2))


if __name__ == "__main__":
    main()
