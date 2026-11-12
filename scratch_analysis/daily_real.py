# -*- coding: utf-8 -*-
"""Lay BANG SO THEO NGAY bang duong nguoi that: vao video truoc (bam tu danh sach),
roi chuyen sang Advanced mode. Khong goto URL explore truc tiep (-> Oops)."""
import sys, os, json, time
sys.path.insert(0, 'tools')

from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_daily as sd

WS = sys.argv[1]
CID = sys.argv[2]
VIDS = sys.argv[3].split(',')
TAG = sys.argv[4] if len(sys.argv) > 4 else '3vid'

DEEP = sc.DEEP  # chuoi JS, KHONG phai ham


def open_video_analytics(page, vid):
    """Vao trang analytics cua video, doi toi khi khong con 'Oops'."""
    page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-overview/period-default",
              wait_until="domcontentloaded")
    for _ in range(20):
        time.sleep(1.5)
        if vid not in page.url or 'tab-overview' not in page.url:
            continue
        if 'Oops' not in (page.evaluate(DEEP) or "")[:300]:
            return True
    return False


def click_advanced(page):
    """Bam 'Advanced mode' / 'Chế độ nâng cao' de mo bang so theo ngay."""
    for label in ("Advanced mode", "Chế độ nâng cao", "詳細モード", "アドバンス"):
        try:
            el = page.get_by_text(label, exact=False).first
            if el.count():
                el.click(timeout=8000)
                time.sleep(6)
                return label
        except Exception:
            continue
    return None


res = {}
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(90000)

    # 1. vao danh sach upload de Studio nap context kenh
    page.goto(f"https://studio.youtube.com/channel/{CID}/videos/upload",
              wait_until="domcontentloaded")
    for _ in range(25):
        time.sleep(2)
        if page.evaluate("() => document.querySelectorAll('ytcp-video-row').length"):
            break
    print("so dong danh sach:", page.evaluate("() => document.querySelectorAll('ytcp-video-row').length"), flush=True)

    for v in VIDS:
        print(f"[{v}] lay bang ngay ...", flush=True)
        try:
            ok = open_video_analytics(page, v)
            print(f"   mo analytics: {ok}  url={page.url[-70:]}", flush=True)
            if not ok:
                res[v] = {"current_distribution_status": "OOPS_ON_ANALYTICS"}
                continue

            # 2. thu Advanced mode
            lab = click_advanced(page)
            print(f"   advanced: {lab}", flush=True)

            # 3. doc bang ngay bang module co san
            r = sd.collect_daily(page, v, DEEP, lifetime_imp=None, hours_since_publish=None)
            print("   =>", json.dumps(r, ensure_ascii=False)[:400], flush=True)
            res[v] = r
        except Exception as e:
            print("   LOI:", str(e)[:250], flush=True)
            res[v] = {"current_distribution_status": f"ERROR: {str(e)[:120]}"}
        time.sleep(3)

open(f'reports/daily_real_{TAG}.json', 'w', encoding='utf-8').write(
    json.dumps(res, ensure_ascii=False, indent=1, default=str))
print("DA GHI", len(res))
