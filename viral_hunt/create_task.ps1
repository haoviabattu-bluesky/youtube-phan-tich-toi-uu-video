# Tao task ViralHunt0300 — chay viral_hunt\run_daily.py moi ngay 03:00
# Khong can quyen admin (chay duoi user hien tai, LogonType Interactive).
# Chay:  powershell -ExecutionPolicy Bypass -File create_task.ps1

$ErrorActionPreference = 'Stop'
$root   = 'E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\viral_hunt'
$pyw    = 'C:\Users\xxx\AppData\Local\Programs\Python\Python313\pythonw.exe'
$script = Join-Path $root 'run_daily.py'

if (-not (Test-Path $pyw))    { throw "Khong thay pythonw: $pyw" }
if (-not (Test-Path $script)) { throw "Khong thay script: $script" }

$action = New-ScheduledTaskAction -Execute $pyw `
    -Argument "`"$script`" --quiet" `
    -WorkingDirectory $root

# 03:00 moi ngay. May ngu thi StartWhenAvailable chay bu khi thuc day.
$trigger = New-ScheduledTaskTrigger -Daily -At '03:00'

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 20)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName 'ViralHunt0300' `
    -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description 'Tim video nguon dang no cho lane L/N/O/M -> bao cao HTML sang Syncthing (results). 2 de/lane/ngay.' `
    -Force | Out-Null

Write-Output 'DA TAO task ViralHunt0300'
Get-ScheduledTask -TaskName 'ViralHunt0300' | Select-Object TaskName, State | Format-List
Get-ScheduledTaskInfo -TaskName 'ViralHunt0300' | Select-Object NextRunTime, LastRunTime, LastTaskResult | Format-List
