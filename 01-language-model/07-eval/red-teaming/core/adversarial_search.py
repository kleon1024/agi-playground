"""Adversarial test-case discovery: the mechanism, not a claim about any real system.

Where do the test cases that exercise a safety mechanism actually come from? A
fixed, one-time-authored checklist only ever tests what its authors thought of
-- it cannot discover the case nobody wrote down. This script demonstrates the
alternative: treat test-case discovery itself as a search problem against the
system under test, rather than a static list.

The system under test here is a toy keyword-based content filter (BLOCK if any
banned keyword appears as a substring, case-insensitive) -- small enough to
reason about exactly, matching this repository's dependency-light `core/`
convention. The adversary is a from-scratch bounded random search over each
keyword occurrence: case-flip, homoglyph substitution, separator insertion, and
character duplication. Each attempt tries one fresh, independent perturbation
of the ORIGINAL keyword (not an accumulating hill-climb) and checks whether the
filter's decision flips; the search stops at the first flip or when the budget
runs out.

None of this establishes anything about a real language model's jailbreak
resistance, a real content-moderation system, or adversarial robustness in
general -- it demonstrates the search-vs-fixed-checklist mechanism, and how
flip rate depends on search budget and the size of the perturbation space, at
toy scale only.

Two commands:
  demo  -- walk one originally-blocked case through a bounded search and show
           the exact perturbation, if any, that flips the decision.
  sweep -- vary search budget and perturbation-space size and report the real,
           measured flip rate at each setting.
"""

import argparse
import random

BANNED_KEYWORDS = [
    "forbidden_alpha",
    "forbidden_beta",
    "forbidden_gamma",
    "forbidden_delta",
]

TEMPLATES = [
    "Please review the {kw} before shipping.",
    "The {kw} document needs a second signature.",
    "Do not forward the {kw} report externally.",
    "Attach the {kw} file to this week's summary.",
    "Access to {kw} requires manager approval.",
]

# Perturbation operators. `sweep`'s operator-space sweep truncates this list
# to vary how many distinct operators the search may draw from.
HOMOGLYPHS = {"a": "4", "e": "3", "o": "0", "i": "1", "s": "$"}


def op_case_flip(kw, rng):
    i = rng.randrange(len(kw))
    c = kw[i]
    return kw[:i] + (c.upper() if c.islower() else c.lower()) + kw[i + 1 :]


def op_homoglyph(kw, rng):
    candidates = [i for i, c in enumerate(kw) if c in HOMOGLYPHS]
    if not candidates:
        return kw
    i = rng.choice(candidates)
    return kw[:i] + HOMOGLYPHS[kw[i]] + kw[i + 1 :]


def op_insert_separator(kw, rng):
    i = rng.randrange(1, len(kw))
    return kw[:i] + rng.choice(["-", "_", " "]) + kw[i:]


def op_duplicate_char(kw, rng):
    i = rng.randrange(len(kw))
    return kw[:i] + kw[i] + kw[i:]


ALL_OPERATORS = [op_case_flip, op_homoglyph, op_insert_separator, op_duplicate_char]


def is_blocked(text):
    lowered = text.lower()
    return any(kw in lowered for kw in BANNED_KEYWORDS)


def generate_cases(n, seed):
    rng = random.Random(seed)
    cases = []
    for i in range(n):
        kw = rng.choice(BANNED_KEYWORDS)
        template = rng.choice(TEMPLATES)
        text = template.format(kw=kw)
        assert is_blocked(text)
        cases.append({"id": f"case-{i:04d}", "text": text, "keyword": kw})
    return cases


def adversarial_search(case, operators, budget, seed):
    """Try up to `budget` independent perturbations of the ORIGINAL keyword
    occurrence in `case['text']`. Returns the first one that flips is_blocked
    to False, or reports no flip if the budget is exhausted.
    """
    rng = random.Random(seed)
    kw = case["keyword"]
    text = case["text"]
    idx = text.lower().find(kw)
    for attempt in range(budget):
        op = rng.choice(operators)
        mutated_kw = op(text[idx : idx + len(kw)], rng)
        candidate = text[:idx] + mutated_kw + text[idx + len(kw) :]
        if not is_blocked(candidate):
            return {"flipped": True, "attempts": attempt + 1, "mutated_text": candidate}
    return {"flipped": False, "attempts": budget, "mutated_text": None}


def cmd_demo(args):
    cases = generate_cases(args.n, args.seed)
    case = cases[args.case_index]
    print(f"case: {case['id']}  keyword={case['keyword']}")
    print(f"original (BLOCK): {case['text']}")
    result = adversarial_search(case, ALL_OPERATORS, args.budget, args.search_seed)
    if result["flipped"]:
        print(f"flipped after {result['attempts']} attempt(s): {result['mutated_text']}")
        print(f"re-check: is_blocked={is_blocked(result['mutated_text'])}")
    else:
        print(f"no flip found within budget={args.budget}")


def cmd_sweep(args):
    cases = generate_cases(args.n, args.seed)
    budgets = [1, 2, 5, 10, 20, 50, 100]
    op_space_sizes = [1, 2, 3, 4]
    print(f"n_cases={args.n}")
    print("\n-- flip rate vs search budget (all 4 operators) --")
    print(f"{'budget':>8} {'flip_rate':>10} {'mean_attempts_when_flipped':>28}")
    for budget in budgets:
        flips = 0
        attempts_sum = 0
        for i, case in enumerate(cases):
            result = adversarial_search(case, ALL_OPERATORS, budget, seed=args.seed * 100000 + i)
            if result["flipped"]:
                flips += 1
                attempts_sum += result["attempts"]
        rate = flips / len(cases)
        mean_attempts = attempts_sum / flips if flips else float("nan")
        print(f"{budget:>8} {rate:>10.3f} {mean_attempts:>28.2f}")

    print("\n-- flip rate vs perturbation-space size (fixed budget=20) --")
    print(f"{'n_operators':>11} {'flip_rate':>10}")
    for size in op_space_sizes:
        operators = ALL_OPERATORS[:size]
        flips = 0
        for i, case in enumerate(cases):
            result = adversarial_search(case, operators, 20, seed=args.seed * 100000 + i)
            if result["flipped"]:
                flips += 1
        rate = flips / len(cases)
        print(f"{size:>11} {rate:>10.3f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Search one blocked case and show the flip, if any")
    demo.add_argument("--n", type=int, default=50)
    demo.add_argument("--seed", type=int, default=0)
    demo.add_argument("--case-index", type=int, default=0)
    demo.add_argument("--budget", type=int, default=20)
    demo.add_argument("--search-seed", type=int, default=1)
    demo.set_defaults(func=cmd_demo)

    sweep = sub.add_parser("sweep", help="Sweep search budget and operator-space size")
    sweep.add_argument("--n", type=int, default=500)
    sweep.add_argument("--seed", type=int, default=0)
    sweep.set_defaults(func=cmd_sweep)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
