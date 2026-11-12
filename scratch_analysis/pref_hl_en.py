# -*- coding: utf-8 -*-
r"""Doc cookie PREF cua youtube, doi hl=<ngon ngu> roi reload Studio -> kiem tra menu 'Content'.
Khong doi cai dat tai khoan Google/YouTube, chi doi tham so ngon ngu trong cookie cua profile.

  PYTHONPATH= py -3.13 scratch_analysis\pref_hl_en.py [--dry]
"""
from __future__ import annotations

import os
import random
import sys
import time
from urllib.parse import parse_qsl, urlencode

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
sys.path.insert(0, TOOLS)

from playwright.sync_api import sync_playwright   # noqa: E402

import daily_profiles as dp                      # noqa: E402
import studio_human as sh                        # noqa: E402

MAIL = "theeuxanh1@gmail.com"
CID = "UC8BO9Ni37bUDbJrHez1zA7w"
DRY = "--dry" in sys.argv


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def check(page, tag):
    out = {}
    for label in ("Content", "Nội dung", "Analytics", "Số liệu phân tích"):
        try:
            out[label] = bool(page.evaluate(sh.FIND, label))
        except Exception as exc:
            out[label] = f"loi {str(exc)[:30]}"
    log(f"{tag}: {out}")
    return out


def main() -> int:
    g = {"engine": "gpm", "mail": MAIL, "tabs": ["X"]}
    with dp.open_group(g, log) as (ws, _l):
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(ws)
            ctx = br.contexts[0]
            page = ctx.new_page()
            page.bring_to_front()
            page.set_default_timeout(90000)
            sh.maximize(page, log)
            try:
                page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
            except Exception as exc:
                log("goto yt:", str(exc)[:80])
            time.sleep(6)

            cks = [c for c in ctx.cookies() if c["name"] in ("PREF", "VISITOR_INFO1_LIVE")]
            for c in cks:
                log(f"cookie {c['name']} domain={c['domain']} = {c['value'][:400]}")
            pref = [c for c in ctx.cookies() if c["name"] == "PREF"]
            if not pref:
                log("KHONG co cookie PREF -> dung")
                return 1
            pairs = dict(parse_qsl(pref[0]["value"]))
            log("PREF hien tai:", pairs)
            if pairs.get("hl") == "en":
                log("PREF da la en -> khong can doi")
            for c in pref:
                old = c["value"]
                kv = dict(parse_qsl(old))
                kv["hl"] = "en"
                new = urlencode(kv)
                log(f"doi PREF {c['domain']}: hl {dict(parse_qsl(old)).get('hl')} -> en")
                if DRY:
                    continue
                ctx.add_cookies([{
                    "name": c["name"], "value": new, "domain": c["domain"], "path": c.get("path", "/"),
                    "expires": c.get("expires", -1), "httpOnly": c.get("httpOnly", False),
                    "secure": c.get("secure", False), "sameSite": c.get("sameSite", "Lax"),
                }])
            if DRY:
                log("--dry: khong ghi cookie")
                page.close()
                return 0

            try:
                page.goto("https://studio.youtube.com/channel/" + CID, wait_until="domcontentloaded", timeout=90000)
            except Exception as exc:
                log("goto studio:", str(exc)[:80])
            time.sleep(random.uniform(12, 15))
            r = check(page, "sau khi doi PREF")
            try:
                page.reload(wait_until="domcontentloaded", timeout=90000)
            except Exception as exc:
                log("reload:", str(exc)[:80])
            time.sleep(random.uniform(10, 13))
            r2 = check(page, "sau reload")
            try:
                page.screenshot(path=os.path.join(os.path.dirname(HERE), "reports", "may1_logon", "pref_en_studio.png"))
            except Exception:
                pass
            page.close()
            return 0 if (r.get("Content") or r2.get("Content")) else 2


if __name__ == "__main__":
    sys.exit(main())
