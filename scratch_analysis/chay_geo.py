# -*- coding: utf-8 -*-
r"""Chay rieng lane GEO bang tay (job 03:00/logon bi loi "goto bi gian doan").

Nguyen nhan goc: studio.youtube.com tu dieu huong sang www.youtube.com DUNG luc goto
-> Playwright nem "Navigation ... is interrupted by another navigation" -> ca lane bi bo.
Script nay boc sh.switch_channel / sh.open_studio bang vong thu lai (khong sua file tools).

  env -u PYTHONPATH py -3.13 scratch_analysis/chay_geo.py --tab Lane-GEO
"""
import os, sys, json, time, random, argparse, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ.pop("PYTHONPATH", None)
from playwright.sync_api import sync_playwright
import daily_profiles as dp
import daily_sheet as dsh
import daily_0500_run as dq
import studio_human as sh
import human_pace as hp


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


ap = argparse.ArgumentParser()
ap.add_argument("--tab", default="Lane-GEO")
ap.add_argument("--mail", default="normaneileenpm218@gmail.com")
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

# ---- boc cac buoc dieu huong bang vong thu lai ----
_orig_switch = sh.switch_channel
_orig_open = sh.open_studio


def safe_switch(page, ch, log=None):
    for i in range(5):
        try:
            if _orig_switch(page, ch, log):
                return True
        except Exception as e:
            log(f"    · goto bi gian doan (lan {i+1}): {str(e)[:90]}")
        time.sleep(random.uniform(6, 11))
        if f"/channel/{ch}" in (page.url or "") and sh._has_menu(page):
            log("    · URL dung kenh + co menu -> di tiep")
            return True
    return False


def safe_open(page, log=None):
    for i in range(4):
        try:
            if _orig_open(page, log):
                return True
        except Exception as e:
            log(f"    · open_studio bi gian doan (lan {i+1}): {str(e)[:90]}")
        time.sleep(random.uniform(4, 8))
    return "/channel/" in (page.url or "")


sh.switch_channel = safe_switch
sh.open_studio = safe_open

g = {"engine": "gpm", "mail": a.mail}
stat = {"videos": 0, "yellow": 0, "video_fail": 0, "write_fail": 0, "lane_fail": []}
log(f"===== GEO TAY: {a.tab} | {a.mail} =====")
t0 = time.time()
s = dsh.svc()
sids = dsh.sheet_ids(s)
with dp.open_group(g, log) as (ws, launched), sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    page = br.contexts[0].new_page()
    page.bring_to_front()
    page.set_default_timeout(90000)
    sh.maximize(page, log)
    try:
        dq.do_tab(page, s, sids, a.tab, a, stat)
    except Exception as e:
        log(f"[{a.tab}] LOI lane: {str(e)[:200]}")
        stat["lane_fail"].append(a.tab)
    page.close()
    if launched:
        try:
            br.new_browser_cdp_session().send("Browser.close")
        except Exception:
            pass
log("===== XONG:", f"{stat['videos']} video · {stat['yellow']} vàng · fail {stat['video_fail']}"
    f" · ghi lỗi {stat['write_fail']} · lane bỏ qua {stat['lane_fail']} · {int(time.time()-t0)//60} phút")
