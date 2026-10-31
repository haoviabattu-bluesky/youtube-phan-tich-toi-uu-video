# -*- coding: utf-8 -*-
"""Thao tac tren youtube.com nhu nguoi: go tim, doc ket qua / cot de xuat, xem, like + dang ky.

Nang cap tu tools/channel_warmup_youtube_search.py (ban 1 lane). Them: doc cot de xuat ben phai
(ca ytd-compact-video-renderer cu lan yt-lockup-view-model moi), tat autoplay (khong de YouTube
tu nhay sang video CHUA soi thumbnail), tat tieng + ha 360p cho nhe may khi 3-4 profile cung chay.
"""
import re, time, random, urllib.parse
from nw_common import sleep_ok

JP = re.compile(r"[぀-ヿ]")   # bat buoc co hiragana/katakana (chi kanji thi lot video tieng Trung)
LIVE = re.compile(r"ライブ配信中|視聴中|プレミア公開|LIVE|Premieres", re.I)

EXTRACT = r"""(scope) => {
  // Trang xem khi dang nhap co 3 phan tu #secondary, cai DAU rong (do that 2026-10-22) -> lay cai nhieu video nhat
  const SEL = 'ytd-video-renderer, ytd-compact-video-renderer, yt-lockup-view-model';
  const roots = scope ? [...document.querySelectorAll(scope)] : [document];
  if (!roots.length) return [];
  const root = roots.reduce((a, b) => b.querySelectorAll(SEL).length > a.querySelectorAll(SEL).length ? b : a);
  const nodes = [...root.querySelectorAll(SEL)];
  const out = [], seen = new Set();
  for (const n of nodes) {
    if (n.closest('ytd-reel-shelf-renderer, ytm-shorts-lockup-view-model, ytd-ad-slot-renderer')) continue;
    const a = n.querySelector('a[href*="/watch?v="]'); if (!a) continue;
    const m = a.href.match(/[?&]v=([\w-]{11})/); if (!m || seen.has(m[1])) continue; seen.add(m[1]);
    const t = n.querySelector('#video-title, h3[title], h3 a, h3');
    const ch = n.querySelector('ytd-channel-name a, ytd-channel-name yt-formatted-string, [class*="MetadataText"], [class*="metadata-text"]');
    const len = n.querySelector('ytd-thumbnail-overlay-time-status-renderer, [class*="badge-shape"] [class*="text"], .badge-shape-wiz__text');
    out.push({id: m[1], title: ((t && (t.getAttribute('title') || t.textContent)) || '').trim(),
              channel: ch ? ch.textContent.trim() : '', length: len ? len.textContent.trim() : '',
              text: (n.innerText || '').slice(0, 400)});
  }
  return out;
}"""


NUM_LINE = re.compile(r"^([\d.,]+)\s*(万|億|千|[KMB])?\s*(?:回視聴|回再生|views?)?$", re.I)
DUR_LINE = re.compile(r"^\d{1,2}(?::\d{2}){1,2}$")
MULT = {"万": 1e4, "億": 1e8, "千": 1e3, "K": 1e3, "M": 1e6, "B": 1e9}


def _lines(*texts):
    return [x.strip() for t in texts for x in (t or "").splitlines() if x.strip()]


def parse_views(text):
    """Giao dien 2026 chi in '1万' / '2.9万' tren 1 dong rieng (khong con chu 回視聴); ban cu co '1.2万回視聴'."""
    for ln in _lines(text):
        m = NUM_LINE.match(ln)
        if m and not DUR_LINE.match(ln):
            return int(float(m.group(1).replace(",", "")) * MULT.get((m.group(2) or "").upper() or m.group(2) or "", 1))
    m = re.search(r"([\d.,]+)\s*(万|億|千)?\s*回(?:視聴|再生)", text)
    if m:
        return int(float(m.group(1).replace(",", "")) * MULT.get(m.group(2) or "", 1))
    return 0


def find_len(*texts):
    """Thoi luong = dong DAU TIEN dang m:ss / h:mm:ss (YouTube in lap 2 lan: '20:33' xuong dong '20:33')."""
    for ln in _lines(*texts):
        if DUR_LINE.match(ln):
            sec = 0
            for x in ln.split(":"):
                sec = sec * 60 + int(x)
            return ln, sec
    return "", 0


def read_videos(page, scope=None, top=10):
    items = page.evaluate(EXTRACT, scope)[:top]
    for x in items:
        x["views"] = parse_views(x["text"])
        x["length"], x["len_sec"] = find_len(x["length"], x["text"])
        x["live"] = bool(LIVE.search(x["text"]))
    return items


def prefilter(items, seen, own_ids, own_names, min_len):
    own = {n.strip() for n in own_names if n}
    return [x for x in items if x["id"] not in seen and x["id"] not in own_ids and not x["live"]
            and JP.search(x["title"]) and x["channel"].strip() not in own
            and (x["len_sec"] == 0 or x["len_sec"] >= min_len)]


def search(page, kw):
    # wait_until="commit" + cho phan tu can dung: "domcontentloaded" cua YouTube co luc giu toi 60s
    page.goto("https://www.youtube.com/?hl=ja&gl=JP", wait_until="commit", timeout=45000)
    page.wait_for_selector("input[name='search_query']", timeout=45000)
    page.wait_for_timeout(random.randint(2500, 4500))
    box = page.locator("input[name='search_query']").first
    try:
        box.click(timeout=15000)
        box.fill("")
        for ch in kw:                       # go cham nhu nguoi
            page.keyboard.type(ch, delay=random.randint(90, 220))
        page.wait_for_timeout(random.randint(600, 1500))
        page.keyboard.press("Enter")
    except Exception:
        page.goto("https://www.youtube.com/results?search_query=" + urllib.parse.quote(kw) + "&hl=ja&gl=JP",
                  wait_until="domcontentloaded")
    # BAY (do that 2026-10-22): trang chu CUNG co the video -> cho selector chung la doc nham feed trang chu
    page.wait_for_url("**/results?**", timeout=30000)
    page.wait_for_selector("ytd-search ytd-video-renderer a[href*='/watch?v=']", timeout=30000)
    page.wait_for_timeout(random.randint(2000, 4000))
    page.mouse.wheel(0, random.randint(300, 900))
    page.wait_for_timeout(random.randint(1500, 3000))


def wait_suggestions(page):
    try:
        page.wait_for_selector("#secondary ytd-compact-video-renderer, #secondary yt-lockup-view-model", timeout=20000)
        page.mouse.wheel(0, random.randint(300, 700))
        page.wait_for_timeout(random.randint(2000, 4000))
        page.mouse.wheel(0, -1500)
    except Exception:
        pass


def history_paused(page):
    page.goto("https://www.youtube.com/feed/history", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    t = page.evaluate("() => document.body.innerText || ''")
    return bool(re.search(r"履歴.{0,20}(一時停止|オフ)|history is (paused|off)", t, re.I))


def _player_setup(page):
    """Tat tieng, ha 360p, tat autoplay (chi bam khi dang BAT)."""
    page.evaluate("""() => { const v = document.querySelector('video'); if (v) { v.muted = true; if (v.paused) v.play(); }
        const p = document.getElementById('movie_player');
        try { p && p.setPlaybackQualityRange && p.setPlaybackQualityRange('medium', 'medium'); } catch (e) {}
        const a = document.querySelector('.ytp-autonav-toggle-button[aria-checked="true"]'); if (a) a.click(); }""")


def like_and_sub(page, like, sub):
    """Chi bam khi nut dang TAT (bam lai la go like / huy dang ky)."""
    page.bring_to_front()
    return page.evaluate("""([like, sub]) => {
        const r = {like: '-', sub: '-'};
        const lk = document.querySelector('like-button-view-model button, #segmented-like-button button');
        if (like && lk) { if (lk.getAttribute('aria-pressed') === 'true') r.like = 'da co'; else { lk.click(); r.like = 'OK'; } }
        const sb = document.querySelector('#owner ytd-subscribe-button-renderer button, #subscribe-button button');
        if (sub && sb) { const t = sb.innerText + ' ' + (sb.getAttribute('aria-label') || '');
            if (/登録済み|登録解除|Subscribed|Unsubscribe/.test(t)) r.sub = 'da co'; else { sb.click(); r.sub = 'OK'; } }
        return r; }""", [like, sub])


def watch(page, v, minutes, deadline, like_prob, sub_prob):
    """Bam vao video (dang hien tren trang) roi xem `minutes` phut. Tra (giay da xem, ghi chu react)."""
    vid = v["id"]
    link = page.locator(f"a[href*='/watch?v={vid}']").first
    try:
        link.scroll_into_view_if_needed(timeout=5000)
        page.wait_for_timeout(random.randint(800, 2000))
        link.click(timeout=10000)
    except Exception:
        page.goto(f"https://www.youtube.com/watch?v={vid}", wait_until="commit", timeout=45000)
    page.wait_for_selector("video", timeout=30000)
    page.wait_for_timeout(4000)
    _player_setup(page)
    t0, react = time.time(), "-"
    react_at = random.uniform(120, 240)
    while time.time() - t0 < minutes * 60:
        if not sleep_ok(random.randint(15, 30), deadline):
            break
        page.evaluate("""() => { const b = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern'); if (b) b.click(); }""")
        if f"v={vid}" not in page.url:      # YouTube tu nhay video khac -> dung, khong xem video chua soi
            break
        if react_at and time.time() - t0 >= react_at:
            react_at = None
            try:
                r = like_and_sub(page, random.random() < like_prob, random.random() < sub_prob)
                react = f"like={r['like']} sub={r['sub']}"
            except Exception as e:
                react = f"like/sub LOI {str(e)[:50]}"
        st = page.evaluate("""() => { const v = document.querySelector('video'); if (!v) return {};
            v.muted = true; if (v.paused && !v.ended) v.play(); return {ended: v.ended}; }""")
        if st.get("ended"):
            break
        if random.random() < 0.08:          # thinh thoang cuon xuong doc binh luan roi len lai
            page.mouse.wheel(0, random.randint(400, 1200))
            page.wait_for_timeout(random.randint(3000, 8000))
            page.mouse.wheel(0, -2000)
    page.evaluate("() => { const v = document.querySelector('video'); if (v) v.pause(); }")
    return time.time() - t0, react
