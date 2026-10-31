# -*- coding: utf-8 -*-
"""Thu so 1 lane tu danh sach video_id (cot L cua sheet), 3 luong song song.

  py -3.13 reports/collect_lane_by_ids.py --lane F-teinengo-real --mail VirgiliTraino95@gmail.com \
      --channel UCIimxP275YufOXXIlu9y9Lg --ids pTmVyc6Z2W4,vy7ucq5Zy64,...

Ghi noi tiep vao youtube_postpublish_metrics.csv (cung schema studio_collect).
Profile duoc mo bang daily_profiles.open_group (xu ly GPM/AdsPower/9222 + ProfileUsingByOther).
"""
import sys, os, time, argparse, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "view_spike"))
if sys.stdout is None or sys.stdout.__class__.__name__ == "NullWriter":
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")
else:
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_daily
import daily_profiles
import spike_sources

LOG = os.path.join(ROOT, "reports", f"collect_byids_{datetime.date.today().isoformat()}.log")


def log(*a):
    line = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def switch_channel(page, ch):
    for _ in range(2):   # bay #5: lan goto dau hay dung o root
        page.goto(f"https://studio.youtube.com/channel/{ch}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)
        if f"/channel/{ch}" in (page.url or ""):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane", required=True)
    ap.add_argument("--channel", required=True)
    ap.add_argument("--ids", required=True)
    ap.add_argument("--mail")
    ap.add_argument("--user-id")
    ap.add_argument("--port", type=int)
    a = ap.parse_args()

    ids = [x.strip() for x in a.ids.split(",") if x.strip()]
    g = {"engine": "gpm", "mail": a.mail, "tabs": [a.lane]}
    if a.user_id:
        g = {"engine": "ads", "user_id": a.user_id, "mail": a.mail, "tabs": [a.lane]}
    if a.port:
        g = {"engine": "cdp", "port": a.port, "tabs": [a.lane]}

    meta = {}
    for it in spike_sources._get(ids, "snippet,statistics"):
        meta[it["id"]] = {"pub": spike_sources.pub_dt(it["snippet"]["publishedAt"]),
                          "title": it["snippet"]["title"],
                          "ch": it["snippet"].get("channelId", ""),
                          "views": int(it["statistics"].get("viewCount", 0))}
    log(f"=== {a.lane} === {len(ids)} id, API co {len(meta)}, profile {a.mail or a.user_id or a.port}")

    rows = []
    with daily_profiles.open_group(g, log) as (ws, launched):
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(ws)
            page = br.contexts[0].new_page()
            page.bring_to_front(); page.set_default_timeout(90000)
            if not switch_channel(page, a.channel):
                log(f"[{a.lane}] KHONG chuyen duoc sang kenh {a.channel} (url={page.url[:90]})")
                return 3
            for n, vid in enumerate(ids, 1):
                if vid not in meta:
                    log(f"[{n}/{len(ids)}] {vid}: API khong co (rieng tu/hen gio) -> bo qua")
                    continue
                m = meta[vid]
                r = None
                for _ in range(2):
                    try:
                        r = sc.collect_video(page, vid)
                        if r.get("impressions"):
                            break
                    except Exception as e:
                        log(f"[{n}/{len(ids)}] {vid}: LOI {str(e)[:110]}")
                if not r or not r.get("impressions"):
                    log(f"[{n}/{len(ids)}] {vid}: khong doc duoc Reach -> bo qua")
                    continue
                hours = (datetime.datetime.now(datetime.timezone.utc) - m["pub"]).total_seconds() / 3600
                r["lane"] = a.lane
                r["channel"] = a.channel
                r["title"] = r.get("title") or m["title"]
                r["hours_since_publish"] = int(hours)
                try:
                    imp = r.get("impressions")
                    imp = float(imp) if imp not in (None, "") else 0.0
                    vw = r.get("views")
                    vw = float(vw) if vw not in (None, "") else None
                    d = studio_daily.collect_daily(page, vid, sc.DEEP, imp, hours, vw)
                    r.update(d)
                except Exception as e:
                    import traceback
                    log(f"[{n}/{len(ids)}] {vid}: LOI daily {str(e)[:110]}")
                    log(traceback.format_exc()[-600:])
                rows.append(r)
                log(f"[{n}/{len(ids)}] {vid} imp={r.get('impressions')} ctr={r.get('ctr')} "
                    f"view={r.get('views')} age={hours:.1f}h ctr24={r.get('ctr_last_24h')} "
                    f"mark={r.get('mark_needed')}")
            page.close()

    if rows:
        with open(sc.CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
            w = sc.csv.DictWriter(f, fieldnames=sc.COLUMNS, extrasaction="ignore")
            for r in rows:
                w.writerow({c: r.get(c, "") for c in sc.COLUMNS})
        log(f"[{a.lane}] DA GHI {len(rows)} dong vao CSV")
    else:
        log(f"[{a.lane}] KHONG thu duoc dong nao")
    return 0


if __name__ == "__main__":
    sys.exit(main())
