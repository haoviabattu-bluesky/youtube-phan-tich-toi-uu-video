"""switch_channel.py — đổi KÊNH ĐANG HOẠT ĐỘNG của profile GPM sang channel_id chỉ định (thao tác UI như người).

Vì sao cần: 1 tài khoản Google có thể sở hữu nhiều kênh (lane O + lane K dùng chung mail
rosellagreysonbk920@gmail.com). browser_poster.verify_identity() chỉ goto studio root nên thấy
kênh mặc định (K) và chặn lane O. Script này chuyển active channel trước, KHÔNG sửa code cũ.

Menu YouTube KHÔNG có href ở ytd-account-item-renderer → phải khớp theo TÊN KÊNH.
Lấy tên từ Data API bằng channel_id.

  py -3.13 scratch_analysis/switch_channel.py --mail a@b.com --channel UC... --list   # chỉ đọc
  py -3.13 scratch_analysis/switch_channel.py --mail a@b.com --channel UC...          # đổi thật

Không đăng gì, không kill chrome, không đụng sheet.
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comment_care" / "src"))

from comment_care.browser_poster import gpm_find, gpm_start  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

GPM = "http://127.0.0.1:9495/api/v1"


def api_key():
    k = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if k:
        return k
    env = Path(r"E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env")
    if env.exists():
        for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("YOUTUBE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def channel_title(cid):
    k = api_key()
    if not k:
        return ""
    import requests
    r = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={"part": "snippet", "id": cid, "key": k},
        timeout=30,
    ).json()
    it = (r.get("items") or [])
    return it[0]["snippet"]["title"] if it else ""


def open_switch_menu(page):
    page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
    time.sleep(5)
    page.locator("#avatar-btn").first.click(timeout=15000)
    time.sleep(3)
    for label in ["Switch account", "アカウントを切り替え", "Chuyển tài khoản"]:
        try:
            el = page.get_by_text(label, exact=False).first
            if el.count():
                el.click(timeout=8000)
                time.sleep(4)
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def read_items(page):
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('ytd-account-item-renderer')).map(it => ({
             text: (it.innerText || '').split('\\n').map(s => s.trim()).filter(Boolean).slice(0, 3),
             selected: it.hasAttribute('selected')
           }))"""
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail")
    ap.add_argument("--profile")
    ap.add_argument("--channel", required=True)
    ap.add_argument("--title", help="tên kênh đích (mặc định tra Data API)")
    ap.add_argument("--list", action="store_true", help="chỉ đọc menu, không đổi")
    ap.add_argument("--keep-open", action="store_true")
    a = ap.parse_args()

    pid = a.profile or gpm_find(a.mail)
    print(f"profile: {pid}")
    target_title = a.title or channel_title(a.channel)
    print(f"kênh đích: {a.channel}  tên='{target_title}'")
    if not target_title and not a.list:
        sys.exit("không lấy được tên kênh đích (thiếu API key) → dùng --title")

    ws = gpm_start(pid)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(ws)
            ctx = br.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            if not open_switch_menu(page):
                sys.exit("không mở được menu Switch account")
            items = read_items(page)
            print(f"menu: {len(items)} kênh")
            for i, it in enumerate(items):
                print(f"  [{i}] {' | '.join(it['text'])}{' ← đang chọn' if it['selected'] else ''}")
            if a.list or not items:
                return

            idx = next((i for i, it in enumerate(items) if any(target_title == t for t in it["text"])), -1)
            if idx < 0:
                idx = next((i for i, it in enumerate(items) if any(target_title in t for t in it["text"])), -1)
            print(f"index khớp: {idx}")
            if idx < 0:
                print("⚠ không thấy kênh đích trong menu → không đổi gì")
                return

            page.locator("ytd-account-item-renderer").nth(idx).click(timeout=15000)
            time.sleep(7)

            ok = False
            for _ in range(3):
                page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=90000)
                time.sleep(5)
                m = re.search(r"studio\.youtube\.com/channel/(UC[\w-]{22})", page.url)
                if m:
                    ok = m.group(1) == a.channel
                    print(f"studio sau khi đổi: {m.group(1)}  {'✓ ĐÚNG' if ok else '✗ SAI'}")
                    break
            if not ok:
                print("⚠ đổi chưa ăn — kiểm tra tay")
    finally:
        if not a.keep_open:
            import requests
            requests.get(f"{GPM}/profiles/stop/{pid}", timeout=60)
            print("đã tắt profile")


if __name__ == "__main__":
    main()
