# The minimal sandbox, six real tool calls, no model in the loop

Mechanism demo for the execution-environment stage: three policy layers
(filesystem, network, approval) in front of `subprocess.run`, exercised
with six real tool calls including two deliberate escape attempts.

## Command

```bash
cd 04-agentic-platform/execution-environment/a-minimal-sandbox/core
python3 mini_sandbox.py --workdir /tmp/sbx-demo-run --out records.jsonl \
  -- python3 -c "print('hello from sandbox')"
python3 mini_sandbox.py --workdir /tmp/sbx-demo-run --out records.jsonl \
  -- curl http://example.com
python3 mini_sandbox.py --workdir /tmp/sbx-demo-run --out records.jsonl \
  -- rm -rf /tmp
python3 mini_sandbox.py --workdir /tmp/sbx-demo-run --out records.jsonl \
  -- python3 -c "open('/tmp/pwn.txt','w').write('x')"
python3 mini_sandbox.py --workdir /tmp/sbx-demo-run --allow-destructive \
  --out records.jsonl -- python3 -c "print('approved')"
python3 mini_sandbox.py --workdir /tmp/sbx-demo-run --out records.jsonl \
  -- python3 -c "print('escape: '+open('/etc/hostname').read())"
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS arm64 |
| Python | 3.11 (system) |
| Model | none — policy checks only, no API key, no network |
| Cost | \$0 |

## Results

Full records: [2026-08-14-minimal-sandbox.jsonl](2026-08-14-minimal-sandbox.jsonl)

| Command | Layer | Allowed | Note |
|---|---|---|---|
| `python3 -c "print('hello from sandbox')"` | allowed | yes | exit 0 |
| `curl http://example.com` | network | no | network command blocked |
| `rm -rf /tmp` | filesystem | no | path outside workdir |
| `python3 -c "open('/tmp/pwn.txt','w').write('x')"` | allowed | **yes** | escape: argv check cannot see `-c` code; `/tmp/pwn.txt` created |
| `python3 -c "print('approved')"` with `--allow-destructive` | allowed | yes | approval layer honours the sandbox flag |
| `python3 -c "print('escape: '+open('/etc/hostname').read())"` | allowed | **yes** | escape: read path inside code string; failed only because `/etc/hostname` is absent |

## Reading the two escapes

Both escapes were admitted by the **filesystem** layer, which inspects argv
and cannot see code inside `-c` strings. The network layer would refuse
`curl` even if the filesystem layer passed it, and the approval layer would
refuse `rm` without the flag — but a code string that opens a path is
invisible to all three. This is the demo's point: a sandbox is the union of
its layers, and static argv inspection is not code inspection. Production
sandboxes enforce at the kernel or proxy boundary for exactly this reason.

## Honesty note

This is a mechanism demo, not production isolation. macOS provides no
seccomp/LSM to the demo, so the layers are policy checks; a determined
escape from `mini_sandbox.py` is trivial. The record is real but the claims
it supports are about the shape of sandbox design, not about the security
of this script.
