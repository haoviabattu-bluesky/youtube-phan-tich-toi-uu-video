# -*- coding: utf-8 -*-
"""Probe: (1) khoang ngay cua bang theo ngay, (2) cac moc giu chan co trong tab Engagement."""
import sys, os, time, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_daily as sd

VID = sys.argv[1] if len(sys.argv) > 1 else "nNlqnf28Kak"
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)

    page.goto(sd.TABLE_URL.format(vid=VID), wait_until="domcontentloaded", timeout=90000)
    parts = []
    for _ in range(20):
        time.sleep(3)
        parts = page.evaluate(sc.DEEP)
        if sd.parse_table(parts):
            break
    print("RANGE_LABEL:", [t for t in parts if sd.RANGE_RE.match(t.strip())][:3])
    rows = sd.parse_table(parts)
    print("DAYS:", sorted(rows))
    print("END_DAY:", sd.report_end_day(parts))

    page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-engagement/period-default",
              wait_until="domcontentloaded", timeout=90000)
    parts2 = sc.wait_text(page, ["Average view duration", "still watching"])
    j = " | ".join(parts2)
    marks = re.findall(r"(\d+)% of viewers are still watching at around the ([\d:]+) mark", j)
    print("RETENTION_MARKS:", marks)
    print("HAS_STILL_WATCHING:", "still watching" in j)
    for k in ("Average view duration", "Average percentage viewed", "Typical view duration"):
        i = next((n for n, t in enumerate(parts2) if t.strip() == k), None)
        print(f"  {k} ->", parts2[i:i + 3] if i is not None else "NOT FOUND")
    page.close()
