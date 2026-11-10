<#
.SYNOPSIS
    Onboard/offboard LOCAL Windows users from a CSV - groups, temp passwords, shared folder ACLs.

.DESCRIPTION
    DRY RUN by default: prints every action without changing anything.
    With -Apply (in an elevated PowerShell, ideally inside a VM) it actually:
      - creates a local group per department (lab-<Dept>) and a shared folder C:\LabShares\<Dept>
      - grants the department group Modify on its own folder (NTFS, inherited)
      - creates users with a random temporary password, "must change at next logon"
      - offboards by DISABLING the account and removing group membership (not deleting)
    Use -Cleanup -Apply to remove everything this script created.

.EXAMPLE
    .\Onboard-Users.ps1                       # dry run
    .\Onboard-Users.ps1 -Apply                # do it (admin)
    .\Onboard-Users.ps1 -Cleanup -Apply       # undo the lab
#>
param(
    [string]$CsvPath = (Join-Path $PSScriptRoot "new-hires.csv"),
    [string]$ShareRoot = "C:\LabShares",
    [switch]$Apply,
    [switch]$Cleanup
)

$ErrorActionPreference = "Stop"
$mode = if ($Apply) { "APPLY" } else { "DRY-RUN" }

function Do-Step([string]$Description, [scriptblock]$Action) {
    Write-Host "[$mode] $Description"
    if ($Apply) { & $Action }
}

function New-TempPassword {
    # 16 random chars from a set without look-alikes (0/O, 1/l) - read out over the phone safely
    $chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#%"
    -join (1..16 | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
}

function Get-Username($row) {
    # first initial + last name, lowercase: Amina Bello -> abello
    ("{0}{1}" -f $row.first.Substring(0, 1), $row.last).ToLower()
}

if ($Apply) {
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
               ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) { throw "-Apply needs an elevated (Run as administrator) PowerShell." }
}

$rows = Import-Csv $CsvPath
$departments = $rows.department | Sort-Object -Unique

if ($Cleanup) {
    foreach ($row in $rows) {
        $u = Get-Username $row
        Do-Step "Remove user $u" { Remove-LocalUser -Name $u -ErrorAction SilentlyContinue }
    }
    foreach ($d in $departments) {
        Do-Step "Remove group lab-$d" { Remove-LocalGroup -Name "lab-$d" -ErrorAction SilentlyContinue }
    }
    Do-Step "Remove $ShareRoot" { Remove-Item $ShareRoot -Recurse -Force -ErrorAction SilentlyContinue }
    return
}

# --- groups + department folders (permissions go on GROUPS, never on individual users) ---
foreach ($d in $departments) {
    $group = "lab-$d"
    $folder = Join-Path $ShareRoot $d
    Do-Step "Create group $group (if missing)" {
        if (-not (Get-LocalGroup -Name $group -ErrorAction SilentlyContinue)) {
            New-LocalGroup -Name $group -Description "Lab department group: $d" | Out-Null
        }
    }
    Do-Step "Create folder $folder and grant $group Modify (OI)(CI) - inherited by files and subfolders" {
        New-Item -ItemType Directory -Force -Path $folder | Out-Null
        icacls $folder /inheritance:r /grant:r "Administrators:(OI)(CI)F" "SYSTEM:(OI)(CI)F" "${group}:(OI)(CI)M" | Out-Null
    }
}

# --- users ---
$credentials = @()
foreach ($row in $rows) {
    $u = Get-Username $row
    $group = "lab-$($row.department)"

    if ($row.action -eq "onboard") {
        $pw = New-TempPassword
        Do-Step "Create user $u ($($row.first) $($row.last)) and add to $group" {
            if (-not (Get-LocalUser -Name $u -ErrorAction SilentlyContinue)) {
                $secure = ConvertTo-SecureString $pw -AsPlainText -Force
                New-LocalUser -Name $u -FullName "$($row.first) $($row.last)" -Password $secure `
                    -Description "Lab user - $($row.department)" | Out-Null
                # "User must change password at next logon"
                net user $u /logonpasswordchg:yes | Out-Null
            }
            Add-LocalGroupMember -Group $group -Member $u -ErrorAction SilentlyContinue
            Add-LocalGroupMember -Group "Users" -Member $u -ErrorAction SilentlyContinue
        }
        $credentials += [pscustomobject]@{ Username = $u; TempPassword = $pw; Group = $group }
    }
    elseif ($row.action -eq "offboard") {
        Do-Step "Offboard $u : DISABLE account (keep data for handover) and remove from $group" {
            if (Get-LocalUser -Name $u -ErrorAction SilentlyContinue) {
                Disable-LocalUser -Name $u
                Remove-LocalGroupMember -Group $group -Member $u -ErrorAction SilentlyContinue
            } else {
                Write-Host "    (user $u does not exist - nothing to do)"
            }
        }
    }
}

Write-Host ""
if ($Apply) {
    Write-Host "Temporary passwords (give each to the user through a separate secure channel, then clear this screen):"
    $credentials | Format-Table -AutoSize
    Write-Host "Verify: Get-LocalGroupMember lab-Finance ; icacls $ShareRoot\Finance"
} else {
    Write-Host "Dry run complete - nothing changed. Re-run with -Apply in an elevated PowerShell (preferably a VM)."
}
