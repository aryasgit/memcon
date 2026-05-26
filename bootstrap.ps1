# Memcon bootstrap — Windows PowerShell.
#
# Usage:
#   iwr -useb https://raw.githubusercontent.com/aryasgit/memcon/main/bootstrap.ps1 | iex
#
# Environment overrides (set before piping into iex):
#   $env:MEMCON_DIR    Target directory (default: $HOME\memcon)
#   $env:MEMCON_REPO   Repo URL        (default: https://github.com/aryasgit/memcon.git)
#   $env:MEMCON_REF    Branch / tag    (default: main)
#   $env:MEMCON_MODEL  Force a specific Ollama model
#   $env:MEMCON_SKIP_MCP=1  Skip Claude Desktop registration
#
# Requirements: git, python (3.10+), Docker Desktop, Ollama.
$ErrorActionPreference = "Stop"

$Repo   = if ($env:MEMCON_REPO) { $env:MEMCON_REPO } else { "https://github.com/aryasgit/memcon.git" }
$Ref    = if ($env:MEMCON_REF)  { $env:MEMCON_REF }  else { "main" }
$Target = if ($env:MEMCON_DIR)  { $env:MEMCON_DIR }  else { Join-Path $HOME "memcon" }

Write-Host "╔══════════════════════════════════════╗"
Write-Host "║          MEMCON — bootstrap          ║"
Write-Host "╚══════════════════════════════════════╝"
Write-Host "  repo: $Repo"
Write-Host "  ref:  $Ref"
Write-Host "  dir:  $Target"
Write-Host ""

# Required tools
foreach ($cmd in @("git","docker","python")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Required command not found on PATH: $cmd"
        Write-Host "   Install it first and re-run."
        exit 1
    }
}

# Clone or update
if (Test-Path (Join-Path $Target ".git")) {
    Write-Host "↻  Existing checkout at $Target — pulling latest"
    git -C "$Target" fetch --quiet origin $Ref
    git -C "$Target" checkout --quiet $Ref
    git -C "$Target" pull --quiet --ff-only origin $Ref
} else {
    Write-Host "⇣  Cloning into $Target"
    git clone --quiet --branch $Ref $Repo "$Target"
}

Set-Location $Target

# Hand off to the Windows installer
& cmd /c "install.bat"

Write-Host ""
Write-Host "✅ Bootstrap complete."
Write-Host "   cd $Target ; start.bat"
