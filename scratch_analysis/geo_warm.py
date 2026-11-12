# -*- coding: utf-8 -*-
"""Lam am profile GEO: tim kiem -> xem video -> like -> 24 tu khoa warm-up.
Chay tren GPM profile alexusmickey94@gmail.com qua CDP.
"""
import json, os, random, re, time, traceback
from playwright.sync_api import sync_playwright

WS = os.environ.get("GEO_WS", "ws://localhost:58957/devtools/browser/fda60c17-211c-4108-8d31-7fe41dd3382b")
LOG = r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\geo_warm_log.txt"

KW_TARGET = [
    ("四国と九州になぜ橋がない？海を抜いて見てみた", (10 * 60, 15 * 60)),
    ("太平洋の真ん中になぜハワイ？海を抜いて見てみた", (15 * 60, 20 * 60)),
]
KW_WARM = ["地理", "地形", "地図", "日本地理", "地理解説", "地形解説", "地理の謎", "地形の謎",
           "地球の謎", "海底地形", "海底トンネル", "地下空間", "巨大建造物", "土木", "インフラ",
           "地質学", "日本の地形", "河川", "湖", "海峡", "防災", "地図で解説", "3D地形",
           "AI映像", "科学解説", "ジオの謎解き"]


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def human(page, lo=0.4, hi=1.6):
    """dung nho: di chuot + nghi ngau nhien"""
    try:
        page.mouse.move(random.randint(200, 1100), random.randint(150, 700), steps=random.randint(4, 14))
    except Exception:
        pass
    time.sleep(random.uniform(lo, hi))


def dismiss_popups(page):
    for sel in ['button[aria-label*="Chấp nhận"]', 'button[aria-label*="Accept"]',
                'tp-yt-paper-dialog button', '#dismiss-button']:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click(timeout=2000)
                time.sleep(1)
        except Exception:
            pass


def search(page, kw):
    """go tu khoa vao o search nhu nguoi that"""
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
        from urllib.parse import quote
        page.goto("https://www.youtube.com/results?search_query=" + quote(kw),
                  wait_until="domcontentloaded", timeout=90000)
        time.sleep(random.uniform(3, 5))
        return
    box.click()
    time.sleep(random.uniform(0.5, 1.2))
    # go tung doan ngan de giong nguoi go
    n = len(kw)
    if n >= 8:
        k = min(3, n // 4)
        cuts = sorted(random.sample(range(2, n), k)) if k > 0 else []
    else:
        cuts = [n // 2] if n >= 4 else []
    prev = 0
    for c in cuts + [n]:
        page.keyboard.insert_text(kw[prev:c])
        prev = c
        time.sleep(random.uniform(0.12, 0.35))
    time.sleep(random.uniform(0.6, 1.4))
    page.keyboard.press("Enter")
    time.sleep(random.uniform(3.5, 5.5))
    dismiss_popups(page)


def results(page, limit=8):
    js = """(lim) => {
      const out = [];
      const els = document.querySelectorAll('ytd-video-renderer, ytd-rich-item-renderer');
      for (const el of els) {
        const a = el.querySelector('a#video-title, a#thumbnail[href*="watch"]');
        if (!a) continue;
        const href = a.getAttribute('href') || '';
        const m = href.match(/[?&]v=([\\w-]{6,})/);
        if (!m) continue;
        const t = (el.querySelector('#video-title')?.textContent || a.getAttribute('title') || '').trim();
        const ch = (el.querySelector('ytd-channel-name a, #channel-name a')?.textContent || '').trim();
        let meta = '';
        const spans = el.querySelectorAll('#metadata-line span');
        if (spans.length) {
          for (const s of spans) {
            const t = (s.textContent||'').trim();
            if (/^[\\d.,]+\\s*(N|K|M|Tr|T)?$/i.test(t)) { meta = t; break; }
          }
          if (!meta) meta = (spans[0]?.textContent||'').trim();
        }
        if (!meta) {
          const it = el.querySelectorAll('.inline-metadata-item');
          for (const s of it) {
            const t = (s.textContent||'').trim();
            if (/^[\\d.,]+\\s*(N|K|M|Tr|T)?$/i.test(t)) { meta = t; break; }
          }
        }
        if (out.find(o => o.id === m[1])) continue;
        out.push({id: m[1], title: t, ch: ch, views: meta});
        if (out.length >= lim) break;
      }
      return out;
    }"""
    try:
        return page.evaluate(js, limit)
    except Exception as e:
        log("  ! loi doc ket qua: %s" % e)
        return []


def parse_views(txt):
    """'1,7 Tr lượt xem' / '1.7M views' -> int. Tra None neu khong phai so luot xem
    (vd '6 ngày trước' KHONG duoc doc thanh 6000)."""
    if not txt:
        return None
    s = txt.replace(",", ".").replace("\u00a0", " ").strip()
    m = re.fullmatch(r"([\d.]+)\s*(N|K|M|Tr|T|triệu|nghìn)?\s*(lượt xem|views|观看)?",
                     s, re.I)
    if not m:
        return None
    try:
        v = float(m.group(1))
    except Exception:
        return None
    unit = (m.group(2) or "").lower()
    mult = 1
    if unit in ("k", "n", "nghìn"):
        mult = 1000
    elif unit in ("m", "tr", "triệu"):
        mult = 1_000_000
    elif unit == "t":
        mult = 1_000_000_000
    return int(v * mult)


def skip_ad(page):
    """bo qua quang cao dang phat (neu co nut Skip)"""
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
    """dam bao video dang phat, am luong nho"""
    js = """() => {
      const v = document.querySelector('video.html5-main-video') || document.querySelector('video');
      if (!v) return {ok:false};
      v.muted = false; v.volume = 0.22;
      const ad = !!document.querySelector('.ad-showing, .ytp-ad-player-overlay');
      if (v.paused && !ad) { v.play().catch(()=>{}); }
      return {ok:true, t:v.currentTime, d:v.duration, paused:v.paused, ad:ad};
    }"""
    for _ in range(15):
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
    """xem video trong `seconds` giay, co cu dong nhu nguoi.
    Neu video ngan ket thuc som -> de autoplay chay tiep video ke tiep (giong nguoi that)."""
    st = ensure_playing(page)
    if not st:
        log("  ! khong phat duoc video %s" % tag)
        return 0
    log("  > bat dau xem %ds (dai video %.0fs) %s" % (seconds, st.get("d") or 0, tag))
    t0 = time.time()
    last_scroll = 0
    ended_count = 0
    while time.time() - t0 < seconds:
        chunk = random.uniform(20, 45)
        time.sleep(min(chunk, max(1, seconds - (time.time() - t0))))
        el = time.time() - t0
        if el - last_scroll > random.uniform(90, 160):
            try:
                page.mouse.wheel(0, random.randint(350, 900))
                time.sleep(random.uniform(3, 7))
                page.mouse.wheel(0, -random.randint(200, 600))
            except Exception:
                pass
            last_scroll = el
        try:
            cur = page.evaluate("""() => {
              const v = document.querySelector('video');
              return v ? {t:v.currentTime, p:v.paused, e:v.ended, d:v.duration} : null;
            }""")
        except Exception:
            cur = None
        if cur and (cur.get("ended") or cur.get("p")):
            ended_count += 1
            log("  ~ video ket thuc/dung o %.0fs -> doi autoplay video ke tiep" % el)
            ok = False
            for _ in range(20):
                time.sleep(2)
                try:
                    cur2 = page.evaluate("""() => {
                      const v = document.querySelector('video');
                      return v ? {t:v.currentTime, p:v.paused, e:v.ended, d:v.duration} : null;
                    }""")
                except Exception:
                    cur2 = None
                if cur2 and not cur2.get("p") and not cur2.get("e") and (cur2.get("t") or 0) > 1:
                    ok = True
                    log("  ~ autoplay chay video moi (dai %.0fs)" % (cur2.get("d") or 0))
                    break
            if not ok:
                skip_ad(page)
                st2 = ensure_playing(page)
                if not st2:
                    log("  ! autoplay khong chay -> dung xem som")
                    break
            if ended_count >= 4:
                log("  ! da qua 4 video lien tiep -> dung")
                break
        human(page, 0.2, 0.8)
        if int(el) % 60 < 30:
            log("  . da xem %ds" % el)
    return int(time.time() - t0)


def like_video(page):
    """like bang like-button-view-model (label VN: 'cùng N người khác thích video này')"""
    js = """() => {
      const btns = document.querySelectorAll('like-button-view-model button');
      for (const b of btns) {
        if (!b.offsetWidth) continue;
        if (b.getAttribute('aria-pressed') === 'true') return {already:true, label:b.getAttribute('aria-label')};
        b.click();
        return {clicked:true, label:b.getAttribute('aria-label')};
      }
      const seg = document.querySelector('segmented-like-dislike-button-view-model button');
      if (seg) { seg.click(); return {clicked:true, label:seg.getAttribute('aria-label'), via:'segmented'}; }
      return {found:false};
    }"""
    r = page.evaluate(js)
    time.sleep(2.0)
    st = page.evaluate("""() => {
      const b = document.querySelector('like-button-view-model button');
      return b ? {pressed: b.getAttribute('aria-pressed'), label: b.getAttribute('aria-label')} : null;
    }""")
    return r, st


def main():
    open(LOG, "w", encoding="utf-8").close()
    log("=== BAT DAU warm profile GEO (alexusmickey94@gmail.com) ===")
    plan = [(k, "target") for k, _ in KW_TARGET] + [(k, "warm") for k in KW_WARM]
    report = []
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(WS)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.set_viewport_size({"width": 1440, "height": 900})
        except Exception:
            pass
        for idx, (kw, kind) in enumerate(plan, 1):
            log("[%d/%d] TU KHOA: %s (%s)" % (idx, len(plan), kw, kind))
            try:
                search(page, kw)
                res = results(page, 8)
                if not res:
                    log("  ! khong co ket qua -> bo qua")
                    report.append({"kw": kw, "kind": kind, "status": "NO_RESULT"})
                    continue
                pick = res[0]
                if kind == "target":
                    # uu tien video dau tien co ~1,7 tr view
                    for r in res:
                        v = parse_views(r.get("views"))
                        if v and v >= 1_000_000:
                            pick = r
                            break
                log("  chon: %s | %s | %s" % (pick.get("id"), (pick.get("views") or "?"), pick.get("title", "")[:60]))
                page.goto("https://www.youtube.com/watch?v=" + pick["id"],
                          wait_until="domcontentloaded", timeout=90000)
                time.sleep(random.uniform(3.5, 6.0))
                dismiss_popups(page)
                # bo qua quang cao neu co
                try:
                    page.click("button.ytp-skip-ad-button", timeout=8000)
                    time.sleep(2)
                except Exception:
                    pass
                if kind == "target":
                    lo, hi = dict(KW_TARGET)[kw]
                    dur = random.randint(lo, hi)
                else:
                    dur = random.randint(95, 200)
                watched = watch(page, dur, kw[:18])
                rec = {"kw": kw, "kind": kind, "id": pick["id"], "title": pick.get("title"),
                       "views": pick.get("views"), "watched_s": watched}
                if kind == "target":
                    r, st = like_video(page)
                    rec["like"] = r
                    rec["aria_pressed"] = st
                    log("  like: %s | aria-pressed=%s" % (r, st))
                report.append(rec)
                human(page, 1.5, 3.5)
            except Exception as e:
                log("  !! LOI: %s" % e)
                log(traceback.format_exc()[-600:])
                report.append({"kw": kw, "kind": kind, "status": "ERROR", "err": str(e)[:200]})
                try:
                    page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=60000)
                except Exception:
                    pass
                time.sleep(5)
        with open(r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\geo_warm_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        log("=== XONG ===")
        br.close()


if __name__ == "__main__":
    main()
