# -*- coding: utf-8 -*-
"""DRY RUN: kiem tra like + o binh luan + go chu (KHONG gui) tren 1 video bat ky.
Dung de validate selector truoc khi chay phien warmup dai 2h."""
import sys, time, json
sys.path.insert(0, r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis")
import importlib.util
spec = importlib.util.spec_from_file_location(
    "wm", r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\warm_miguel.py")
wm = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0]]
spec.loader.exec_module(wm)   # chi nap module, main() khong tu chay

from playwright.sync_api import sync_playwright

WS = wm.WS
VID = "ln2MnW72zHM"   # video lich su KHAC (khong phai 2 video muc tieu)

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.youtube.com/watch?v=" + VID, wait_until="domcontentloaded", timeout=90000)
    time.sleep(9)

    print("--- 1) LIKE INFO (chua bam):", json.dumps(page.evaluate(wm.JS_LIKE_INFO), ensure_ascii=False))
    print("--- 2) RECS (panel phai):")
    rr = wm.recs(page, 12)
    for x in rr:
        print("   ", x["id"], "|", (x.get("dur") or "?"), "|", (x.get("title") or "")[:52], "|", x.get("ch"))
    print("   score vid dau:", wm.score_candidate(rr[0], set()) if rr else "n/a")

    print("--- 3) MO O BINH LUAN + GO THU (khong gui)")
    for _ in range(7):
        page.mouse.wheel(0, 700); time.sleep(1.0)
    time.sleep(3)
    r = page.evaluate(wm.JS_OPEN_BOX)
    print("   simplebox:", r)
    if r:
        page.mouse.click(r["x"], r["y"]); time.sleep(3)
        ce = page.evaluate(wm.JS_CE_RECT)
        print("   contenteditable:", ce)
        if ce:
            page.mouse.click(ce["x"], ce["y"]); time.sleep(1.2)
            wm.go_tu_nhien(page, "テスト")
            time.sleep(1.5)
            print("   text doc lai:", repr(page.evaluate(wm.JS_CE_TEXT)))
            print("   submit rect (enabled?):", page.evaluate(wm.JS_SUBMIT_RECT))
            # HUY: khong gui
            cancelled = page.evaluate("""() => {
              const bs = Array.from(document.querySelectorAll('#cancel-button button, ytd-commentbox #cancel-button'));
              for (const b of bs) { const r=b.getBoundingClientRect(); if (r.width>20) { b.click(); return true; } }
              return false;
            }""")
            print("   da bam Cancel (khong gui):", cancelled)
    page.screenshot(path=r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\dryrun.png")
    br.close()
