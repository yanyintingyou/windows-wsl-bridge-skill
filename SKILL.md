---
name: windows-wsl-bridge
description: Use when a Windows-hosted coding agent needs to inspect, read, write, or run commands in a user's WSL Linux distribution without pretending Windows and WSL are the same environment.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [windows, wsl, bridge, codex, sandbox, filesystem]
    related_skills: [safety-guard, systematic-debugging]
---

# Windows WSL Bridge

## Overview

This skill is for an agent that is running on Windows but needs to operate inside a user's WSL Linux distribution. The common case is a Windows desktop coding agent that can see Windows files and can invoke `wsl.exe`, while the actual Linux tools, services, user files, or development environment live inside WSL.

The examples use a distribution named `Ubuntu-24.04`, Windows user `LTY`, and Linux user `lty` only as local examples. Do not assume those names on another machine. Always discover the distribution name, active user, paths, and sandbox policy before making changes.

## When to Use

Use this skill when:

- A Windows-hosted agent must run Linux commands through WSL.
- A Windows agent must read or edit files that live inside a WSL distribution.
- A task spans Windows workspace files under `/mnt/<drive>/...` and Linux tools inside WSL.
- A sandboxed Windows agent cannot see the user's WSL distribution even though it exists for the interactive Windows account.
- You need to explain exactly which side of the Windows/WSL boundary a command touches.

Do not use this skill for:

- Native Linux agents already running inside WSL.
- Remote SSH machines that are not the user's local WSL distribution.
- Direct virtual-disk repair or filesystem forensics. Those require a separate recovery workflow.

## Core Guardrails

- Treat WSL as the user's real Linux environment, not as a disposable sandbox.
- Start with read-only discovery before any write, package, service, network, or permission action.
- Never claim WSL is absent until you have checked whether the Windows agent is running under a sandboxed Windows identity.
- Prefer ordinary user access. Use elevated Linux access only when the user explicitly approves a system-level task.
- Show or verify the exact target path before writing across the Windows/WSL boundary.
- Do not print credential material, full environment dumps, private key material, token files, or authentication stores.
- Do not modify credential stores, agent configuration directories, user configuration directories, or system directories unless the user explicitly approves the exact target and you have a backup plan.
- Do not run broad recursive delete, move, ownership, or mode-changing operations.
- Do not directly manipulate WSL virtual disk files.
- Before changing services, inspect service status, recent logs, and the relevant configuration file.
- Before changing DNS, proxy, or WSL boot settings, inspect current network symptoms and existing configuration.

## Discovery Workflow

Run these checks from the Windows agent side before deciding how to operate:

```powershell
wsl.exe --list --all --verbose
wsl.exe --status
```

Then run a read-only identity and system check using the discovered distribution name:

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc "whoami; pwd; uname -a"
```

If WSL is visible to the user in normal PowerShell but not visible to the agent, check whether the agent executes commands under a managed or sandboxed Windows account. In that case, request approval for the specific `wsl.exe` command outside the sandbox rather than assuming the distribution is missing.

Record these facts before writing:

- Distribution name, state, and WSL version.
- Windows account or sandbox identity used by the agent.
- Linux username returned by WSL.
- Current working directory on both sides of the boundary.
- Whether the target file is on the Windows filesystem, inside the Linux filesystem, or reached through a UNC path.

## Access Patterns

### Run Commands In WSL

Use the exact distribution name from discovery:

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc "cd /home/lty/project && python3 script.py"
```

Keep commands short. For complex logic, prefer a reviewed script file in the target workspace, then invoke that script through WSL. This avoids fragile quoting between PowerShell and Bash.

### Read WSL Files From Windows

Use the WSL UNC path for normal user-owned files:

```powershell
Get-Content "\\wsl.localhost\Ubuntu-24.04\home\lty\file.md"
```

Use this for inspection and small edits when the Windows-side agent is better at editing files. Do not operate on WSL's backing virtual-disk file directly.

### Write WSL Files From Windows

For small writes from Windows, target one explicit file and read it back:

```powershell
Set-Content "\\wsl.localhost\Ubuntu-24.04\home\lty\agent-write-check\README.md" "# WSL write check"
Get-Content "\\wsl.localhost\Ubuntu-24.04\home\lty\agent-write-check\README.md"
```

For multi-file or code-generating writes, prefer writing from inside WSL so Linux permissions, line endings, and tooling behavior match the target project.

### Let WSL Access Windows Workspace Files

WSL usually exposes Windows drives under `/mnt`. This is often the cleanest shared-workspace pattern:

```bash
cd /mnt/c/Users/LTY/Desktop/Software/codex_workspace
```

Use this when Windows Codex edits files in a Windows workspace and WSL tools such as Python, Git, or Hermes need to inspect or execute those files.

### Convert Paths Explicitly

When reporting or planning work, translate paths rather than mixing them implicitly:

- Windows path example: `C:\Users\LTY\Desktop\project`
- WSL mount path example: `/mnt/c/Users/LTY/Desktop/project`
- WSL UNC path example: `\\wsl.localhost\Ubuntu-24.04\home\lty\project`
- Linux home path example: `/home/lty/project`

## Permission Model

Default to the normal Linux user returned by the discovery command. That is sufficient for project files, files under the user's Linux home directory, and Windows workspace files under `/mnt/<drive>/...`.

Use elevated Linux access only for clearly system-level work, such as changing WSL boot configuration, installing system packages, or editing root-owned service files. Do not probe for or rely on unattended elevation unless the user has explicitly requested that path.

If a task appears to need elevated access, pause and report:

- The exact file, service, or setting that requires it.
- Why ordinary user access is insufficient.
- The safer read-only command already used to confirm the need.
- The backup or rollback plan.

## Safe Write Pattern

For any write across the Windows/WSL boundary:

1. State the target side: Windows filesystem, WSL Linux filesystem, or UNC path.
2. Print or derive the exact path.
3. Create parent directories only when they are task-specific and narrow.
4. Write only the requested file or a small explicit set of files.
5. Read the changed file back.
6. Verify ownership, permissions, or line endings when relevant.
7. Report exactly what changed.

Example from Windows into WSL:

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc "python3 - <<'PY'
from pathlib import Path
p = Path('/home/lty/agent-write-check/README.md')
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text('# WSL write check\n', encoding='utf-8')
print(p)
print(p.read_text(encoding='utf-8'))
PY"
```

## Common Pitfalls

1. **Wrong distribution name.** Use the exact name printed by `wsl.exe --list --all --verbose`.
2. **Sandbox identity mismatch.** A desktop agent may run as a managed Windows identity that cannot see distributions registered under the user's interactive account.
3. **Quoting confusion.** PowerShell may expand variables or command-substitution syntax before Bash receives the command. Simplify the command or use a reviewed script.
4. **Wrong side of the filesystem.** Check whether the target is `/home/...`, `/mnt/c/...`, or `\\wsl.localhost\...` before writing.
5. **Network diagnosis shortcut.** If WSL tools cannot reach the web while local commands work, inspect DNS, proxy, VPN, and routing symptoms before blaming the application.
6. **Line-ending mismatch.** Windows-side writes can introduce line endings that break shell scripts. Verify or normalize when writing scripts.
7. **Overbroad cleanup.** Never run sweeping cleanup commands across home directories, mounted drives, or system directories.

## Verification Checklist

- [ ] Distribution name came from live discovery, not from an assumption.
- [ ] The agent's Windows identity or sandbox context was considered.
- [ ] Linux username and current directory were checked before writes.
- [ ] The target path was classified as Windows, WSL Linux, UNC, or mounted Windows path.
- [ ] No credential material or authentication store was printed.
- [ ] Elevated access was avoided or explicitly justified and approved.
- [ ] Changed files were read back after writing.
- [ ] The final report names the distribution, user, touched paths, commands run, and any approvals required.

## Output Discipline

When reporting WSL work, include:

- Distribution name used.
- Linux user used and whether elevated access was used.
- Exact paths touched, with Windows and WSL forms when useful.
- What was read, written, or executed.
- Any command that required sandbox-external approval.
- Sensitive files or values deliberately not displayed.
