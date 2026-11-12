# -*- coding: utf-8 -*-
r"""Lam nong profile GPM lane X roi attach: doi kenh active qua channel_switcher, CHO trang dieu huong
xong han, dua tab ve Studio /channel/<id>, roi moi goi daily_0500_run.py --attach.

Ly do: studio_human._switch_via_switcher bam kenh xong nghi 7-10s roi goto studio -> Playwright bao
"Navigation to studio.youtube.com is interrupted by another navigation to www.youtube.com"
(tai hien 2 lan 2026-11-01 10:11 va 10:15). Script nay chi lam buoc chuyen kenh that cham, khong sua
code cu.

  PYTHONPATH= py -3.13 scratch_analysis\warm_lane_x.py
"""
from __future__ import annotations

import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
sys.path.insert(0, TOOLS)

from playwright.sync_api import sync_playwright   # noqa: E402

import daily_profiles as dp                      # noqa: E402
import studio_human as sh                        # noqa: E402

MAIL = "theeuxanh1@gmail.com"
TAB = "X"
TITLE = "AI謎解き研究所"


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def goto_safe(page, url, tries=4, log_fn=log):
    for i in range(tries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(random.uniform(6, 9))
            return True
        except Exception as exc:
            log_fn(f"    goto loi lan {i + 1}: {str(exc)[:110]}")
            time.sleep(random.uniform(8, 12))
    return False


def main() -> int:
    g = {"engine": "gpm", "mail": MAIL, "tabs": [TAB]}
    with dp.open_group(g, log) as (ws, _launched):
        log("ws =", ws)
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(ws)
            page = br.contexts[0].new_page()
            page.bring_to_front()
            page.set_default_timeout(90000)
            sh.maximize(page, log)

            goto_safe(page, "https://www.youtube.com/channel_switcher")
            item = page.locator("ytd-account-item-renderer", has_text=TITLE)
            log("so muc kenh khop:", item.count())
            if item.count():
                box = item.first.bounding_box()
                if box:
                    page.mouse.click(int(box["x"] + box["width"] / 2), int(box["y"] + box["height"] / 2))
                else:
                    item.first.click()
                # CHO that su: trang tu dieu huong sang youtube.com -> phai doi xong han
                try:
                    page.wait_for_load_state("load", timeout=60000)
                except Exception as exc:
                    log("    wait load:", str(exc)[:100])
                time.sleep(random.uniform(10, 14))
                log("sau khi bam, url =", (page.url or "")[:90])

            cid = ""
            for i in range(4):                      # bay #5: lan goto dau hay dung o root
                goto_safe(page, "https://studio.youtube.com/")
                cid = sh._studio_cid(page)
                log(f"lan {i + 1}: cid={cid or '?'} menu={'co' if sh._has_menu(page) else 'KHONG'}")
                if cid and sh._has_menu(page):
                    break
            if not cid:
                log("KHONG vao duoc Studio -> dung")
                page.close()
                return 1

            goto_safe(page, f"https://studio.youtube.com/channel/{cid}")
            log("url cuoi =", (page.url or "")[:90], "menu =", sh._has_menu(page))

            env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            env.update({
                "PYTHONIOENCODING": "utf-8",
                "DAILY_LANES_FILE": os.path.join(TOOLS, "daily_lanes_may1.json"),
                "DAILY_REPORT_SUBDIR": "may1_logon",
            })
            cmd = [sys.executable, os.path.join(TOOLS, "daily_0500_run.py"),
                   "--attach", ws, "--tab", TAB, "--no-lock"]
            log("chay:", " ".join(cmd[1:]))
            rc = subprocess.run(cmd, cwd=os.path.dirname(HERE), env=env).returncode
            log("daily_0500_run exit =", rc)
            try:
                page.close()
            except Exception:
                pass
            return rc


if __name__ == "__main__":
    sys.exit(main())
