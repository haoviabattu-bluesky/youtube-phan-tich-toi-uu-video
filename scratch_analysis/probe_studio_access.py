"""probe_studio_access.py — CHỈ ĐỌC: kiểm tài khoản trong profile GPM có mở được Studio của 1 channel_id không.

Dùng để chẩn đoán IDENTITY_MISMATCH. Không đăng gì, không đổi kênh, không sửa code cũ.

  py -3.13 scratch_analysis/probe_studio_access.py --mail a@b.com --channel UCnwgkB18gTTON1YXNQvxsbg
"""
import argparse
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comment_care" / "src"))

from comment_care.browser_poster import gpm_find, gpm_start  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail")
    ap.add_argument("--profile")
    ap.add_argument("--channel", action="append", required=True)
    a = ap.parse_args()

    pid = a.profile or gpm_find(a.mail)
    print(f"profile: {pid}")
    ws = gpm_start(pid)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(ws)
            ctx = br.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=90000)
            time.sleep(4)
            m = re.search(r"/channel/(UC[\w-]{22})", page.url)
            print(f"kênh mặc định: {m.group(1) if m else '?'}")

            for cid in a.channel:
                page.goto(f"https://studio.youtube.com/channel/{cid}", wait_until="domcontentloaded", timeout=90000)
                time.sleep(6)
                got = re.search(r"/channel/(UC[\w-]{22})", page.url)
                ok = bool(got and got.group(1) == cid)
                body = ""
                try:
                    body = page.inner_text("body")[:200].replace("\n", " ")
                except Exception:  # noqa: BLE001
                    pass
                print(f"  {cid}: mở được={ok}  url={page.url[:70]}  body='{body[:90]}'")
    finally:
        import requests
        requests.get(f"http://127.0.0.1:9495/api/v1/profiles/stop/{pid}", timeout=60)
        print("đã tắt profile")


if __name__ == "__main__":
    main()
