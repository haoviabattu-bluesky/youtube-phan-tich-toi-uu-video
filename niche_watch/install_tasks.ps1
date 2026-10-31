# Tao 2 task nuoi ngach (anh chot 2026-10-22):
#   NicheWatch1800       18:00 -> run_evening.py (xoay vong 3-4 profile/luot den 21:00, tu dong profile)
#   NicheWatchClose2105  21:05 -> close_all.py --sweep (LUOI AN TOAN: dong moi profile tool con de mo)
# Interactive (can phien dang nhap de mo Chrome/GPM). Chay lai file nay = ghi de task cu.

$ErrorActionPreference = 'Stop'
$root = 'E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\niche_watch'
$pyw  = 'C:\Users\xxx\AppData\Local\Programs\Python\Python313\pythonw.exe'
if (-not (Test-Path $pyw)) { throw "Khong thay pythonw: $pyw" }

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

function New-NwTask($name, $script, $argsLine, $at, $limitHours, $desc) {
    $path = Join-Path $root $script
    if (-not (Test-Path $path)) { throw "Khong thay script: $path" }
    $action   = New-ScheduledTaskAction -Execute $pyw -Argument "`"$path`" $argsLine" -WorkingDirectory $root
    $trigger  = New-ScheduledTaskTrigger -Daily -At $at
    $settings = New-ScheduledTaskSettingsSet -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Hours $limitHours) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings `
        -Principal $principal -Description $desc -Force | Out-Null
    Write-Output "DA TAO task $name"
    (Get-ScheduledTaskInfo -TaskName $name) | Select-Object TaskName, NextRunTime | Format-List
}

# KHONG bat StartWhenAvailable: may mo sau 21:00 thi khong chay bu (run_evening cung tu thoat neu het gio)
New-NwTask 'NicheWatch1800' 'run_evening.py' '' '18:00' 4 `
    'Nuoi ngach 10 lane YouTube 18:00-21:00: tim theo sheet, loc LLM+thumbnail, xem 10-15p, dong profile'
New-NwTask 'NicheWatchClose2105' 'close_all.py' '--sweep' '21:05' 1 `
    'Luoi an toan: dong moi profile niche_watch con mo (theo id/PID, khong kill chrome theo ten)'
