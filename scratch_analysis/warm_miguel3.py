# -*- coding: utf-8 -*-
r"""
BUOC 3 (chay rieng): tu panel goi y cua video 明智光秀 -> loc video lich su lane X
-> click -> xem 15-20 phut -> LIKE. Lap lai MAX_EXTRA video.
Neu panel khong co ung vien dat -> TIM KIEM bang tu khoa lane X.
"""
import json, os, random, sys, time, traceback, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("wm", os.path.join(HERE, "warm_miguel.py"))
wm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wm)

LOG = os.path.join(HERE, "warm_miguel_log.txt")
REPORT = os.path.join(HERE, "warm3_report.json")
log = wm.log

SEED_VIDEO = "t_7hE3EJhvM"        # 明智光秀 (buoc 2 da xem xong)
ALREADY = {"CR9KU_5djOg", "t_7hE3EJhvM", "thETMkoP0lk"}
WATCH = (15 * 60, 20 * 60)
MAX_EXTRA = 3
BUDGET_S = 110 * 60

# tu khoa tim kiem du phong (khi panel het ung vien)
SEARCH_KW = [
    "本能寺の変 一次史料 AI 推理",
    "日本史 歴史ミステリー AI 検証",
    "戦国時代 生存説 歴史考察",
]

JS_SCROLL_SIDE = """(px) => {
  const cont = document.querySelector('#secondary');
  if (!cont) return null;
  cont.scrollTop = cont.scrollTop + px;
  return {top: cont.scrollTop};
}"""

JS_CLICK_SIDE = """(vid) => {
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
}"""

_t0 = time.time()


def open_from_panel(page, vid, tries=3):
    """click THAT vao the goi y trong panel; cho SPA dieu huong toi 25s truoc khi fallback"""
    for t in range(tries):
        if not wm._click_js(page, JS_CLICK_SIDE, vid):
            return False
        for _ in range(25):
            time.sleep(1)
            if vid in page.url:
                time.sleep(random.uniform(2, 4))
                return True
        log("  ~ click lan %d chua dieu huong (url=%s)" % (t + 1, page.url[:70]))
        time.sleep(random.uniform(1.5, 3))
    return False


def open_direct(page, vid):
    page.goto("https://www.youtube.com/watch?v=" + vid, wait_until="domcontentloaded", timeout=90000)
    time.sleep(random.uniform(5, 8))
    return True


def collect_recs(page, rounds=6):
    """doc panel + cuon panel de load them, gop lai"""
    seen, out = set(), []
    for i in range(rounds):
        rr = wm.recs(page, 40)
        for x in rr:
            if x["id"] not in seen:
                seen.add(x["id"])
                out.append(x)
        page.evaluate(JS_SCROLL_SIDE, random.randint(800, 1200))
        time.sleep(random.uniform(2.0, 3.4))
    return out


def main():
    log("")
    log("=== BUOC 3: LOC GOI Y LANE X -> xem tiep — %s ===" % time.strftime("%H:%M:%S"))
    rep = {"start": time.strftime("%Y-%m-%d %H:%M:%S"), "steps": []}
    done = set(ALREADY)

    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(wm.WS)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.set_viewport_size({"width": 1600, "height": 900})
        except Exception:
            pass
        try:
            log("mo lai video 明智光秀 de lay panel goi y")
            open_direct(page, SEED_VIDEO)
            wm.dismiss_popups(page)
            time.sleep(random.uniform(2, 4))

            n = 0
            kw_i = 0
            while n < MAX_EXTRA and time.time() - _t0 < BUDGET_S - 16 * 60:
                cand = None
                rr = collect_recs(page, rounds=5)
                scored = []
                for x in rr:
                    s = wm.score_candidate(x, done)
                    if s > 0:
                        scored.append((s, x))
                scored.sort(key=lambda z: -z[0])
                if scored:
                    log("  ung vien panel (%d doc duoc): " % len(rr)
                        + " | ".join("%s(%d)" % (t["title"][:32], s) for s, t in scored[:5]))
                    cand = scored[0][1]
                    if not open_from_panel(page, cand["id"]):
                        log("  ~ click panel khong an -> goto truc tiep")
                        open_direct(page, cand["id"])
                else:
                    if kw_i >= len(SEARCH_KW):
                        log("  ! het ung vien ca panel lan tu khoa -> dung")
                        break
                    kw = SEARCH_KW[kw_i]; kw_i += 1
                    log("  panel khong co ung vien dat (%d video) -> TIM KIEM: %s" % (len(rr), kw))
                    wm.search(page, kw)
                    res = wm.search_results(page, 10)
                    picks = [(wm.score_candidate(x, done), x) for x in res]
                    picks = sorted([z for z in picks if z[0] > 0], key=lambda z: -z[0])
                    if not picks:
                        log("  ! tim kiem khong co ket qua dat -> thu tu khoa khac")
                        continue
                    log("  ung vien search: " + " | ".join("%s(%d)" % (t["title"][:32], s) for s, t in picks[:5]))
                    cand = picks[0][1]
                    open_direct(page, cand["id"])

                wm.dismiss_popups(page)
                done.add(cand["id"])
                log("  chon: %s | %s | %s | %s" % (cand["id"], cand.get("dur"),
                                                   cand["title"][:66], cand.get("ch")))
                w, vlen = wm.watch(page, random.randint(*WATCH), "buoc3-%d" % (n + 1))
                lk = wm.like_video(page)
                rep["steps"].append({"step": 3, "idx": n + 1, "video": cand, "watched_s": w,
                                     "video_len": vlen, "like": lk})
                log("  => buoc 3.%d: xem %ds | like=%s" % (n + 1, w, (lk or {}).get("ok")))
                n += 1
                wm.human(page, 3, 7)

            rep["status"] = "DONE"
        except Exception as e:
            log("!! LOI: %s" % e)
            log(traceback.format_exc()[-1000:])
            rep["status"] = "ERROR"
            rep["error"] = str(e)[:300]
        finally:
            rep["end"] = time.strftime("%Y-%m-%d %H:%M:%S")
            rep["elapsed_min"] = round((time.time() - _t0) / 60, 1)
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(rep, f, ensure_ascii=False, indent=1)
            log("=== KET THUC buoc 3: %s | %.1f phut | %d video ===" %
                (rep.get("status"), rep["elapsed_min"], len(rep["steps"])))
            try:
                br.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
