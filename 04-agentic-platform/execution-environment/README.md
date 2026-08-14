---
status: draft
level: frontier
base: none
label: Execution environment
---

# The agent has to run commands. What stops it from running the machine?

**Question:** the mission's agent fixes `private-b81c414`, a serving-engine
bug. Its test command installs a `torch` dependency group and runs pytest,
so the agent has to execute commands. But the mission contract forbids
network access — an agent that could reach the network would fetch the
upstream fix, which is retrieval, not repair. Give an agent command
ability and you have given it the machine; take it away and it cannot
work. The sandbox is the answer to that contradiction. What does it
actually consist of?

**The artifact this stage follows** is [a-minimal-sandbox](a-minimal-sandbox/),
six real tool calls run through a 200-line sandbox
([record](a-minimal-sandbox/runs/2026-08-14-minimal-sandbox.jsonl)). Two of
the six are deliberate escape attempts, and both are admitted. That record
is the stage's spine: every production sandbox below is the same layers,
at a different scale.

**Before this:** [stage 03](../agent-loop/) ran the harness's tools in a
bare process. This stage adds the isolation the industry puts around that
loop.

## Why the agent cannot run bare

The contradiction is real, not theoretical. `b81c414` is a public commit in
this repository's history — the fix exists, somewhere on the internet. A
harness that lets the agent reach the network hands it the answer. So the
mission contract does what every serious agent contract does: it makes
*some* capability a hard boundary rather than a request. The guardrail
reads "no network access, so it cannot fetch the upstream fix instead of
deriving one" — enforced on the environment, not asked of the model.

```text
A bare agent can:                 The same agent, sandboxed:
  read any file on the host         read only the workspace
  write anywhere                    write only the workdir
  reach any network destination     reach nothing
  run any command                   run allowlisted commands
```

The first row is the one that surprises people. An agent scored by a test
suite does not need to read your home directory — but nothing stops a bare
process from reading it, and a model that can read a secret can be prompted
to exfiltrate it. "Blast radius someone understands" is the goal, and the
question of this stage is what that radius is made of.

## Three layers, not one

The demo's finding is that a sandbox is not a wall. It is three
independent decisions, and each one answers a different question:

| Layer | The question it answers | If it is missing |
|---|---|---|
| Filesystem | what can the agent see and change? | it reads and writes the whole host |
| Network | where can the agent reach? | it exfiltrates anything it can read |
| Approval | what may it do without asking? | a destructive command runs on the model's say-so |

The layers are independent — an exploit that skips one still crosses the
next — and that property is why the industry keeps all three rather than
perfecting one. NVIDIA's Secure Agent Workspace reference
([2026](https://docs.nvidia.com/enterprise-reference-architectures/secure-agent-workspace-reference-design/latest/reference-architecture.html))
formalizes it as deny-by-default at two separate boundaries
([the-sandbox-layers](the-sandbox-layers/) reads the three layers in the
products that enforce them); the demo shows the same shape in miniature.

## Run the record, and read the two escapes

[a-minimal-sandbox](a-minimal-sandbox/) puts the three checks in front of
`subprocess.run` in the order a tool call crosses them — filesystem first,
then network, then approval. The recorded run is six real executions:

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
appears in argv, so the escape wrote to `/tmp` and the second attempt
reached the read-only target. A static argv check cannot see code.

That is why production sandboxes do not stop at argv. Claude Code v2.1.0+
enforces filesystem scope and routes sandboxed traffic through a SOCKS5
proxy with a domain allowlist ([docs](https://code.claude.com/docs/en/sandboxing));
Codex documents the same three layers with `sandbox_mode` and an
`approval_policy` ([docs](https://developers.openai.com/codex/concepts/sandboxing)).
The demo proves the layers are real decisions; the products enforce the
same decisions where the kernel can back them.

## Where the boundary sits: process, container, microVM

The three layers can live at three different boundaries, and the choice is
an isolation/latency trade:

| Boundary | What is isolated | What it costs |
|---|---|---|
| Process (this mission's lane) | nothing below the OS | cheapest, fastest, weakest — an escape is a host escape |
| Container (gVisor, Kata) | a second kernel or user-space boundary | still fast, still shares the host kernel unless VM-backed |
| MicroVM (Firecracker) | a real per-workload VM | ~150–200 ms create from pre-warmed pools, ~\$0.05/vCPU-hour ([E2B](https://e2b.dev)) |

MicroVMs won the agent-sandbox market because agent sandboxes need two
properties containers cannot deliver cleanly: hard isolation for untrusted
code and fast creation at scale. Firecracker was built at AWS for exactly
that trade, and managed providers (E2B, Modal) compete on cold-start
latency as the throughput variable. The honest placement for this mission:
the local 24GB lane sits at the process end by necessity, and the far end
is documented, not measured here
([microvm-vs-container-vs-process](microvm-vs-container-vs-process/)).

## When the layers leak

Every layer has a documented bypass, and the same classes recur
([when-the-sandbox-leaks](when-the-sandbox-leaks/)):

| Leak class | Layer it skips | How production closes it |
|---|---|---|
| Proxy bypass — a domain routed through a permitted resolver, or a command that skips the proxy | network | deny-by-default, enforced at two boundaries |
| Allowlist gap — a wildcard or an unlisted destination | network | signed, explicit allowlist |
| No network policy at all | network | the simplest leak: read anything, exfiltrate anything |
| Agent-created persistence — a shell rc file written once runs forever | filesystem | "no agent-created persistence", mutable only from the control plane |

The last row is the subtlest. A `.bashrc` or hook written during one task
executes on every future session, independent of any prompt — a persistent
backdoor that outlives the agent. NVIDIA's invariants name it explicitly
("no agent-created persistence", "no suppressed audit"), which is the same
audit the demo performs at mechanism scale.

## The filesystem as an interface (a boundary worth knowing)

One more shape is emerging: making the filesystem itself programmable via
FUSE, so an agent's most reliable capability — file I/O — reaches things
that are not files. BranchFS gives every directory copy-on-write branch
semantics, so an agent can fork the world, experiment, and fold back only
what worked; AgentFS exposes agent state (memory, tasks) as a POSIX tree
([fuse-and-the-filesystem-interface](fuse-and-the-filesystem-interface/)).
A branch is a checkpoint with a name — which is the exact handoff to the
next stage.

## What this stage does and does not establish

It establishes the mechanism: three independent layers, the two ways the
mission's own demo leaks, and the industrial gradient from process to
microVM with the failure classes each layer must survive. The mechanism is
verified by a real recorded run; the production claims are dated surveys
with sources cited.

It does not claim the demo sandbox is production-safe — it is 200 lines of
policy checks on a laptop, with no kernel enforcement, and the chapter says
so. And it does not claim any single boundary is always right: the threat
model decides, which is exactly why the three layers exist as separate
decisions in the first place.

**Next:** the sandbox exists, but the process inside it can crash, be
preempted, or lose its session — [runtime and durability](../runtime-and-durability/).
