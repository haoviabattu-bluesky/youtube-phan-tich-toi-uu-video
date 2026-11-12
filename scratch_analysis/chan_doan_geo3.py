# -*- coding: utf-8 -*-
r"""Chan doan sau: vao Studio kenh GEO KHONG dung channel_switcher.

  env -u PYTHONPATH py -3.13 scratch_analysis/chan_doan_geo3.py
"""
import os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ.pop("PYTHONPATH", None)
from playwright.sync_api import sync_playwright
import daily_profiles as dp
import studio_human as sh

CH = "UCDSfOc6Zy36qgt66I-SQyYg"
OUT = os.path.join(ROOT, "reports", "geo_chan_doan")
os.makedirs(OUT, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def goto_safe(page, url, tag=""):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        log(f"{tag} goto ok -> {page.url[:110]}")
        return True
    except Exception as e:
        log(f"{tag} goto LOI: {str(e)[:110]} | url={page.url[:90]}")
        return False


def poll_menu(page, secs=45):
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            if sh._has_menu(page):
                log(f"   menu CO sau {int(time.time()-t0)}s | url={page.url[:100]}")
                return True
        except Exception as e:
            log("   _has_menu loi:", str(e)[:60])
        time.sleep(2)
    log(f"   menu KHONG co sau {secs}s | url={page.url[:100]}")
    return False


with dp.open_group({"engine": "gpm", "mail": "normaneileenpm218@gmail.com"}, log) as (ws, launched):
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(ws)
        ctx = br.contexts[0]
        page = ctx.new_page()
        page.bring_to_front()
        page.on("framenavigated", lambda f: log("   [nav]", (f.url or "")[:100]) if f == page.main_frame else None)
        goto_safe(page, "https://studio.youtube.com/", "1)")
        time.sleep(6)
        log("  url sau 6s:", page.url[:110])
        goto_safe(page, f"https://studio.youtube.com/channel/{CH}", "2)")
        ok = poll_menu(page, 45)
        if not ok:
            goto_safe(page, f"https://studio.youtube.com/channel/{CH}", "3)")
            ok = poll_menu(page, 45)
        try:
            log("  title:", (page.title() or "")[:80])
            log("  text:", page.inner_text("body")[:200].replace("\n", " | "))
        except Exception as e:
            log("  doc text loi:", str(e)[:80])
        page.screenshot(path=os.path.join(OUT, "sau_goto.png"))
        log("  ket qua:", "VAO DUOC" if ok else "KHONG VAO DUOC")
        try:
            page.close()
        except Exception:
            pass
        if launched:
            try:
                br.new_browser_cdp_session().send("Browser.close")
            except Exception:
                pass
