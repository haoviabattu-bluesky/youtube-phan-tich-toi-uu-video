# MAY 1 (anh chot 2026-10-31): task May1DailyMetricsLogon
#   Kich 5 PHUT sau khi anh dang nhap Windows -> tools\may1_logon_run.py --scheduled
#   Chi lane X, GEO, P (tools\daily_lanes_may1.json). Moi ngay 1 lan thanh cong (tool tu bo qua lan sau).
#   KHONG tao DailyMetrics0300/0500 tren may 1.
# Chay:  powershell -ExecutionPolicy Bypass -File E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\create_task_may1_logon.ps1

$ErrorActionPreference = 'Stop'
$root   = 'E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO'
$pyw    = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\pythonw.exe'
$script = Join-Path $root 'tools\may1_logon_run.py'
if (-not (Test-Path $pyw))    { throw "Khong thay pythonw: $pyw" }
if (-not (Test-Path $script)) { throw "Khong thay script: $script" }

$action = New-ScheduledTaskAction -Execute $pyw -Argument "`"$script`" --scheduled" -WorkingDirectory $root

$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$trigger.Delay = 'PT5M'

$settings = New-ScheduledTaskSettingsSet `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -MultipleInstances IgnoreNew

# Interactive: can phien dang nhap de mo cua so GPM/Chrome
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName 'May1DailyMetricsLogon' `
    -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description 'May 1: 5 phut sau dang nhap doc Studio lane X/GEO/P -> sheet N-S,K + bao cao YIE inbox\may1 (1 lan/ngay)' `
    -Force | Out-Null

Write-Output 'DA TAO task May1DailyMetricsLogon'
$t = Get-ScheduledTask -TaskName 'May1DailyMetricsLogon'
$t | Select-Object TaskName, State | Format-List
$t.Triggers | Select-Object @{n='Trigger';e={$_.CimClass.CimClassName}}, Delay, UserId | Format-List
