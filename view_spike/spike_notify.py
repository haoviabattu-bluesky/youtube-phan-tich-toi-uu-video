# -*- coding: utf-8 -*-
r"""
BAO ANH: thong bao Windows (toast goc phai duoi) + ghi state/alerts.jsonl.
Phuong an TAM (anh chot 2026-10-15). Toast qua PowerShell an cua so (CREATE_NO_WINDOW).
"""
import subprocess, time, datetime
from xml.sax.saxutils import escape
import spike_state

PS = r"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$x = New-Object Windows.Data.Xml.Dom.XmlDocument
$x.LoadXml([Console]::In.ReadToEnd())
$app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show([Windows.UI.Notifications.ToastNotification]::new($x))
"""


def toast(title, body, url=None):
    launch = f' activationType="protocol" launch="{escape(url)}"' if url else ""
    xml = (f'<toast{launch} scenario="reminder"><visual><binding template="ToastGeneric">'
           f'<text>{escape(title)}</text><text>{escape(body)}</text></binding></visual>'
           f'<actions><action content="Đóng" arguments="dismiss" activationType="system"/></actions></toast>')
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", PS],
                       input=xml.encode("utf-8"), timeout=30, creationflags=0x08000000,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def alert(kind, lane_tab, vid, title, per_hour, detail):
    """kind: SPIKE (Studio >=1000/gio) | KHONG_XAC_MINH (API nghi len nhung khong mo duoc Studio)."""
    rec = {"at": datetime.datetime.now().isoformat(timespec="seconds"), "t": time.time(), "kind": kind,
           "lane": lane_tab, "vid": vid, "title": title, "per_hour": per_hour, "detail": detail}
    spike_state.append_jsonl(spike_state.ALERTS, rec)
    head = f"🔥 {per_hour} view/giờ — {lane_tab}" if kind == "SPIKE" else f"⚠️ Nghi đang lên — {lane_tab}"
    toast(head, f"{title[:60]}\n{detail}", f"https://studio.youtube.com/video/{vid}/analytics/tab-overview/period-default")
    return rec
