# -*- coding: utf-8 -*-
r"""
Xem video YouTube nhu nguoi that qua profile GPM (CDP):
  - vao youtube.com, go tu khoa, mo video dau tien
  - xem 15-20 phut (play 1x, thinh thoang scroll/nhu mouse nhe)
  - nhan LIKE + DANG KY KENH
  - roi xem tiep video de xuat dau tien o cot phai, lap lai N video

  py -3.13 yt_watch_session.py --ws ws://localhost:PORT/... --query "..." --watch-min 15 --watch-max 20 --videos 3
"""
import sys, os, time, json, random, argparse
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def human_pause(a=0.6, b=1.8):
    time.sleep(random.uniform(a, b))


def human_move(page):
    """di chuyen chuot nhe + scroll nhe de giong nguoi."""
    try:
        vp = page.viewport_size or {"width": 1280, "height": 800}
        page.mouse.move(random.randint(100, vp["width"] - 100), random.randint(120, vp["height"] - 120), steps=random.randint(8, 20))
    except Exception:
        pass


def accept_consent(page):
    for sel in ["button:has-text('Accept all')", "button:has-text('Tất cả')", "button[aria-label*='Accept']",
                "tp-yt-paper-button:has-text('Accept all')"]:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                log("da bam consent:", sel)
                human_pause(1, 2)
                return True
        except Exception:
            pass
    return False


def search_first(page, query):
    log("goto youtube.com")
    page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
    human_pause(2.5, 4)
    accept_consent(page)
    # o tim kiem
    box = None
    for sel in ["input#search", "input[name=search_query]", "ytd-searchbox input"]:
        try:
            box = page.wait_for_selector(sel, timeout=15000)
            if box:
                break
        except Exception:
            continue
    if not box:
        raise RuntimeError("khong thay o tim kiem")
    box.click()
    human_pause(0.4, 1)
    box.fill("")
    # go tung ky tu kieu nguoi
    for ch in query:
        box.type(ch, delay=random.randint(40, 130))
    human_pause(0.5, 1.2)
    page.keyboard.press("Enter")
    log("da tim:", query)
    # doi ket qua
    page.wait_for_selector("ytd-video-renderer, ytd-rich-item-renderer", timeout=45000)
    human_pause(2, 3)


def first_result_info(page):
    js = r"""() => {
      const out = [];
      const items = [...document.querySelectorAll('ytd-video-renderer')];
      for (const it of items.slice(0, 6)) {
        const a = it.querySelector('a#video-title, a#thumbnail');
        if (!a) continue;
        const t = (it.querySelector('#video-title')?.textContent || '').trim();
        const meta = (it.querySelector('#metadata-line')?.innerText || '').replace(/\s+/g,' ').trim();
        const ch = (it.querySelector('ytd-channel-name a, #channel-name a')?.textContent || '').trim();
        out.push({title: t, href: a.href, meta, channel: ch});
      }
      return out;
    }"""
    return page.evaluate(js)


def open_first_result(page):
    log("mo ket qua dau tien")
    el = page.query_selector("ytd-video-renderer a#video-title")
    if not el:
        el = page.query_selector("ytd-video-renderer a#thumbnail")
    href = el.get_attribute("href")
    log("href:", href)
    el.click()
    human_pause(2, 4)
    page.wait_for_selector("video.html5-main-video", timeout=45000)
    return href


def video_state(page):
    js = r"""() => {
      const v = document.querySelector('video.html5-main-video');
      const t = document.querySelector('h1.ytd-watch-metadata yt-formatted-string, h1 yt-formatted-string');
      const ch = document.querySelector('#owner #channel-name a, ytd-channel-name#channel-name a');
      return {time: v ? v.currentTime : 0, dur: v ? v.duration : 0, paused: v ? v.paused : null,
              title: t ? t.textContent.trim() : '', channel: ch ? ch.textContent.trim() : '',
              url: location.href};
    }"""
    return page.evaluate(js)


def ensure_playing(page):
    st = video_state(page)
    if st["paused"]:
        log("video dang pause -> play")
        try:
            page.click("video.html5-main-video", position={"x": 400, "y": 300})
        except Exception:
            page.evaluate("() => document.querySelector('video.html5-main-video')?.play()")
        human_pause(1.5, 3)
    # tat autoplay neu dang bat? khong can
    return video_state(page)


def click_like(page):
    js = r"""() => {
      // nut like trong ytd-menu-renderer cua watch metadata
      const sels = ['ytd-watch-metadata #top-level-buttons-computed like-button-view-model button',
                    'ytd-watch-metadata like-button-view-model button',
                    'ytd-watch-metadata #segmented-like-button button',
                    'segmented-like-dislike-button-view-model like-button-view-model button'];
      for (const s of sels) {
        const el = document.querySelector(s);
        if (el) return el;
      }
      return null;
    }"""
    el = page.evaluate_handle(js).as_element()
    if not el:
        log("!! khong tim thay nut like")
        return False
    aria = el.get_attribute("aria-pressed") or el.get_attribute("aria-label") or ""
    log("like btn aria truoc:", aria)
    if "true" in (el.get_attribute("aria-pressed") or ""):
        log("da like truoc do")
        return True
    el.click()
    human_pause(1.5, 3)
    el2 = page.evaluate_handle(js).as_element()
    after = (el2.get_attribute("aria-pressed") if el2 else "") or ""
    log("like btn aria-pressed sau:", after)
    return after == "true"


def subscribe(page):
    js = r"""() => {
      const sels = ['ytd-watch-metadata #subscribe-button button',
                    '#owner #subscribe-button button',
                    'ytd-subscribe-button-renderer button'];
      for (const s of sels) { const el = document.querySelector(s); if (el) return el; }
      return null;
    }"""
    el = page.evaluate_handle(js).as_element()
    if not el:
        log("!! khong tim thay nut dang ky")
        return False
    txt = (el.inner_text() or "").strip()
    log("nut dang ky text:", txt)
    if "đã đăng ký" in txt.lower() or "subscribed" in txt.lower():
        log("da dang ky truoc do")
        return True
    el.click()
    human_pause(2, 3.5)
    el2 = page.evaluate_handle(js).as_element()
    after = (el2.inner_text() if el2 else "").strip()
    log("nut dang ky text sau:", after)
    return ("đã đăng ký" in after.lower()) or ("subscribed" in after.lower())


def watch(page, target_sec, label=""):
    """xem den khi currentTime >= target_sec (hoac video ket thuc)."""
    start = time.time()
    last_log = 0
    while True:
        st = ensure_playing(page)
        elapsed = time.time() - start
        if st["time"] >= target_sec or (st["dur"] and st["time"] >= st["dur"] - 3):
            log(f"{label} xem du {int(st['time'])}s / {int(target_sec)}s")
            return st
        if elapsed > target_sec * 3 + 300:
            log(f"{label} !! qua thoi gian cho ({int(elapsed)}s), dung")
            return st
        if elapsed - last_log > 60:
            last_log = elapsed
            log(f"{label} dang xem: {int(st['time'])}/{int(st['dur'])}s  '{st['title'][:40]}'")
        human_move(page)
        time.sleep(random.uniform(6, 14))


def scroll_sidebar(page):
    try:
        page.mouse.move(1150, 500)
        page.mouse.wheel(0, random.randint(200, 500))
        human_pause(0.8, 1.6)
    except Exception:
        pass


def recommended(page):
    js = r"""() => {
      const box = document.querySelector('ytd-watch-next-secondary-results-renderer #contents') ||
                  document.querySelector('#secondary #contents');
      if (!box) return [];
      const out = [];
      const items = [...box.querySelectorAll('ytd-compact-video-renderer, ytd-rich-item-renderer')];
      for (const it of items) {
        const a = it.querySelector('a#thumbnail, a#video-title');
        const t = (it.querySelector('#video-title')?.textContent || '').trim();
        if (!a || !t) continue;
        out.push({title: t, href: a.href,
                  channel: (it.querySelector('ytd-channel-name a')?.textContent || '').trim()});
      }
      return out;
    }"""
    return page.evaluate(js)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--watch-min", type=int, default=15)
    ap.add_argument("--watch-max", type=int, default=20)
    ap.add_argument("--videos", type=int, default=3, help="so video xem (1 = chi video dau)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    report = {"query": a.query, "videos": []}
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(a.ws)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.set_viewport_size({"width": 1366, "height": 850})
        except Exception:
            pass

        search_first(page, a.query)
        infos = first_result_info(page)
        log("ket qua dau:", json.dumps(infos[:3], ensure_ascii=False)[:600])
        open_first_result(page)
        human_pause(3, 5)

        for i in range(a.videos):
            st = ensure_playing(page)
            log(f"--- VIDEO {i+1}: {st['title']} | {st['channel']} | {int(st['dur'])}s")
            target = random.randint(a.watch_min * 60, a.watch_max * 60)
            if st["dur"] and st["dur"] < target:
                target = max(int(st["dur"] * 0.85), 60)
            watch(page, target, label=f"V{i+1}")
            scroll_sidebar(page)
            human_pause(1.5, 3)
            liked = click_like(page)
            human_pause(1, 2.5)
            subbed = subscribe(page)
            ev = {"n": i + 1, "title": st["title"], "channel": st["channel"], "url": st["url"],
                  "duration_sec": int(st["dur"] or 0), "watched_target_sec": target,
                  "liked": bool(liked), "subscribed": bool(subbed)}
            report["videos"].append(ev)
            log("KET QUA:", json.dumps(ev, ensure_ascii=False))
            if i + 1 >= a.videos:
                break
            # sang video de xuat dau tien
            for _ in range(2):
                recs = recommended(page)
                if recs:
                    break
                scroll_sidebar(page)
                human_pause(1, 2)
            recs = recommended(page)
            log("de xuat:", json.dumps(recs[:4], ensure_ascii=False)[:700])
            if not recs:
                log("!! khong co video de xuat -> dung")
                break
            nxt = recs[0]
            log("sang video de xuat:", nxt["title"])
            page.goto(nxt["href"], wait_until="domcontentloaded", timeout=90000)
            human_pause(3, 6)
            page.wait_for_selector("video.html5-main-video", timeout=45000)

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    log("XONG")
    print("REPORT_JSON=" + json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
