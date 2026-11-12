# -*- coding: utf-8 -*-
"""Chay bu 8 tu khoa ngan bi loi chia doan go phim."""
import json, sys, time
sys.path.insert(0, r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis")
import geo_warm as G
from playwright.sync_api import sync_playwright

MISSING = ["地理", "地形", "地図", "土木", "河川", "湖", "海峡", "防災"]
LOG2 = r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\geo_warm_retry_log.txt"
open(LOG2, "w", encoding="utf-8").close()


def log(m):
    line = time.strftime("%H:%M:%S ") + m
    print(line, flush=True)
    open(LOG2, "a", encoding="utf-8").write(line + "\n")


rep = []
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(G.WS)
    page = br.contexts[0].pages[0]
    for i, kw in enumerate(MISSING, 1):
        log("[%d/%d] TU KHOA: %s (warm)" % (i, len(MISSING), kw))
        try:
            G.search(page, kw)
            res = G.results(page, 8)
            if not res:
                log("  ! khong co ket qua")
                rep.append({"kw": kw, "status": "NO_RESULT"})
                continue
            pick = res[0]
            log("  chon: %s | %s | %s" % (pick["id"], (pick.get("views") or "?"), pick.get("title", "")[:55]))
            page.goto("https://www.youtube.com/watch?v=" + pick["id"],
                      wait_until="domcontentloaded", timeout=90000)
            time.sleep(5)
            G.dismiss_popups(page)
            G.skip_ad(page)
            dur = __import__("random").randint(95, 200)
            w = G.watch(page, dur, kw)
            rep.append({"kw": kw, "kind": "warm", "id": pick["id"], "title": pick.get("title"),
                        "views": pick.get("views"), "watched_s": w})
            time.sleep(__import__("random").uniform(1.5, 3.5))
        except Exception as e:
            log("  !! LOI: %s" % e)
            rep.append({"kw": kw, "status": "ERROR", "err": str(e)[:150]})
    br.close()

path = r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\geo_warm_retry_report.json"
json.dump(rep, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("=== XONG BU ===")
