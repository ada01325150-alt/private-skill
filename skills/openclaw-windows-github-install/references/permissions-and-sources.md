# Permissions and sources

## Official sources

- OpenClaw GitHub repository: `https://github.com/openclaw/openclaw.git`
- Windows WSL documentation: `https://learn.microsoft.com/windows/wsl/install`

## Windows permission model

- `wsl --install` and enabling Windows virtualization features may require an elevated PowerShell session.
- The PowerShell entry script only self-elevates when Windows-side WSL setup is required.
- If WSL is already available, stay in the current non-admin session and continue with the WSL-side install.

## WSL permission model

- `apt-get update` and package installation require `sudo` on Ubuntu.
- Call `sudo -v` before package installation so the password prompt happens at a predictable point.
- If the Linux account is not in `sudoers`, stop and report that instead of retrying blindly.

## Stop conditions

- `wsl --install` completed but Windows requests a reboot.
- The target distro is installed but the initial Linux user has not been created yet.
- `sudo -v` fails.
- The cloned repo does not contain a recognized installer file and the agent has not yet read the repo `README.md`.

## Source integrity checks

- Print `git remote get-url origin` and ensure it matches `https://github.com/openclaw/openclaw.git`.
- Print `git rev-parse HEAD` before running the installer.
- Do not swap to forks, mirrors, release reposts, or blog-provided archives.
