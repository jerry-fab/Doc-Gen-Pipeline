<#
.SYNOPSIS
    Installs the Automated Documentation Pre-Commit Hook into any local Git repository.
.DESCRIPTION
    Copies the pre-commit hook into the target repository's .git/hooks directory.
    Zero changes are made to remote Git servers (Lumina Gogs, GitHub, etc.).
.EXAMPLE
    .\install-git-hook.ps1 -TargetRepo "D:\Project-Folders\Flexpub2.0"
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$TargetRepo = "."
)

$ErrorActionPreference = "Stop"

$PipelineRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$TargetResolved = (Resolve-Path $TargetRepo).Path
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

# Copy hook file
Copy-Item -Path $SourceHook -Destination $DestHook -Force

Write-Host "============================================================" -ForegroundColor Green
Write-Host "[SUCCESS] Doc-Gen Pre-Commit Hook Installed Successfully!" -ForegroundColor Green
Write-Host "Target Repository: $TargetResolved" -ForegroundColor Cyan
Write-Host "Hook Location:     $DestHook" -ForegroundColor Cyan
Write-Host "Pipeline Location: $PipelineRoot" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Workflow:" -ForegroundColor Yellow
Write-Host "  1. Edit your source code (.cs, .py, .java) in $TargetResolved"
Write-Host "  2. Run 'git add <files>'"
Write-Host "  3. Run 'git commit -m `"your message`"'"
Write-Host "     -> Documentation will be generated and auto-staged into the commit!"
Write-Host "  4. Run 'git push origin master'"
Write-Host "     -> Code and documentation will be pushed directly to your Git server."
Write-Host "Zero server configuration needed." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
