# -*- coding: utf-8 -*-
"""Thu so Studio: don modal, vao danh sach upload, roi doc tung video."""
import sys, os, json, time
sys.path.insert(0, 'tools')

from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_human as sh
import human_pace as hp

WS = sys.argv[1]
CID = sys.argv[2]
VIDS = sys.argv[3].split(',')

out = []
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(90000)

    # don modal/dialog dang mo
    page.keyboard.press("Escape")
    time.sleep(1.5)
    try:
        page.evaluate("""() => {
          for (const b of document.querySelectorAll('ytcp-button, tp-yt-paper-button, button')) {
            const t = (b.innerText||'').trim();
            if (['Close','Cancel','Deselect all'].includes(t)) {}
          }
        }""")
    except Exception:
        pass

    print("vao danh sach upload...", flush=True)
    page.goto(f"https://studio.youtube.com/channel/{CID}/videos/upload", wait_until="domcontentloaded")
    for _ in range(20):
        time.sleep(2)
        n = page.evaluate("() => document.querySelectorAll('ytcp-video-row').length")
        if n:
            print("  so dong:", n, flush=True)
            break
    print("  URL:", page.url[:100], flush=True)

    for v in VIDS:
        print(f"[{v}] thu...", flush=True)
        try:
            row = sc.collect_video(page, v, log=lambda *x: print("   ", *x, flush=True))
            print("   OK impr={impressions} ctr={ctr} views={views} avd={avd_sec} apv={apv_pct} "
                  "browse={browse_pct} sugg={suggested_pct} search={search_pct}".format(**row), flush=True)
            out.append(row)
        except Exception as e:
            print("   LOI:", str(e)[:250], flush=True)
        time.sleep(3)

    open('reports/collect_3vid.json', 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    print("DA GHI reports/collect_3vid.json", len(out))
