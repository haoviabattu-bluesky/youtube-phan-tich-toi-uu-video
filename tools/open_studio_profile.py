# -*- coding: utf-8 -*-
r"""
MO PROFILE CHROME RIENG CUA DU AN (cho cac kenh KHONG nam trong GPMLogin, vd lane A
shinya_shiryoshitsu / haoviabattu@gmail.com dang login o Chrome ca nhan).

  py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\open_studio_profile.py
  py -3.13 ...\open_studio_profile.py --check        (chi kiem tra da login chua, khong mo them)

LUAT AN TOAN (quy tac chung cua may, doc ky truoc khi sua):
  * Thu muc --user-data-dir RIENG: E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\studio_profile
    TUYET DOI khong tro vao "User Data" mac dinh cua Chrome ca nhan — App-Bound Encryption
    se xoa sach cookie/session neu duong dan bi doi hoac bi truy cap sai cach.
  * Cong RIENG 9350 (VEO3_PROFILE dung 9333, GROK_PROFILE dung 9334 — khong duoc trung).
    Cong bi mot Chrome KHAC chiem thi DOI CONG, khong bao gio kill no de chiem lai.
  * Khong taskkill chrome.exe theo ten. Muon dong thi dong dung PID co --user-data-dir nay.

Dang nhap: script KHONG tu dang nhap duoc (mail chinh cua anh, co 2FA) — no chi mo san
trang dang nhap; anh go tay 1 lan, cookie nam lai trong studio_profile cho cac lan sau.
"""
import os, sys, time, subprocess, argparse, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_DIR = os.path.join(ROOT, "studio_profile")
PORT = 9350
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def cdp_alive(port=PORT):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3) as r:
            return json.load(r)
    except Exception:
        return None


def ws_url(port=PORT):
    v = cdp_alive(port)
    return v.get("webSocketDebuggerUrl") if v else None


def launch():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    args = [CHROME,
            f"--user-data-dir={PROFILE_DIR}",
            f"--remote-debugging-port={PORT}",
            "--no-first-run", "--no-default-browser-check",
            "--new-window", "https://studio.youtube.com/"]
    # DETACHED: Chrome phai song doc lap voi shell da mo no (shell dong khong keo theo Chrome)
    flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(args, creationflags=flags, close_fds=True)


def who(port=PORT):
    """Doc tai khoan dang login + channel id qua CDP (khong can playwright)."""
    from playwright.sync_api import sync_playwright
    w = ws_url(port)
    if not w:
        return None
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(w)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=90000)
        for _ in range(20):
            time.sleep(3)
            u = page.url or ""
            if "/channel/" in u:
                return {"channel_id": u.split("/channel/")[1].split("/")[0], "url": u}
            if "accounts.google" in u or "signin" in u:
                return {"channel_id": None, "url": u}
        return {"channel_id": None, "url": page.url}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="khong mo them cua so, chi bao trang thai")
    a = ap.parse_args()

    v = cdp_alive()
    if v:
        print(f"Chrome cua du an DANG chay o cong {PORT}: {v.get('Browser')}")
    elif a.check:
        print(f"Chua chay. Cong {PORT} khong co CDP."); return 1
    else:
        print("Dang mo Chrome rieng cua du an...")
        print("  user-data-dir:", PROFILE_DIR)
        print("  port         :", PORT)
        launch()
        for _ in range(20):
            time.sleep(2)
            if cdp_alive():
                break
        v = cdp_alive()
        if not v:
            print("KHONG mo duoc CDP -> kiem tra duong dan chrome.exe hoac cong bi chiem"); return 2
        print("OK:", v.get("Browser"))

    print("WS:", ws_url())
    st = who()
    if st and st["channel_id"]:
        print("DA LOGIN. CHANNEL_ID =", st["channel_id"])
        print("Chay tiep:")
        print(rf'  py -3.13 {os.path.join(ROOT, "tools", "studio_collect.py")} --ws {ws_url()} --channel {st["channel_id"]} --lane toshi-densetsu-jp')
    else:
        print("CHUA LOGIN -> anh dang nhap TAY bang haoviabattu@gmail.com trong cua so vua mo,")
        print("xong chay lai lenh nay voi --check de em doc channel id.")
        print("URL hien tai:", st["url"] if st else "?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
