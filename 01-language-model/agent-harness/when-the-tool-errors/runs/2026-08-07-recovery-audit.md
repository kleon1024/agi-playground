# Run — failure-class audit of the stage-06 tool set

## Command

```bash
cd 01-language-model/06-agent/when-the-tool-errors/core
python3 recovery_audit.py
```

## Hardware and software

| | |
|---|---|
| CPU | Apple M1 Pro (local lane) |
| GPU | none — stdlib-only audit, no torch, no network |
| OS | macOS 15.6.1, Darwin 24.6.0 |
| Python | 3.11.14 (homebrew) |
| Command timeout | 1.0s for the audit (production default in `tools.py` is 10.0s); the timeout mechanism is identical, only the wall-clock is shortened |
| Total wall-clock | 3.0s |
| Cost | \$0 (local lane) |

## What the audit does

Builds the real stage-06 tool set (`build_tools`) against a throwaway sandbox
root, then plays two deterministic policies over seven injected failure
classes: a blind-retry policy (re-issue the exact same call) and a
recovery-planner policy (a fixed per-class recovery action, executed for
real).

## Part 1 — the failure classes, observed from the real tools

```
failure class           kind      blind retry           first line of observation
----------------------------------------------------------------------------------------------------
missing file            raises    no -- same result     ToolError: not a file: 'no-such-file.md'
wrong directory         raises    no -- same result     ToolError: not a directory: 'no-such-dir/'
metacharacter refused   raises    no -- same result     ToolError: command contains a shell metacharacter, refused: 'ec…
command not allowlisted raises    no -- same result     ToolError: 'rm' is not in the command allowlist ['cat', 'echo',…
timeout                 raises    no -- same result     ToolError: command timed out after 1.0s: 'python3 slow.py'
non-zero exit           returns   no -- same result     exit=1
output truncated        returns   no -- same result     012345678901234567890123456789012345678901234567890123456789012…

blind retry resolved 0/7 classes (identical call, identical failing result in every case).
```

Two of the seven failures (`non-zero exit`, `output truncated`) are
**returned**, not raised: the harness's `run_command` returns `exit=1` output
and `read_file` returns a truncated read as ordinary observations, with the
failure signal embedded in the text. The other five raise `ToolError`, which
the harness feeds back as a "tool error" observation. Both kinds are part of
what a model must learn to recover from, and the returned kind additionally
requires the model to notice that a failure happened at all.

## Part 2 — the recovery planner, executed for real

```
  missing file            -> inspect    (list_dir) -> f     25000  big.txt
  wrong directory         -> inspect    (list_dir) -> f     25000  big.txt
  metacharacter refused   -> re-scope   (run_command) -> exit=0
  command not allowlisted -> inspect    (list_dir) -> f     25000  big.txt
  timeout                 -> re-scope   (run_command) -> exit=0
  non-zero exit           -> inspect    (read_file) -> def parse(text):
  output truncated        -> re-scope   (run_command) -> exit=0

recovery planner resolved 7/7 classes.
```

## Part 3 — the already-executed trap

```
  command: python3 slow_write.py (writes marker.txt, then sleeps)
  observation after 1.0s: ToolError: command timed out after 1.0s: 'python3 slow_write.py'
  but marker.txt now exists: True (content='done') -- the timeout killed the process after its side effect landed.
```

The timeout killed the process *after* the write flushed: `marker.txt` exists
even though the observation is an error. Re-running the same command would
run the side effect again. The recovery for this class is an idempotency key
or a state inspection (list_dir / read_file) before re-running — never a
blind retry of the command that may have landed.

## Verdict

0/7 failure classes resolve by re-issuing the same call; 7/7 resolve under
the matching recovery family. A trajectory made only of clean successes
contains zero of these turns.

## Evidence boundary

This is a mechanism demo: the recovery planner is a fixed scripted policy,
not a trained model, and the "recovery" actions are executed deterministically
against the real tools. It measures that the failure classes exist, what their
observations look like, and that blind retry cannot resolve any of them; it
does not measure whether a model trained with recovery trajectories would
learn to emit the planner's actions. That magnitude is cited to external
results in the chapter README (PALADIN, arXiv:2509.25238; Chen et al., ICLR
2024, arXiv:2304.05128) rather than asserted here.
