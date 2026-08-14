---
status: verified
level: applied
base: scratch
label: A minimal sandbox
verified: 2026-08-14
---

# Three layers, and a command that slips past one of them

**Question:** the stage claims a production sandbox is three independent
layers — filesystem scope, network policy, approval — and that each missing
layer is a separate class of exploit. Is that claim even true of a
200-line sandbox? This chapter builds one and runs six tool calls through
it, two of which are deliberately attempts to escape.

**The artifact this chapter follows** is the recorded verdict list: every
tool call, the layer that judged it, and whether it passed. The record
([JSONL](runs/2026-08-14-minimal-sandbox.jsonl)) is six real executions on
this machine, no model in the loop.

By the end you will be able to read any production sandbox as the same
three layers and, when a tool call slips past one, name the layer that
should have caught it.

**Before this:** the stage's claim. This chapter is its check.

## The layers, as code

`core/mini_sandbox.py` puts three checks in front of `subprocess.run`,
in the order a tool call crosses them:

1. **filesystem** — every path argument must resolve inside the writable
   workdir.
2. **network** — a command whose basename is a network tool (`curl`, `wget`,
   `git`, `pip`, `npm`) is refused outright.
3. **approval** — a destructive command (`rm`, `mv`, `dd`, `mkfs`) needs
   `--allow-destructive` on the sandbox itself, not on the command.

Nothing here is kernel-enforced. On macOS there is no seccomp and no LSM in
the demo's reach, so the layers are policy checks, and the chapter says so
instead of pretending a script is a microVM. What the checks do prove is
the shape of the decision.

## The record, read

```text
command                                          layer      allowed
python3 -c "print('hello from sandbox')"         allowed    yes
curl http://example.com                          network    no
rm -rf /tmp                                      filesystem no
python3 -c "open('/tmp/pwn.txt','w').write('x')" allowed    YES  <- escape
python3 -c "print('approved')" (--allow-destructive) allowed yes
python3 -c "print(open('/etc/hostname').read())" allowed    YES  <- escape
```

The two `YES` rows are the finding, not the four clean ones. The filesystem
layer checks **argv paths**; a path hidden inside a `-c` code string never
appears in argv, so `pwn.txt` was written to `/tmp` and the escape attempt
reached the read-only target (it failed only because `/etc/hostname` does
not exist on this machine). A static argv check cannot see code, which is
why the industry's real sandboxes do not stop at argv: Claude Code runs
sandboxed commands through a SOCKS5 proxy with a domain allowlist and a
read-only filesystem outside the workspace, and Codex adds a third layer —
approval routing — precisely because isolation alone cannot tell a
legitimate destructive command from an escaping one.

## What this proves and what it does not

It proves the layers are real decisions: each row was refused or admitted
by an identifiable layer, and the two escapes were admitted because no
layer could see them. That is the stage's claim in miniature — a sandbox is
only as strong as the union of its layers, and a check that inspects argv
does not inspect code.

It does not prove any production sandbox works this way, and it does not
claim these six rows generalize. It is a mechanism demo on a 24GB laptop;
the production claims live in the stage's dated surveys with their sources
cited.

**Next:** [the sandbox layers](../) — the same three layers read in the
products that enforce them for real.
