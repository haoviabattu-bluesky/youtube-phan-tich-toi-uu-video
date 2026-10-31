# -*- coding: utf-8 -*-
"""Probe 3: overview tab — cac moc 'still watching' + nhan khoang ngay; va vung nhan khoang ngay cua bang."""
import sys, os, time, re, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_daily as sd

VID = sys.argv[1] if len(sys.argv) > 1 else "nNlqnf28Kak"
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)

    page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-overview/period-default",
              wait_until="domcontentloaded", timeout=90000)
    parts = sc.wait_text(page, ["still watching", "Average view duration"])
    j = " | ".join(parts)
    print("N:", len(parts))
    print("MARKS:", re.findall(r"(\d+)% of viewers are still watching at around the ([\d:]+) mark", j))
    print("ERR:", "Oops, something went wrong" in j)
    for kw in ("still watching", "Average view duration", "Average percentage viewed", "Typical"):
        print(kw, "->", [t for t in parts if kw in t][:4])

    page.goto(sd.TABLE_URL.format(vid=VID), wait_until="domcontentloaded", timeout=90000)
    time.sleep(12)
    parts2 = page.evaluate(sc.DEEP)
    for i, t in enumerate(parts2):
        if re.fullmatch(r"[A-Z][a-z]{2} \d{1,2}, \d{4}", t.strip()) and i < 60:
            print("DATE_LABEL_AT", i, repr(parts2[max(0, i - 4):i + 4]))
            break
    print("EARLY:", parts2[:40])
    page.close()
