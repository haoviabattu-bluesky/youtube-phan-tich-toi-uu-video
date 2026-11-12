# -*- coding: utf-8 -*-
r"""
Xem video YouTube nhu nguoi that qua profile GPM (CDP):
  search tu khoa -> mo ket qua dau tien -> xem 15-20 phut -> LIKE + DANG KY
  -> sang video de xuat dau tien o cot phai -> lap lai.

  py -3.13 yt_watch_v2.py --ws ws://localhost:PORT/... --query "..." --watch-min 15 --watch-max 20 --videos 3

Da tinh: ad quang cao (pre-roll) phai SKIP va KHONG duoc tinh vao thoi gian xem.
"""
import sys, os, time, json, random, argparse, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def hp(a=0.6, b=1.8):
    time.sleep(random.uniform(a, b))


STATE_JS = r"""() => {
  const v = document.querySelector('video.html5-main-video');
  const pr = window.ytInitialPlayerResponse;
  return {
    url: location.href,
    videoId: pr?.videoDetails?.videoId || null,
    prTitle: pr?.videoDetails?.title || null,
    author: pr?.videoDetails?.author || null,
    lengthSec: pr?.videoDetails?.lengthSeconds ? +pr.videoDetails.lengthSeconds : null,
    t: v ? v.currentTime : 0,
    d: v ? v.duration : 0,
    paused: v ? v.paused : null,
    muted: v ? v.muted : null,
    adShowing: !!document.querySelector('.ad-showing'),
    title: (document.querySelector('h1.ytd-watch-metadata yt-formatted-string')?.textContent || '').trim(),
    channel: (document.querySelector('#owner #channel-name a, ytd-channel-name#channel-name a')?.textContent || '').trim(),
  };
}"""


def state(page):
    try:
        return page.evaluate(STATE_JS)
    except Exception:
        return {}


def handle_ads(page, limit=180):
    """bam 'Bo qua' neu co; cho ad ket thuc. Tra ve True neu da sach ad."""
    t0 = time.time()
    while time.time() - t0 < limit:
        st = state(page)
        if not st.get("adShowing"):
            return True
        clicked = page.evaluate(r"""() => {
          const cands = ['.ytp-skip-ad-button', '.ytp-ad-skip-button', '.ytp-ad-skip-button-modern',
                         '.ytp-skip-ad button', 'button.ytp-ad-skip-button-container'];
          for (const s of cands) {
            const e = document.querySelector(s);
            if (e && e.offsetParent !== null) { e.click(); return s; }
          }
          return null;
        }""")
        if clicked:
            log("   [ad] da bam bo qua:", clicked)
        time.sleep(2)
    return False


def ensure_playing(page):
    for _ in range(4):
        st = state(page)
        if st.get("adShowing"):
            handle_ads(page)
            continue
        if st.get("paused"):
            log("   video pause -> play lai")
            try:
                page.evaluate("() => document.querySelector('video.html5-main-video')?.play()")
            except Exception:
                pass
            time.sleep(2)
            continue
        return st
    return state(page)


def human_move(page):
    try:
        vp = page.viewport_size or {"width": 1366, "height": 850}
        page.mouse.move(random.randint(150, vp["width"] - 150), random.randint(150, vp["height"] - 150),
                        steps=random.randint(8, 18))
    except Exception:
        pass


def search_and_first(page, query):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    log("mo trang ket qua tim kiem")
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    try:
        page.wait_for_selector("ytd-video-renderer a#video-title", timeout=45000)
    except Exception:
        log("!! khong thay ket qua")
        return None
    hp(2, 3.5)
    res = page.evaluate(r"""() => [...document.querySelectorAll('ytd-video-renderer')].slice(0,5).map(it => {
        const a = it.querySelector('a#video-title');
        return {t:(a?.textContent||'').trim(), href:a?.href||'',
                meta:(it.querySelector('#metadata-line')?.innerText||'').replace(/\s+/g,' '),
                ch:(it.querySelector('ytd-channel-name a')?.textContent||'').trim()};
      })""")
    log("ket qua tim kiem (5 dau):")
    for i, r in enumerate(res):
        log(f"   {i+1}. {r['t'][:70]} | {r['ch']} | {r['meta']}")
    if not res:
        return None
    first = res[0]
    log("=> chon ket qua 1:", first["t"][:70])
    page.goto(first["href"], wait_until="domcontentloaded", timeout=90000)
    hp(3, 5)
    return first


def click_like(page):
    el = page.evaluate_handle(r"""() => {
      const sels = ['ytd-watch-metadata #top-level-buttons-computed like-button-view-model button',
                    'ytd-watch-metadata like-button-view-model button',
                    'ytd-watch-metadata #segmented-like-button button',
                    'segmented-like-dislike-button-view-model button'];
      for (const s of sels) { const e = document.querySelector(s); if (e) return e; }
      return null;
    }""").as_element()
    if not el:
        log("   !! khong thay nut like")
        return False
    if (el.get_attribute("aria-pressed") or "") == "true":
        log("   like: DA LIKE TU TRUOC")
        return True
    el.click()
    hp(2, 3)
    el2 = page.evaluate_handle(r"""() => document.querySelector('like-button-view-model button')""").as_element()
    ok = bool(el2) and (el2.get_attribute("aria-pressed") or "") == "true"
    log("   like ->", "OK (aria-pressed=true)" if ok else "KHONG XAC NHAN DUOC")
    return ok


def click_subscribe(page):
    el = page.evaluate_handle(r"""() => {
      const sels = ['ytd-watch-metadata #subscribe-button button', '#owner #subscribe-button button',
                    'ytd-subscribe-button-renderer button'];
      for (const s of sels) { const e = document.querySelector(s); if (e) return e; }
      return null;
    }""").as_element()
    if not el:
        log("   !! khong thay nut dang ky")
        return False
    txt = (el.inner_text() or "").strip()
    if "đã đăng ký" in txt.lower() or "subscribed" in txt.lower():
        log("   dang ky: DA DANG KY TU TRUOC")
        return True
    el.click()
    hp(2.5, 4)
    el2 = page.evaluate_handle(r"""() => document.querySelector('#subscribe-button button, ytd-subscribe-button-renderer button')""").as_element()
    after = (el2.inner_text() if el2 else "").strip()
    ok = ("đã đăng ký" in after.lower()) or ("subscribed" in after.lower())
    log("   dang ky ->", "OK (" + after + ")" if ok else "KHONG XAC NHAN DUOC (" + after + ")")
    return ok


def watch_until(page, target_sec, label):
    """Xem den khi noi dung dat target_sec (khong tinh ad). Tra ve state cuoi."""
    t_start = time.time()
    last_log = -999
    while True:
        st = ensure_playing(page)
        cur = float(st.get("t") or 0)
        dur = float(st.get("d") or 0)
        wall = time.time() - t_start
        if cur >= target_sec:
            log(f"   {label} xong: da xem {int(cur)}s noi dung (muc tieu {target_sec}s)")
            return st
        if dur and cur >= dur - 5:
            log(f"   {label} video ket thuc o {int(cur)}/{int(dur)}s")
            return st
        if wall > target_sec * 2 + 600:
            log(f"   {label} !! vuot thoi gian cho ({int(wall)}s) -> dung")
            return st
        if wall - last_log >= 90:
            last_log = wall
            log(f"   {label} dang xem {int(cur)}/{int(dur)}s | ad={st.get('adShowing')} | {str(st.get('title'))[:45]}")
        human_move(page)
        time.sleep(random.uniform(8, 15))


def get_recommended(page, limit=8):
    return page.evaluate(r"""() => {
      const box = document.querySelector('ytd-watch-next-secondary-results-renderer #contents')
               || document.querySelector('#secondary #contents');
      if (!box) return [];
      const out = [];
      for (const it of box.querySelectorAll('ytd-compact-video-renderer, ytd-rich-item-renderer')) {
        const a = it.querySelector('a#thumbnail, a#video-title');
        const t = (it.querySelector('#video-title')?.textContent || '').trim();
        if (!a || !t) continue;
        out.push({title: t, href: a.href,
                  channel: (it.querySelector('ytd-channel-name a')?.textContent || '').trim(),
                  meta: (it.querySelector('#metadata-line')?.innerText || '').replace(/\s+/g,' ')});
      }
      return out;
    }""")[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--watch-min", type=int, default=15)
    ap.add_argument("--watch-max", type=int, default=20)
    ap.add_argument("--videos", type=int, default=3)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    report = {"query": a.query, "started": time.strftime("%Y-%m-%d %H:%M:%S"), "videos": []}
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(a.ws)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.set_viewport_size({"width": 1366, "height": 850})
        except Exception:
            pass

        first = search_and_first(page, a.query)
        if not first:
            log("KHONG CO KET QUA -> dung")
            return 2

        for i in range(a.videos):
            handle_ads(page)
            st = ensure_playing(page)
            if not st.get("videoId"):
                hp(2, 3)
                st = ensure_playing(page)
            log(f"=== VIDEO {i+1}: {st.get('title') or st.get('prTitle')}")
            log(f"    kenh={st.get('channel') or st.get('author')} | dai={st.get('lengthSec')}s | id={st.get('videoId')}")
            target = random.randint(a.watch_min * 60, a.watch_max * 60)
            if st.get("lengthSec") and int(st["lengthSec"]) < target:
                target = max(int(int(st["lengthSec"]) * 0.9), 60)
                log(f"    video ngan hon {a.watch_min} phut -> xem {target}s (90% do dai)")
            watch_until(page, target, f"V{i+1}")
            # scroll sidebar nhe roi like + sub
            try:
                page.mouse.move(1150, 500)
                page.mouse.wheel(0, random.randint(150, 400))
                hp(1, 2)
            except Exception:
                pass
            liked = click_like(page)
            hp(1, 2.5)
            subbed = click_subscribe(page)
            ev = {"n": i + 1, "video_id": st.get("videoId"), "title": st.get("title") or st.get("prTitle"),
                  "channel": st.get("channel") or st.get("author"), "url": st.get("url"),
                  "length_sec": st.get("lengthSec"), "watched_target_sec": target,
                  "liked": liked, "subscribed": subbed,
                  "at": time.strftime("%H:%M:%S")}
            report["videos"].append(ev)
            log("   KET QUA:", json.dumps(ev, ensure_ascii=False))

            if i + 1 >= a.videos:
                break
            recs = []
            for _ in range(3):
                recs = get_recommended(page)
                if recs:
                    break
                try:
                    page.mouse.wheel(0, 600)
                except Exception:
                    pass
                hp(1.5, 2.5)
            if not recs:
                log("!! khong co video de xuat -> dung")
                break
            log("   de xuat dau tien:")
            for j, r in enumerate(recs[:4]):
                log(f"      {j+1}. {r['title'][:65]} | {r['channel']}")
            nxt = recs[0]
            log("   -> sang:", nxt["title"][:65])
            page.goto(nxt["href"], wait_until="domcontentloaded", timeout=90000)
            hp(3, 5)

        report["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        log("XONG")
        print("REPORT_JSON=" + json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
