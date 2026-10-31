# -*- coding: utf-8 -*-
"""Thu CTR 24h TRUOT (now-24h..now = cot Q) cho danh sach video_id — dung dinh nghia anh chot 2026-10-18.

  py -3.13 reports/collect_rolling24h.py --lane F-teinengo-real --mail ... --channel UC... --ids ...
Ghi JSON: reports/rolling24h_<lane>_<ngay>.json
"""
import sys, os, json, time, argparse, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
if sys.stdout is None or sys.stdout.__class__.__name__ == "NullWriter":
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")
else:
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright
import daily_profiles
from sheet_metrics_sync import read_video_full

LOG = os.path.join(ROOT, "reports", f"rolling24h_{datetime.date.today().isoformat()}.log")


def log(*a):
    line = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def switch_channel(page, ch):
    for _ in range(2):
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

    res = {}
    with daily_profiles.open_group(g, log) as (ws, launched):
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(ws)
            page = br.contexts[0].new_page()
            page.bring_to_front(); page.set_default_timeout(90000)
            if not switch_channel(page, a.channel):
                log(f"[{a.lane}] KHONG chuyen duoc kenh {a.channel}")
                return 3
            for n, vid in enumerate(ids, 1):
                r = None
                for _ in range(2):
                    try:
                        r = read_video_full(page, vid)
                        if r and r.get("ok"):
                            break
                    except Exception as e:
                        log(f"[{n}/{len(ids)}] {vid} LOI {str(e)[:100]}")
                res[vid] = r or {"ok": False}
                log(f"[{n}/{len(ids)}] {vid} ctr_24h_truot={r.get('ctr_24h') if r else None} "
                    f"imp_24h={r.get('imp_24h') if r else None} views={r.get('views') if r else None}")
            page.close()

    out = os.path.join(ROOT, "reports", f"rolling24h_{a.lane}_{datetime.date.today().isoformat()}.json")
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"[{a.lane}] GHI {out} ({len(res)} video)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
