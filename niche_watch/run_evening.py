# -*- coding: utf-8 -*-
r"""DIEU PHOI nuoi ngach moi toi (Task Scheduler NicheWatch1800 goi luc 18:00).

Anh chot 2026-10-22: xoay vong 3-4 profile/luot. 10 lane, batch 4 -> 3 luot (4/3/3), chia deu thoi gian
con lai den 21:00 (~60'/luot). Thu tu lane xoay theo ngay de lane nao cung co hom duoc chay luot dau.
Moi lane = 1 tien trinh con (lane_worker.py) co han chot rieng; qua han + 4' an han ma chua thoat thi
taskkill CA CAY roi close_all dong profile. Het gio -> sweep dong moi profile con mo.

  py -3.13 niche_watch\run_evening.py                       # nhu Task Scheduler (cho toi 18:00 neu chay som)
  py -3.13 niche_watch\run_evening.py --start-now --end 19:30 --lanes E,F   # chay thu
  py -3.13 niche_watch\run_evening.py --dry-run            # in lich chia luot, khong mo gi
"""
import os, sys, math, time, random, argparse, datetime, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nw_common import ROOT, STATE, STOP_FILE, load_cfg, make_log, today_at, sleep_ok, pid_alive
import close_all

GRACE_S = 240
NEWGRP_NOWIN = 0x00000200 | 0x08000000
LOCK = os.path.join(STATE, "run_evening.lock")


def take_lock(log):
    if os.path.exists(LOCK):
        try:
            old = int(open(LOCK).read().strip())
            if pid_alive(old):
                log(f"Da co run_evening dang chay (PID {old}) -> thoat")
                return False
        except Exception:
            pass
    open(LOCK, "w").write(str(os.getpid()))
    return True


def make_batches(lanes, size):
    """Xoay thu tu theo ngay roi chia deu: 10 lane, size 4 -> [4,3,3]."""
    k = datetime.date.today().toordinal() % len(lanes)
    lanes = lanes[k:] + lanes[:k]
    nb = math.ceil(len(lanes) / size)
    base, extra = divmod(len(lanes), nb)
    out, i = [], 0
    for b in range(nb):
        n = base + (1 if b < extra else 0)
        out.append(lanes[i:i + n])
        i += n
    return out


def run_batch(batch, slot_end, end, log, extra=()):
    worker = os.path.join(ROOT, "lane_worker.py")
    procs = {}
    for j, lc in enumerate(batch):
        if j and not sleep_ok(random.randint(45, 90), slot_end):   # mo cach nhau cho do giat may
            break
        p = subprocess.Popen([sys.executable, worker, "--lane", lc["lane"], "--until", str(slot_end), "--force-busy", *extra],
                             cwd=ROOT, creationflags=NEWGRP_NOWIN)
        procs[lc["lane"]] = p
        log(f"  mo worker lane {lc['lane']} (PID {p.pid})")
    while any(p.poll() is None for p in procs.values()) and time.time() < min(slot_end, end) + GRACE_S:
        time.sleep(10)
    for lane, p in procs.items():
        if p.poll() is None:
            log(f"  worker lane {lane} qua han chua thoat -> taskkill ca cay PID {p.pid}")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True, creationflags=0x08000000)
        else:
            log(f"  worker lane {lane} thoat, ma {p.returncode}")
    cfg_lanes = {lc["lane"]: lc for lc in batch}
    for lane in procs:                      # luon dong lai lan nua (idempotent) — BAT BUOC dong
        close_all.close_lane(cfg_lanes[lane], log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-now", action="store_true")
    ap.add_argument("--end", help="HH:MM, mac dinh theo config")
    ap.add_argument("--lanes", default="", help="vd E,F,M (mac dinh: ca 10 lane)")
    ap.add_argument("--batch", type=int)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--watch-min", help="CHI de test, chuyen xuong worker: vd 2,3")
    a = ap.parse_args()
    cfg = load_cfg()
    log = make_log("run_evening")
    lanes = cfg["lanes"]
    if a.lanes:
        want = {x.strip().upper() for x in a.lanes.split(",") if x.strip()}
        lanes = [lc for lc in lanes if lc["lane"].upper() in want]
    end = today_at(a.end or cfg["end"])
    start = time.time() if a.start_now else max(time.time(), today_at(cfg["start"]))
    batches = make_batches(lanes, a.batch or cfg["batch_size"])
    slot = (end - start) / len(batches) if end > start else 0
    log(f"=== LICH {datetime.date.today()}: {len(lanes)} lane, {len(batches)} luot x {slot / 60:.0f}' — "
        f"{datetime.datetime.fromtimestamp(start):%H:%M} -> {datetime.datetime.fromtimestamp(end):%H:%M}")
    for i, b in enumerate(batches):
        log(f"  luot {i + 1}: {', '.join(lc['lane'] for lc in b)}")
    if a.dry_run or slot < 300:
        if slot < 300:
            log("Con duoi 5 phut moi luot -> khong chay")
        return
    if not take_lock(log):
        return
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)
    try:
        if not sleep_ok(start - time.time(), end):
            return
        for i, b in enumerate(batches):
            if time.time() >= end - 300 or os.path.exists(STOP_FILE):
                log("Het gio / co STOP -> khong mo luot moi")
                break
            slot_end = min(time.time() + slot, end)
            log(f"--- LUOT {i + 1}: {', '.join(lc['lane'] for lc in b)} den {datetime.datetime.fromtimestamp(slot_end):%H:%M}")
            run_batch(b, slot_end, end, log, ("--watch-min", a.watch_min) if a.watch_min else ())
    finally:
        close_all.sweep(log)
        try:
            os.remove(LOCK)
        except Exception:
            pass
        log("=== XONG buoi toi, da sweep dong profile")


if __name__ == "__main__":
    main()
