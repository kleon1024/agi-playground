---
status: unverified
---

# Local lane — RTX 4090 via Tailscale + WSL2

This is the default compute lane for agi-playground: a Mac (or any) dev box
reaching a Windows 11 machine with an RTX 4090, over Tailscale, into a WSL2
Ubuntu environment where all the actual training/inference code runs. It
fits everything in the curriculum except the multi-GPU labs (see
[`modal.md`](modal.md) for those).

The remote-dev setup itself is teachable content, not a footnote: this
document is written so that any reader with a consumer GPU and a Windows
box can reproduce the topology.

> **Status: unverified.** The steps below are the intended setup. No
> command output in this document has been recorded from a real run yet.
> Verification attempted 2026-07-24: Tailscale connected from the dev box,
> but the Windows/WSL2 machine was offline in the tailnet (last seen 94
> days prior), so the SSH + CUDA smoke test could not run. This notice and
> the frontmatter flip to `verified` once the smoke test output is recorded.

## Target topology

```
┌─────────────────┐         Tailscale          ┌───────────────────────────┐
│  Mac dev box     │ ───────────────────────►  │  Windows 11 host          │
│  (editor, CLI,   │        (WireGuard mesh,    │  RTX 4090 (24GB)          │
│   VS Code)       │         no port forwarding)│  └─ WSL2: Ubuntu          │
└─────────────────┘                             │      └─ CUDA + uv + repo │
                                                 └───────────────────────────┘
```

The Mac never talks to Windows directly over the open internet — Tailscale
puts both machines on the same private mesh network, and all SSH traffic
rides that tunnel. Inside Windows, WSL2 Ubuntu is where the repo actually
lives and runs; the GPU is passed through from Windows into WSL2 by the
NVIDIA driver stack (see pitfalls below).

## Setup checklist

- [ ] **Tailscale on both ends.** Install Tailscale on the Mac and on the
      Windows host, sign both into the same tailnet. Confirm the Windows
      host shows up in `tailscale status` from the Mac and resolves via
      its tailnet hostname (e.g. `windows-4090`) or 100.x Tailscale IP.
- [ ] **SSH reachability into WSL2.** Either:
  - Run `sshd` inside WSL2 Ubuntu directly, and configure a Windows
    `netsh interface portproxy` rule that forwards a Windows port (e.g.
    2222) to the WSL2 VM's internal IP and port 22, since WSL2's networking
    is NAT'd behind Windows by default; or
  - Use **Tailscale SSH** (enable it in the Tailscale admin console and via
    `tailscale up --ssh` on the box actually running `sshd`), which
    sidesteps manual port forwarding by handling auth and routing at the
    Tailscale layer.
- [ ] **Key-based auth.** Generate an SSH key pair on the Mac, add the
      public key to WSL2 Ubuntu's `~/.ssh/authorized_keys`, and disable
      password auth once key auth is confirmed working.
- [ ] **`uv` + CUDA PyTorch in WSL2.** Install `uv` inside WSL2 Ubuntu, then
      use it to create the project environment and install a CUDA-enabled
      PyTorch build matching the GPU driver's supported CUDA version.
- [ ] **Smoke test.** From inside the WSL2 environment, run:

      ```bash
      python -c "import torch; print(torch.cuda.get_device_name(0))"
      ```

      Expected output:

      ```
      NVIDIA GeForce RTX 4090
      ```

      This confirms the GPU is visible end-to-end: Windows driver → WSL2
      GPU passthrough → CUDA → PyTorch. Recording this output for real is
      the acceptance bar for flipping this doc's `status` to verified.

## VS Code / CLI remote-dev notes

- VS Code's Remote-SSH extension can target the WSL2 host directly using
  the same SSH config entry set up above (host, port, key) — point it at
  the WSL2 `sshd`/portproxy endpoint or the Tailscale SSH hostname, not at
  Windows' own OpenSSH server, so the editor lands inside the Ubuntu
  environment where the repo and CUDA toolchain live.
- For a CLI-only workflow, an `~/.ssh/config` entry with `HostName`,
  `Port`, `User`, and `IdentityFile` set once makes every subsequent
  `ssh <alias>` (and any tool that shells out to SSH) work without
  repeating connection details.
- Keep the repo checkout on the WSL2 side; treat the Mac purely as a thin
  client for editing and running commands remotely.

## Common WSL2 pitfalls

- **GPU driver passthrough is Windows-side.** The NVIDIA driver is
  installed on Windows, not inside WSL2 — WSL2 uses that host driver via
  a special passthrough path. Do not install a separate Linux NVIDIA
  driver inside WSL2; doing so breaks the passthrough. Driver updates
  happen on the Windows side only.
- **Clock drift after sleep.** WSL2's internal clock can drift or freeze
  when the Windows host sleeps/resumes, which can produce confusing
  symptoms (SSH auth failures, TLS errors, odd timestamps in logs). If
  something inexplicable breaks right after a laptop/desktop sleep cycle,
  resync the WSL2 clock (e.g. `sudo hwclock -s` or restarting the WSL2
  instance) before debugging further.
- **Filesystem performance: keep data on ext4, not `/mnt/c`.** Files
  accessed through the `/mnt/c/...` Windows-filesystem bridge are much
  slower than the native WSL2 ext4 filesystem, especially for the small
  random-access I/O patterns common in data loading and checkpointing.
  Keep the repo, datasets, and checkpoints inside the WSL2 Linux
  filesystem (e.g. under `~/`), and use `/mnt/c` only for occasional
  interchange with Windows-side tools.
