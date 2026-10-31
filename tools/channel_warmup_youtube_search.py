"""Lam nong kenh moi: mo profile GPM -> YouTube -> tim tu khoa tieng Nhat -> xem ~5 phut/video -> lap.

Chay:  py -3.13 tools\\channel_warmup_youtube_search.py --mail theeuxanh1@gmail.com
Dung:  tao file tools\\warmup_STOP (hoac Ctrl+C). Log: reports\\warmup_<mail>_<ngay>.log
- Chi chon video co tieu de tieng Nhat (hiragana/katakana/kanji), bo Shorts, bo video da xem.
- GPM bao ProfileUsingByOther -> DUNG, khong kill (CLAUDE.md bay #9).
"""
import sys, os, re, time, random, argparse, datetime, urllib.parse
import requests
from playwright.sync_api import sync_playwright

GPM = "http://127.0.0.1:9495/api/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP_FILE = os.path.join(ROOT, "tools", "warmup_STOP")
# Bat buoc co hiragana/katakana: chi kanji thi lot ca video tieng Trung (da dinh 2026-10-17)
JP = re.compile(r"[぀-ヿ]")

PRIORITY = ["AI 歴史ミステリー", "AI 未解決の謎", "AIに推理させた"]
# Anh chot 2026-10-17: chi tim chu de "AI giai ma bi an" -> moi tu khoa deu co AI
KEYWORDS = [
    "AI 謎解き", "AI 歴史ミステリー", "AI 未解決の謎", "AI 歴史の真実", "AI 考察 謎", "AI 推理 歴史",
    "AI 未解読", "AIで解析してみた 謎", "AIに推理させた", "AIが導き出した答え 謎",
    "AI 本能寺の変 黒幕", "AI 日本史 最大の謎", "AI 歴史の闇", "AI 歴史の謎 考察", "AI 戦国時代 謎",
    "AI 織田信長 真相", "AI 徳川家康 都市伝説", "AI 日本史の謎 ゆっくり解説", "AI 古代日本 ミステリー",
    "AI 歴史の定説が覆る", "ヴォイニッチ手稿 AI", "AI 世界の未解決ミステリー", "AI 未解読の古代文字",
    "AI 古代文明の謎", "AI 失われた文明", "AI 世界の謎 解明", "AI 人類最大の謎", "AI 考古学 ミステリー",
    "AI 封印された歴史", "AI 世界の謎 ゆっくり解説",
]
# (?<![A-Za-z]) chan "AI" nam trong chu khac (VAIENCE, TRAIN...)
AI = re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])|ＡＩ|人工知能|ChatGPT|チャットGPT|GPT|Gemini", re.I)
MYSTERY = re.compile(r"謎|ミステリー|未解決|未解明|解読|真相|真実|推理|考察|伝説|闇|黒幕|暗号|正体|解明|封印")


# "Dung chu de" = tieu de/kenh co tu lich su-bi an co dai (an mang hien dai nhu 世田谷 KHONG tinh)
TOPIC = re.compile(r"歴史|日本史|世界史|戦国|古代|文明|考古|本能寺|信長|家康|秀吉|光秀|ヴォイニッチ|手稿|古文書|"
                   r"未解読|古代文字|ピラミッド|遺跡|封印|定説|縄文|弥生|邪馬台国|卑弥呼|幕末|江戸|平安|鎌倉|"
                   r"解読|死海文書|聖書|神話|年の謎|ミイラ|王朝|皇帝|ファラオ|オーパーツ")


def log(msg):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def gpm_find(mail):
    page = 1
    while True:
        d = requests.get(f"{GPM}/profiles", params={"page": page, "per_page": 100}, timeout=30).json()["data"]
        for p in d["data"]:
            n = p["name"].strip().lower()
            if n in (mail.lower(), mail.lower().split("@")[0]):
                return p["id"]
        if page >= d["last_page"]:
            return None
        page += 1


def gpm_start(pid):
    j = requests.get(f"{GPM}/profiles/start/{pid}", timeout=180).json()
    if j.get("message") == "ProfileUsingByOther":
        raise RuntimeError("PROFILE_BUSY: profile dang mo o noi khac -> khong kill, doi anh dong roi chay lai")
    d = j.get("data")
    ws = d.get("websocket_debugging_url") if isinstance(d, dict) else ""
    if ws:
        return ws
    # Profile da mo san (lan chay truoc) -> lay cong debug cua DUNG chrome co --user-data-dir chua id
    import subprocess
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
                          "Select-Object -ExpandProperty CommandLine"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.search(r"--remote-debugging-port=(\d+)", line)
        if pid in line and m:
            return requests.get(f"http://127.0.0.1:{m.group(1)}/json/version", timeout=10).json()["webSocketDebuggerUrl"]
    raise RuntimeError(f"GPM start khong co websocket va khong do duoc cong: {j}")


def load_seen():
    if not os.path.exists(LOG_PATH):
        return set()
    return set(re.findall(r"\| ([\w-]{11})(?= \||$)", open(LOG_PATH, encoding="utf-8").read(), re.M))


def stopped():
    return os.path.exists(STOP_FILE)


def sleep_watch(sec):
    """Ngu tung nhip ngan de con bat duoc lenh DUNG."""
    end = time.time() + sec
    while time.time() < end:
        if stopped():
            return False
        time.sleep(min(5, end - time.time()))
    return True


def search(page, kw):
    page.goto("https://www.youtube.com/?hl=ja&gl=JP", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(random.randint(2500, 4500))
    box = page.locator("input[name='search_query']").first
    try:
        box.click(timeout=15000)
        box.fill("")
        for ch in kw:  # go cham nhu nguoi
            page.keyboard.type(ch, delay=random.randint(90, 220))
        page.wait_for_timeout(random.randint(600, 1500))
        page.keyboard.press("Enter")
    except Exception:
        q = urllib.parse.quote(kw)
        page.goto(f"https://www.youtube.com/results?search_query={q}&hl=ja&gl=JP", wait_until="domcontentloaded")
    page.wait_for_selector("ytd-video-renderer a#video-title", timeout=30000)
    page.wait_for_timeout(random.randint(2000, 4000))
    page.mouse.wheel(0, random.randint(300, 900))
    page.wait_for_timeout(random.randint(1500, 3000))


def pick_video(page, seen):
    items = page.evaluate("""() => [...document.querySelectorAll('ytd-video-renderer')].slice(0, 15).map(r => {
        const a = r.querySelector('a#video-title');
        const ch = r.querySelector('ytd-channel-name a');
        return {href: a ? a.href : '', title: a ? (a.title || a.textContent).trim() : '',
                channel: ch ? ch.textContent.trim() : ''};
    })""")
    ok = [x for x in items if "/watch?v=" in x["href"] and JP.search(x["title"])
          and x["href"].split("v=")[1][:11] not in seen]
    if not ok:
        return None
    best = [x for x in ok if is_topic(x)]  # uu tien AI + bi an/lich su
    ai_ok = [x for x in ok if AI.search(x["title"] + " " + x["channel"])]
    return random.choice((best or ai_ok or ok)[:6])


ABOUT_AI = re.compile(r"AIの歴史|AI業界|生成AI|ChatGPTはどう|NewsPicks|ニューズピックス|脳|意識|"
                      r"OpenAI|Claude|業務|自動化|仕事|副業|デスクワーク|速報|宇宙をデザイン|Linux|プログラ")


def is_topic(v):
    """Dung chu de = co AI + (bi an hoac lich su), va KHONG phai video noi ve chinh AI."""
    txt = v["title"] + " " + v["channel"]
    return bool(AI.search(txt) and (MYSTERY.search(txt) or TOPIC.search(txt)) and not ABOUT_AI.search(txt))


def skip_ads(page):
    try:
        page.evaluate("""() => { const b = document.querySelector(
            '.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern'); if (b) b.click(); }""")
    except Exception:
        pass


def like_and_sub(page):
    """Chi bam khi nut dang TAT (bam lai la go like/huy dang ky)."""
    page.bring_to_front()
    return page.evaluate("""() => {
        const r = {like: 'none', sub: 'none'};
        const lk = document.querySelector('like-button-view-model button, #segmented-like-button button');
        if (lk) { if (lk.getAttribute('aria-pressed') === 'true') r.like = 'da co';
                  else { lk.click(); r.like = 'OK'; } }
        const sb = document.querySelector('#owner ytd-subscribe-button-renderer button, #subscribe-button button');
        if (sb) { const t = (sb.innerText + ' ' + (sb.getAttribute('aria-label') || ''));
                  if (/登録済み|登録解除|Subscribed|Unsubscribe/.test(t)) r.sub = 'da co';
                  else { sb.click(); r.sub = 'OK'; } }
        return r; }""")


def watch(page, video, minutes):
    vid = video["href"].split("v=")[1][:11]
    link = page.locator(f"ytd-video-renderer a#video-title[href*='{vid}']").first
    try:
        link.scroll_into_view_if_needed(timeout=5000)
        link.click(timeout=10000)
    except Exception:
        page.goto(f"https://www.youtube.com/watch?v={vid}", wait_until="domcontentloaded")
    page.wait_for_selector("video", timeout=30000)
    page.wait_for_timeout(4000)
    page.evaluate("() => { const v = document.querySelector('video'); if (v && v.paused) v.play(); }")
    target = minutes * 60
    t0 = time.time()
    on_topic = is_topic(video)
    react_at = random.uniform(120, 240) if on_topic else None
    video["react"] = "lech chu de -> khong like/sub"
    while time.time() - t0 < target:
        if not sleep_watch(random.randint(15, 30)):
            return vid, time.time() - t0
        skip_ads(page)
        if react_at and time.time() - t0 >= react_at:
            react_at = None
            try:
                r = like_and_sub(page)
                video["react"] = f"like={r['like']} sub={r['sub']}"
            except Exception as e:
                video["react"] = f"like/sub LOI {str(e)[:60]}"
        st = page.evaluate("""() => { const v = document.querySelector('video');
            if (!v) return {}; if (v.paused && !v.ended) v.play();
            return {ended: v.ended, dur: v.duration, cur: v.currentTime}; }""")
        if st.get("ended"):
            break
        if random.random() < 0.08:  # thinh thoang cuon xuong xem binh luan roi len lai
            page.mouse.wheel(0, random.randint(400, 1200))
            page.wait_for_timeout(random.randint(3000, 8000))
            page.mouse.wheel(0, -2000)
    return vid, time.time() - t0


def run(mail):
    pid = gpm_find(mail)
    if not pid:
        raise RuntimeError(f"Khong thay profile GPM {mail}")
    ws = gpm_start(pid)
    log(f"Da mo profile {mail} ({pid})")
    seen, n = load_seen(), 0
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws, timeout=60000)
        ctx = br.contexts[0]
        page = ctx.new_page()
        page.bring_to_front()
        rnd = 0
        while not stopped():
            rnd += 1
            kws = KEYWORDS[:]
            random.shuffle(kws)
            if rnd == 1:
                kws = PRIORITY + [k for k in kws if k not in PRIORITY]
            for kw in kws:
                if stopped():
                    break
                try:
                    search(page, kw)
                    v = pick_video(page, seen)
                    if not v:
                        log(f"[{kw}] khong co video tieng Nhat moi -> bo qua")
                        continue
                    vid, sec = watch(page, v, random.uniform(4.5, 5.5))
                    seen.add(vid)
                    n += 1
                    log(f"#{n} [{kw}] xem {sec/60:.1f}p | {v['title'][:60]} | {v['channel']} | {vid} | {v.get('react')}")
                except Exception as e:
                    log(f"[{kw}] LOI {type(e).__name__}: {str(e)[:150]} -> bo qua")
                    if not br.is_connected():
                        raise RuntimeError("BROWSER_CLOSED")
                    if page.is_closed():
                        page = ctx.new_page()
                if not sleep_watch(random.randint(5, 20)):
                    break
    log(f"DUNG theo lenh. Tong da xem {n} video.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    LOG_PATH = os.path.join(ROOT, "reports", f"warmup_{a.mail.split('@')[0]}_{datetime.date.today()}.log")
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)
    fails = 0
    while not stopped() and fails < 5:
        try:
            run(a.mail)
            fails = 0
        except KeyboardInterrupt:
            log("Ctrl+C -> dung")
            break
        except Exception as e:
            if "PROFILE_BUSY" in str(e):
                log(str(e))
                break
            fails += 1
            log(f"MAT KET NOI ({type(e).__name__}: {str(e)[:120]}) -> tat profile, mo lai sau 30s (lan {fails}/5)")
            try:
                requests.get(f"{GPM}/profiles/stop/{gpm_find(a.mail)}", timeout=60)
            except Exception:
                pass
            sleep_watch(30)
