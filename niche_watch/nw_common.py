# -*- coding: utf-8 -*-
"""Dung chung cho niche_watch: duong dan, log, han chot/STOP, so "profile dang mo".

So profile dang mo = state/active_<lane>.json (moi lane 1 file -> cac worker ghi song song khong de nhau).
close_all.py --sweep doc cac file nay de dong; view_spike doc de KHONG stop ngang profile dang nuoi ngach.
"""
import os, sys, json, time, glob, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(ROOT)
TOOLS = os.path.join(PROJ, "tools")
H2DEV = os.environ.get("H2DEV_PIPELINE", r"E:\CLAUDE\YOUTUBE\h2dev\pipeline")
STATE = os.path.join(ROOT, "state")
LOGS = os.path.join(PROJ, "reports", "niche_watch")
STOP_FILE = os.path.join(ROOT, "STOP")
os.makedirs(STATE, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


def load_cfg():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def lane_cfg(cfg, lane):
    for x in cfg["lanes"]:
        if x["lane"].upper() == lane.upper():
            return x
    raise KeyError(f"khong co lane {lane} trong config.json")


def today_at(hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime.datetime.now().replace(hour=h, minute=m, second=0, microsecond=0).timestamp()


def day_dir():
    d = os.path.join(LOGS, f"{datetime.date.today()}")
    os.makedirs(d, exist_ok=True)
    return d


def make_log(name):
    path = os.path.join(day_dir(), f"{name}.log")

    def log(msg):
        line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
        try:
            print(line, flush=True)
        except Exception:
            pass   # pythonw: khong co stdout
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    return log


def stopped(deadline):
    return time.time() >= deadline or os.path.exists(STOP_FILE)


def sleep_ok(sec, deadline):
    """Ngu tung nhip <=5s; tra False neu toi han chot / co file STOP."""
    end = min(time.time() + sec, deadline)
    while time.time() < end:
        if os.path.exists(STOP_FILE):
            return False
        time.sleep(max(0.1, min(5, end - time.time())))
    return not stopped(deadline)


# ---------------- so profile dang mo ----------------
def _active_path(lane):
    return os.path.join(STATE, f"active_{lane}.json")


def mark_active(lane_c, worker_pid):
    info = {"lane": lane_c["lane"], "engine": lane_c["engine"], "mail": lane_c.get("mail"),
            "port": lane_c.get("port"), "user_id": lane_c.get("user_id"),
            "worker_pid": worker_pid, "opened_at": datetime.datetime.now().isoformat(timespec="seconds")}
    tmp = _active_path(lane_c["lane"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False)
    os.replace(tmp, _active_path(lane_c["lane"]))


def unmark_active(lane):
    try:
        os.remove(_active_path(lane))
    except FileNotFoundError:
        pass


def read_active():
    out = []
    for p in glob.glob(os.path.join(STATE, "active_*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            pass
    return out


def pid_alive(pid):
    """KHONG dung os.kill(pid, 0): tren Windows signal 0 = CTRL_C_EVENT, gui nham la giet tien trinh."""
    import subprocess
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                       creationflags=0x08000000)
    return str(pid) in r.stdout


def is_busy(mail=None, port=None):
    """view_spike goi: profile nay dang nuoi ngach khong? (mail so khong phan biet hoa thuong).
    File active cua worker DA CHET (crash, bi kill) thi bo qua — khong de view_spike bo lane mai mai."""
    for a in read_active():
        if a.get("worker_pid") and not pid_alive(a["worker_pid"]):
            continue
        if mail and (a.get("mail") or "").lower() == mail.lower():
            return True
        if port and a.get("port") == port:
            return True
    return False
