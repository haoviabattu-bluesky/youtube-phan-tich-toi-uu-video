# -*- coding: utf-8 -*-
r"""
VIEW SPIKE WATCH — bao anh khi video MOI DANG dat >=1000 view/gio (so Studio).

  py -3.13 spike_watch.py                 1 vong (Task Scheduler goi moi 15 phut)
  py -3.13 spike_watch.py --dry-run       chi tang 1, khong mo Studio, khong toast, khong ghi snapshot
  py -3.13 spike_watch.py --force ID,ID   ep kiem Studio cac video nay (de test), bo qua nguong/cooldown
  py -3.13 spike_watch.py --test-toast    chi bat 1 toast thu

Luong (anh duyet 2026-10-15):
  Tang 1: sheet (cot L 10 tab lane) -> moi lane 2 video moi nhat <=72h -> API viewCount (1 unit/vong)
          -> view/gio cong khai >= 300 -> NGHI
  Tang 2: chi video NGHI -> mo dung profile kenh -> the Realtime -> >=1000 -> toast + alerts.jsonl
Khong ghi gi vao Google Sheet, khong sua gi tren YouTube. 0 token LLM.
"""
import os, sys, time, json, argparse, datetime, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "state", "spike_watch.log")


def _ensure_std():
    """pythonw (Task Scheduler, khong cua so) -> sys.stdout la None; module tools/ goi .reconfigure()
    luc import se crash cam. Phai chay TRUOC moi import khac."""
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if sys.stdout is None or sys.stderr is None:
        f = open(LOG, "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or f
        sys.stderr = sys.stderr or f
    else:
        sys.stdout.reconfigure(encoding="utf-8")


_ensure_std()
import spike_sources as src      # noqa: E402
import spike_state as ss         # noqa: E402
import spike_notify as notify    # noqa: E402


def log(msg):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    if not getattr(sys.stdout, "name", "") == LOG:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def studio_round(cfg, targets, status, dry):
    """targets = [(lane, vid, info, api_rate)] -> doc Studio theo tung profile, bao neu >= nguong."""
    import spike_studio_realtime as rt
    groups = {}
    for lane, vid, info, rate in targets:
        key = (f"port:{lane['port']}" if lane.get("port") else
               f"mail:{lane['mail']}" if lane.get("mail") else f"none:{lane['tab']}")
        groups.setdefault(key, []).append((lane, vid, info, rate))
    for key, items in groups.items():
        lane0 = items[0][0]
        log(f"  TANG 2 mo {key} cho {[v for _, v, _, _ in items]}")
        try:
            if key.startswith("none:"):
                raise RuntimeError("KHONG_CO_PROFILE: " + lane0.get("_ly_do", "chua khai mail/port"))
            res = rt.check_lane(lane0, [(v, i["channel_id"]) for _, v, i, _ in items], log)
        except Exception as e:
            log(f"  !! {key}: {e}")
            for lane, vid, info, rate in items:
                status.setdefault(vid, {})["studio_at"] = time.time()
                if not dry and rate is not None and time.time() - status[vid].get("unverified_at", 0) >= 3 * 3600:
                    why = "profile đang mở nơi khác" if "PROFILE_BUSY" in str(e) else "không mở được Studio"
                    notify.alert("KHONG_XAC_MINH", lane["tab"], vid, info["title"], round(rate),
                                 f"API ~{round(rate)} view/giờ (số công khai, thấp hơn Studio) — {why}")
                    status[vid]["unverified_at"] = time.time()
            continue
        for lane, vid, info, rate in items:
            r = res.get(vid, {})
            st = status.setdefault(vid, {})
            st["studio_at"], st["last_studio"] = time.time(), r
            log(f"  {lane['tab']} {vid}: Studio {r}")
            ph = r.get("per_hour")
            if ph is not None and ph >= cfg["alert_per_hour_studio"]:
                if time.time() - st.get("alert_at", 0) >= cfg["alert_cooldown_hours"] * 3600 and not dry:
                    hrs = ", ".join(f"{a}: {b:g}" for a, b in r.get("hours", [])) or r.get("mode")
                    notify.alert("SPIKE", ("(TEST) " if cfg.get("_test") else "") + lane["tab"], vid, info["title"], int(ph), hrs)
                    if not cfg.get("_test"):          # bao TEST khong duoc chan bao that 6 tieng
                        st["alert_at"] = time.time()
                    log(f"  >>> BAO ANH: {lane['tab']} {vid} {int(ph)} view/gio")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", default="", help="id,id: ep kiem Studio (test)")
    ap.add_argument("--test-toast", action="store_true")
    ap.add_argument("--alert", type=int, help="TEST: ha nguong Studio tam thoi (bao co nhan TEST, khong ghi cooldown that)")
    a = ap.parse_args()
    if a.test_toast:
        print("toast:", notify.toast("VIEW SPIKE (TEST)", "Thông báo thử của view_spike — bỏ qua"))
        return
    if not ss.acquire_lock():
        log("vong truoc chua xong (run.lock) -> bo qua vong nay")
        return
    t0 = time.time()
    try:
        cfg = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
        if a.alert is not None:
            cfg["alert_per_hour_studio"], cfg["alert_cooldown_hours"], cfg["_test"] = a.alert, 0, True
        meta = src.refresh_meta(cfg)
        wl = src.watch_list(cfg, meta)
        views = src.views_now([v for _, v, _, _ in wl])
        snaps, now, status = ss.read_snaps(), time.time(), ss.load_status()
        force = [x for x in a.force.split(",") if x]
        targets = []
        log(f"VONG MOI: {len(wl)} video dang theo doi")
        for lane, vid, info, age in wl:
            v = views.get(vid)
            if v is None:
                continue
            rate, how = ss.rate_per_hour(snaps, vid, v, now, age)
            if not a.dry_run:
                ss.append_jsonl(ss.SNAP, {"t": now, "vid": vid, "views": v})
            last = status.get(vid, {}).get("studio_at", 0)
            due = now - last >= cfg["studio_recheck_minutes"] * 60
            sus = rate is not None and rate >= cfg["suspect_per_hour_api"]
            flag = "NGHI" if sus else ""
            log(f"  {lane['tab']:<24} {vid} {age:5.1f}h view={v:<6} api/gio={'-' if rate is None else round(rate):<5} ({how}) {flag}")
            if vid in force or (sus and due):
                targets.append((lane, vid, info, rate))
        if targets and not a.dry_run:
            studio_round(cfg, targets, status, a.dry_run)
            ss.save_status(status)
        elif targets:
            log(f"  (dry-run) se mo Studio cho {[t[1] for t in targets]}")
        ss.prune_snaps()
        log(f"XONG {time.time() - t0:.1f}s · unit API vong nay = {src.UNITS_USED['n']} · mo Studio = {len(targets)} video")
    except Exception:
        log("LOI:\n" + traceback.format_exc())
    finally:
        ss.release_lock()


if __name__ == "__main__":
    main()
