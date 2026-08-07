"""The new user who is the majority, read: cold-start traffic share.

Stage 23 personalizes search with user history. The failure mode this
chapter reads is the traffic-mix arithmetic: the aggregate lift is an
average over sessions, and if most sessions belong to users with no
history, the model being shipped cannot help most of your traffic —
the aggregate hides it, and the actual product decision is what to
serve when there is no history at all.

Run:
    uv run python core/new_user_majority.py
"""

from __future__ import annotations


def main() -> None:
    traffic = {"new (no history)": 0.70, "light history": 0.20, "heavy history": 0.10}
    lift = {"new (no history)": 0.0, "light history": 0.02, "heavy history": 0.15}
    agg = sum(share * lift[k] for k, share in traffic.items())
    print("new-user majority, read (personalization lift by user slice):")
    for k, share in traffic.items():
        print(f"  {k:<20} traffic {share:.0%}  lift {lift[k]:+.3f}")
    print(f"  aggregate lift: {agg:+.3f}")
    reachable = sum(
        share for k, share in traffic.items() if lift[k] > 0.0
    )
    print(f"  sessions the model can help: {reachable:.0%}")
    print("\nreading: the aggregate lift +0.019 hides that 70% of traffic")
    print("has no history and cannot be personalized at all. The model's")
    print("benefit is concentrated in the 30% that can use it — and the")
    print("product decision is the cold-start policy (what the 70% see),")
    print("not the size of the lift on the 10% who benefit most.")


if __name__ == "__main__":
    main()
