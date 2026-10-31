# -*- coding: utf-8 -*-
r"""1 LANE: mo profile -> (M/O chuyen dung kenh) -> tim theo sheet -> xem video dung ngach 10-15' ->
di tiep theo cot de xuat ben phai -> ... -> toi han chot thi DONG profile (luon, ke ca khi loi).

  py -3.13 niche_watch\lane_worker.py --lane E --until-min 20     # chay thu 20 phut
  py -3.13 niche_watch\lane_worker.py --lane E --dry-run          # chi doc sheet, in ngach + 10 truy van
run_evening.py goi voi --until <epoch>. Dung giua chung: tao file niche_watch\STOP.
Ghi: reports\niche_watch\<ngay>\<lane>.log + watched_<lane>.csv ; state\seen_<lane>.json (video da xem).
"""
import os, sys, csv, json, time, random, argparse, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nw_common import (STATE, load_cfg, lane_cfg, make_log, day_dir, stopped, sleep_ok,
                       mark_active, unmark_active)
import sheet_queries as sq
import judge
import yt_actions as yt
import daily_profiles as dp
import close_all


class Seen:
    def __init__(self, lane):
        self.path = os.path.join(STATE, f"seen_{lane}.json")
        try:
            self.ids = set(json.load(open(self.path, encoding="utf-8")))
        except Exception:
            self.ids = set()

    def add(self, vid):
        self.ids.add(vid)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(sorted(self.ids), f)


def csv_row(lane, row):
    p = os.path.join(day_dir(), f"watched_{lane}.csv")
    new = not os.path.exists(p)
    with open(p, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "lane", "video_id", "title", "channel", "views", "length", "source", "minutes", "react"])
        w.writerow(row)


def session(page, lc, cfg, ctx_data, deadline, log):
    niche, examples, pool, own_ids, seen = ctx_data
    own_names = [lc.get("channel_name", "")]
    model, n, chain, on_watch, errs = cfg["vision_model"], 0, 0, False, 0
    while not stopped(deadline):
        try:
            if not on_watch:
                q = pool.next()
                log(f"TIM: {q}")
                yt.search(page, q)
                cands, source = yt.read_videos(page, "ytd-search", cfg["search_top"]), f"search:{q}"
            else:
                yt.wait_suggestions(page)
                cands, source = yt.read_videos(page, "#secondary", cfg["suggest_top"]), "suggest"
            cands = yt.prefilter(cands, seen.ids, own_ids, own_names, cfg["min_length_sec"])
            ok = judge.pick_ok(cands, niche, examples, model, log) if cands else []
            if not ok:
                log(f"  {'ket qua' if not on_watch else 'de xuat'}: khong co video dat ({len(cands)} ung vien) -> tim truy van khac")
                on_watch, chain = False, 0
                if not sleep_ok(random.randint(15, 45), deadline):
                    break
                continue
            best = max(ok, key=lambda x: x["views"])
            mins = random.uniform(*cfg["watch_minutes"])
            log(f"  XEM ({source[:40]}) {best['views']:,} view | {best['title'][:60]} | {best['channel']} | {best['id']} | dinh {mins:.1f}'")
            sec, react = yt.watch(page, best, mins, deadline, cfg["like_prob"], cfg["sub_prob"])
            seen.add(best["id"])
            n += 1
            chain = chain + 1 if on_watch else 1
            log(f"  #{n} da xem {sec / 60:.1f}' | {react}")
            csv_row(lc["lane"], [f"{datetime.datetime.now():%H:%M:%S}", lc["lane"], best["id"], best["title"],
                                 best["channel"], best["views"], best["length"], source, round(sec / 60, 1), react])
            on_watch = chain < cfg["max_chain"]
            errs = 0
            if not sleep_ok(random.randint(5, 20), deadline):
                break
        except Exception as e:
            errs += 1
            log(f"  LOI {type(e).__name__}: {str(e)[:160]} -> lam lai tu tim kiem (loi lien tiep {errs})")
            on_watch, chain = False, 0
            if page.is_closed() or not page.context.browser.is_connected():
                raise
            # Do that 2026-10-22 lane E: Chrome TREO (ca /json/list khong tra loi) nhung CDP van "connected"
            # -> goto timeout lap lai den het gio. 2 loi lien tiep = coi nhu hong -> dong profile, mo lai.
            if errs >= 2:
                raise RuntimeError(f"TRINH_DUYET_TREO: {errs} loi lien tiep") from e
            sleep_ok(20, deadline)
    return n


def run_once(lc, cfg, ctx_data, deadline, log, force_busy):
    from playwright.sync_api import sync_playwright
    if lc["engine"] == "gpm":
        close_all.gpm_id(lc, log)            # nho id luc GPM con tra loi -> GPM treo van dong duoc
    for k in range(3):                       # anh chot: chay theo lich, profile ban -> tu dong + mo lai "bang duoc"
        try:
            with dp.open_group(lc, log, force_busy=force_busy, keep=True) as (ws, _launched):
                break
        except Exception as e:
            log(f"MO PROFILE that bai lan {k + 1}/3: {str(e)[:150]}")
            if "PROFILE_BUSY" in str(e):     # chay tay ban ngay: giu bay #9, khong dong profile nguoi khac dang dung
                raise
            close_all.close_lane(lc, log)
            if not sleep_ok(60, deadline):
                return 0
    else:
        raise RuntimeError("khong mo duoc profile sau 3 vong")
    mark_active(lc, os.getpid())
    log(f"Da mo profile lane {lc['lane']} ({lc.get('mail') or lc.get('user_id')})")
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws, timeout=60000)
        page = br.contexts[0].new_page()
        page.bring_to_front()                # tab nen khong an chuot on dinh (bay lane M)
        if lc.get("channel_id"):
            import studio_human as sh
            sh.CH_TITLES[lc["channel_id"]] = lc["channel_name"]
            if not sh.switch_channel(page, lc["channel_id"], log):
                raise RuntimeError(f"KHONG chuyen duoc sang kenh {lc['channel_name']} -> khong xem (se tinh cho kenh khac)")
            log(f"Da o dung kenh {lc['channel_name']}")
        if yt.history_paused(page):
            log("CANH BAO: 'Lich su xem' cua kenh nay dang TAT -> xem bao nhieu YouTube cung khong hoc ngach. Anh bat lai giup.")
        return session(page, lc, cfg, ctx_data, deadline, log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane", required=True)
    ap.add_argument("--until", type=float, help="epoch han chot")
    ap.add_argument("--until-min", type=float, help="chay N phut tu bay gio")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force-busy", action="store_true",
                    help="CHI run_evening (lich 18h) dung: profile ban -> tu dong roi mo lai. Chay tay khong co co nay")
    ap.add_argument("--watch-min", help="CHI de test: ghi de watch_minutes, vd 2,3")
    a = ap.parse_args()
    cfg = load_cfg()
    if a.watch_min:
        cfg["watch_minutes"] = [float(x) for x in a.watch_min.split(",")]
    lc = lane_cfg(cfg, a.lane)
    log = make_log(lc["lane"])
    data = sq.read_tab(lc["tab"])
    niche, examples = sq.niche_text(lc, data)
    pool = sq.QueryPool(lc, data)
    if a.dry_run:
        log(f"[DRY] lane {lc['lane']} tab {lc['tab']} | {len(data['eps'])} tap co E | {len(data['own_ids'])} id cua minh | {len(pool.items)} truy van")
        log(f"[DRY] NGACH: {niche}")
        for q in random.sample(list(pool.items), min(8, len(pool.items))):
            log(f"[DRY]   truy van: {q[:80]}")
        return
    deadline = a.until or (time.time() + (a.until_min or 30) * 60)
    log(f"=== BAT DAU lane {lc['lane']} — han chot {datetime.datetime.fromtimestamp(deadline):%H:%M:%S}")
    ctx_data = (niche, examples, pool, data["own_ids"], Seen(lc["lane"]))
    total, fails, last_err = 0, 0, ""
    try:
        while not stopped(deadline) and fails < 3:
            try:
                total += run_once(lc, cfg, ctx_data, deadline, log, a.force_busy)
                fails = 0
            except Exception as e:
                fails, last_err = fails + 1, str(e)
                if "PROFILE_BUSY" in last_err:
                    log(f"PROFILE BAN ({last_err[:120]}) -> dung lane, khong kill (chay tay)")
                    break
                log(f"MAT KET NOI / LOI ({type(e).__name__}: {str(e)[:150]}) lan {fails}/3 -> dong profile, mo lai sau 30s")
                close_all.close_lane(lc, log)
                if "KHONG chuyen duoc" in str(e) or "PROFILE_BUSY" in str(e):
                    break
                sleep_ok(30, deadline)
    finally:
        if "PROFILE_BUSY" in last_err:          # profile cua nguoi khac dang dung -> KHONG dong
            log(f"=== KET THUC lane {lc['lane']}: profile dang ban (chay tay) -> khong mo, khong dong")
            return
        ok = close_all.close_lane(lc, log)    # BAT BUOC dong
        if ok:
            unmark_active(lc["lane"])
        log(f"=== KET THUC lane {lc['lane']}: xem {total} video | profile {'DA DONG' if ok else 'CHUA DONG — sweep 21:05 se dong'}")


if __name__ == "__main__":
    main()
