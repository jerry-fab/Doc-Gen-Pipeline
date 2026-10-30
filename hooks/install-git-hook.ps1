<#
.SYNOPSIS
    Installs the Automated Documentation Pre-Commit Hook into any local Git repository.
.DESCRIPTION
    Works in two flexible ways:
    1. If copied inside a project's "hooks" folder, just right-click / run directly!
       It detects the parent repository automatically and moves the hook into .git/hooks/
    2. Or run with -TargetRepo "D:\path\to\repo" from anywhere.
.EXAMPLE
    .\install-git-hook.ps1
    .\install-git-hook.ps1 -TargetRepo "D:\Project-Folders\Flexpub2.0"
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$TargetRepo = ""
)

$ErrorActionPreference = "Stop"

# Auto-detect target repository
if ([string]::IsNullOrWhiteSpace($TargetRepo) -or $TargetRepo -eq ".") {
    # Check 1: Is the script running inside a subfolder (e.g. <project>/hooks/)?
    $ParentDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    if (Test-Path (Join-Path $ParentDir ".git")) {
        $TargetResolved = $ParentDir
    }
    # Check 2: Is the current working directory a git repo?
    elseif (Test-Path (Join-Path (Get-Location).Path ".git")) {
        $TargetResolved = (Get-Location).Path
    }
    else {
        Write-Error "[Error] Could not find a .git folder in '$ParentDir' or '$(Get-Location).Path'. Specify -TargetRepo path."
        exit 1
    }
} else {
    $TargetResolved = (Resolve-Path $TargetRepo).Path
}

$GitDir = Join-Path $TargetResolved ".git"

if (-not (Test-Path $GitDir)) {
    Write-Error "[Error] '$TargetResolved' is not a valid Git repository (.git folder not found)."
    exit 1
}

$HooksDir = Join-Path $GitDir "hooks"
if (-not (Test-Path $HooksDir)) {
    New-Item -ItemType Directory -Path $HooksDir -Force | Out-Null
}

$SourceHook = Join-Path $PSScriptRoot "pre-commit"
$DestHook = Join-Path $HooksDir "pre-commit"

if (-not (Test-Path $SourceHook)) {
    Write-Error "[Error] Source hook file not found at '$SourceHook'."
    exit 1
}

# Copy hook file into .git/hooks/pre-commit
Copy-Item -Path $SourceHook -Destination $DestHook -Force

Write-Host "============================================================" -ForegroundColor Green
Write-Host "[SUCCESS] Doc-Gen Pre-Commit Hook Installed Successfully!" -ForegroundColor Green
Write-Host "Target Repository: $TargetResolved" -ForegroundColor Cyan
Write-Host "Hook Location:     $DestHook" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Workflow:" -ForegroundColor Yellow
Write-Host "  1. Edit your source code (.cs, .py, .java, etc.)"
Write-Host "  2. Run 'git add <files>'"
Write-Host "  3. Run 'git commit -m `"your message`"'"
Write-Host "     -> Documentation will be generated and auto-staged into the commit!"
Write-Host "  4. Run 'git push origin master'"
Write-Host "     -> Code and documentation will be pushed directly to your Git server."
Write-Host "Zero server configuration needed." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
