#!/usr/bin/env bash
set -euo pipefail

repo_url="${1:-https://github.com/openclaw/openclaw.git}"
repo_dir="${2:-$HOME/openclaw-src}"

case "$repo_dir" in
  '$HOME'*)
    repo_dir="${repo_dir/'$HOME'/$HOME}"
    ;;
  '~'*)
    repo_dir="$HOME${repo_dir#\~}"
    ;;
esac

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit "${2:-1}"
}

require_sudo() {
  command -v sudo >/dev/null 2>&1 || fail "sudo 不可用，无法安装 WSL 内依赖。" 20
  sudo -v || fail "sudo 验证失败，请确认当前 Linux 账号具备 sudo 权限。" 21
}

ensure_packages() {
  local missing=0
  command -v git >/dev/null 2>&1 || missing=1
  command -v curl >/dev/null 2>&1 || missing=1

  if [[ "$missing" -eq 1 ]]; then
    require_sudo
    sudo apt-get update
    sudo apt-get install -y git curl
  fi
}

clone_or_update_repo() {
  mkdir -p "$(dirname "$repo_dir")"

  if [[ -d "$repo_dir/.git" ]]; then
    git -C "$repo_dir" remote set-url origin "$repo_url"
    git -C "$repo_dir" fetch --all --tags --prune
    git -C "$repo_dir" pull --ff-only
  elif [[ -e "$repo_dir" ]]; then
    fail "目标路径已存在但不是 Git 仓库: $repo_dir" 22
  else
    git clone "$repo_url" "$repo_dir"
  fi
}

run_repo_installer() {
  cd "$repo_dir"

  local origin
  local commit
  origin="$(git remote get-url origin)"
  commit="$(git rev-parse HEAD)"

  printf 'origin=%s\n' "$origin"
  printf 'commit=%s\n' "$commit"

  [[ "$origin" == "https://github.com/openclaw/openclaw.git" ]] || fail "origin 不匹配官方 GitHub 仓库。" 23

  if [[ -x "./install.sh" || -f "./install.sh" ]]; then
    printf 'installer_path=install.sh\n'
    bash ./install.sh
    return 0
  fi

  if [[ -x "./scripts/install.sh" || -f "./scripts/install.sh" ]]; then
    printf 'installer_path=scripts/install.sh\n'
    bash ./scripts/install.sh
    return 0
  fi

  if [[ -f "./README.md" ]]; then
    printf 'installer_path=README.md\n'
    printf '未发现 repo 内安装脚本。请先阅读官方仓库 README.md，并执行其中记录的官方安装命令。\n' >&2
    exit 24
  fi

  fail "官方仓库内未找到已知安装入口。" 25
}

ensure_packages
clone_or_update_repo
run_repo_installer
