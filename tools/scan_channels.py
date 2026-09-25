# -*- coding: utf-8 -*-
r"""
QUET CAC PROFILE GPM CUA DU AN: profile nao con login, kenh nao, bao nhieu video da dang.
Dung truoc studio_collect.py de biet doc kenh nao.

  py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\scan_channels.py
  py -3.13 ...\scan_channels.py --only VirgiliTraino95,cobbytheona159

Ten profile GPM co the CO hoac KHONG co duoi @gmail.com (vd 'haoviabattu' vs
'AmmarHilham@gmail.com') -> doi chieu ca hai dang, khong khop tuyet doi.
"""
import sys, time, json, argparse
sys.stdout.reconfigure(encoding="utf-8")
import requests
from playwright.sync_api import sync_playwright

GPM = "http://127.0.0.1:9495/api/v1"
BANNER = "GPMLogin Global API"

# tab_sheet (ten TAB that trong Google Sheet, cap nhat 2026-09-25) -> mail = ten profile GPM
# (nguon: sheet GMAIL doc lai 2026-09-25 + list_sheets). Lane D (irogatatarukioku, mail
# AmmarHilham@gmail.com) anh chot BO, KHONG theo doi nua -> khong con trong danh sach nay.
LANES = [
    ("A-shinya_shiryoshitsu", "haoviabattu@gmail.com"),
    ("Satori-Lopezzapa68", "LopezzapataHilla@gmail.com"),
    ("E-70dai-kenko", "normaneileenpm218@gmail.com"),
    ("F-teinengo-real", "VirgiliTraino95@gmail.com"),
    ("G-teinengo-tanoshimi", "cobbytheona159@gmail.com"),
    ("K-yakkyoku-sukatto", "rosellagreysonbk920@gmail.com"),
    ("L-shakai-no-naze", "SyedualiBajwa92@gmail.com"),
    ("kokoro-kazoku", "FuentesMitsy202@gmail.com"),
    ("sengoku-uragawa", "AldenorRodrigues626@gmail.com"),
    ("teinengo-fuufu", "MinyardJuan231@gmail.com"),
]


def all_profiles():
    out, page = [], 1
    while True:
        d = requests.get(f"{GPM}/profiles", params={"page": page, "per_page": 100}, timeout=30).json()["data"]
        out += d["data"]
        if page >= d["last_page"]:
            return out
        page += 1


def match(profiles, mail):
    """Khop ten profile voi mail: ca ban day du lan ban bo duoi @gmail.com."""
    m = mail.strip().lower()
    stem = m.split("@")[0]
    for p in profiles:
        n = p["name"].strip().lower()
        if n == m or n == stem:
            return p["id"]
    return None


def start(pid):
    j = requests.get(f"{GPM}/profiles/start/{pid}", timeout=180).json()
    d = j.get("data")
    if j.get("message") == "ProfileUsingByOther":
        # BAT BUOC (anh chot 2026-09-25): profile nay dang duoc dung o noi khac (co the anh
        # dang mo tay xem Studio). TUYET DOI KHONG kill/dong no de chiem lai -> bo qua, dung lai.
        raise RuntimeError("PROFILE_BUSY: dang duoc dung o noi khac (co the anh dang mo tay) -> BO QUA, khong dong/kill")
    if not j.get("success") or d == BANNER or not isinstance(d, dict):
        raise RuntimeError(j.get("message") or str(d))
    ws = d.get("websocket_debugging_url") or ""
    if not ws:
        raise RuntimeError("websocket RONG (profile dang mo do)")
    return ws


def stop(pid):
    try:
        requests.get(f"{GPM}/profiles/stop/{pid}", timeout=60)
    except Exception:
        pass


def probe(ws):
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(90000)
        # BAY: lan goto DAU studio.youtube.com hay dung lai o ROOT (khong redirect),
        # lan thu 2 moi nhay vao /channel/<id>. Bo qua bay nay = bao "CHUA LOGIN" oan
        # cho ca 6 kenh dang login binh thuong.
        cid, u = None, ""
        for _ in range(3):
            page.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
            for _ in range(12):
                time.sleep(3)
                u = page.url or ""
                if "/channel/" in u or "accounts.google" in u or "/signin" in u:
                    break
            if "/channel/" in u:
                cid = u.split("/channel/")[1].split("/")[0]
                break
            if "accounts.google" in u or "/signin" in u:
                return {"login": False, "channel_id": None, "videos": [], "url": u}
        if not cid:
            return {"login": False, "channel_id": None, "videos": [], "url": u}
        page.goto(f"https://studio.youtube.com/channel/{cid}/videos/upload", wait_until="domcontentloaded")
        rows = []
        for _ in range(15):
            time.sleep(3)
            rows = page.eval_on_selector_all("ytcp-video-row", """els => els.map(e => {
                const a = e.querySelector('a#video-title');
                return {id: a ? (a.href.split('/video/')[1]||'').split('/')[0] : '', title: a ? a.innerText.trim() : ''};
            })""")
            if rows:
                break
        return {"login": True, "channel_id": cid, "videos": [r for r in rows if r["id"]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="loc theo mail/lane, phan cach bang dau phay")
    a = ap.parse_args()
    profiles = all_profiles()
    print("Tong profile GPM:", len(profiles))
    only = [x.strip().lower() for x in a.only.split(",") if x.strip()]
    result = {}
    for lane, mail in LANES:
        if only and not any(o in lane.lower() or o in mail.lower() for o in only):
            continue
        pid = match(profiles, mail)
        if not pid:
            print(f"[{lane}] {mail}: KHONG co profile GPM"); continue
        try:
            ws = start(pid)
        except Exception as e:
            print(f"[{lane}] {mail}: start LOI -> {e}"); continue
        try:
            st = probe(ws)
        except Exception as e:
            print(f"[{lane}] {mail}: doc LOI -> {str(e)[:120]}"); stop(pid); continue
        if not st["login"]:
            print(f"[{lane}] {mail}: CHUA LOGIN (url={st.get('url','?')[:80]})")
        else:
            print(f"[{lane}] {mail}: channel={st['channel_id']} videos={len(st['videos'])}")
            for v in st["videos"]:
                print("      ", v["id"], v["title"][:60])
        result[lane] = {"mail": mail, "profile_id": pid, **st}
        stop(pid)
        time.sleep(3)
    with open("scan_channels.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("Da ghi scan_channels.json")


if __name__ == "__main__":
    main()
