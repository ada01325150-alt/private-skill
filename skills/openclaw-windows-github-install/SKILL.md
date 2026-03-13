---
name: openclaw-windows-github-install
description: Use when a task is to quickly install OpenClaw on Windows, first detect whether WSL2 is already available, bootstrap WSL2 and Ubuntu when missing, then install OpenClaw only from the official GitHub repository with explicit Windows admin and WSL sudo permission handling.
version: "1.0.0"
---

# openclaw-windows-github-install

Version: `1.0.0`

## Use this skill when

- The user wants a fast Windows install path for `OpenClaw`.
- The workflow must detect `WSL2` first.
- `WSL2` should be installed automatically when missing.
- `OpenClaw` must come from the official GitHub repository, not an unofficial mirror.
- Permission handling is important, especially Windows elevation and WSL `sudo`.

## Do not use this skill when

- The machine is not Windows.
- The user asks to install from a third-party package, mirror, or repacked archive.
- Browser login, account binding, or post-install channel setup is the main goal.

## Source policy

- Official repository only: `https://github.com/openclaw/openclaw.git`
- Install instructions must be taken from the cloned official repo or its repo-contained installer files.
- Do not replace the official GitHub source with a mirror, blog attachment, or unverified zip.

## Permission rules

- Installing or enabling `WSL2` on Windows requires an elevated PowerShell session.
- If `WSL2` is already ready, do not request Windows admin unnecessarily.
- Installing Linux packages inside WSL may require `sudo`; warm up with `sudo -v` before `apt-get`.
- If the Ubuntu first-run user has not been created yet, stop and ask the user to finish the initial WSL account setup, then rerun.
- If Windows asks for a reboot after `wsl --install`, stop and resume after reboot instead of forcing the next steps.

## Quick start

Run the bundled PowerShell entrypoint on the Windows host:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-openclaw-windows.ps1
```

Optional flags:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-openclaw-windows.ps1 -Distro Ubuntu
powershell -ExecutionPolicy Bypass -File .\scripts\install-openclaw-windows.ps1 -RepoDir "$env:USERPROFILE\openclaw-src"
powershell -ExecutionPolicy Bypass -File .\scripts\install-openclaw-windows.ps1 -SkipOpenClawInstall
```

## Workflow

### 1. Detect Windows + WSL2 state

- Run `scripts/install-openclaw-windows.ps1`.
- The script checks `wsl.exe`, `wsl --status`, and `wsl -l -q`.
- If no usable WSL distro exists, it relaunches itself with elevation and runs `wsl --install -d <Distro>`.

### 2. Stop at the right boundary

- If `wsl --install` reports a reboot or the distro still needs first-launch account creation, stop there.
- Tell the user to reboot, open Ubuntu once, finish the Linux username/password setup, then rerun the same script.

### 3. Install OpenClaw from official GitHub only

- After WSL is ready, the script calls `scripts/install-openclaw-from-github-wsl.sh` inside WSL.
- That script ensures `git` and `curl` are present, cloning or updating only `https://github.com/openclaw/openclaw.git`.
- It prints the remote URL and commit hash before installation.

### 4. Prefer repo-contained installer files

- The WSL script looks for installer entrypoints in this order:
  - `install.sh`
  - `scripts/install.sh`
- If neither file exists, stop and read `README.md` from the cloned official repo, then execute only the repo-documented official install command.
- Do not invent an unofficial install path just to keep going.

### 5. Validate source and result

- Keep the printed `origin` and `commit` in the handoff.
- If the repo contains a documented health check, run that.
- Otherwise, report that the source was cloned successfully and note which official installer path was used.

## Files

- `scripts/install-openclaw-windows.ps1`: Windows entrypoint with WSL detection, elevation, reboot gating, and WSL invocation.
- `scripts/install-openclaw-from-github-wsl.sh`: WSL-side installer that clones the official repo and runs repo-contained installers.
- `references/permissions-and-sources.md`: exact permission model and source constraints.
- `references/test-cases-v1.0.0.md`: trigger prompts, expected decisions, and sample invocations.

## Handoff format

- `WSL state`: installed or bootstrapped
- `Distro`: selected distro name
- `Source`: exact `origin` URL
- `Commit`: exact Git commit used
- `Installer path`: `install.sh`, `scripts/install.sh`, or `README.md` fallback
- `Blocked by`: reboot needed, Ubuntu first-run needed, or `sudo` credentials missing
