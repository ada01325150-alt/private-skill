[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu",
    [string]$RepoUrl = "https://github.com/openclaw/openclaw.git",
    [string]$RepoDir = '$HOME/openclaw-src',
    [switch]$SkipOpenClawInstall,
    [switch]$ForceWslBootstrap,
    [switch]$Elevated
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-IsWindowsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Split-ArgsForRelaunch {
    param([string[]]$ArgsToSplit)

    $quoted = foreach ($item in $ArgsToSplit) {
        if ($item -match '[\s"]') {
            '"{0}"' -f ($item -replace '"', '""')
        } else {
            $item
        }
    }

    return ($quoted -join ' ')
}

function Get-WslInventory {
    $inventory = [ordered]@{
        HasWslCommand = $false
        StatusText = ''
        RawList = @()
        RawVerboseList = @()
        Distros = @()
        DistroVersions = @{}
        HasVersion2Hint = $false
    }

    $wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if (-not $wsl) {
        return [pscustomobject]$inventory
    }

    $inventory.HasWslCommand = $true

    try {
        $statusOutput = & wsl.exe --status 2>&1
        if ($LASTEXITCODE -eq 0 -or $statusOutput) {
            $inventory.StatusText = ($statusOutput | Out-String).Trim()
            if ($inventory.StatusText -match 'Default Version:\s*2' -or $inventory.StatusText -match '默认版本[:：]\s*2') {
                $inventory.HasVersion2Hint = $true
            }
        }
    } catch {
    }

    try {
        $listOutput = & wsl.exe -l -q 2>&1
        if ($LASTEXITCODE -eq 0) {
            $inventory.RawList = @($listOutput)
            $inventory.Distros = @($listOutput | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        }
    } catch {
    }

    try {
        $verboseOutput = & wsl.exe -l -v 2>&1
        if ($LASTEXITCODE -eq 0) {
            $inventory.RawVerboseList = @($verboseOutput)
            foreach ($line in $verboseOutput) {
                $normalized = ($line -replace [char]0, '').Trim()
                if (-not $normalized -or $normalized -match '^NAME\s+STATE\s+VERSION$') {
                    continue
                }

                $normalized = $normalized.TrimStart('*').Trim()
                if ($normalized -match '^(?<name>.+?)\s{2,}(?<state>\S+)\s+(?<version>\d+)$') {
                    $inventory.DistroVersions[$matches.name.Trim()] = [int]$matches.version
                }
            }
        }
    } catch {
    }

    return [pscustomobject]$inventory
}

function Ensure-Wsl2Version {
    param(
        [string]$TargetDistro,
        [hashtable]$DistroVersions
    )

    if (-not $DistroVersions.ContainsKey($TargetDistro)) {
        return
    }

    if ($DistroVersions[$TargetDistro] -eq 2) {
        return
    }

    Write-Host "$TargetDistro 当前不是 WSL2，正在尝试切换到版本 2。"
    & wsl.exe --set-version $TargetDistro 2

    if ($LASTEXITCODE -ne 0) {
        throw "无法将 $TargetDistro 切换到 WSL2，请检查虚拟化与 Windows 可选组件状态。"
    }
}

function Ensure-WslBootstrap {
    param(
        [string]$TargetDistro,
        [string]$OriginalScript,
        [string]$OriginalRepoUrl,
        [string]$OriginalRepoDir,
        [switch]$OriginalSkipOpenClawInstall
    )

    if (-not (Test-IsWindowsAdmin)) {
        $args = @(
            '-ExecutionPolicy', 'Bypass',
            '-File', $OriginalScript,
            '-Distro', $TargetDistro,
            '-RepoUrl', $OriginalRepoUrl,
            '-RepoDir', $OriginalRepoDir,
            '-ForceWslBootstrap',
            '-Elevated'
        )

        if ($OriginalSkipOpenClawInstall) {
            $args += '-SkipOpenClawInstall'
        }

        $argString = Split-ArgsForRelaunch -ArgsToSplit $args
        Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $argString | Out-Null
        Write-Host '已请求管理员权限来安装或启用 WSL2。请在提升后的 PowerShell 窗口中继续。'
        exit 0
    }

    Write-Host "正在安装或修复 WSL2，目标发行版: $TargetDistro"
    & wsl.exe --install -d $TargetDistro

    if ($LASTEXITCODE -ne 0) {
        throw "wsl --install 执行失败，退出码: $LASTEXITCODE"
    }

    Write-Host 'WSL2 安装命令已执行完成。若系统提示重启，请先重启 Windows。'
    Write-Host "重启并首次打开 $TargetDistro 完成 Linux 账号初始化后，重新运行此脚本。"
    exit 0
}

function Get-ReadyDistro {
    param([string[]]$Distros, [string]$PreferredDistro)

    if ($Distros.Count -eq 0) {
        return $null
    }

    if ($Distros -contains $PreferredDistro) {
        return $PreferredDistro
    }

    return $Distros[0]
}

function Test-DistroFirstRunComplete {
    param([string]$TargetDistro)

    & wsl.exe -d $TargetDistro -- bash -lc 'id -un >/dev/null 2>&1'
    return $LASTEXITCODE -eq 0
}

function Invoke-WslInstaller {
    param(
        [string]$TargetDistro,
        [string]$TargetRepoUrl,
        [string]$TargetRepoDir,
        [string]$ScriptPath
    )

    $linuxScript = (& wsl.exe -d $TargetDistro -- wslpath -a $ScriptPath 2>$null).Trim()
    if (-not $linuxScript) {
        throw '无法将本地脚本路径转换为 WSL 路径。'
    }

    & wsl.exe -d $TargetDistro -- bash -lc "bash '$linuxScript' '$TargetRepoUrl' '$TargetRepoDir'"

    if ($LASTEXITCODE -ne 0) {
        throw "WSL 内安装流程失败，退出码: $LASTEXITCODE"
    }
}

$inventory = Get-WslInventory
$selectedDistro = Get-ReadyDistro -Distros $inventory.Distros -PreferredDistro $Distro

if ($ForceWslBootstrap -or -not $inventory.HasWslCommand -or -not $selectedDistro) {
    Ensure-WslBootstrap -TargetDistro $Distro -OriginalScript $PSCommandPath -OriginalRepoUrl $RepoUrl -OriginalRepoDir $RepoDir -OriginalSkipOpenClawInstall:$SkipOpenClawInstall
}

Ensure-Wsl2Version -TargetDistro $selectedDistro -DistroVersions $inventory.DistroVersions

if (-not (Test-DistroFirstRunComplete -TargetDistro $selectedDistro)) {
    Write-Host "$selectedDistro 已安装，但尚未完成首次启动。"
    Write-Host "请先打开 $selectedDistro，创建 Linux 用户和密码，然后重新运行此脚本。"
    exit 0
}

Write-Host "WSL 已就绪，使用发行版: $selectedDistro"

if ($SkipOpenClawInstall) {
    Write-Host '已按要求跳过 OpenClaw 安装步骤。'
    exit 0
}

$installerScript = Join-Path $PSScriptRoot 'install-openclaw-from-github-wsl.sh'
Invoke-WslInstaller -TargetDistro $selectedDistro -TargetRepoUrl $RepoUrl -TargetRepoDir $RepoDir -ScriptPath $installerScript

Write-Host 'OpenClaw GitHub 安装流程已执行完成。请根据上面的 origin、commit 和 installer path 记录结果。'
