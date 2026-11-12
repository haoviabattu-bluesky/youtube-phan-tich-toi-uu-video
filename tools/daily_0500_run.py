# -*- coding: utf-8 -*-
r"""
JOB 05:00 MOI SANG (anh duyet 2026-10-16, plan plans/261016-0500-daily-metrics-sync/).
Moi lane: mo profile -> moi video cot L: rotate O->R, Q->S, ghi N–Q moi tu Studio -> ghi K + to/bo vang
CA DONG theo tools/daily_k_rules.py -> dong profile.

  py -3.13 tools\daily_0500_run.py --dry-run --tab F-teinengo-real     (chi in, KHONG ghi sheet)
  py -3.13 tools\daily_0500_run.py --tab F-teinengo-real               (that, 1 lane)
  pythonw  tools\daily_0500_run.py --scheduled                         (Task Scheduler DailyMetrics0500)

--scheduled: duoc tu dong profile GPM dang bi bao ProfileUsingByOther (memory daily-0500-profile-busy).
Loi 1 video / 1 lane -> ghi log, bo qua, chay tiep (memory skip-errors-never-halt).
Dung chung khoa view_spike/state/run.lock -> ViewSpikeWatch tu bo qua vong trong luc job nay chay.
"""
import os, sys, time, json, argparse, datetime, collections, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "view_spike"))
if sys.stdout is None or sys.stdout.__class__.__name__ == "NullWriter":
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")   # pythonw: khong co console
else:
    sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from sheet_metrics_sync import read_video_full
from daily_k_rules import k_note, vn_pct
from daily_profiles import open_group
import daily_sheet as dsh
import spike_sources, spike_state
import human_pace as hp
import studio_human as sh

TODAY = datetime.date.today().isoformat()
# May 1 (2026-10-31): DAILY_LANES_FILE / DAILY_REPORT_SUBDIR do tools/may1_logon_run.py dat -> lane + log rieng.
# Khong dat env thi y nhu cu (may 2: daily_lanes.json + reports/daily_0500).
LANES_FILE = os.environ.get("DAILY_LANES_FILE") or os.path.join(HERE, "daily_lanes.json")
SUBDIR = os.environ.get("DAILY_REPORT_SUBDIR") or "daily_0500"
OUT = os.path.join(ROOT, "reports", SUBDIR, TODAY)
LOGF = os.path.join(ROOT, "reports", SUBDIR, f"{TODAY}.log")
SESSION_BREAK_EVERY = 12   # cu 12 video nghi dai 90-240s (nhip nguoi that)
MAX_CONSEC_FAIL = 3        # 3 video lien tiep khong doc duoc -> dung lane (dung dot thoi gian vo ich)


TAG = os.environ.get("DAILY_TAG", "")   # nhan luong do daily_parallel.py dat — log 3 luong khong bi tron lan


def log(*a):
    line = time.strftime("%H:%M:%S ") + (f"<{TAG}> " if TAG else "") + " ".join(str(x) for x in a)
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOGF), exist_ok=True)
    with open(LOGF, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _pid_alive(pid):
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in r.stdout
    except Exception:
        return True   # khong kiem duoc thi coi nhu con song (an toan)


def lock_take(wait_min=15):
    """Lay khoa view_spike/state/run.lock.

    Khoa cua tien trinh DA CHET (bi kill/Ctrl+C/mat dien) phai bo ngay, khong doi 15 phut:
    dinh that 2026-10-18 — test bi kill luc 08:03 de lai lock PID 29620, task 05:00
    dung cho het 15 phut roi moi chay (Last Result 267009 = still running).
    """
    for _ in range(wait_min * 4):
        if spike_state.acquire_lock():
            return True
        try:
            pid = int(open(spike_state.LOCK).read().split()[0])
            if not _pid_alive(pid):
                os.remove(spike_state.LOCK)
                continue
        except Exception:
            pass
        time.sleep(15)
    return False


def lock_touch():
    open(spike_state.LOCK, "w").write(f"{os.getpid()} {time.time()}")


def api_meta(ids):
    """{vid: {'pub': datetime, 'ch': channelId, 'views': n}} — video rieng tu/hen gio khong co trong ket qua."""
    out = {}
    for it in spike_sources._get(ids, "snippet,statistics") if ids else []:
        out[it["id"]] = {"pub": spike_sources.pub_dt(it["snippet"]["publishedAt"]),
                         "ch": it["snippet"].get("channelId", ""),
                         "ch_title": it["snippet"].get("channelTitle", ""),
                         "views": int(it["statistics"].get("viewCount", 0))}
    return out


def cell_num(t):
    try:
        return float(t.strip())
    except Exception:
        return None


def do_tab(page, s, sids, tab, args, stat):
    rows, yel = dsh.read_tab(s, tab)
    targets = [(i, r[11].strip()) for i, r in enumerate(rows[1:], start=2) if len(r) > 11 and len(r[11].strip()) == 11]
    if not targets:
        log(f"[{tab}] khong co video_id o cot L -> bo qua"); return
    meta = api_meta([v for _, v in targets])
    chs = collections.Counter(m["ch"] for m in meta.values())
    if not chs:
        log(f"[{tab}] API khong tra video nao (rieng tu/hen gio) -> bo qua"); return
    ch = chs.most_common(1)[0][0]
    for m in meta.values():
        if m["ch"] and m["ch_title"]:
            sh.CH_TITLES[m["ch"]] = m["ch_title"]
    # sh.switch_channel: kiem CA menu (trang "Oops" cung co /channel/<id> trong URL), sai kenh active
    # thi tu doi qua channel_switcher. Ham cu o day chi so URL -> lane A bao "da vao kenh" roi truot het.
    if not sh.switch_channel(page, ch, log):
        log(f"[{tab}] KHONG chuyen duoc sang kenh {ch} (url={page.url[:90]}) -> bo qua lane"); stat["lane_fail"].append(tab); return
    dsh.backup(os.path.join(OUT, f"{tab}_truoc.json"), tab, rows, yel)
    updates = []
    fails_in_row = 0
    # R/S = so cua LAN CHAY TRUOC (ngay hom truoc). Chay lai trong ngay (sau khi sua tool, lane loi...)
    # ma xoay tiep thi R = chinh so vua ghi sang nay -> mat so cu. Luu R/S cua lan ghi DAU TIEN trong ngay.
    rot_path = os.path.join(OUT, f"{tab}_RS_goc.json")
    try:
        rotated = json.load(open(rot_path, encoding="utf-8"))
    except Exception:
        rotated = {}
    for row, vid in targets:
        lock_touch()
        if fails_in_row >= MAX_CONSEC_FAIL:
            log(f"[{tab}] {MAX_CONSEC_FAIL} video lien tiep khong doc duoc -> DUNG LANE nay, "
                f"khong dot tiep thoi gian (Studio dang chan / kenh co van de)")
            stat["lane_fail"].append(tab); break
        if stat["videos"] and stat["videos"] % SESSION_BREAK_EVERY == 0:
            hp.session_break(log)          # nguoi that nghi dai sau ~1 phien
        else:
            hp.between_videos(log)         # giua 2 video: doi 20-55s
        m = meta.get(vid)
        if not m:
            log(f"[{tab}] dong {row} {vid}: API khong co (chua cong khai?) -> bo qua"); continue
        r = None
        for attempt in (1, 2):
            try:
                r = read_video_full(page, vid, log=lambda *a: log(*a), expect_ch=ch)
                if r["ok"]:
                    break
            except Exception as e:
                log(f"[{tab}] dong {row} {vid}: LOI doc Studio {str(e)[:120]}")
            if attempt == 1:
                hp.after_oops(log)   # khong thu lai ngay lap tuc — Studio con dang chan
        if not r or not r["ok"]:
            log(f"[{tab}] dong {row} {vid}: khong doc duoc trang Reach 24h -> bo qua")
            stat["video_fail"] += 1; fails_in_row += 1; continue
        fails_in_row = 0
        cur = rows[row - 1] + [""] * 19
        hours = (datetime.datetime.now(datetime.timezone.utc) - m["pub"]).total_seconds() / 3600
        # Studio doc hut O/P -> GIU gia tri cu (so API cong khai thap hon Studio ~26%, khong dung de ghi de)
        old_o = cell_num(cur[14].replace(".", "").replace(",", ""))
        views = r["views"] if r["views"] is not None else (int(old_o) if old_o is not None else m["views"])
        ctr_total = r["ctr_total"] if r["ctr_total"] is not None else cell_num(cur[15].replace("%", "").replace(",", "."))
        if hours < 24 and r["ctr_24h"] is None and r["ctr_total"] is not None:
            r["ctr_24h"] = r["ctr_total"]   # dang <24h: "24h gan nhat" = tron doi; Studio custom period con tre so
        note, yellow = k_note(hours, views, ctr_total, r["ctr_24h"], r["imp_24h"])
        rs = rotated.setdefault(str(row), {"R": cur[14], "S": cur[16]})   # chi xoay 1 lan/ngay
        vals = {"R": rs["R"], "S": rs["S"], "N": str(int(hours // 24)), "O": str(int(views)),
                "P": vn_pct(ctr_total) if ctr_total is not None else "",
                "Q": vn_pct(r["ctr_24h"]) if r["ctr_24h"] is not None else "", "K": note}
        paint = True if yellow else (False if yel.get(row) else None)
        u = {"row": row, "vals": vals, "yellow": paint, "stt": cur[0], "bad": bool(yellow)}
        updates.append(u)
        stat["videos"] += 1; stat["yellow"] += yellow
        log(f"[{tab}] dong {row} {vid}: N={vals['N']} O={vals['O']} P={vals['P']} Q={vals['Q'] or '—'}"
            f" imp24h={r['imp_24h']} | {'VANG' if yellow else 'ok'} | K={note}")
        # Anh chot 2026-10-22: kiem xong TAP NAO GHI SHEET TAP DO NGAY (khong doi het lane — lane dai
        # 1-2 tieng, chet giua chung la mat het). Ghi loi -> log + di tiep tap khac.
        if not args.dry_run:
            try:
                dsh.write(s, tab, sids[tab], [u])
                json.dump(rotated, open(rot_path, "w", encoding="utf-8"), ensure_ascii=False)
                log(f"[{tab}] dong {row}: DA GHI SHEET")
            except Exception as e:
                log(f"[{tab}] dong {row}: LOI ghi sheet {str(e)[:160]}"); stat["write_fail"] += 1
                continue
            try:   # TONGHOP: tap CTR 24h thap -> "SỬA CTR" o (tap, lane)
                for x in dsh.tonghop(s, tab, [(u["stt"], u["bad"])],
                                     os.path.join(OUT, f"TONGHOP_truoc_{tab}_{time.strftime('%H%M%S')}.json")):
                    log(f"[{tab}] TONGHOP {x}")
            except Exception as e:
                log(f"[{tab}] LOI ghi TONGHOP: {str(e)[:200]}")
    if args.dry_run:
        log(f"[{tab}] DRY-RUN: {len(updates)} dong, KHONG ghi sheet")
    else:
        log(f"[{tab}] xong lane: {len(updates)} dong da ghi sheet (ghi tung tap ngay khi doc xong)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab", default="", help="chi chay cac tab nay (phan cach dau phay)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scheduled", action="store_true", help="che do 05:00: tu xu ly ProfileUsingByOther")
    ap.add_argument("--no-lock", action="store_true", help="tien trinh con cua daily_parallel.py (cha giu khoa)")
    ap.add_argument("--attach", default="", help="ws CDP cua profile DA MO SAN (daily_parallel.py mo ho, con chi doc)")
    ap.add_argument("--fast", action="store_true", help="TAT nhip nguoi that (chi de test/do thoi gian)")
    a = ap.parse_args()
    if a.fast:
        hp.set_on(False)
        log("--fast: TAT nhip nguoi that (chi dung de test)")
    cfg = json.load(open(LANES_FILE, encoding="utf-8"))
    only = {t.strip() for t in a.tab.split(",") if t.strip()}
    log(f"===== BAT DAU {'(DRY-RUN) ' if a.dry_run else ''}{'scheduled' if a.scheduled else 'tay'} =====")
    if not a.no_lock and not lock_take():
        log("view_spike dang giu khoa qua 15 phut -> DUNG"); return 1
    stat = {"videos": 0, "yellow": 0, "video_fail": 0, "write_fail": 0, "lane_fail": []}
    t0 = time.time()
    try:
        s = dsh.svc(); sids = dsh.sheet_ids(s)
        if a.attach:
            # Profile do CHA (daily_parallel.py) mo san -> chi attach, KHONG tu mo/dong profile.
            log(f"--- attach vao profile da mo san: {a.attach[:60]}...")
            tabs = []
            for g in cfg["groups"]:
                tabs += [t for t in g["tabs"] if (not only or t in only) and t in sids]
            log(f"--- tab se doc: {tabs}")
            with sync_playwright() as p:
                br = p.chromium.connect_over_cdp(a.attach)
                page = br.contexts[0].new_page()
                page.bring_to_front(); page.set_default_timeout(90000)
                sh.maximize(page, log)   # cua so hep -> menu Studio thu thanh icon (dinh 2026-10-22)
                for tab in tabs:
                    try:
                        do_tab(page, s, sids, tab, a, stat)
                    except Exception as e:
                        log(f"[{tab}] LOI lane: {str(e)[:200]}"); stat["lane_fail"].append(tab)
                    hp.pause(8, 25, "chuyen tab", log)
                page.close()
            msg = (f"{stat['videos']} video · {stat['yellow']} dòng vàng · lỗi {stat['video_fail']} video"
                   f" · lỗi ghi sheet {stat['write_fail']} · lane bỏ qua: {', '.join(stat['lane_fail']) or 'không'} · {int(time.time() - t0) // 60} phút")
            log("===== XONG:", msg)
            return 0
        for g in cfg["groups"]:
            tabs = [t for t in g["tabs"] if (not only or t in only)]
            tabs = [t for t in tabs if t in sids] if tabs else []
            if not tabs:
                continue
            log(f"--- nhom {g['engine']} {g.get('mail') or g.get('port')}: {tabs}")
            try:
                with open_group(g, log, force_busy=a.scheduled) as (ws, launched), sync_playwright() as p:
                    br = p.chromium.connect_over_cdp(ws)
                    page = br.contexts[0].new_page()
                    page.bring_to_front(); page.set_default_timeout(90000)
                    sh.maximize(page, log)
                    for tab in tabs:
                        try:
                            do_tab(page, s, sids, tab, a, stat)
                        except Exception as e:
                            log(f"[{tab}] LOI lane: {str(e)[:200]}"); stat["lane_fail"].append(tab)
                        hp.pause(8, 25, "chuyen tab", log)   # nguoi that doi sang tab khac
                    page.close()
                    if launched:
                        br.new_browser_cdp_session().send("Browser.close")   # chi dong Chrome do tool vua mo
            except Exception as e:
                log(f"LOI mo profile {g.get('mail') or g.get('port')}: {str(e)[:200]}"); stat["lane_fail"] += tabs
    finally:
        if not a.no_lock:
            spike_state.release_lock()
    msg = (f"{stat['videos']} video · {stat['yellow']} dòng vàng · lỗi {stat['video_fail']} video"
           f" · lỗi ghi sheet {stat['write_fail']} · lane bỏ qua: {', '.join(stat['lane_fail']) or 'không'} · {int(time.time() - t0) // 60} phút")
    log("===== XONG:", msg)
    if a.scheduled:
        import spike_notify
        spike_notify.toast("Chỉ số 05:00 xong", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
