# -*- coding: utf-8 -*-
r"""
CHAY JOB 05:00 DA LUONG: mo 3-4 PROFILE CUNG LUC (anh yeu cau 2026-10-20).

Vi sao khong dung ban cu (daily_parallel_old.py): ban cu chi chia TAB cho tien trinh con, con van
tu mo profile va tu cho GPM/AdsPower -> mo profile lai tunh tu, 3 con cung goi GPM API mot luc de
bi ProfileUsingByOther. Ban nay: CHA mo san N profile (moi profile 1 lan, cach nhau vai giay), roi
giao (ws, tab) cho tien trinh con qua --attach -> con chi connect_over_cdp va doc. Con xong thi CHA
dong profile (con khong tu stop GPM nua).

  py -3.13 tools\daily_parallel.py --tab F-teinengo-real,Lane-Q,..  --workers 3
  py -3.13 tools\daily_parallel.py --workers 3 --dry-run
  pythonw  tools\daily_parallel.py --scheduled        (Task Scheduler DailyMetrics0500)

Nhip nguoi that (tools/human_pace.py) van bat: --workers tang so PROFILE, khong pha nhip moi trang.
Test nhanh: HUMAN_PACE_SCALE=0.05 hoac --fast.
"""
import os, sys, json, time, argparse, subprocess, threading
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "view_spike"))
if sys.stdout is None or sys.stdout.__class__.__name__ == "NullWriter":
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")
import spike_state
import daily_profiles as dp
import human_pace as hp

TODAY = time.strftime("%Y-%m-%d")
LOGF = os.path.join(ROOT, "reports", "daily_0500", f"{TODAY}.log")


def log(*a):
    line = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOGF), exist_ok=True)
    with open(LOGF, "a", encoding="utf-8") as f:
        f.write(line + "\n")


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


def gname(g):
    return g.get("mail") or g.get("user_id") or f"cdp{g.get('port')}"


def child_cmd(g, ws, a):
    return ([sys.executable, os.path.join(HERE, "daily_0500_run.py"),
             "--no-lock", "--attach", ws, "--tab", ",".join(g["tabs"])]
            + (["--dry-run"] if a.dry_run else []) + (["--fast"] if a.fast else []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab", default="", help="chi chay cac tab nay (phan cach dau phay); bo trong = tat ca")
    ap.add_argument("--workers", type=int, default=3, help="so profile mo CUNG LUC (3-4)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scheduled", action="store_true")
    ap.add_argument("--fast", action="store_true", help="TAT nhip nguoi that (chi de test)")
    ap.add_argument("--no-lock", action="store_true",
                    help="BO QUA khoa run.lock — CHI dung khi test 1-2 tab tren profile KHONG bi job khac dung")
    a = ap.parse_args()
    if a.fast:
        hp.set_on(False)
        log("--fast: TAT nhip nguoi that (chi de test)")

    cfg = json.load(open(os.path.join(HERE, "daily_lanes.json"), encoding="utf-8"))
    only = {t.strip() for t in a.tab.split(",") if t.strip()}
    groups = []
    for g in cfg["groups"]:
        tabs = [t for t in g["tabs"] if (not only or t in only)]
        if tabs:
            groups.append({**g, "tabs": tabs})
    if not groups:
        log("khong co tab nao khop -> dung"); return 1

    workers = max(1, min(a.workers, len(groups)))
    # chia theo SO TAB de can bang khoi luong (lane M 14 video vs lane K 2 video)
    load, buckets = [0] * workers, [[] for _ in range(workers)]
    for g in sorted(groups, key=lambda x: -len(x["tabs"])):
        i = load.index(min(load))
        buckets[i].append(g); load[i] += len(g["tabs"])
    log(f"===== DA LUONG {workers} profile cung luc | {len(groups)} nhom | "
        f"{len(only) or 'tat ca'} tab {'(DRY-RUN)' if a.dry_run else ''} =====")
    for i, b in enumerate(buckets, 1):
        log(f"  luong {i}: {[gname(g) for g in b]}")

    if not a.no_lock and not take_lock():
        log("view_spike giu khoa qua 15 phut -> DUNG"); return 1
    if a.no_lock:
        log("--no-lock: BO QUA khoa run.lock (chi dung de test)")
    t0 = time.time()
    open_lock = threading.Lock()   # GPM/AdsPower: moi lan chi MO 1 profile (3 luong goi API cung luc de ProfileInUse)

    def run_bucket(i, bucket):
        """1 luong = 1 hang doi profile: mo -> con doc -> DONG THAT -> profile tiep theo.

        Ban 2026-10-20 sai 2 cho (sua 2026-10-22): (1) mo voi keep=True nen cm.__exit__ KHONG dong
        profile nao — profile mo chong len nhau ca buoi; (2) cha cho tung luong THEO THU TU nen hang
        doi cua luong 2/3 phai doi luong 1 xong moi chay (job 101 phut).
        """
        hp.pause(0 if i == 1 else 8 * (i - 1), 15 * (i - 1) + 1, f"luong {i} cho mo profile", log)
        for g in bucket:
            name = gname(g)
            try:
                with open_lock:
                    log(f"  luong {i} mo profile: {g['engine']} {name}")
                    cm = dp.open_group(g, log, force_busy=a.scheduled)
                    ws, _ = cm.__enter__()
                try:
                    log(f"  luong {i} chay: {name} | tabs={g['tabs']}")
                    rc = subprocess.run(child_cmd(g, ws, a), cwd=ROOT,
                                        env={**os.environ, "PYTHONIOENCODING": "utf-8", "DAILY_TAG": name.split("@")[0]}
                                        ).returncode
                    log(f"  luong {i}: {name} xong (exit {rc})")
                finally:
                    cm.__exit__(None, None, None)    # daily_profiles stop GPM/AdsPower (9222 thi giu nguyen)
                    log(f"  luong {i}: dong profile {name}")
            except Exception as e:
                log(f"  luong {i} LOI {name}: {str(e)[:160]} -> bo qua, sang profile tiep")
            hp.pause(8, 15, "mo profile tiep theo", log)

    try:
        ths = [threading.Thread(target=run_bucket, args=(i, b), daemon=True) for i, b in enumerate(buckets, 1)]
        for t in ths:
            t.start()
        for t in ths:
            t.join()
    finally:
        if not a.no_lock:
            spike_state.release_lock()
    log(f"===== XONG DA LUONG: {int(time.time()-t0)//60} phut ({workers} profile cung luc)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
