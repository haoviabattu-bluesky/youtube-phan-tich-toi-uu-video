# keep_visible.ps1 — watchdog giữ cửa sổ Chrome của ĐÚNG 1 profile GPM luôn HIỆN trên màn hình khi tool đăng bình luận
# (anh yêu cầu 2026-10-22: cửa sổ phải hiện thật, không chạy ẩn/thu nhỏ/nằm ngoài màn hình).
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tools\keep_visible.ps1 -ProfileId <id GPM>
#
# Chỉ đụng cửa sổ của tiến trình chrome có --user-data-dir chứa ProfileId (tiến trình browser chính, không có --type=).
# KHÔNG đóng / kill / di chuyển profile khác. Tự thoát khi profile đã đóng (hoặc chưa mở sau -StartWaitSec giây).
# Viết cho Windows PowerShell 5.1 (máy này không có pwsh).
param(
    [Parameter(Mandatory = $true)][string]$ProfileId,
    [int]$IntervalSec = 3,
    [int]$StartWaitSec = 300
)
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class KvWin {
    public delegate bool EnumProc(IntPtr h, IntPtr l);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr h);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    public static List<IntPtr> WindowsOf(uint pid) {
        var res = new List<IntPtr>();
        EnumWindows((h, l) => {
            uint p; GetWindowThreadProcessId(h, out p);
            if (p == pid && GetWindowTextLength(h) > 0 && (IsWindowVisible(h) || IsIconic(h))) res.Add(h);
            return true;
        }, IntPtr.Zero);
        return res;
    }
}
"@
Add-Type -AssemblyName System.Windows.Forms

function Log($m) { Write-Output ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $m) }

function Get-BrowserPids {
    Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*$ProfileId*" -and $_.CommandLine -notlike "*--type=*" } |
        ForEach-Object { [uint32]$_.ProcessId }
}

$screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
$start = Get-Date
$seen = $false
$miss = 0
Log "theo dõi cửa sổ profile $ProfileId (mỗi ${IntervalSec}s)"
while ($true) {
    $pids = @(Get-BrowserPids)
    if ($pids.Count -eq 0) {
        if ($seen) {
            $miss++
            if ($miss -ge 3) { Log "profile đã đóng → thoát"; break }
        } elseif (((Get-Date) - $start).TotalSeconds -gt $StartWaitSec) {
            Log "chờ ${StartWaitSec}s mà profile chưa mở → thoát"; break
        }
    } else {
        $seen = $true
        $miss = 0
        foreach ($procId in $pids) {
            foreach ($h in [KvWin]::WindowsOf($procId)) {
                if ([KvWin]::IsIconic($h)) {
                    [KvWin]::ShowWindow($h, 9) | Out-Null          # SW_RESTORE
                    Log "khôi phục cửa sổ đang thu nhỏ (pid $procId)"
                } elseif (-not [KvWin]::IsWindowVisible($h)) {
                    [KvWin]::ShowWindow($h, 5) | Out-Null          # SW_SHOW
                    Log "hiện cửa sổ đang ẩn (pid $procId)"
                }
                $r = New-Object KvWin+RECT
                if ([KvWin]::GetWindowRect($h, [ref]$r)) {
                    $off = ($r.Right -lt ($screen.Left + 80)) -or ($r.Bottom -lt ($screen.Top + 80)) -or
                           ($r.Left -gt ($screen.Right - 80)) -or ($r.Top -gt ($screen.Bottom - 80))
                    if ($off) {
                        # SWP_NOSIZE(1) | SWP_NOZORDER(4) | SWP_NOACTIVATE(0x10): chỉ kéo vào màn hình, không đổi cỡ, không giành focus
                        [KvWin]::SetWindowPos($h, [IntPtr]::Zero, $screen.Left + 40, $screen.Top + 40, 0, 0, 0x15) | Out-Null
                        Log "kéo cửa sổ nằm ngoài màn hình vào lại (pid $procId)"
                    }
                }
            }
        }
    }
    Start-Sleep -Seconds $IntervalSec
}
