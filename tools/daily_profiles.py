# -*- coding: utf-8 -*-
r"""
MO / DONG PROFILE CHO JOB 05:00 (tools/daily_0500_run.py).

Anh chot 2026-10-16 (memory daily-0500-profile-busy):
  * GPM / AdsPower chua bat -> tool tu bat app.
  * GPM bao ProfileUsingByOther -> TU XU LY: profiles/stop/<id> -> dong chrome cua DUNG profile do
    (PID co --user-data-dir chua <id>, KHONG bao gio theo ten chrome.exe) -> start lai.
    CHI ap cho job 05:00 (gio do chi Claude dung). Chay tay ban ngay van giu bay #9 (dung, bao anh).
  * Chrome cong 9222 (lane A + M): dang mo thi chi attach; tool vua mo thi tool dong lai.
"""
import os, time, json, subprocess, urllib.request
from contextlib import contextmanager
import requests

GPM = "http://127.0.0.1:9495/api/v1"
GPM_EXE = os.path.expandvars(r"%LOCALAPPDATA%\Programs\GPMLoginGlobal\GPMLoginGlobal.exe")   # may 1 user admin, may 2 user xxx
ADS = "http://127.0.0.1:50325"
ADS_EXE = r"C:\Program Files\AdsPower Global\AdsPower Global.exe"
ADS_ENV = r"D:\CLAUDE\UK_LOGIN\.env"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_9222 = r"E:\CLAUDE\YOUTUBE\HAOVIABATTU_PROFILE"
DETACH = 0x00000008 | 0x00000200   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP -> song doc lap voi shell


def _alive(url):
    try:
        with urllib.request.urlopen(url, timeout=5):
            return True
    except Exception:
        return False


def _ensure_app(name, probe, exe, log, wait=120):
    if _alive(probe):
        return
    log(f"  {name} chua bat -> tu mo {exe}")
    subprocess.Popen([exe], creationflags=DETACH, close_fds=True)
    for _ in range(wait // 3):
        time.sleep(3)
        if _alive(probe):
            time.sleep(5)   # API len truoc khi app san sang han
            return
    raise RuntimeError(f"{name} khong bat len duoc sau {wait}s")


# ---------------- GPM ----------------
def _gpm_find(mail):
    m = mail.strip().lower(); stem = m.split("@")[0]
    page = 1
    while True:
        d = requests.get(f"{GPM}/profiles", params={"page": page, "per_page": 100}, timeout=30).json()["data"]
        for p in d["data"]:
            if p["name"].strip().lower() in (m, stem):
                return p["id"]
        if page >= d["last_page"]:
            return None
        page += 1


def _gpm_stop(pid):
    try:
        requests.get(f"{GPM}/profiles/stop/{pid}", timeout=60)
    except Exception:
        pass


def _kill_profile_chrome(pid, log):
    """Dong chrome cua DUNG profile pid (tien trinh chinh, khong co --type=), theo PID."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
          "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                         timeout=60, creationflags=0x08000000).stdout.strip()
    procs = json.loads(out) if out else []
    procs = [procs] if isinstance(procs, dict) else procs
    hit = [p["ProcessId"] for p in procs
           if p.get("CommandLine") and pid in p["CommandLine"] and "--type=" not in p["CommandLine"]]
    for x in hit:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(x)], capture_output=True, creationflags=0x08000000)
    log(f"  da dong {len(hit)} tien trinh chrome cua profile {pid[:8]} (theo PID {hit})")


def _gpm_start(pid, log, force_busy, tries=4):
    """Mo profile GPM, chiu duoc ProfileInUse.

    Do that 2026-10-20: GPM bao "ProfileInUse" NGAY CA KHI profile da stop (trang thai treo ben
    GPM), va phai stop LAN 2 + cho ~15s moi start duoc. Ban cu chi stop 1 lan + cho 5s -> 3 lan
    thu deu that bai, ca lane bi bo. Vi vay: stop, cho lau dan (8/15/22s), va sau lan 2 thi
    stop them mot lan nua.
    """
    last = ""
    for i in range(tries):
        j = requests.get(f"{GPM}/profiles/start/{pid}", timeout=180).json()
        d = j.get("data")
        ws = d.get("websocket_debugging_url") if isinstance(d, dict) else ""
        if j.get("success") and ws:
            return ws
        last = j.get("message") or str(d)[:120]
        if last == "ProfileUsingByOther" and not force_busy:
            raise RuntimeError("PROFILE_BUSY: profile dang duoc dung o noi khac -> chay tay thi KHONG dong (bay #9)")
        log(f"  GPM start lan {i+1}: {last or 'websocket rong'} -> stop + dong chrome cua profile roi thu lai")
        _gpm_stop(pid)
        wait = 8 + i * 7          # 8s, 15s, 22s — GPM can thoi gian giai phong trang thai
        time.sleep(wait)
        _kill_profile_chrome(pid, log)
        time.sleep(6)
        if i >= 1:                 # tu lan 2: stop them mot lan nua (GPM hay treo trang thai)
            _gpm_stop(pid)
            time.sleep(8)
    raise RuntimeError(f"GPM khong mo duoc profile sau {tries} lan: {last}")


# ---------------- AdsPower ----------------
def _ads_headers():
    k = os.environ.get("ADSPOWER_API_KEY", "")
    if not k and os.path.exists(ADS_ENV):
        for ln in open(ADS_ENV, encoding="utf-8"):
            if ln.startswith("ADSPOWER_API_KEY="):
                k = ln.split("=", 1)[1].strip().strip('"')
    return {"Authorization": f"Bearer {k}"} if k else {}


def _ads(path, **params):
    time.sleep(1.2)   # gioi han 1 req/s cua ca may
    return requests.get(ADS + path, params=params, headers=_ads_headers(), timeout=120).json()


def _ads_start(uid, log):
    for i in range(3):
        j = _ads("/api/v1/browser/start", user_id=uid)
        if j.get("code") == 0:
            return j["data"]["ws"]["puppeteer"]
        log(f"  AdsPower start lan {i+1}: {j.get('msg')} -> stop roi thu lai")
        _ads("/api/v1/browser/stop", user_id=uid); time.sleep(8)
    raise RuntimeError(f"AdsPower khong mo duoc {uid}: {j.get('msg')}")


# ---------------- Chrome 9222 ----------------
def _open_9222(port, log):
    """Tra (ws, launched)."""
    url = f"http://127.0.0.1:{port}"
    if _alive(url + "/json/version"):
        return url, False
    log(f"  cong {port} trong -> mo Chrome dung lenh cu (--user-data-dir {PROFILE_9222})")
    subprocess.Popen([CHROME, f"--user-data-dir={PROFILE_9222}", f"--remote-debugging-port={port}", "--no-first-run"],
                     creationflags=DETACH, close_fds=True)
    for _ in range(30):
        time.sleep(1.5)
        if _alive(url + "/json/version"):
            return url, True
    raise RuntimeError(f"khong mo duoc Chrome cong {port}")


@contextmanager
def open_group(g, log, force_busy=False, keep=False):
    """yield (ws, launched_9222). Ra khoi with -> dong dung profile vua mo.

    keep=True: MO profile va TRA ws, KHONG dong khi ra khoi with — nguoi goi tu dong sau
    (daily_parallel.py mo 3-4 profile cung luc, con chay xong moi dong).
    """
    eng = g["engine"]
    if eng == "gpm":
        _ensure_app("GPMLogin", f"{GPM}/profiles?per_page=1", GPM_EXE, log)
        pid = _gpm_find(g["mail"])
        if not pid:
            raise RuntimeError(f"khong thay profile GPM ten {g['mail']}")
        ws = _gpm_start(pid, log, force_busy)
        try:
            yield ws, False
        finally:
            if not keep:
                _gpm_stop(pid)
    elif eng == "ads":
        _ensure_app("AdsPower", f"{ADS}/status", ADS_EXE, log)
        ws = _ads_start(g["user_id"], log)
        try:
            yield ws, False
        finally:
            if not keep:
                _ads("/api/v1/browser/stop", user_id=g["user_id"])
    else:
        ws, launched = _open_9222(g["port"], log)
        yield ws, launched
