<#
.SYNOPSIS
    READ-ONLY Windows hardening audit - checks defense-in-depth layers and writes results as JSON.

.DESCRIPTION
    Changes nothing. Some checks (BitLocker, a few Defender details) need an elevated PowerShell;
    without it they report UNKNOWN instead of failing.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Audit-Host.ps1
    python report.py results\<COMPUTERNAME>.json
#>
param([string]$OutDir = (Join-Path $PSScriptRoot "results"))

$results = New-Object System.Collections.Generic.List[object]
function Add-Result($Layer, $Check, $Status, $Detail, $Fix) {
    $results.Add([pscustomobject]@{ layer = $Layer; check = $Check; status = $Status; detail = "$Detail"; fix = $Fix })
    $color = @{ PASS = "Green"; WARN = "Yellow"; FAIL = "Red"; UNKNOWN = "DarkGray" }[$Status]
    Write-Host ("[{0,-7}] {1,-12} {2,-34} {3}" -f $Status, $Layer, $Check, $Detail) -ForegroundColor $color
}
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "Host $env:COMPUTERNAME - elevated: $isAdmin`n"

# --- Network layer: host firewall ------------------------------------------------------
try {
    foreach ($p in Get-NetFirewallProfile -ErrorAction Stop) {
        if (-not $p.Enabled) { Add-Result "firewall" "$($p.Name) profile" "FAIL" "disabled" "Set-NetFirewallProfile -Name $($p.Name) -Enabled True" }
        elseif ($p.DefaultInboundAction -eq "Allow") { Add-Result "firewall" "$($p.Name) profile" "FAIL" "enabled but default inbound = Allow" "Set default inbound to Block" }
        else {
            # NotConfigured = not set by policy, so the Windows default applies, which is Block
            $inbound = if ("$($p.DefaultInboundAction)" -eq "NotConfigured") { "Block (Windows default)" } else { $p.DefaultInboundAction }
            Add-Result "firewall" "$($p.Name) profile" "PASS" "enabled, inbound default $inbound" ""
        }
    }
} catch { Add-Result "firewall" "profiles" "UNKNOWN" $_.Exception.Message "" }

# --- Antimalware --------------------------------------------------------------------------
try {
    $mp = Get-MpComputerStatus -ErrorAction Stop
    if ($mp.RealTimeProtectionEnabled) { Add-Result "antimalware" "Defender real-time protection" "PASS" "on" "" }
    else { Add-Result "antimalware" "Defender real-time protection" "FAIL" "off (or another AV is active - verify)" "Turn on real-time protection" }
    $age = $mp.AntivirusSignatureAge
    $st = if ($age -le 3) { "PASS" } elseif ($age -le 7) { "WARN" } else { "FAIL" }
    Add-Result "antimalware" "Signature age" $st "$age day(s) old" "Update-MpSignature"
} catch { Add-Result "antimalware" "Defender status" "UNKNOWN" "Get-MpComputerStatus unavailable (third-party AV?)" "" }

# --- Patching -----------------------------------------------------------------------------
try {
    $last = Get-HotFix | Where-Object InstalledOn | Sort-Object InstalledOn -Descending | Select-Object -First 1
    $days = ((Get-Date) - $last.InstalledOn).Days
    $st = if ($days -le 35) { "PASS" } elseif ($days -le 60) { "WARN" } else { "FAIL" }
    Add-Result "patching" "Last update installed" $st "$($last.HotFixID) on $($last.InstalledOn.ToString('yyyy-MM-dd')) ($days days ago)" "Run Windows Update"
} catch { Add-Result "patching" "Last update installed" "UNKNOWN" $_.Exception.Message "" }
$os = Get-CimInstance Win32_OperatingSystem
$uptime = ((Get-Date) - $os.LastBootUpTime).Days
$st = if ($uptime -le 14) { "PASS" } else { "WARN" }
Add-Result "patching" "Uptime" $st "$uptime day(s) since last reboot" "Reboot to finish installing updates"

# --- Data: disk encryption ----------------------------------------------------------------
if ($isAdmin) {
    try {
        $bl = Get-BitLockerVolume -MountPoint $env:SystemDrive -ErrorAction Stop
        if ($bl.ProtectionStatus -eq "On") { Add-Result "encryption" "BitLocker $env:SystemDrive" "PASS" "protection on ($($bl.EncryptionMethod))" "" }
        else { Add-Result "encryption" "BitLocker $env:SystemDrive" "FAIL" "protection $($bl.ProtectionStatus)" "Enable BitLocker and escrow the recovery key" }
    } catch { Add-Result "encryption" "BitLocker" "UNKNOWN" "not available on this edition?" "" }
} else { Add-Result "encryption" "BitLocker $env:SystemDrive" "UNKNOWN" "needs an elevated PowerShell" "" }

# --- Accounts -----------------------------------------------------------------------------
try {
    $admins = @(Get-LocalGroupMember -SID "S-1-5-32-544" -ErrorAction Stop)
    $st = if ($admins.Count -le 2) { "PASS" } else { "WARN" }
    Add-Result "accounts" "Local Administrators members" $st "$($admins.Count): $(($admins.Name) -join ', ')" "Remove users who don't need admin; use separate admin accounts"
    $builtin = Get-LocalUser | Where-Object { $_.SID -like "*-500" }
    $st = if (-not $builtin.Enabled) { "PASS" } else { "WARN" }
    Add-Result "accounts" "Built-in Administrator" $st ($(if ($builtin.Enabled) { "enabled" } else { "disabled" })) "Disable-LocalUser -Name '$($builtin.Name)'"
    $guest = Get-LocalUser | Where-Object { $_.SID -like "*-501" }
    $st = if (-not $guest.Enabled) { "PASS" } else { "FAIL" }
    Add-Result "accounts" "Guest account" $st ($(if ($guest.Enabled) { "enabled" } else { "disabled" })) "Disable-LocalUser -Name Guest"
} catch {
    # Domain-joined machines or locked-down endpoints may refuse local group enumeration
    Add-Result "accounts" "Local accounts" "UNKNOWN" $_.Exception.Message ""
}
$uac = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -ErrorAction SilentlyContinue).EnableLUA
$st = if ($uac -eq 1) { "PASS" } else { "FAIL" }
Add-Result "accounts" "UAC" $st ($(if ($uac -eq 1) { "enabled" } else { "disabled" })) "Re-enable UAC (EnableLUA=1)"

# --- Attack surface -----------------------------------------------------------------------
try {
    $smb1 = (Get-SmbServerConfiguration -ErrorAction Stop).EnableSMB1Protocol
    $st = if (-not $smb1) { "PASS" } else { "FAIL" }
    Add-Result "surface" "SMBv1 server" $st ($(if ($smb1) { "ENABLED" } else { "disabled" })) "Set-SmbServerConfiguration -EnableSMB1Protocol `$false"
} catch { Add-Result "surface" "SMBv1 server" "UNKNOWN" "needs elevation" "" }
$rdpDeny = (Get-ItemProperty "HKLM:\System\CurrentControlSet\Control\Terminal Server" -ErrorAction SilentlyContinue).fDenyTSConnections
if ($rdpDeny -eq 1) { Add-Result "surface" "Remote Desktop" "PASS" "disabled" "" }
else {
    $nla = (Get-ItemProperty "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -ErrorAction SilentlyContinue).UserAuthentication
    $st = if ($nla -eq 1) { "WARN" } else { "FAIL" }
    Add-Result "surface" "Remote Desktop" $st "enabled (NLA $(if ($nla -eq 1) {'on'} else {'OFF'}))" "Disable RDP if unused; otherwise require NLA and restrict via firewall/VPN"
}
$autorun = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" -ErrorAction SilentlyContinue).NoDriveTypeAutoRun
$st = if ($autorun -eq 255) { "PASS" } else { "WARN" }
$autorunDetail = if ($autorun -eq 255) { "disabled" } elseif ($null -eq $autorun) { "not set by policy (Windows default allows some drive types)" } else { "partially disabled (value $autorun)" }
Add-Result "surface" "AutoRun for all drives" $st $autorunDetail "Set NoDriveTypeAutoRun=255 via Group Policy"
$listening = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -in @("0.0.0.0", "::") } | Select-Object -ExpandProperty LocalPort -Unique | Sort-Object)
if ($listening.Count -eq 0) {
    Add-Result "surface" "Ports listening on all interfaces" "PASS" "none (services only listen on localhost)" ""
} else {
    Add-Result "surface" "Ports listening on all interfaces" "WARN" ($listening -join ", ") "Review: is each one needed? Is the firewall blocking it on Public networks?"
}

# --- Output -------------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$file = Join-Path $OutDir "$env:COMPUTERNAME.json"
[pscustomobject]@{ host = $env:COMPUTERNAME; os = $os.Caption; elevated = $isAdmin
                   collected = (Get-Date).ToString("s"); results = $results } |
    ConvertTo-Json -Depth 4 | Out-File -Encoding utf8 $file
Write-Host "`nSaved -> $file   (python report.py `"$file`")"
