# -*- coding: utf-8 -*-
r"""
TRANG THAI: snapshot view API, tinh view/gio, cooldown, khoa chong chay chong.

  state/snapshots.jsonl  {"t": epoch, "vid": ..., "views": ...}   (moi vong 1 dong / video)
  state/status.json      {vid: {"studio_at": epoch, "alert_at": epoch, "last_studio": {...}}}
  state/alerts.jsonl     moi lan bao anh 1 dong
  state/run.lock         pid + epoch; qua 30 phut coi la khoa chet
"""
import os, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
SNAP = os.path.join(STATE, "snapshots.jsonl")
STATUS = os.path.join(STATE, "status.json")
ALERTS = os.path.join(STATE, "alerts.jsonl")
LOCK = os.path.join(STATE, "run.lock")
KEEP_SNAP_HOURS = 80     # video >72h khong con theo doi -> snapshot cu hon 80h bo di


def append_jsonl(path, obj):
    os.makedirs(STATE, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush(); os.fsync(f.fileno())


def read_snaps():
    out = []
    if os.path.exists(SNAP):
        for ln in open(SNAP, encoding="utf-8"):
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def prune_snaps():
    snaps = read_snaps()
    keep = [s for s in snaps if time.time() - s["t"] < KEEP_SNAP_HOURS * 3600]
    if len(keep) != len(snaps):
        tmp = SNAP + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for s in keep:
                f.write(json.dumps(s) + "\n")
        os.replace(tmp, SNAP)


def rate_per_hour(snaps, vid, views, now, age_h):
    """view/gio CONG KHAI.
    Co snapshot cach 40-120 phut -> dung no (gan 60 phut nhat). Khong co (video moi / lan dau chay)
    -> views / tuoi video (chi khi tuoi >= 0.5h, tranh chia cho so qua nho)."""
    best = None
    for s in snaps:
        if s["vid"] != vid:
            continue
        dt = (now - s["t"]) / 60
        if 40 <= dt <= 120 and (best is None or abs(dt - 60) < abs((now - best["t"]) / 60 - 60)):
            best = s
    if best:
        return (views - best["views"]) / ((now - best["t"]) / 3600), "delta"
    if age_h >= 0.5:
        return views / age_h, "tu_luc_dang"
    return None, "chua_du"


def load_status():
    try:
        return json.load(open(STATUS, encoding="utf-8"))
    except Exception:
        return {}


def save_status(st):
    os.makedirs(STATE, exist_ok=True)
    tmp = STATUS + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, STATUS)


def acquire_lock():
    os.makedirs(STATE, exist_ok=True)
    if os.path.exists(LOCK):
        try:
            pid, t = open(LOCK).read().split()
            if time.time() - float(t) < 30 * 60:
                return False
        except Exception:
            pass
    open(LOCK, "w").write(f"{os.getpid()} {time.time()}")
    return True


def release_lock():
    try:
        os.remove(LOCK)
    except Exception:
        pass
