<#
.SYNOPSIS
    Build a standard workstation from apps.json using winget - idempotent, logged, dry-run by default.

.DESCRIPTION
    For each app with a winget ID:
      - checks whether it's already installed (skip if so -> safe to re-run any number of times)
      - DRY-RUN (default): reports what would be installed
      - -Apply: installs silently, accepting agreements, and records the exit code
    -RequiredOnly limits to apps marked "required": true.
    Writes a log to .\logs\ and a summary CSV - the compliance evidence for the ticket.

.EXAMPLE
    .\Install-Workstation.ps1                    # what would happen on this PC?
    .\Install-Workstation.ps1 -RequiredOnly
    .\Install-Workstation.ps1 -Apply             # install missing apps (may prompt UAC per app)
#>
param(
    [string]$Manifest = (Join-Path $PSScriptRoot "apps.json"),
    [switch]$Apply,
    [switch]$RequiredOnly
)

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget not found. Install 'App Installer' from the Microsoft Store (Windows 10 1809+ / Windows 11)."
}

$build = Get-Content $Manifest -Raw | ConvertFrom-Json
$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = Join-Path $logDir "install-$env:COMPUTERNAME-$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$mode = if ($Apply) { "APPLY" } else { "DRY-RUN" }
Write-Host "Build: $($build.build_name) v$($build.version) on $env:COMPUTERNAME  [$mode]`n"

$results = foreach ($app in $build.apps) {
    if (-not $app.winget) { continue }                         # Linux-only entry
    if ($RequiredOnly -and -not $app.required) { continue }

    # winget list exits 0 when a matching package is installed
    winget list --id $app.winget -e --accept-source-agreements *> $null
    $installed = ($LASTEXITCODE -eq 0)

    if ($installed) {
        $status = "already installed"
    } elseif (-not $Apply) {
        $status = "WOULD INSTALL"
    } else {
        Write-Host "Installing $($app.name)..."
        winget install --id $app.winget -e --silent --accept-package-agreements --accept-source-agreements
        $status = if ($LASTEXITCODE -eq 0) { "installed" } else { "FAILED (exit $LASTEXITCODE)" }
    }
    Write-Host ("  {0,-16} {1,-32} {2}" -f $app.name, $app.winget, $status)
    [pscustomobject]@{
        Computer = $env:COMPUTERNAME; App = $app.name; WingetId = $app.winget
        Required = $app.required; Status = $status; Time = (Get-Date -Format s)
    }
}

$csv = Join-Path $logDir "summary-$env:COMPUTERNAME-$stamp.csv"
$results | Export-Csv -NoTypeInformation -Encoding UTF8 $csv
$missingRequired = $results | Where-Object { $_.Required -and $_.Status -notin @("already installed", "installed") }

Write-Host ""
if ($missingRequired) {
    Write-Host "NOT COMPLIANT - required apps missing/failed: $($missingRequired.App -join ', ')" -ForegroundColor Yellow
} else {
    Write-Host "COMPLIANT - all required apps present." -ForegroundColor Green
}
Write-Host "Summary -> $csv"
Stop-Transcript | Out-Null
