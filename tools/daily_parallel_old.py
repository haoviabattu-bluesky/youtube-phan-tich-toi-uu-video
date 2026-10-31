# -*- coding: utf-8 -*-
r"""
Chay daily_0500_run.py DA LUONG: chia cac nhom profile (daily_lanes.json) cho N tien trinh con,
moi tien trinh mo 1 profile mot luc -> toi da N profile mo cung luc (anh yeu cau 2026-10-17).

  py -3.13 tools\daily_parallel.py --tab F-teinengo-real,Lane-N,... [--workers 3] [--dry-run]

Cha giu khoa view_spike/state/run.lock (con chay --no-lock, van lock_touch moi video).
"""
import os, sys, json, time, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "view_spike"))
import spike_state


def pid_alive(pid):
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
    return str(pid) in r.stdout


def take_lock(wait_min=15):
    for _ in range(wait_min * 4):
        if spike_state.acquire_lock():
            return True
        try:   # khoa cua tien trinh da chet -> bo
            pid = int(open(spike_state.LOCK).read().split()[0])
            if not pid_alive(pid):
                os.remove(spike_state.LOCK); continue
        except Exception:
            pass
        time.sleep(15)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    only = [t.strip() for t in a.tab.split(",") if t.strip()]
    cfg = json.load(open(os.path.join(HERE, "daily_lanes.json"), encoding="utf-8"))
    groups = [[t for t in g["tabs"] if t in only] for g in cfg["groups"]]
    groups = [g for g in groups if g]
    buckets = [[] for _ in range(min(a.workers, len(groups)))]
    for i, g in enumerate(groups):
        buckets[i % len(buckets)] += g
    if not take_lock():
        print("view_spike giu khoa qua 15 phut -> DUNG"); return 1
    try:
        procs = []
        for b in buckets:
            cmd = [sys.executable, os.path.join(HERE, "daily_0500_run.py"), "--no-lock", "--tab", ",".join(b)]
            if a.dry_run:
                cmd.append("--dry-run")
            print("chay:", b, flush=True)
            procs.append(subprocess.Popen(cmd, env={**os.environ, "PYTHONIOENCODING": "utf-8"}))
            time.sleep(20)   # gian cach mo profile, tranh dồn API GPM/AdsPower
        codes = [p.wait() for p in procs]
        print("xong, exit codes:", codes)
    finally:
        spike_state.release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
