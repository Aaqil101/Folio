<#
.SYNOPSIS
Builds the Folio Windows app and its installer (issue #14).

.DESCRIPTION
1. Wipes build\ and dist\ so every run starts from a known state.
2. Reads APP_VERSION / APP_NAME / AUTHOR / WEBSITE_URL from utils/constants.py
   (single source of truth).
3. Runs PyInstaller against Folio.spec -> dist\Folio\Folio.exe (onedir).
4. Pauses so you can check the built app (press r to launch it) before the
   installer is compiled.
5. Compiles installer\folio.iss with Inno Setup 7 ->
   dist\installer\Folio-Setup-<version>.exe.
6. Removes the intermediates (build\ and dist\Folio\), leaving only the
   installer behind.

Run from anywhere; the script locates the repo root itself. Easiest entry
point is installer\build.cmd (double-click or call from a terminal; forwards
arguments like -AppOnly).

.EXAMPLE
powershell -ExecutionPolicy Bypass -File installer\build.ps1

.EXAMPLE
# App build only - keeps dist\Folio, skips Inno Setup
powershell -ExecutionPolicy Bypass -File installer\build.ps1 -AppOnly
#>
param(
    # Skip the Inno Setup step and keep dist\Folio (no end cleanup of it).
    [switch]$AppOnly
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Remove-Tree([string]$RelativePath) {
    $Path = Join-Path $Root $RelativePath
    if (Test-Path $Path) {
        Write-Host "Removing $RelativePath\"
        Remove-Item $Path -Recurse -Force
    }
}

# --- 1. Clean slate ---------------------------------------------------------
Remove-Tree "build"
Remove-Tree "dist"

# --- 2. Version metadata from utils/constants.py ---------------------------
$Constants = Get-Content "utils\constants.py" -Raw
function Get-Const([string]$Name, [string]$Default) {
    $Pattern = '(?m)^' + $Name + '\s*:\s*str\s*=\s*"([^"]*)"'
    if ($Constants -match $Pattern) { return $Matches[1] }
    return $Default
}
$AppVersion  = Get-Const "APP_VERSION" "0.1.0"
$AppName     = Get-Const "APP_NAME" "Folio"
$AppPublisher = Get-Const "AUTHOR" "Aaqil"
$AppUrl      = Get-Const "WEBSITE_URL" "https://github.com/Aaqil101/Folio"
Write-Host "Building $AppName $AppVersion"

# --- 3. PyInstaller ---------------------------------------------------------
$PyInstaller = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $PyInstaller)) {
    throw ".venv not found at .venv\Scripts\python.exe - create it first: python -m venv .venv && pip install -r requirements.txt -r requirements-build.txt"
}
& $PyInstaller -m PyInstaller --noconfirm --clean (Join-Path $Root "Folio.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
$AppExe = Join-Path $Root "dist\Folio\Folio.exe"
if (-not (Test-Path $AppExe)) { throw "Expected output missing: $AppExe" }
Write-Host "App built: $AppExe"
if ($AppOnly) {
    Remove-Tree "build"   # PyInstaller work dir is never the deliverable
    exit 0
}

# --- 4. Pause: check the app before packaging ------------------------------
while ($true) {
    Write-Host ""
    Write-Host "Check the app now: $AppExe"
    $Choice = Read-Host "[Enter] continue to Inno Setup, [r] launch app to check, [q] quit"
    if ($Choice -eq "") { break }
    switch ($Choice.ToLower()) {
        "r" { Start-Process -FilePath $AppExe -WorkingDirectory (Split-Path $AppExe) }
        "q" {
            Write-Host "Quit - no installer built. App kept at $AppExe"
            exit 0
        }
        default { Write-Host "Unknown choice '$Choice' - Enter/r/q" }
    }
}

# --- 5. Inno Setup ----------------------------------------------------------
$Iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 7\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
    Write-Warning "ISCC.exe not found (Inno Setup 6/7) - installer skipped. App build is in dist\Folio."
    exit 0
}

& $Iscc `
    "/DMyAppVersion=$AppVersion" `
    "/DMyAppPublisher=$AppPublisher" `
    "/DMyAppUrl=$AppUrl" `
    (Join-Path $Root "installer\folio.iss")
if ($LASTEXITCODE -ne 0) { throw "ISCC failed with exit code $LASTEXITCODE" }

$Setup = Join-Path $Root "dist\installer\Folio-Setup-$AppVersion.exe"
if (-not (Test-Path $Setup)) { throw "Expected installer missing: $Setup" }

# --- 6. Clean intermediates, keep only the installer ------------------------
Remove-Tree "build"
Remove-Tree "dist\Folio"

Write-Host "Installer built: $Setup"
