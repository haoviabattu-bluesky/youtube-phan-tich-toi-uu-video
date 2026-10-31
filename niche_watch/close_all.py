# -*- coding: utf-8 -*-
r"""DONG profile cua lane (BAT BUOC sau moi phien — anh chot 2026-10-22).

  gpm : GPM profiles/stop/<id> -> dong chrome cua DUNG profile theo PID (--user-data-dir chua id)
  ads : AdsPower browser/stop -> kiem lai trang thai Inactive
  cdp : Chrome 9222 lane M -> CDP Browser.close -> con song thi kill theo PID khop --user-data-dir
        (anh chot: lane M dong CA Chrome, ke ca khi AUTO_LIST mo san)
KHONG BAO GIO taskkill theo ten chrome.exe.

Chay tay / Task Scheduler 21:05 (luoi an toan):
  py -3.13 niche_watch\close_all.py --sweep          # dong moi lane con file state/active_*.json + giet worker con song
  py -3.13 niche_watch\close_all.py --lanes E,M      # dong dung cac lane nay
"""
import os, sys, json, time, argparse, subprocess
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nw_common import STATE, load_cfg, lane_cfg, make_log, read_active, unmark_active, pid_alive
import daily_profiles as dp

NOWIN = 0x08000000


def _chrome_procs():
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
          "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                         timeout=60, creationflags=NOWIN).stdout.strip()
    procs = json.loads(out) if out else []
    return [procs] if isinstance(procs, dict) else procs


def main_pids(marker):
    """PID tien trinh chrome CHINH (khong co --type=) co command line chua `marker` (khong phan biet hoa thuong)."""
    mk = marker.lower()
    return [p["ProcessId"] for p in _chrome_procs()
            if p.get("CommandLine") and mk in p["CommandLine"].lower() and "--type=" not in p["CommandLine"]]


def kill_by_marker(marker, log):
    """taskkill cay; con song thi Stop-Process -Force. Do that 2026-10-22 (may het RAM, GPM treo): taskkill
    bao "no running instance" trong khi Get-Process van thay tien trinh -> Stop-Process moi dong duoc."""
    hit = main_pids(marker)
    for x in hit:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(x)], capture_output=True, creationflags=NOWIN)
    if hit:
        time.sleep(3)
        left = main_pids(marker)
        if left:
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            f"Stop-Process -Id {','.join(map(str, left))} -Force -ErrorAction SilentlyContinue"],
                           capture_output=True, timeout=60, creationflags=NOWIN)
            time.sleep(3)
    return hit


ID_CACHE = os.path.join(STATE, "gpm_ids.json")


def gpm_id(lc, log):
    """Id profile GPM KHONG doi -> nho vao state/gpm_ids.json. GPM treo (API khong tra loi) van biet
    profile nao can dong (do that 2026-10-22: GPM Not Responding -> ca 3 lop dong deu that bai)."""
    try:
        cache = json.load(open(ID_CACHE, encoding="utf-8"))
    except Exception:
        cache = {}
    key = lc["mail"].lower()
    if key in cache:
        return cache[key]
    pid = dp._gpm_find(lc["mail"])
    if pid:
        cache[key] = pid
        with open(ID_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=1)
    return pid


def _close_9222(port, log):
    try:
        from playwright.sync_api import sync_playwright
        if dp._alive(f"http://127.0.0.1:{port}/json/version"):
            with sync_playwright() as p:
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=30000)
                br.new_browser_cdp_session().send("Browser.close")
            time.sleep(4)
    except Exception as e:
        log(f"  CDP Browser.close loi ({str(e)[:80]}) -> dong theo PID")
    hit = kill_by_marker(dp.PROFILE_9222, log)
    if hit:
        log(f"  Chrome 9222 con song -> da dong theo PID {hit}")
    return not dp._alive(f"http://127.0.0.1:{port}/json/version")


def close_lane(lc, log):
    """Tra True neu xac nhan da dong."""
    eng, name = lc["engine"], lc["lane"]
    try:
        if eng == "gpm":
            pid = gpm_id(lc, log)
            if not pid:
                log(f"[{name}] khong thay profile GPM {lc['mail']}")
                return False
            try:
                requests.get(f"{dp.GPM}/profiles/stop/{pid}", timeout=20)
                time.sleep(6)
            except Exception as e:
                log(f"[{name}] GPM khong tra loi ({type(e).__name__}) -> dong thang theo PID")
            hit = kill_by_marker(pid, log)
            ok = not main_pids(pid)
            log(f"[{name}] dong profile {pid[:8]}" + (f", dong them PID {hit}" if hit else "") + (" OK" if ok else " VAN CON"))
        elif eng == "ads":
            try:
                dp._ads("/api/v1/browser/stop", user_id=lc["user_id"])
            except Exception as e:
                log(f"[{name}] AdsPower khong tra loi ({type(e).__name__}) -> dong theo PID")
            time.sleep(4)
            hit = kill_by_marker(lc["user_id"], log)   # thu muc profile AdsPower chua user_id
            ok = not main_pids(lc["user_id"])
            log(f"[{name}] AdsPower {lc['user_id']}" + (f", dong them PID {hit}" if hit else "") + (" OK" if ok else " VAN CON"))
        else:
            ok = _close_9222(lc["port"], log)
            log(f"[{name}] Chrome {lc['port']}: {'da dong' if ok else 'VAN CON MO'}")
    except Exception as e:
        log(f"[{name}] LOI khi dong: {type(e).__name__} {str(e)[:150]}")
        return False
    if ok:
        unmark_active(name)
    return ok


def kill_worker(pid, log):
    if pid and pid_alive(pid):
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, creationflags=NOWIN)
        log(f"  da dung worker PID {pid} (ca cay tien trinh)")


def sweep(log):
    cfg = load_cfg()
    act = read_active()
    if not act:
        log("SWEEP: khong con profile nao tool mo -> xong")
        return True
    ok_all = True
    for a in act:
        kill_worker(a.get("worker_pid"), log)
        ok_all &= close_lane(lane_cfg(cfg, a["lane"]), log)
    log(f"SWEEP xong: {'tat ca da dong' if ok_all else 'CON PROFILE CHUA DONG — xem log'}")
    return ok_all


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--lanes", default="")
    a = ap.parse_args()
    log = make_log("close_all")
    if a.sweep:
        sys.exit(0 if sweep(log) else 1)
    cfg = load_cfg()
    res = [close_lane(lane_cfg(cfg, x.strip()), log) for x in a.lanes.split(",") if x.strip()]
    sys.exit(0 if all(res) else 1)
