# -*- coding: utf-8 -*-
r"""Thu 2 duong: (1) ep Accept-Language en-US xem Studio co ra tieng Anh khong;
(2) tim muc doi ngon ngu tren trang /account.

  env -u PYTHONPATH py -3.13 scratch_analysis/thu_doi_ngon_ngu.py
"""
import os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ.pop("PYTHONPATH", None)
from playwright.sync_api import sync_playwright
import daily_profiles as dp
import studio_human as sh

OUT = os.path.join(ROOT, "reports", "geo_chan_doan")
os.makedirs(OUT, exist_ok=True)
CH = "UCDSfOc6Zy36qgt66I-SQyYg"


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


with dp.open_group({"engine": "gpm", "mail": "normaneileenpm218@gmail.com"}, log) as (ws, launched):
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(ws)
        ctx = br.contexts[0]
        # (1) ep Accept-Language
        try:
            ctx.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
            log("da dat Accept-Language en-US cho context")
        except Exception as e:
            log("khong dat duoc header:", str(e)[:80])
        page = ctx.new_page()
        page.bring_to_front()
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)
        url = page.url[:100]
        try:
            has_en = bool(page.evaluate(sh.FIND, "Content"))
        except Exception:
            has_en = False
        log(f"studio url={url} | menu 'Content' = {has_en}")
        try:
            log("  title:", (page.title() or "")[:70])
            log("  text:", page.inner_text("body")[:150].replace("\n", " | "))
        except Exception:
            pass
        page.screenshot(path=os.path.join(OUT, "studio_header_en.png"))
        # (2) trang account: tim muc ngon ngu
        page.goto("https://www.youtube.com/account", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        full = page.inner_text("body")
        log("account text dai:", len(full))
        idx = full.find("Ngôn ngữ")
        log("vi tri 'Ngôn ngữ':", idx)
        if idx >= 0:
            log("  doan:", full[max(0, idx - 200):idx + 400].replace("\n", " | ")[:600])
        try:
            page.close()
        except Exception:
            pass
        if launched:
            try:
                br.new_browser_cdp_session().send("Browser.close")
            except Exception:
                pass
