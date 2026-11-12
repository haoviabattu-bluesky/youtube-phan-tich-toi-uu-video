# -*- coding: utf-8 -*-
r"""
WARMUP tiep (buoc 2 + 3) cho profile miguelcarolineo0071023@gmail.com.
Buoc 1 da xong that (xem 1069s + like + comment da dang, verify @AIHistoryJP).

BUOC 2: tu panel de xuat ben phai -> video 【440年の謎】明智光秀は本当に死んだのか？
        (panel cuon duoc; neu khong con -> tim bang search)
        -> xem 15-20 phut -> LIKE -> BINH LUAN 「素晴らしい！本当に最高です！」
BUOC 3: tu panel goi y loc video lich su / tu khoa lane X -> click -> xem 15-20 phut -> like
"""
import json, os, random, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "wm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "warm_miguel.py"))
wm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wm)

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "warm_miguel_log.txt")
REPORT = os.path.join(HERE, "warm2_report.json")

MY_HANDLE = "AIHistoryJP"        # handle that cua kenh 歴史の謎をAIで解く
COMMENT_JA = "素晴らしい！本当に最高です！"

TARGET2_KW = "【440年の謎】明智光秀は本当に死んだのか？天海説まで5つの説をAIに1582年の記録で採点させたら、意外な結果に"
TARGET2_HINT = "明智光秀は本当に死んだのか"
WATCH = (15 * 60, 20 * 60)
MAX_EXTRA = 4
BUDGET_S = 150 * 60

_t0 = time.time()
log = wm.log


# --------------------------------------------------- panel: cuon de load them goi y
JS_SCROLL_SIDE = """(px) => {
  const s = document.querySelector('#secondary #contents, #secondary, ytd-watch-next-secondary-results-renderer #contents');
  if (!s) return null;
  const before = s.scrollHeight;
  const cont = s.closest('#secondary') || s;
  cont.scrollTop = cont.scrollTop + px;
  return {before: before, after: s.scrollHeight, top: cont.scrollTop};
}"""


def recs_deep(page, want_hint, rounds=8, limit=60):
    """doc panel nhieu lan + cuon panel de load them"""
    best = None
    for i in range(rounds):
        rr = wm.recs(page, limit)
        for x in rr:
            if want_hint in (x.get("title") or ""):
                return x
        if rr:
            best = rr
        page.evaluate(JS_SCROLL_SIDE, random.randint(700, 1100))
        time.sleep(random.uniform(2.2, 3.6))
    return None


# --------------------------------------------------- verify comment theo HANDLE
def verify_my_comment(page, handle, text_head=12):
    try:
        return page.evaluate("""(h) => {
          const els = document.querySelectorAll('ytd-comment-thread-renderer');
          const rows = [];
          for (const el of els) {
            const au = el.querySelector('#author-text');
            const tx = el.querySelector('#content-text');
            if (!au || !tx) continue;
            rows.push({a: (au.textContent||'').trim(), t: (tx.textContent||'').trim()});
          }
          const mine = rows.filter(r => r.a.replace(/^@/, '').toLowerCase() === h.toLowerCase());
          return {n: rows.length, mine: mine.slice(0, 3),
                  hit: mine.some(r => r.t.length > 0)};
        }""", handle)
    except Exception as e:
        return {"err": str(e)[:120]}


def comment_video(page, text, handle=MY_HANDLE):
    """mo o binh luan, go, gui, verify theo handle"""
    for _ in range(7):
        try:
            page.mouse.wheel(0, random.randint(500, 800))
        except Exception:
            pass
        time.sleep(random.uniform(0.9, 1.6))
    time.sleep(random.uniform(2, 4))

    r = page.evaluate(wm.JS_OPEN_BOX)
    if not r:
        log("  ! khong thay o binh luan")
        return {"ok": False, "err": "no_simplebox"}
    page.mouse.move(r["x"] + random.uniform(-4, 4), r["y"] + random.uniform(-3, 3), steps=12)
    time.sleep(random.uniform(0.3, 0.7))
    page.mouse.click(r["x"], r["y"])
    time.sleep(random.uniform(2.0, 3.5))

    ce = None
    for _ in range(40):
        ce = page.evaluate(wm.JS_CE_RECT)
        if ce:
            break
        time.sleep(1)
    if not ce:
        log("  ! o nhap khong hien")
        return {"ok": False, "err": "no_ce"}
    page.mouse.click(ce["x"], ce["y"])
    time.sleep(random.uniform(0.8, 1.6))
    wm.go_tu_nhien(page, text)
    time.sleep(random.uniform(1.2, 2.2))
    typed = page.evaluate(wm.JS_CE_TEXT)
    log("  go xong: %r" % typed)
    if not typed.strip():
        return {"ok": False, "err": "empty_after_type"}

    sub = None
    for _ in range(12):
        sub = page.evaluate(wm.JS_SUBMIT_RECT)
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
    log("  da bam gui")
    time.sleep(random.uniform(6, 9))

    # reload de chac chan comment da len server
    try:
        page.reload(wait_until="domcontentloaded", timeout=90000)
        time.sleep(9)
        for _ in range(8):
            page.mouse.wheel(0, 800); time.sleep(1.0)
        time.sleep(4)
        # sort newest
        page.evaluate("""() => {
          const b = document.querySelector('yt-sort-filter-sub-menu-renderer tp-yt-paper-button');
          if (b) b.click();
        }""")
        time.sleep(2.5)
        page.evaluate("""() => {
          const items = Array.from(document.querySelectorAll('tp-yt-paper-item, ytd-menu-service-item-renderer'));
          for (const it of items) { if (/Newest/i.test(it.innerText||'')) { it.click(); return; } }
        }""")
        time.sleep(5)
    except Exception as e:
        log("  ~ reload verify loi: %s" % e)

    v = verify_my_comment(page, handle)
    ok = bool(v.get("hit"))
    log("  VERIFY (%s): %s" % (handle, json.dumps(v, ensure_ascii=False)[:220]))
    return {"ok": ok, "typed": typed, "verify": v}


# --------------------------------------------------- click goi y trong panel
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


def open_from_panel(page, vid):
    ok = wm._click_js(page, JS_CLICK_SIDE, vid)
    if ok:
        time.sleep(random.uniform(5, 8))
        if vid in page.url:
            return True
    return False


def open_direct(page, vid):
    page.goto("https://www.youtube.com/watch?v=" + vid, wait_until="domcontentloaded", timeout=90000)
    time.sleep(random.uniform(5, 8))
    return True


# --------------------------------------------------- main
def main():
    log("")
    log("=== WARMUP TIEP (buoc 2+3) — %s ===" % time.strftime("%H:%M:%S"))
    rep = {"start": time.strftime("%Y-%m-%d %H:%M:%S"), "steps": []}
    watched = set()

    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(wm.WS)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.set_viewport_size({"width": 1600, "height": 900})
        except Exception:
            pass
        try:
            # ---------- BUOC 2
            log("[2] mo lai video 1 de lay panel de xuat, tim: %s" % TARGET2_HINT)
            open_direct(page, "CR9KU_5djOg")
            wm.dismiss_popups(page)
            time.sleep(random.uniform(2, 4))
            r2 = recs_deep(page, TARGET2_HINT, rounds=9)
            if r2:
                log("  THAY trong panel: %s | %s | %s" % (r2["id"], r2.get("dur"), r2["title"][:70]))
                if not open_from_panel(page, r2["id"]):
                    log("  ~ click panel khong an -> goto truc tiep")
                    open_direct(page, r2["id"])
            else:
                log("  ! panel khong con video do -> TIM KIEM tu khoa")
                wm.search(page, TARGET2_KW)
                res = wm.search_results(page, 8)
                log("  %d ket qua" % len(res))
                pick = None
                for x in res:
                    if TARGET2_HINT in (x.get("title") or ""):
                        pick = x
                        break
                if not pick and res:
                    pick = res[0]
                if not pick:
                    raise RuntimeError("khong tim duoc video 明智光秀")
                r2 = pick
                log("  chon: %s | %s" % (pick["id"], pick["title"][:70]))
                open_direct(page, pick["id"])

            wm.dismiss_popups(page)
            watched.add(r2["id"])
            w2, vlen2 = wm.watch(page, random.randint(*WATCH), "buoc2")
            like2 = wm.like_video(page)
            wm.human(page, 1.2, 2.6)
            cm2 = comment_video(page, COMMENT_JA)
            rep["steps"].append({"step": 2, "video": r2, "watched_s": w2, "video_len": vlen2,
                                 "like": like2, "comment": cm2})
            log("  => buoc 2: xem %ds | like=%s | comment=%s"
                % (w2, (like2 or {}).get("ok"), (cm2 or {}).get("ok")))
            wm.human(page, 3, 6)

            # ---------- BUOC 3
            log("[3] loc goi y lane X -> xem tiep (toi da %d video)" % MAX_EXTRA)
            n = 0
            while n < MAX_EXTRA and time.time() - _t0 < BUDGET_S - 16 * 60:
                rr = wm.recs(page, 30)
                if len(rr) < 6:
                    page.evaluate(JS_SCROLL_SIDE, 900)
                    time.sleep(3)
                    rr = wm.recs(page, 40)
                scored = []
                for x in rr:
                    s = wm.score_candidate(x, watched)
                    if s > 0:
                        scored.append((s, x))
                scored.sort(key=lambda z: -z[0])
                if not scored:
                    log("  ! khong con goi y khop -> dung")
                    break
                log("  ung vien: " + " | ".join("%s(%d)" % (t["title"][:34], s) for s, t in scored[:5]))
                cand = scored[0][1]
                log("  chon: %s | %s | %s | %s" % (cand["id"], cand.get("dur"),
                                                   cand["title"][:66], cand.get("ch")))
                if not open_from_panel(page, cand["id"]):
                    open_direct(page, cand["id"])
                wm.dismiss_popups(page)
                watched.add(cand["id"])
                w3, vlen3 = wm.watch(page, random.randint(*WATCH), "buoc3-%d" % (n + 1))
                like3 = wm.like_video(page)
                rep["steps"].append({"step": 3, "idx": n + 1, "video": cand, "watched_s": w3,
                                     "video_len": vlen3, "like": like3})
                log("  => buoc 3.%d: xem %ds | like=%s" % (n + 1, w3, (like3 or {}).get("ok")))
                n += 1
                wm.human(page, 3, 7)

            rep["status"] = "DONE"
        except Exception as e:
            log("!! LOI: %s" % e)
            log(traceback.format_exc()[-1200:])
            rep["status"] = "ERROR"
            rep["error"] = str(e)[:400]
        finally:
            rep["end"] = time.strftime("%Y-%m-%d %H:%M:%S")
            rep["elapsed_min"] = round((time.time() - _t0) / 60, 1)
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(rep, f, ensure_ascii=False, indent=1)
            log("=== KET THUC buoc2+3: %s | %.1f phut ===" % (rep.get("status"), rep["elapsed_min"]))
            try:
                br.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
