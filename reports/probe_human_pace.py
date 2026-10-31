# -*- coding: utf-8 -*-
r"""Do nhip MOI: mo Chrome 9222 -> doc 1 video bang read_video_full (ban da sua) -> in thoi gian.

  py -3.13 reports/probe_human_pace.py --video 6rM_7jwLs2k
"""
import sys, os, time, argparse, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import human_pace as hp
from playwright.sync_api import sync_playwright
import sheet_metrics_sync as sc

ap = argparse.ArgumentParser()
ap.add_argument("--video", required=True)
ap.add_argument("--port", type=int, default=9222)
a = ap.parse_args()

ws = json.load(__import__("urllib.request", fromlist=["urlopen"]).urlopen(
    f"http://127.0.0.1:{a.port}/json/version", timeout=5))["webSocketDebuggerUrl"]
print("WS:", ws, flush=True)

t0 = time.time()
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.bring_to_front()
    page.set_default_timeout(90000)
    t1 = time.time()
    r = sc.read_video_full(page, a.video, log=lambda *x: print(*x, flush=True))
    el = time.time() - t1
print("\nKET QUA:", r)
print(f"THOI GIAN doc 1 video (nhip nguoi that) = {el:.0f}s = {el/60:.1f} phut")
print(f"TONG ca mo browser = {time.time()-t0:.0f}s")
