# Test cases v1.0.0

## Goal

Make invocation of `openclaw-windows-github-install` more reliable by giving the agent clear trigger prompts, expected decisions, and concise sample calls.

## Recommended trigger prompts

- 帮我在 Windows 上快速安装 OpenClaw，先检查有没有 WSL2，没有就装，有就直接装 OpenClaw，只能用 GitHub 官方仓库。
- 用这个 skill 检查我的 Windows 环境，如果没有 WSL2 就自动安装 Ubuntu 和 WSL2，然后从官方 GitHub 安装 OpenClaw。
- 请处理好权限问题：Windows 需要管理员时自动提升，WSL 里需要 sudo 时先验证，再安装 OpenClaw。
- 在 Windows 上安装 OpenClaw，必须先确认 WSL2，不能用第三方镜像、压缩包或博客附件。

## Expected behavior

### Case 1: WSL2 missing

Expected actions:
- Detect that `wsl.exe` is missing or no usable distro exists.
- Relaunch in elevated PowerShell only for WSL bootstrap.
- Run `wsl --install -d Ubuntu`.
- Stop cleanly if Windows requests a reboot.
- Tell the user to open Ubuntu once and finish first-run username/password creation.
- After rerun, continue with the GitHub-based OpenClaw install.

Expected handoff:
- `WSL state: bootstrapped`
- `Blocked by: reboot needed` or `Blocked by: Ubuntu first-run needed`

### Case 2: WSL present, distro exists, not version 2

Expected actions:
- Detect the existing distro.
- Run `wsl --set-version <Distro> 2`.
- Continue only after version 2 is ready.
- Avoid unnecessary Windows admin prompts if no Windows-side bootstrap is needed.

Expected handoff:
- `WSL state: installed`
- `Distro: <name>`
- `Blocked by: none`

### Case 3: WSL ready, OpenClaw install begins

Expected actions:
- Enter WSL and run `sudo -v` before package installation.
- Ensure `git` and `curl` are available.
- Clone or update only `https://github.com/openclaw/openclaw.git`.
- Print `origin` and `commit`.
- Run `install.sh` or `scripts/install.sh` if present.
- If no installer file exists, stop at `README.md` instead of inventing an unofficial path.

Expected handoff:
- `Source: https://github.com/openclaw/openclaw.git`
- `Commit: <sha>`
- `Installer path: install.sh | scripts/install.sh | README.md`

### Case 4: Permission problem inside WSL

Expected actions:
- Fail early on `sudo -v`.
- Do not retry package installation blindly.
- Tell the user the current Linux account lacks usable sudo privileges.

Expected handoff:
- `Blocked by: sudo credentials missing`

## Example invocation strings

### Minimal

```text
Use $openclaw-windows-github-install to install OpenClaw on Windows: check WSL2 first, install WSL2 and Ubuntu if missing, otherwise install OpenClaw directly from the official GitHub repo, and handle Windows admin plus WSL sudo permissions carefully.
```

### Chinese natural language

```text
用 $openclaw-windows-github-install 帮我在 Windows 上快速安装 OpenClaw：先检测有没有 WSL2，没有就安装 Ubuntu + WSL2，有的话直接继续安装 OpenClaw；整个过程只允许使用 GitHub 官方仓库 https://github.com/openclaw/openclaw.git，并特别注意管理员权限和 sudo 权限问题。
```

### With a custom repo directory

```text
Use $openclaw-windows-github-install and keep the cloned repo under C:\\Users\\me\\openclaw-src. Detect WSL2 first, bootstrap it if missing, then install OpenClaw only from the official GitHub repository.
```
