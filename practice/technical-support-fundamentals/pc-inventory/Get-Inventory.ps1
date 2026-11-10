<#
.SYNOPSIS
    Windows-only, deeper inventory: serial number, model, BIOS, disks (by type), and installed software.

.DESCRIPTION
    Uses CIM/WMI classes (the same data tools like SCCM/Intune collect) and the registry
    Uninstall keys (the same list "Apps & features" shows). Read-only - changes nothing.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Get-Inventory.ps1
    powershell -ExecutionPolicy Bypass -File .\Get-Inventory.ps1 -OutDir .\reports
#>
param(
    [string]$OutDir = (Join-Path $PSScriptRoot "reports")
)

$ErrorActionPreference = "Stop"

# --- Hardware ---------------------------------------------------------------
$cs    = Get-CimInstance Win32_ComputerSystem
$bios  = Get-CimInstance Win32_BIOS
$os    = Get-CimInstance Win32_OperatingSystem
$cpu   = Get-CimInstance Win32_Processor | Select-Object -First 1

# Physical disks: MediaType tells SSD vs HDD (Get-PhysicalDisk is in the Storage module, Win8+)
$physical = Get-PhysicalDisk | Select-Object FriendlyName, MediaType, BusType,
    @{n = "SizeGB"; e = { [math]::Round($_.Size / 1GB, 0) } }, HealthStatus

$volumes = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID,
    @{n = "SizeGB"; e = { [math]::Round($_.Size / 1GB, 1) } },
    @{n = "FreeGB"; e = { [math]::Round($_.FreeSpace / 1GB, 1) } },
    FileSystem

# --- Software ---------------------------------------------------------------
# 64-bit apps, 32-bit apps on 64-bit Windows (WOW6432Node), and per-user installs
$uninstallKeys = @(
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
$software = Get-ItemProperty $uninstallKeys -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -and -not $_.SystemComponent } |
    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
    Sort-Object DisplayName -Unique

# --- Build the report -------------------------------------------------------
$report = [ordered]@{
    CollectedAt   = (Get-Date).ToString("s")
    Hostname      = $env:COMPUTERNAME
    Manufacturer  = $cs.Manufacturer
    Model         = $cs.Model
    SerialNumber  = $bios.SerialNumber          # what you give the vendor for warranty claims
    BIOSVersion   = $bios.SMBIOSBIOSVersion
    OS            = "$($os.Caption) ($($os.OSArchitecture)) build $($os.BuildNumber)"
    LastBoot      = $os.LastBootUpTime.ToString("s")
    CPU           = $cpu.Name.Trim()
    Cores         = $cpu.NumberOfCores
    LogicalCPUs   = $cpu.NumberOfLogicalProcessors
    RAMGB         = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
    PhysicalDisks = $physical
    Volumes       = $volumes
    SoftwareCount = $software.Count
    Software      = $software
}

Write-Host "Host     : $($report.Hostname)  ($($report.Manufacturer) $($report.Model), S/N $($report.SerialNumber))"
Write-Host "OS       : $($report.OS), last boot $($report.LastBoot)"
Write-Host "CPU      : $($report.CPU) - $($report.Cores) cores / $($report.LogicalCPUs) threads"
Write-Host "RAM      : $($report.RAMGB) GB"
$physical | ForEach-Object { Write-Host "Disk     : $($_.FriendlyName) - $($_.MediaType) / $($_.BusType), $($_.SizeGB) GB, $($_.HealthStatus)" }
$volumes  | ForEach-Object { Write-Host "Volume   : $($_.DeviceID) $($_.FreeGB) GB free of $($_.SizeGB) GB ($($_.FileSystem))" }
Write-Host "Software : $($software.Count) installed applications (see JSON/CSV)"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$jsonPath = Join-Path $OutDir "$($env:COMPUTERNAME)-full.json"
$csvPath  = Join-Path $OutDir "$($env:COMPUTERNAME)-software.csv"
$report | ConvertTo-Json -Depth 4 | Out-File -Encoding utf8 $jsonPath
$software | Export-Csv -NoTypeInformation -Encoding UTF8 $csvPath
Write-Host "`nSaved -> $jsonPath"
Write-Host "Saved -> $csvPath"
