# -*- coding: utf-8 -*-
"""Debug: mo profile GPM roi xem Chrome song duoc bao lau, chet vi gi."""
import sys, os, time, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import requests
from daily_profiles import GPM, _gpm_find, _gpm_start, _gpm_stop

pid = _gpm_find("VirgiliTraino95@gmail.com")
print("profile id:", pid)

ws = _gpm_start(pid, lambda *a: print(*a, flush=True), force_busy=True)
print("WS:", ws)

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    page = br.contexts[0].new_page()
    page.set_default_timeout(60000)
    print("mo page OK")

    for step in range(6):
        t = time.time()
        try:
            page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=45000)
            dt = time.time() - t
            print(f"  goto lan {step+1}: {dt:.1f}s | url={page.url[:70]}")
        except Exception as e:
            print(f"  goto lan {step+1}: LOI {str(e)[:90]}")
            break
        time.sleep(5)
        o = subprocess.run(["wmic", "process", "where", "name='chrome.exe'", "get", "ProcessId"],
                           capture_output=True, text=True).stdout
        print(f"    chrome proc con: {o.count('chrome.exe')}")
    try:
        page.close()
    except Exception:
        pass

_gpm_stop(pid)
print("da stop profile")
