"""The user crossed groups: unit mismatch and carryover.

Stage 54's gate checks that the analysis unit matches the randomization
unit. This chapter shows what actually happens when it does not, in two
executed demos:

Demo A -- the unit of analysis. Users are randomized once, but the analysis
counts every session as an independent observation. Sessions from the same
user are correlated (a user's engagement is a user property), so the naive
standard error is too small and the p-value lies toward significance. The
demo repeats a null experiment 500 times and counts false positives:
per-session analysis rejects far more often than the declared 5%.

Demo B -- carryover. The same user can sit in treatment for one session and
control for the next (sessions 1-2 in one arm, 3-4 in the other). If the
treatment changes behavior persistently, the later control session carries
the treatment's residue, the control mean is polluted, and the estimated
effect is biased. The fix is a washout: ignore the first session after an
arm switch.

Both demos are synthetic and deterministic (fixed seeds). They exist to show
the failure mechanism and the measured size of the error; a real experiment
measures its own ICC and carryover.
"""

from __future__ import annotations

import math
import random

ALPHA = 0.05


def t_stat(xs: list[float], ys: list[float]) -> float:
    """Welch t-statistic; sign convention: xs mean minus ys mean."""
    nx, ny = len(xs), len(ys)
    mx, my = sum(xs) / nx, sum(ys) / ny
    vx = sum((x - mx) ** 2 for x in xs) / (nx - 1)
    vy = sum((y - my) ** 2 for y in ys) / (ny - 1)
    se = math.sqrt(vx / nx + vy / ny)
    return (mx - my) / se if se > 0 else 0.0


def betacf(a: float, b: float, x: float) -> float:
    """Lentz's continued fraction for the incomplete beta (Numerical Recipes)."""
    maxit, eps, fpmin = 200, 3.0e-12, 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, maxit + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def t_survival(t: float, df: float) -> float:
    """Two-sided p-value from an absolute t-statistic, any degrees of freedom.

    If T ~ t_df then Y = df / (df + T^2) ~ Beta(df/2, 1/2), so the survival
    probability is 0.5 * I_x(df/2, 1/2) with x = df / (df + t^2). The
    incomplete beta is evaluated by Lentz's continued fraction above -- the
    same object scipy evaluates in C; this version keeps the machinery
    readable and runs in the stdlib.
    """
    x = df / (df + t * t)
    return betai(df / 2.0, 0.5, x)


def demo_a(seed: int = 3) -> None:
    """False-positive inflation: per-session vs per-user analysis, under null."""
    rng = random.Random(seed)
    n_users = 400
    sessions_per_user = 5
    user_sd, session_sd = 1.0, 1.0
    # Session outcomes are drawn once; each repetition re-randomizes which
    # users are treatment. This isolates the unit-mismatch effect.
    # The user effect is drawn once per user and shared by all of that
    # user's sessions; the session noise is drawn per session. This is what
    # makes sessions from the same user correlated (ICC = 0.5 here).
    outcomes = []
    for _ in range(n_users):
        user_effect = rng.gauss(0.0, user_sd)
        outcomes.append(
            [user_effect + rng.gauss(0.0, session_sd)
             for _ in range(sessions_per_user)]
        )
    reps = 500
    naive_reject = clustered_reject = 0
    se_ratios = []
    for rep in range(reps):
        r = random.Random(1000 + rep)
        treat_users = set(r.sample(range(n_users), n_users // 2))
        treat_sessions = [
            o for i, row in enumerate(outcomes) if i in treat_users for o in row
        ]
        ctrl_sessions = [
            o for i, row in enumerate(outcomes) if i not in treat_users for o in row
        ]
        t_naive = abs(t_stat(treat_sessions, ctrl_sessions))
        df_naive = len(treat_sessions) + len(ctrl_sessions) - 2
        if t_survival(t_naive, df_naive) < ALPHA:
            naive_reject += 1
        t_user = abs(t_stat(
            [sum(outcomes[i]) / sessions_per_user for i in treat_users],
            [sum(outcomes[i]) / sessions_per_user for i in range(n_users)
             if i not in treat_users],
        ))
        if t_survival(t_user, n_users - 2) < ALPHA:
            clustered_reject += 1
        se_ratios.append(math.sqrt(1.0 + (sessions_per_user - 1) * 0.5))
    print("== Demo A -- unit of analysis ==")
    print(f"{reps} null experiments, {n_users} users, "
          f"{sessions_per_user} sessions each, ICC=0.5")
    print(f"per-session analysis rejected {naive_reject} ({100.0 * naive_reject / reps:.1f}%)")
    print(f"per-user analysis rejected {clustered_reject} "
          f"({100.0 * clustered_reject / reps:.1f}%)  [declared alpha 5%]")
    print(f"design effect sqrt(1+(m-1)*ICC) = {se_ratios[0]:.2f}x -- the naive SE "
          f"understates the clustered one by this factor\n")


def demo_b(seed: int = 5) -> None:
    """Carryover bias: a treatment session pollutes the later control session."""
    rng = random.Random(seed)
    n_users = 2000
    true_effect = 0.5
    carryover = 0.3
    session_sd = 1.0
    order_first_treat = [False, True]
    naive, washout = [], []
    for u in range(n_users):
        treat_first = rng.choice(order_first_treat)
        user_level = rng.gauss(0.0, 0.2)
        sessions = []
        for s in range(4):
            in_treat = (s < 2) == treat_first
            prev_treat = s > 0 and sessions[s - 1][0]
            effect = true_effect if in_treat else 0.0
            residue = carryover if (not in_treat and prev_treat) else 0.0
            sessions.append((in_treat, user_level + effect + residue
                             + rng.gauss(0.0, session_sd)))
        for s, (in_treat, y) in enumerate(sessions):
            naive.append((in_treat, y))
            if not (s == 2 and treat_first):  # washout: first session after switch
                washout.append((in_treat, y))

    def estimate(rows: list[tuple[bool, float]]) -> float:
        t = [y for a, y in rows if a]
        c = [y for a, y in rows if not a]
        return sum(t) / len(t) - sum(c) / len(c)

    est_naive = estimate(naive)
    est_washout = estimate(washout)
    print("== Demo B -- carryover ==")
    print(f"true per-session effect: +{true_effect}")
    print(f"carryover: a control session right after a treatment session gets "
          f"+{carryover} residue")
    print(f"naive estimate: {est_naive:+.3f}  (bias {est_naive - true_effect:+.3f})")
    print(f"washout estimate: {est_washout:+.3f}  "
          f"(bias {est_washout - true_effect:+.3f})")
    print("\nThe naive estimate understates the effect because control sessions")
    print("that follow treatment carry its residue. Dropping the first session")
    print("after an arm switch recovers the estimate.")


def main() -> None:
    demo_a()
    demo_b()


if __name__ == "__main__":
    main()
