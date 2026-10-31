# -*- coding: utf-8 -*-
r"""Xem video YouTube theo BO TU KHOA CHU DE (dia ly / dia chat / cong trinh Nhat Ban).

Chay:
  py -3.13 tools\youtube_topic_watch.py --mail alexusmickey94@gmail.com
  py -3.13 tools\youtube_topic_watch.py --mail alexusmickey94@gmail.com --minutes 6 --per-keyword 2

DUNG khi nao:
  * Anh DONG profile trong GPM  -> script tu thoat (khong tu mo lai).
  * Hoac tao file tools\topicwatch_STOP  -> thoat sau video dang xem.
  * Ctrl+C.

Ghi ra:
  reports\topic_watch\<mail>_<ngay>.csv   (1 dong / video da xem: keyword, title, channel, view, ngay dang...)
  reports\topic_watch\<mail>_<ngay>.log   (nhat ky chay)

Luat an toan (theo CLAUDE.md):
  * GPM bao ProfileUsingByOther -> DUNG NGAY, khong kill profile (bay #9).
  * GPM bao ProxyCheckFailed    -> DUNG NGAY va bao ro proxy chet (khong tu doi proxy cua profile).
  * Khong taskkill chrome.exe theo ten.
"""
import sys, os, re, csv, time, random, argparse, datetime, urllib.parse
import requests
from playwright.sync_api import sync_playwright

GPM = "http://127.0.0.1:9495/api/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP_FILE = os.path.join(ROOT, "tools", "topicwatch_STOP")
OUT_DIR = os.path.join(ROOT, "reports", "topic_watch")

# ---- 15 tu khoa anh chot (2026-10-19) ----
KEYWORDS = [
    "青函トンネル なぜ橋じゃない",
    "青函トンネル 断面図",
    "津軽海峡 海底地形",
    "日本 地形の謎",
    "日本列島 地形 3D",
    "海の水を抜いてみた 日本",
    "日本 海底トンネル なぜ",
    "日本 地図の謎",
    "日本 海底の謎",
    "地形 断面図 解説",
    "明石海峡大橋 なぜ",
    "関門海峡 橋 トンネル",
    "日本 巨大土木工事 解説",
    "日本の地理 不思議",
    "地図で見る 日本",
]

JP = re.compile(r"[぀-ヿ]")           # bat buoc co hiragana/katakana -> loai video tieng Trung
TOPIC = re.compile(
    r"トンネル|海峡|橋|地形|地質|地図|海底|断面|土木|工事|ダム|湾|半島|列島|プレート|断層|"
    r"山脈|海岸|埋立|港|運河|地殻|火山|平野|盆地|地盤|掘削|シールド|橋梁|高架|造成|"
    r"地すべり|津波|干拓|岬|地層|岩盤|海溝|堆積|隆起|侵食|地下|ケーソン|沈埋|"
    r"青函|津軽|明石|関門|瀬戸|本州|四国|九州|北海道|沖縄|日本海|太平洋"
)


def log(msg):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def gpm_find(mail):
    """Khop mail day du HOAC phan truoc @ (bay #6)."""
    page, key = 1, mail.strip().lower()
    short = key.split("@")[0]
    while True:
        d = requests.get(f"{GPM}/profiles", params={"page": page, "per_page": 100}, timeout=30).json()["data"]
        for p in d["data"]:
            n = (p.get("name") or "").strip().lower()
            if n in (key, short):
                return p["id"]
        if page >= d["last_page"]:
            return None
        page += 1


def gpm_start(pid):
    j = requests.get(f"{GPM}/profiles/start/{pid}", timeout=240).json()
    msg = j.get("message") or ""
    if msg == "ProfileUsingByOther":
        raise SystemExit("PROFILE_BUSY: profile dang mo o noi khac -> KHONG kill, doi anh dong roi chay lai")
    if msg == "ProxyCheckFailed":
        raise SystemExit("PROXY_CHET: proxy cua profile khong qua duoc kiem tra -> khong tu doi proxy, bao anh")
    d = j.get("data") or {}
    ws = d.get("websocket_debugging_url") or ""
    if not ws:
        raise SystemExit(f"GPM start khong tra websocket: {j}")
    return ws, d.get("remote_debugging_port")


def stopped():
    return os.path.exists(STOP_FILE)


def sleep_watch(sec):
    end = time.time() + sec
    while time.time() < end:
        if stopped():
            return False
        time.sleep(min(4, max(0.3, end - time.time())))
    return True


def do_search(page, kw):
    """Go tung ky tu nhu nguoi; loi thi goto thang URL ket qua."""
    try:
        page.goto("https://www.youtube.com/?hl=ja&gl=JP", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(random.randint(2000, 4000))
        box = page.locator("input[name='search_query']").first
        box.click(timeout=15000)
        box.fill("")
        for ch in kw:
            page.keyboard.type(ch, delay=random.randint(70, 190))
        page.wait_for_timeout(random.randint(500, 1400))
        page.keyboard.press("Enter")
        page.wait_for_selector("ytd-video-renderer", timeout=30000)
    except Exception:
        page.goto(f"https://www.youtube.com/results?search_query={urllib.parse.quote(kw)}&hl=ja&gl=JP",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("ytd-video-renderer", timeout=30000)
    page.wait_for_timeout(random.randint(1800, 3500))
    page.mouse.wheel(0, random.randint(300, 800))
    page.wait_for_timeout(random.randint(1200, 2600))


def grab_results(page, limit=20):
    return page.evaluate("""(limit) => [...document.querySelectorAll('ytd-video-renderer')].slice(0, limit).map(r => {
        const a = r.querySelector('a#video-title');
        const ch = r.querySelector('ytd-channel-name a');
        const meta = [...r.querySelectorAll('#metadata-line span')].map(s => s.textContent.trim());
        return {href: a ? a.href : '', title: a ? (a.title || a.textContent).trim() : '',
                channel: ch ? ch.textContent.trim() : '', meta: meta.join(' | ')};
    })""", limit)


def pick(items, seen):
    ok = []
    for x in items:
        if "/watch?v=" not in x["href"]:
            continue
        vid = x["href"].split("v=")[1][:11]
        if vid in seen or not JP.search(x["title"]):
            continue
        ok.append({**x, "vid": vid})
    if not ok:
        return None
    on_topic = [x for x in ok if TOPIC.search(x["title"])]
    pool = (on_topic or ok)[:8]
    return random.choice(pool)


def watch_meta(page):
    try:
        return page.evaluate("""() => {
            const t = document.querySelector('h1.ytd-watch-metadata yt-formatted-string, #title h1 yt-formatted-string, h1 yt-formatted-string');
            const ch = document.querySelector('#owner #channel-name a, ytd-channel-name#channel-name a');
            const info = [...document.querySelectorAll('#info span, #info-strings yt-formatted-string')]
                         .map(e => e.textContent.trim()).filter(Boolean).slice(0, 8);
            const v = document.querySelector('video');
            return {title: t ? t.textContent.trim() : '', channel: ch ? ch.textContent.trim() : '',
                    info: info.join(' | '), duration: v ? Math.round(v.duration || 0) : 0};
        }""")
    except Exception:
        return {}


def skip_ads(page):
    try:
        page.evaluate("""() => { const b = document.querySelector(
            '.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern'); if (b) b.click(); }""")
    except Exception:
        pass


def watch(page, vid, minutes):
    """Xem den khi het 'minutes' hoac video ket thuc. Tra ve (giay_da_xem, trang_thai)."""
    page.goto(f"https://www.youtube.com/watch?v={vid}&hl=ja", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("video", timeout=30000)
    page.wait_for_timeout(random.randint(2500, 4500))
    page.evaluate("() => { const v = document.querySelector('video'); if (v && v.paused) v.play(); }")
    target, t0 = minutes * 60, time.time()
    while time.time() - t0 < target:
        if not sleep_watch(random.randint(12, 25)):
            return time.time() - t0, "STOP_FILE"
        skip_ads(page)
        try:
            st = page.evaluate("""() => { const v = document.querySelector('video');
                if (!v) return {gone: true};
                if (v.paused && !v.ended) v.play();
                return {ended: v.ended, cur: v.currentTime, dur: v.duration}; }""")
        except Exception:
            return time.time() - t0, "PAGE_LOI"
        if st.get("gone"):
            return time.time() - t0, "VIDEO_MAT"
        if st.get("ended"):
            return time.time() - t0, "HET_VIDEO"
        if random.random() < 0.07:      # thinh thoang cuon xuong xem mo ta/binh luan roi len
            page.mouse.wheel(0, random.randint(400, 1100))
            page.wait_for_timeout(random.randint(2500, 6000))
            page.mouse.wheel(0, -2500)
    return time.time() - t0, "DU_GIO"


def append_csv(row):
    new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["ts", "keyword", "video_id", "title", "channel", "views_meta",
                        "publish_info", "duration_s", "watched_s", "result", "url"])
        w.writerow(row)


def load_seen():
    if not os.path.exists(CSV_PATH):
        return set()
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        return {r["video_id"] for r in csv.DictReader(f) if r.get("video_id")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail", required=True)
    ap.add_argument("--minutes", type=float, default=5.0, help="so phut xem moi video (mac dinh 5)")
    ap.add_argument("--per-keyword", type=int, default=1, help="so video xem cho moi tu khoa")
    ap.add_argument("--keywords", default="", help="ghi de danh sach, ngan cach bang |")
    ap.add_argument("--ws", default="", help="dung CDP co san, khong goi GPM start")
    a = ap.parse_args()

    global LOG_PATH, CSV_PATH
    os.makedirs(OUT_DIR, exist_ok=True)
    tag = a.mail.split("@")[0]
    day = datetime.date.today()
    LOG_PATH = os.path.join(OUT_DIR, f"{tag}_{day}.log")
    CSV_PATH = os.path.join(OUT_DIR, f"{tag}_{day}.csv")
    kws = [k.strip() for k in a.keywords.split("|") if k.strip()] or KEYWORDS

    if a.ws:
        ws = a.ws
        log(f"Dung CDP co san: {ws}")
    else:
        pid = gpm_find(a.mail)
        if not pid:
            raise SystemExit(f"Khong thay profile GPM cho {a.mail}")
        ws, port = gpm_start(pid)
        log(f"Mo profile {a.mail} ({pid}) | CDP port {port}")

    seen = load_seen()
    n, rnd = 0, 0
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws, timeout=60000)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.bring_to_front()
        log(f"Bat dau. {len(kws)} tu khoa | {a.minutes}p/video | da xem truoc do: {len(seen)}")

        while not stopped():
            rnd += 1
            order = kws[:]
            random.shuffle(order)
            for kw in order:
                if stopped():
                    break
                # profile bi dong -> thoat ngay, khong tu mo lai
                if not br.is_connected():
                    log("DUNG: profile da bi dong (browser mat ket noi).")
                    return 0
                try:
                    do_search(page, kw)
                    items = grab_results(page, 20)
                    picked = 0
                    for _ in range(a.per_keyword):
                        v = pick(items, seen)
                        if not v:
                            log(f"[{kw}] khong con video moi phu hop -> bo qua")
                            break
                        m0 = watch_meta(page)          # metadata truoc khi vao (de phong)
                        sec, result = watch(page, v["vid"], a.minutes)
                        if result in ("STOP_FILE",):
                            log(f"[{kw}] {v['title'][:60]} | dung theo STOP_FILE")
                            return 0
                        m = watch_meta(page) or m0
                        title = m.get("title") or v["title"]
                        ch = m.get("channel") or v["channel"]
                        views = ""
                        pub = ""
                        for part in (m.get("info") or "").split(" | "):
                            if "回" in part:
                                views = part
                            elif "公開" in part or "配信" in part or re.search(r"\d{4}[/年]", part):
                                pub = part
                        append_csv([datetime.datetime.now().isoformat(timespec="seconds"), kw, v["vid"],
                                    title, ch, views or v["meta"], pub, m.get("duration", ""),
                                    round(sec), result, f"https://www.youtube.com/watch?v={v['vid']}"])
                        seen.add(v["vid"])
                        n += 1
                        picked += 1
                        log(f"#{n} [{kw}] {sec/60:.1f}p {result} | {title[:70]} | {ch} | {views}")
                        items = [x for x in items if x.get("vid") != v["vid"]]
                        if not sleep_watch(random.randint(6, 18)):
                            break
                    if picked == 0:
                        page.goto("https://www.youtube.com/?hl=ja&gl=JP", wait_until="domcontentloaded")
                except Exception as e:
                    if not br.is_connected():
                        log(f"DUNG: profile da bi dong ({type(e).__name__}).")
                        return 0
                    log(f"[{kw}] LOI {type(e).__name__}: {str(e)[:160]} -> bo qua")
                    try:
                        if page.is_closed():
                            page = ctx.new_page()
                            page.bring_to_front()
                    except Exception:
                        log("DUNG: khong tao duoc tab moi (profile da dong).")
                        return 0
                if not sleep_watch(random.randint(5, 15)):
                    break
    log(f"KET THUC. Tong da xem {n} video.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
