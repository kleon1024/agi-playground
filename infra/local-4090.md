---
status: verified
verified: 2026-07-24
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

> **Status: verified 2026-07-24.** The full path — Mac → Tailscale → WSL2 →
> CUDA → PyTorch — was exercised end-to-end over SSH. Recorded output is in
> [Verification record](#verification-record) below.

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
- [ ] **SSH reachability into WSL2.** Pick one of three approaches:
  - **Tailscale inside WSL2 (simplest, and what the verification run used).**
    Install Tailscale in the WSL2 Ubuntu instance itself and join the tailnet
    from there, so WSL2 is its own tailnet node with its own 100.x address.
    Run `sshd` inside WSL2 and connect straight to that address — no Windows
    port forwarding involved at all. If WSL2 has no systemd, start the daemon
    in userspace-networking mode
    (`tailscaled --tun=userspace-networking`), which still accepts inbound
    connections by proxying them to local ports.
  - **Tailscale on Windows + portproxy.** Join the tailnet on the Windows
    host, run `sshd` inside WSL2, and add a `netsh interface portproxy` rule
    forwarding a Windows port (e.g. 2222) to the WSL2 VM's internal IP on
    port 22, since WSL2 networking is NAT'd behind Windows by default.
    **Caveat:** the WSL2 VM's internal IP is dynamic and typically changes on
    every reboot, so a static portproxy rule silently breaks after a restart —
    script the rule's re-creation at boot, or prefer the first approach.
  - **Tailscale SSH** (`tailscale up --ssh`, plus an SSH rule in the tailnet
    ACL). This is an *alternative* to running a traditional `sshd`, not a
    layer on top of one: `tailscaled` itself terminates the SSH session and
    handles authentication via tailnet identity, so there are no host keys or
    `authorized_keys` to manage.
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

## Verification record

Run 2026-07-24 from a macOS dev box over Tailscale SSH into WSL2 Ubuntu
(kernel `6.6.87.2-microsoft-standard-WSL2`), environment created with
`uv venv --python 3.12` + `uv pip install torch`:

```
$ /usr/lib/wsl/lib/nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
NVIDIA GeForce RTX 4090, 24564 MiB, 591.86

$ .venv/bin/python smoke.py
torch 2.13.0+cu130
cuda available: True
device: NVIDIA GeForce RTX 4090
capability: (8, 9)
vram_gb: 25.8
bf16 matmul TFLOP/s: 138.8
```

The last line is a 4096×4096 bf16 matmul loop (50 iterations, synchronized).
At ~139 TFLOP/s it lands near the expected fraction of the card's dense bf16
peak — a useful one-line regression check that the lane is not silently
running degraded (thermal throttling, a driver regression, or CPU-bound
dispatch would all show up here as a large drop).

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

- **Nothing you start by hand survives a WSL restart.** This is the one that
  will actually cost you hours. WSL2 ships without systemd, so a `tailscaled`
  or `sshd` you launched manually has no supervisor: restarting WSL — or
  Windows sleeping, which suspends WSL with it — kills both, permanently. The
  machine then sits in a state that looks like a network fault from the far
  end: the tailnet still lists the peer, but `tx` climbs while `rx` stays
  frozen, because packets go out and nothing answers. Restarting WSL again does
  not fix it; restarting WSL is what caused it.

  Make it persistent instead of restarting it by hand:

  ```bash
  printf '[boot]\nsystemd=true\n' | sudo tee -a /etc/wsl.conf
  # from Windows PowerShell:
  wsl --shutdown
  # reopen WSL, then:
  sudo systemctl enable --now tailscaled ssh
  ```

  Diagnose it from the client side with `tailscale status`: a peer that is
  registered but unreachable shows `offline, last seen <n> ago` with a rising
  `tx` and a static `rx`. That pattern means the daemon is gone, not that the
  network is broken. Check the *whole* peer list too — if the node re-registered
  under a different hostname you will be pinging a stale address.


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
- **`nvidia-smi` is not on the non-interactive SSH `PATH`.** The WSL2 GPU
  tooling lives in `/usr/lib/wsl/lib`, which login shells add to `PATH` but
  a non-interactive `ssh host "nvidia-smi ..."` command does not inherit.
  The bare command then fails with `command not found` even though the GPU
  is perfectly healthy — an easy false alarm when scripting remote checks.
  Use the absolute path `/usr/lib/wsl/lib/nvidia-smi`, or wrap remote
  commands in `bash -lc "..."` to get a login shell. PyTorch is unaffected:
  it loads `libcuda.so` from that directory through the linker
  configuration, not through `PATH`.
- **A bare `torch` install has no NumPy.** Installing only `torch` produces
  a working CUDA stack that still prints
  `UserWarning: Failed to initialize NumPy` on first tensor conversion.
  Harmless for pure-GPU work, but install `numpy` alongside `torch` to keep
  the warning out of run logs, since noisy logs make real failures easier to
  miss.
