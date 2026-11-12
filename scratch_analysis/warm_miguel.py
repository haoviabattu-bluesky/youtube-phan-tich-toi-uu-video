# -*- coding: utf-8 -*-
r"""
WARMUP profile GPM miguelcarolineo0071023@gmail.com (kenh 歴史の謎をAIで解く)
theo kieu lane X (AI謎解き研究所 / lich su Nhat - AI giai ma lich su).

LUONG (dung nhu anh yeu cau 2026-10-22):
  1) Tim kiem  【440年の謎】信長の遺体はどこへ消えたのか？...  -> chon video DAU TIEN
     -> xem ~20 phut -> LIKE -> BINH LUAN 「素晴らしい！本当に最高です！」
  2) Nhin panel de xuat ben phai, click video
     【440年の謎】明智光秀は本当に死んだのか？天海説まで5つの説をAI...
     -> xem 20-22 phut -> LIKE -> BINH LUAN nhu tren
  3) Tu panel goi y, loc video lich su khop tu khoa lane X -> click -> xem tiep (lap vai video)

Chay NEN, ghi log: scratch_analysis/warm_miguel_log.txt
Bao cao:            scratch_analysis/warm_miguel_report.json
"""
import json, os, random, re, sys, time, traceback
from urllib.parse import quote
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

WS = os.environ.get("WARM_WS", "ws://localhost:60233/devtools/browser/b1e4d7fe-8a03-462d-b315-5918fe6b815a")
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "warm_miguel_log.txt")
REPORT = os.path.join(HERE, "warm_miguel_report.json")
STATE = os.path.join(HERE, "warm_miguel_state.json")

CHANNEL_NAME = "歴史の謎をAIで解く"
COMMENT_JA = "素晴らしい！本当に最高です！"

# (tu khoa, so giay xem) — MOI video deu xem 15-20 phut (anh chot 2026-10-22)
WATCH = (15 * 60, 20 * 60)
TARGET_1 = ("【440年の謎】信長の遺体はどこへ消えたのか？一次史料だけでAIに推理させたら、意外な場所が浮かび上がった", WATCH)
TARGET_2_HINT = "明智光秀は本当に死んだのか"          # tim trong panel de xuat ben phai
TARGET_2_WATCH = WATCH

# Tu khoa lane X (dung de CHAM DIEM video goi y o buoc 3)
KW_LANE_X = [
    "日本史", "歴史の謎", "AI歴史", "AI歴史分析", "歴史ミステリー", "日本史ミステリー",
    "歴史考察", "歴史検証", "歴史の真相", "歴史の謎解き", "一次史料", "史料検証",
    "未解決事件", "歴史上の謎", "歴史人物", "戦国時代", "幕末", "平安時代",
    "本能寺の変", "豊臣秀頼", "坂本龍馬", "源義経", "日本史解説", "歴史ドキュメンタリー",
    "生存説", "陰謀説",
    # them bien the hay xuat hien trong tieu de that
    "謎", "AI", "歴史", "戦国", "信長", "光秀", "秀吉", "家康", "幕末", "新選組",
    "邪馬台国", "古代", "江戸", "武将", "合戦", "史料", "都市伝説", "検証", "推理",
]
# BAT BUOC phai co it nhat 1 tu khoa MANH trong tieu de (tranh chon nham video
# "tom tat sach tai chinh" chi vi tinh co chua chu 戦国時代)
KW_STRONG = [
    "日本史", "歴史の謎", "AI歴史", "歴史ミステリー", "日本史ミステリー", "歴史考察",
    "歴史検証", "歴史の真相", "歴史の謎解き", "一次史料", "史料検証", "歴史上の謎",
    "歴史人物", "本能寺の変", "豊臣秀頼", "坂本龍馬", "源義経", "日本史解説",
    "歴史ドキュメンタリー", "生存説", "陰謀説", "戦国時代", "幕末", "平安時代",
    "未解決事件", "歴史", "戦国", "信長", "光秀", "秀吉", "家康", "新選組",
    "邪馬台国", "武将", "合戦", "史料", "日本神話", "古代史", "江戸時代",
]
# loai han khoi danh sach (khong phai lich su / qua ngan)
KW_BLOCK = ["Listening Practice", "日本語", "JLPT", "Gregorian", "LIVE", "Stuka",
            "Dưa Leo", "Phê Phim", "TOÁN HỌC", "北朝鮮", "Tutankhamun", "Kings and Generals",
            "本要約", "要約", "スカッと", "朗読", "睡眠", "作業用", "BGM", "事故",
            "墜落", "映画", "ドラマ", "アニメ", "ニュース", "切り抜き", "生配信"]

WATCH_MIN_S = 15 * 60          # buoc 3: xem toi thieu
WATCH_MAX_S = 20 * 60          # buoc 3: xem toi da
MAX_EXTRA_VIDEOS = 4           # buoc 3: so video them
TOTAL_BUDGET_S = 210 * 60      # tran toan bo phien (~3h30)

_t0 = time.time()


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def save_state(d):
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


# ------------------------------------------------------------------ nguoi
def human(page, lo=0.4, hi=1.6):
    try:
        page.mouse.move(random.randint(250, 1150), random.randint(180, 700),
                        steps=random.randint(5, 15))
    except Exception:
        pass
    time.sleep(random.uniform(lo, hi))


def dismiss_popups(page):
    for sel in ['button[aria-label*="Accept"]', 'button[aria-label*="Chấp nhận"]',
                'tp-yt-paper-dialog button', '#dismiss-button',
                'ytd-consent-bump-v2-lightbox button']:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click(timeout=2000)
                time.sleep(1.2)
        except Exception:
            pass


def go_tu_nhien(page, text, lo=0.07, hi=0.16):
    """go tung ky tu, delay ngau nhien, nghi lau sau dau cau (skill human-like-typing)"""
    DAU = set("。、．，,!?！？…;；:：—ー")
    for ch in text:
        page.keyboard.type(ch)
        d = random.uniform(lo, hi)
        if ch in DAU:
            d += random.uniform(0.3, 0.7)
        elif ch == " ":
            d += random.uniform(0.06, 0.18)
        if random.random() < 0.03:
            d += random.uniform(0.5, 1.2)
        page.wait_for_timeout(int(d * 1000))


# ------------------------------------------------------------------ tim kiem
def search(page, kw):
    page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
    time.sleep(random.uniform(2.5, 4.5))
    dismiss_popups(page)
    box = None
    for sel in ["input#search", "input[name='search_query']", "ytd-searchbox input"]:
        box = page.query_selector(sel)
        if box:
            break
    if box is None:
        log("  ! khong thay o search -> dung URL truc tiep")
        page.goto("https://www.youtube.com/results?search_query=" + quote(kw),
                  wait_until="domcontentloaded", timeout=90000)
        time.sleep(random.uniform(3.5, 5.5))
        return
    box.click()
    time.sleep(random.uniform(0.5, 1.2))
    # go thanh vai doan ngan (giong nguoi go tung cum tu)
    n = len(kw)
    k = min(3, n // 5) if n >= 10 else 0
    cuts = sorted(random.sample(range(2, n), k)) if k > 0 else []
    prev = 0
    for c in cuts + [n]:
        page.keyboard.insert_text(kw[prev:c])
        prev = c
        time.sleep(random.uniform(0.15, 0.45))
    time.sleep(random.uniform(0.7, 1.5))
    page.keyboard.press("Enter")
    time.sleep(random.uniform(3.5, 5.5))
    dismiss_popups(page)


JS_RESULTS = """(lim) => {
  const out = [];
  const els = document.querySelectorAll('ytd-video-renderer, ytd-rich-item-renderer');
  for (const el of els) {
    const a = el.querySelector('a#video-title, a#thumbnail[href*="watch"]');
    if (!a) continue;
    const m = (a.getAttribute('href')||'').match(/[?&]v=([\\w-]{6,})/);
    if (!m) continue;
    const t = (el.querySelector('#video-title')?.textContent || a.getAttribute('title') || '').trim();
    const ch = (el.querySelector('ytd-channel-name a, #channel-name a')?.textContent || '').trim();
    const meta = Array.from(el.querySelectorAll('#metadata-line span, .inline-metadata-item'))
        .map(s => (s.textContent||'').trim()).filter(Boolean);
    if (out.find(o => o.id === m[1])) continue;
    out.push({id: m[1], title: t, ch: ch, meta: meta});
    if (out.length >= lim) break;
  }
  return out;
}"""


def search_results(page, limit=10):
    try:
        return page.evaluate(JS_RESULTS, limit)
    except Exception as e:
        log("  ! loi doc ket qua: %s" % e)
        return []


# ------------------------------------------------------------------ panel goi y phai
JS_RECS = """(lim) => {
  const out = [];
  const side = document.querySelector('#secondary, ytd-watch-next-secondary-results-renderer');
  if (!side) return out;
  const els = side.querySelectorAll('yt-lockup-view-model, ytd-compact-video-renderer, ytd-video-renderer');
  for (const el of els) {
    const a = el.querySelector('a[href*="watch?v="]');
    if (!a) continue;
    const m = (a.getAttribute('href')||'').match(/[?&]v=([\\w-]{6,})/);
    if (!m) continue;
    if (out.find(o => o.id === m[1])) continue;
    const lines = (el.innerText||'').split('\\n').map(s=>s.trim()).filter(Boolean);
    // lines: [thoi luong?, New?, tieu de, kenh, view, thoi gian]
    let dur = null, title = null, ch = null;
    for (const L of lines) {
      if (!dur && /^(\\d{1,2}:)?\\d{1,2}:\\d{2}$/.test(L)) { dur = L; continue; }
    }
    const iDur = dur ? lines.indexOf(dur) : -1;
    const rest = lines.slice(iDur + 1);
    const rest2 = rest[0] === 'New' ? rest.slice(1) : rest;
    title = rest2[0] || ''; ch = rest2[1] || '';
    out.push({id: m[1], title: title, ch: ch, dur: dur, lines: lines.slice(0,6)});
    if (out.length >= lim) break;
  }
  return out;
}"""


def recs(page, limit=25):
    for _ in range(3):
        try:
            r = page.evaluate(JS_RECS, limit)
            if r:
                return r
        except Exception:
            pass
        time.sleep(2)
    return []


def dur_sec(s):
    if not s:
        return None
    p = s.split(":")
    try:
        p = [int(x) for x in p]
    except Exception:
        return None
    if len(p) == 2:
        return p[0] * 60 + p[1]
    if len(p) == 3:
        return p[0] * 3600 + p[1] * 60 + p[2]
    return None


# ------------------------------------------------------------------ click that
def click_rect(page, js_finder, what=""):
    """js_finder: JS tra ve {x,y} tam phan tu -> di chuot roi click that"""
    r = page.evaluate(js_finder)
    if not r or not r.get("x"):
        return False
    page.mouse.move(r["x"] + random.uniform(-4, 4), r["y"] + random.uniform(-3, 3),
                    steps=random.randint(9, 20))
    time.sleep(random.uniform(0.25, 0.6))
    page.mouse.click(r["x"], r["y"])
    return True


def click_rec_by_id(page, vid):
    js = """(vid) => {
      const side = document.querySelector('#secondary, ytd-watch-next-secondary-results-renderer');
      if (!side) return null;
      const els = side.querySelectorAll('yt-lockup-view-model, ytd-compact-video-renderer, ytd-video-renderer');
      for (const el of els) {
        const a = el.querySelector('a[href*="watch?v="]');
        if (!a) continue;
        const m = (a.getAttribute('href')||'').match(/[?&]v=([\\w-]{6,})/);
        if (!m || m[1] !== vid) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 50 || r.height < 30) continue;
        if (r.top < 0 || r.top > window.innerHeight - 80) {
          el.scrollIntoView({block: 'center'});
        }
        const r2 = el.getBoundingClientRect();
        return {x: r2.x + Math.min(120, r2.width/2), y: r2.y + r2.height/2};
      }
      return null;
    }"""
    return click_rect(page, lambda: None) if False else _click_js(page, js, vid)


def _click_js(page, js, arg):
    r = page.evaluate(js, arg)
    if not r or not r.get("x"):
        return False
    time.sleep(random.uniform(0.4, 0.9))
    page.mouse.move(r["x"] + random.uniform(-4, 4), r["y"] + random.uniform(-3, 3),
                    steps=random.randint(9, 20))
    time.sleep(random.uniform(0.25, 0.6))
    page.mouse.click(r["x"], r["y"])
    return True


# ------------------------------------------------------------------ phat / xem
def skip_ad(page):
    for sel in ["button.ytp-skip-ad-button", "button.ytp-ad-skip-button-modern",
                ".ytp-ad-skip-button"]:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click(timeout=2000)
                time.sleep(2.5)
                return True
        except Exception:
            pass
    return False


def ensure_playing(page):
    js = """() => {
      const v = document.querySelector('video.html5-main-video') || document.querySelector('video');
      if (!v) return {ok:false};
      v.muted = false; if (v.volume < 0.05) v.volume = 0.25;
      const ad = !!document.querySelector('.ad-showing, .ytp-ad-player-overlay');
      if (v.paused && !ad) { v.play().catch(()=>{}); }
      return {ok:true, t:v.currentTime, d:v.duration, paused:v.paused, ad:ad};
    }"""
    for _ in range(18):
        try:
            st = page.evaluate(js)
            if st and st.get("ok"):
                if st.get("ad"):
                    skip_ad(page)
                    time.sleep(2)
                    continue
                if not st.get("paused"):
                    return st
        except Exception:
            pass
        try:
            page.click("button.ytp-large-play-button", timeout=1500)
        except Exception:
            pass
        time.sleep(1.5)
    return None


def watch(page, seconds, tag=""):
    """xem `seconds` giay, cu dong chuot nhe; KHONG tua, KHONG bo qua"""
    st = ensure_playing(page)
    if not st:
        log("  ! khong phat duoc video %s" % tag)
        return 0, None
    d = st.get("d") or 0
    log("  > bat dau xem %ds (dai %.0fs = %d:%02d) %s" % (seconds, d, int(d)//60, int(d) % 60, tag))
    t0 = time.time()
    last_move = 0.0
    while time.time() - t0 < seconds:
        if time.time() - _t0 > TOTAL_BUDGET_S:
            log("  ! het ngan sach thoi gian phien -> dung xem")
            break
        chunk = random.uniform(18, 40)
        time.sleep(min(chunk, max(1, seconds - (time.time() - t0))))
        el = time.time() - t0
        # cu dong chuot / cuon nhe nhu nguoi
        if el - last_move > random.uniform(55, 120):
            human(page, 0.3, 1.2)
            if random.random() < 0.35:
                try:
                    page.mouse.wheel(0, random.randint(200, 520))
                    time.sleep(random.uniform(2, 5))
                    page.mouse.wheel(0, -random.randint(150, 460))
                except Exception:
                    pass
            last_move = el
        skip_ad(page)
        try:
            cur = page.evaluate("""() => {
              const v = document.querySelector('video');
              return v ? {t:v.currentTime, p:v.paused, e:v.ended, d:v.duration} : null;
            }""")
        except Exception:
            cur = None
        if cur and (cur.get("ended") or cur.get("p")):
            # het video / bi dung -> thu phat lai 1 lan
            log("  ~ video dung/ket thuc o %.0fs -> thu phat lai" % el)
            ensure_playing(page)
        if int(el) % 300 < 40:
            log("  . da xem %.0fs / %ds" % (el, seconds))
    return int(time.time() - t0), (cur or {}).get("d")


# ------------------------------------------------------------------ like
JS_LIKE_INFO = """() => {
  const b = document.querySelector('segmented-like-dislike-button-view-model button');
  if (!b) {
    const bs = Array.from(document.querySelectorAll('like-button-view-model button')).filter(x=>x.offsetWidth);
    if (!bs.length) return null;
    return {aria: bs[0].getAttribute('aria-label'), pressed: bs[0].getAttribute('aria-pressed')};
  }
  return {aria: b.getAttribute('aria-label'), pressed: b.getAttribute('aria-pressed')};
}"""

JS_LIKE_CLICK = """() => {
  let b = document.querySelector('segmented-like-dislike-button-view-model button');
  if (!b) {
    const bs = Array.from(document.querySelectorAll('like-button-view-model button')).filter(x=>x.offsetWidth);
    b = bs[0];
  }
  if (!b) return null;
  b.scrollIntoView({block:'center'});
  const r = b.getBoundingClientRect();
  return {x: r.x + r.width/2, y: r.y + r.height/2,
          pressed: b.getAttribute('aria-pressed'), aria: b.getAttribute('aria-label')};
}"""


def like_video(page):
    before = page.evaluate(JS_LIKE_INFO)
    if before and before.get("pressed") == "true":
        log("  = da like tu truoc (aria-pressed=true)")
        return {"already": True, "before": before}
    r = page.evaluate(JS_LIKE_CLICK)
    if not r:
        log("  ! khong thay nut like")
        return {"found": False}
    time.sleep(random.uniform(0.8, 1.6))
    r = page.evaluate(JS_LIKE_CLICK)      # do lai sau scroll
    if not r:
        return {"found": False}
    page.mouse.move(r["x"] + random.uniform(-3, 3), r["y"] + random.uniform(-2, 2),
                    steps=random.randint(8, 16))
    time.sleep(random.uniform(0.2, 0.5))
    page.mouse.click(r["x"], r["y"])
    time.sleep(random.uniform(2.0, 3.2))
    after = page.evaluate(JS_LIKE_INFO)
    ok = bool(after and after.get("pressed") == "true")
    log("  LIKE -> aria-pressed=%s | %s" % (after and after.get("pressed"), after and after.get("aria")))
    return {"clicked": True, "ok": ok, "before": before, "after": after}


# ------------------------------------------------------------------ comment
JS_OPEN_BOX = """() => {
  const ph = document.querySelector('ytd-comment-simplebox-renderer #simplebox-placeholder, #simplebox-placeholder');
  if (ph) {
    ph.scrollIntoView({block:'center'});
    const r = ph.getBoundingClientRect();
    return {x: r.x + r.width/2, y: r.y + r.height/2, how:'placeholder'};
  }
  const sb = document.querySelector('ytd-comment-simplebox-renderer');
  if (sb) {
    sb.scrollIntoView({block:'center'});
    const r = sb.getBoundingClientRect();
    return {x: r.x + Math.min(300, r.width/2), y: r.y + r.height/2, how:'simplebox'};
  }
  return null;
}"""

JS_CE_RECT = """() => {
  const els = Array.from(document.querySelectorAll('#contenteditable-root, div[contenteditable="true"]'));
  for (const e of els) {
    const r = e.getBoundingClientRect();
    if (r.width > 100 && r.height > 8) return {x: r.x + Math.min(200, r.width/2), y: r.y + r.height/2};
  }
  return null;
}"""

JS_SUBMIT_RECT = """() => {
  const bs = Array.from(document.querySelectorAll('#submit-button button, ytd-commentbox #submit-button'));
  for (const b of bs) {
    const r = b.getBoundingClientRect();
    if (r.width > 20 && !b.disabled) return {x: r.x + r.width/2, y: r.y + r.height/2};
  }
  return null;
}"""

JS_CE_TEXT = """() => {
  const e = document.querySelector('#contenteditable-root, div[contenteditable="true"]');
  if (!e) return '';
  const r = document.createRange(); r.selectNodeContents(e); return r.toString();
}"""


def comment_video(page, text, timeout_open=40):
    # cuon toi khu comment
    for _ in range(7):
        try:
            page.mouse.wheel(0, random.randint(500, 800))
        except Exception:
            pass
        time.sleep(random.uniform(0.9, 1.6))
    time.sleep(random.uniform(2, 4))

    r = page.evaluate(JS_OPEN_BOX)
    if not r:
        log("  ! khong thay o binh luan")
        return {"ok": False, "err": "no_simplebox"}
    page.mouse.move(r["x"] + random.uniform(-4, 4), r["y"] + random.uniform(-3, 3), steps=12)
    time.sleep(random.uniform(0.3, 0.7))
    page.mouse.click(r["x"], r["y"])
    time.sleep(random.uniform(2.0, 3.5))

    ce = None
    for _ in range(timeout_open):
        ce = page.evaluate(JS_CE_RECT)
        if ce:
            break
        time.sleep(1)
    if not ce:
        log("  ! o nhap binh luan khong hien")
        return {"ok": False, "err": "no_ce"}

    page.mouse.click(ce["x"], ce["y"])
    time.sleep(random.uniform(0.8, 1.6))
    go_tu_nhien(page, text)
    time.sleep(random.uniform(1.2, 2.2))

    typed = page.evaluate(JS_CE_TEXT)
    log("  go xong binh luan: %r" % typed)
    if not typed.strip():
        return {"ok": False, "err": "empty_after_type"}

    sub = None
    for _ in range(12):
        sub = page.evaluate(JS_SUBMIT_RECT)
        if sub:
            break
        time.sleep(1)
    if not sub:
        log("  ! nut Comment khong bat")
        return {"ok": False, "err": "submit_disabled", "typed": typed}

    time.sleep(random.uniform(0.7, 1.4))
    page.mouse.move(sub["x"] + random.uniform(-3, 3), sub["y"] + random.uniform(-2, 2), steps=10)
    time.sleep(random.uniform(0.2, 0.5))
    page.mouse.click(sub["x"], sub["y"])
    log("  da bam gui binh luan")
    time.sleep(random.uniform(4, 6))

    # verify: o nhap rong + ten kenh xuat hien trong danh sach comment
    left = page.evaluate(JS_CE_TEXT)
    found = page.evaluate("""(name) => {
      const els = document.querySelectorAll('ytd-comment-thread-renderer #author-text, ytd-comment-view-model #author-text');
      const arr = Array.from(els).slice(0, 12).map(e => (e.textContent||'').trim().replace(/^@/, ''));
      return {authors: arr, hit: arr.some(a => a.includes(name))};
    }""", CHANNEL_NAME)
    ok = (not left.strip()) and bool(found.get("hit"))
    log("  VERIFY comment: o nhap con %r | thay ten kenh=%s" % (left.strip()[:40], found.get("hit")))
    return {"ok": ok, "typed": typed, "left": left.strip(), "verify": found}


# ------------------------------------------------------------------ cham diem goi y
def score_candidate(rec, watched_ids):
    t = rec.get("title") or ""
    if not t or rec["id"] in watched_ids:
        return -1
    for b in KW_BLOCK:
        if b.lower() in t.lower():
            return -1
    d = dur_sec(rec.get("dur"))
    if d is not None and d < 8 * 60:
        return -1
    # BAT BUOC co it nhat 1 tu khoa MANH cua lane X trong tieu de
    if not any(k in t for k in KW_STRONG):
        return -1
    s = 0
    for k in KW_LANE_X:
        if k in t:
            s += 3 if len(k) >= 4 else 1
    if "AI" in t:
        s += 2
    if "【" in t:
        s += 1
    if (rec.get("ch") or "") in ("AI謎解き研究所", "AI都市伝説検証室", "AI歴史の教科書チャンネル"):
        s += 3
    return s


# ------------------------------------------------------------------ main
def main():
    open(LOG, "w", encoding="utf-8").close()
    log("=== WARMUP %s (kenh %s) ===" % ("miguelcarolineo0071023@gmail.com", CHANNEL_NAME))
    report = {"start": time.strftime("%Y-%m-%d %H:%M:%S"), "steps": []}
    watched = set()

    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(WS)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.set_viewport_size({"width": 1600, "height": 900})
        except Exception:
            pass

        try:
            # ---------- BUOC 1: tim kiem -> video dau tien -> xem 20' -> like -> comment
            kw1, (lo1, hi1) = TARGET_1
            log("[1/3] TIM KIEM: %s" % kw1)
            search(page, kw1)
            res = search_results(page, 8)
            log("  %d ket qua" % len(res))
            if not res:
                raise RuntimeError("khong co ket qua tim kiem")
            pick = res[0]
            log("  chon video DAU TIEN: %s | %s | %s" % (pick["id"], pick["title"][:70], pick["ch"]))

            page.goto("https://www.youtube.com/watch?v=" + pick["id"],
                      wait_until="domcontentloaded", timeout=90000)
            time.sleep(random.uniform(4, 6.5))
            dismiss_popups(page)
            try:
                page.click("button.ytp-skip-ad-button", timeout=9000)
                time.sleep(2)
            except Exception:
                pass
            watched.add(pick["id"])
            dur = random.randint(lo1, hi1)
            w1, vlen = watch(page, dur, "buoc1")
            like1 = like_video(page)
            human(page, 1.2, 2.6)
            cm1 = comment_video(page, COMMENT_JA)
            report["steps"].append({"step": 1, "kind": "target_search", "kw": kw1,
                                    "video": pick, "watched_s": w1, "video_len": vlen,
                                    "like": like1, "comment": cm1})
            save_state(report)
            log("  => buoc 1 xong: xem %ds | like=%s | comment=%s"
                % (w1, (like1 or {}).get("ok"), (cm1 or {}).get("ok")))
            human(page, 3, 6)

            # ---------- BUOC 2: panel phai -> video 明智光秀 -> xem 20-22' -> like -> comment
            log("[2/3] TIM TRONG PANEL DE XUAT: %s" % TARGET_2_HINT)
            r2 = None
            for attempt in range(4):
                rr = recs(page, 25)
                log("  doc duoc %d goi y" % len(rr))
                for x in rr:
                    if TARGET_2_HINT in (x.get("title") or ""):
                        r2 = x
                        break
                if r2:
                    break
                try:
                    page.mouse.wheel(0, 600)
                except Exception:
                    pass
                time.sleep(4)
            if not r2:
                raise RuntimeError("khong thay video 明智光秀 trong panel de xuat")
            log("  chon: %s | %s | %s | %s" % (r2["id"], (r2.get("dur") or "?"), r2["title"][:70], r2.get("ch")))
            ok_click = _click_js(page, """(vid) => {
              const side = document.querySelector('#secondary, ytd-watch-next-secondary-results-renderer');
              if (!side) return null;
              const els = side.querySelectorAll('yt-lockup-view-model, ytd-compact-video-renderer, ytd-video-renderer');
              for (const el of els) {
                const a = el.querySelector('a[href*="watch?v="]');
                if (!a) continue;
                const m = (a.getAttribute('href')||'').match(/[?&]v=([\\w-]{6,})/);
                if (!m || m[1] !== vid) continue;
                el.scrollIntoView({block:'center'});
                const r = el.getBoundingClientRect();
                if (r.width < 50) continue;
                return {x: r.x + Math.min(150, r.width/2), y: r.y + r.height/2};
              }
              return null;
            }""", r2["id"])
            if not ok_click:
                log("  ! click goi y that bai -> goto truc tiep")
                page.goto("https://www.youtube.com/watch?v=" + r2["id"],
                          wait_until="domcontentloaded", timeout=90000)
            time.sleep(random.uniform(5, 8))
            cur_url = page.url
            if r2["id"] not in cur_url:
                log("  ! click khong doi trang (%s) -> goto truc tiep" % cur_url[:90])
                page.goto("https://www.youtube.com/watch?v=" + r2["id"],
                          wait_until="domcontentloaded", timeout=90000)
                time.sleep(random.uniform(4, 6))
            dismiss_popups(page)
            watched.add(r2["id"])
            lo2, hi2 = TARGET_2_WATCH
            w2, vlen2 = watch(page, random.randint(lo2, hi2), "buoc2")
            like2 = like_video(page)
            human(page, 1.2, 2.6)
            cm2 = comment_video(page, COMMENT_JA)
            report["steps"].append({"step": 2, "kind": "from_recommendation", "video": r2,
                                    "watched_s": w2, "video_len": vlen2,
                                    "like": like2, "comment": cm2})
            save_state(report)
            log("  => buoc 2 xong: xem %ds | like=%s | comment=%s"
                % (w2, (like2 or {}).get("ok"), (cm2 or {}).get("ok")))
            human(page, 3, 6)

            # ---------- BUOC 3: tu panel goi y, loc video lich su lane X -> xem tiep
            log("[3/3] LOC GOI Y LANE X -> xem tiep (toi da %d video)" % MAX_EXTRA_VIDEOS)
            n = 0
            while n < MAX_EXTRA_VIDEOS and time.time() - _t0 < TOTAL_BUDGET_S - 20 * 60:
                rr = recs(page, 25)
                scored = []
                for x in rr:
                    s = score_candidate(x, watched)
                    if s > 0:
                        scored.append((s, x))
                scored.sort(key=lambda z: -z[0])
                if not scored:
                    log("  ! khong con goi y khop -> dung buoc 3")
                    break
                top = [z[1] for z in scored[:6]]
                log("  ung vien: " + " | ".join("%s(%d)" % (t["title"][:38], s) for s, t in scored[:5]))
                cand = top[0]
                log("  chon: %s | %s | %s | %s" % (cand["id"], (cand.get("dur") or "?"),
                                                   cand["title"][:70], cand.get("ch")))
                ok_click = _click_js(page, """(vid) => {
                  const side = document.querySelector('#secondary, ytd-watch-next-secondary-results-renderer');
                  if (!side) return null;
                  const els = side.querySelectorAll('yt-lockup-view-model, ytd-compact-video-renderer, ytd-video-renderer');
                  for (const el of els) {
                    const a = el.querySelector('a[href*="watch?v="]');
                    if (!a) continue;
                    const m = (a.getAttribute('href')||'').match(/[?&]v=([\\w-]{6,})/);
                    if (!m || m[1] !== vid) continue;
                    el.scrollIntoView({block:'center'});
                    const r = el.getBoundingClientRect();
                    if (r.width < 50) continue;
                    return {x: r.x + Math.min(150, r.width/2), y: r.y + r.height/2};
                  }
                  return null;
                }""", cand["id"])
                if not ok_click:
                    page.goto("https://www.youtube.com/watch?v=" + cand["id"],
                              wait_until="domcontentloaded", timeout=90000)
                time.sleep(random.uniform(5, 8))
                if cand["id"] not in page.url:
                    page.goto("https://www.youtube.com/watch?v=" + cand["id"],
                              wait_until="domcontentloaded", timeout=90000)
                    time.sleep(random.uniform(4, 6))
                dismiss_popups(page)
                watched.add(cand["id"])
                w3, vlen3 = watch(page, random.randint(WATCH_MIN_S, WATCH_MAX_S), "buoc3-%d" % (n + 1))
                like3 = like_video(page)
                report["steps"].append({"step": 3, "idx": n + 1, "kind": "lane_x_candidate",
                                        "video": cand, "watched_s": w3, "video_len": vlen3,
                                        "like": like3})
                save_state(report)
                log("  => buoc 3.%d xong: xem %ds | like=%s" % (n + 1, w3, (like3 or {}).get("ok")))
                n += 1
                human(page, 3, 7)

            report["status"] = "DONE"
        except Exception as e:
            log("!! LOI: %s" % e)
            log(traceback.format_exc()[-1200:])
            report["status"] = "ERROR"
            report["error"] = str(e)[:400]
        finally:
            report["end"] = time.strftime("%Y-%m-%d %H:%M:%S")
            report["elapsed_min"] = round((time.time() - _t0) / 60, 1)
            report["watched_ids"] = sorted(watched)
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=1)
            save_state(report)
            log("=== KET THUC: %s | %.1f phut | %d video ===" %
                (report.get("status"), report["elapsed_min"], len(watched)))
            try:
                br.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
