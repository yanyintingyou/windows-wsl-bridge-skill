# Windows WSL Bridge Skill

[简体中文](README.zh-CN.md) | English

`windows-wsl-bridge` is a reusable agent skill for Windows-hosted coding agents that need to inspect, read, write, or run commands inside a user's WSL Linux distribution safely.

The core use case is a Windows desktop agent, such as a local coding assistant, that can access Windows files and invoke `wsl.exe`, while the required Linux tooling or user workspace lives inside WSL.

> Note: examples use `Ubuntu-24.04`, Windows user `LTY`, and Linux user `lty` as local placeholders. Verify the real distribution name, users, paths, and sandbox behavior before applying commands on another machine.

## What It Covers

- Discovering WSL distributions from Windows.
- Running commands through `wsl.exe -d <DistroName> -- ...`.
- Reading and writing WSL files through `\\wsl.localhost\<DistroName>\...`.
- Letting WSL tools operate on Windows workspace files under `/mnt/<drive>/...`.
- Handling Windows-agent sandbox identity mismatches.
- Avoiding unsafe filesystem, service, network, and credential-handling mistakes.

## Skill Layout

```text
windows-wsl-bridge-skill/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── LICENSE
├── agents/
│   └── openai.yaml
└── tests/
    └── test_skill_integrity.py
```

## Installation

Install or copy the folder containing `SKILL.md` into the skills directory used by your agent. For a Codex-style local skill, the final directory should contain `SKILL.md` at its root.

If your agent supports GitHub-hosted skills, point it at this repository or copy the folder into the configured skills path.

## Quick Start

List WSL distributions:

```powershell
wsl.exe --list --all --verbose
```

Run a read-only check inside a discovered distribution:

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc "whoami; pwd; uname -a"
```

Read a WSL file from Windows:

```powershell
Get-Content "\\wsl.localhost\Ubuntu-24.04\home\lty\README.md"
```

Run a Linux tool against a Windows workspace:

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc "cd /mnt/c/Users/LTY/Desktop/Software/codex_workspace && pwd"
```

## Security Model

Start with read-only discovery. Use the ordinary Linux user for project work. Use elevated Linux access only for a clearly system-level task and only after the user approves the exact target and rollback plan.

Do not display credential material, full environment dumps, private key material, token files, or authentication stores. Do not directly modify WSL's backing virtual-disk file.

## Validation

Run the lightweight integrity test from the repository root:

```bash
python3 tests/test_skill_integrity.py
```

If you are validating inside Hermes, also run the Hermes skill security scanner against a Linux filesystem copy of the skill. Windows-mounted files may appear executable from WSL depending on mount options, which can create local false positives.

## License

MIT. See `LICENSE`.
