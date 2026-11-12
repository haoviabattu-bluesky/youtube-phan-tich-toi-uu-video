"""dump_account_menu.py — CHỈ ĐỌC: dump DOM menu tài khoản youtube.com để tìm selector đúng.

  py -3.13 scratch_analysis/dump_account_menu.py --mail a@b.com
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comment_care" / "src"))

from comment_care.browser_poster import gpm_find, gpm_start  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

GPM = "http://127.0.0.1:9495/api/v1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail")
    ap.add_argument("--profile")
    ap.add_argument("--keep-open", action="store_true")
    a = ap.parse_args()
    pid = a.profile or gpm_find(a.mail)
    ws = gpm_start(pid)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(ws)
            ctx = br.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
            time.sleep(6)

            info = page.evaluate(
                """() => {
                  const av = document.querySelector('#avatar-btn');
                  const out = {hasAvatar: !!av, tags: {}};
                  if (av) {
                    const r = av.getBoundingClientRect();
                    out.avatarBox = [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
                  }
                  for (const t of ['ytd-account-item-renderer','ytd-account-section-list-renderer','ytd-multi-page-menu-renderer','ytd-topbar-menu-button-renderer','tp-yt-paper-item','ytd-compact-link-renderer']) {
                    out.tags[t] = document.querySelectorAll(t).length;
                  }
                  return out;
                }"""
            )
            print("trước click:", info)

            try:
                page.locator("#avatar-btn").first.click(timeout=10000)
            except Exception as e:  # noqa: BLE001
                print("click avatar lỗi:", e)
            time.sleep(4)

            info2 = page.evaluate(
                """() => {
                  const out = {tags: {}, texts: []};
                  for (const t of ['ytd-account-item-renderer','ytd-account-section-list-renderer','ytd-multi-page-menu-renderer','ytd-compact-link-renderer','tp-yt-paper-item']) {
                    out.tags[t] = document.querySelectorAll(t).length;
                  }
                  const menu = document.querySelector('ytd-multi-page-menu-renderer');
                  if (menu) out.menuText = (menu.innerText || '').slice(0, 800);
                  return out;
                }"""
            )
            print("sau click:", info2)

            # thử mở "Switch account"
            for label in ["Switch account", "Chuyển tài khoản", "アカウントを切り替え"]:
                try:
                    el = page.get_by_text(label, exact=False).first
                    if el.count():
                        print(f"thấy nút '{label}' → bấm")
                        el.click(timeout=8000)
                        time.sleep(4)
                        break
                except Exception as e:  # noqa: BLE001
                    print(f"  '{label}': {e}")

            info3 = page.evaluate(
                """() => {
                  const out = {tags: {}, items: []};
                  for (const t of ['ytd-account-item-renderer','ytd-account-section-list-renderer']) {
                    out.tags[t] = document.querySelectorAll(t).length;
                  }
                  for (const it of document.querySelectorAll('ytd-account-item-renderer')) {
                    out.items.push({
                      text: (it.innerText || '').replace(/\\n/g, ' | ').slice(0, 120),
                      href: it.querySelector('a') ? it.querySelector('a').getAttribute('href') : null,
                      selected: it.hasAttribute('selected')
                    });
                  }
                  return out;
                }"""
            )
            print("sau Switch:", info3)
    finally:
        if not a.keep_open:
            import requests
            requests.get(f"{GPM}/profiles/stop/{pid}", timeout=60)
            print("đã tắt profile")


if __name__ == "__main__":
    main()
