"""check_channels.py — CHỈ ĐỌC: mở profile GPM, xem tài khoản Google đang sở hữu những kênh YouTube nào.

Dùng để chẩn đoán IDENTITY_MISMATCH (profile đăng nhập kênh khác kênh của lane).
KHÔNG đăng gì, KHÔNG đổi kênh, KHÔNG sửa code cũ. Không kill chrome.

  py -3.13 scratch_analysis/check_channels.py --mail rosellagreysonbk920@gmail.com
  py -3.13 scratch_analysis/check_channels.py --profile b74cbbd9-c90f-40f4-ab5f-705c5f23bd9a --keep-open
"""
import argparse
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
    ap.add_argument("--keep-open", action="store_true")
    a = ap.parse_args()

    pid = a.profile or gpm_find(a.mail)
    if not pid:
        sys.exit(f"không thấy profile GPM cho {a.mail}")
    print(f"profile: {pid}")

    ws = gpm_start(pid)
    print(f"ws ok: {ws[:60]}…")
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(ws)
            ctx = br.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            # 1) Studio đang ở kênh nào
            for _ in range(3):
                page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=90000)
                time.sleep(4)
                if "studio.youtube.com/channel/" in page.url:
                    break
            print(f"studio url: {page.url}")

            # 2) Danh sách kênh tài khoản sở hữu (trang chuyển kênh, chỉ đọc)
            page.goto("https://www.youtube.com/channel_switcher", wait_until="domcontentloaded", timeout=90000)
            time.sleep(6)
            items = page.evaluate(
                """() => {
                  const out = [];
                  const seen = new Set();
                  for (const el of document.querySelectorAll('a[href*="/channel/UC"]')) {
                    const m = el.href.match(/channel\\/(UC[\\w-]{22})/);
                    if (!m || seen.has(m[1])) continue;
                    seen.add(m[1]);
                    const t = (el.innerText || '').trim().split('\\n').map(s => s.trim()).filter(Boolean);
                    out.push({id: m[1], text: t.slice(0, 2)});
                  }
                  return out;
                }"""
            )
            print(f"channel_switcher: {len(items)} kênh")
            for it in items:
                print(f"  {it['id']}  {it['text']}")
            print(f"url sau switcher: {page.url}")
            if not items:
                print("  (không đọc được danh sách — có thể trang yêu cầu đăng nhập lại)")
                print(f"  title: {page.title()}")
    finally:
        if not a.keep_open:
            import requests
            requests.get(f"http://127.0.0.1:9495/api/v1/profiles/stop/{pid}", timeout=60)
            print("đã tắt profile")
        else:
            print("giữ profile mở (--keep-open)")


if __name__ == "__main__":
    main()
