# -*- coding: utf-8 -*-
r"""
DOC SO STUDIO BANG DUONG NGUOI THAT — 100% CLICK, KHONG `goto` URL VIDEO.

Anh chot 2026-10-20: cam duong tat `goto https://studio.youtube.com/video/<id>/analytics/...`.
Moi thu phai lam nhu nguoi ngoi truoc man hinh:

    mo studio.youtube.com  ->  bam "Content" (menu trai)
      ->  cuon danh sach, TIM dong video can xem  ->  CLICK vao ten video
      ->  cho trang video hien ra  ->  bam tab "Analytics"
      ->  bam tab "Reach"  ->  doc so
      ->  (doi khoang thoi gian) bam nhan ngay -> bam "Custom" -> go ngay -> "Apply"

Vi sao phai nhu vay: job cu goto thang URL tung video, moi trang ~4s, Studio tra
"Oops, something went wrong" hang loat (lane A: 5 video lien tiep, 457s/video, 0 so).
Nguoi that mo 1 video mat 20-40s va Studio khong chan.

Dung:
    import studio_human as sh
    sh.open_studio(page, log)                       # ve trang chu Studio
    sh.open_content(page, log)                      # bam Content -> danh sach video
    sh.click_video(page, vid, log)                  # cuon + click dung video
    sh.click_tab(page, "Analytics", log)
    sh.click_tab(page, "Reach", log)
    sh.set_day_range(page, start_d, end_d, log)     # menu ngay -> Custom -> Apply
"""
import time, random, datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import human_pace as hp

DEEP = """() => {
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']);
  const out = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      if (skip.has(el.tagName)) continue;
      if (el.shadowRoot) walk(el.shadowRoot);
      if (el.children.length === 0) { const t=(el.textContent||'').trim(); if (t && t.length<200) out.push(t); } } };
  walk(document); return out;
}"""

# Tim phan tu la co chuoi DUNG BANG label, tra toa do de bam bang chuot that
FIND = """(label) => {
  let hit = null;
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      if (el.shadowRoot) walk(el.shadowRoot);
      if (!hit && el.children.length === 0 && (el.textContent||'').trim() === label) hit = el; } };
  walk(document);
  if (!hit) return null;
  const r = hit.getBoundingClientRect();
  if (r.width < 2 || r.height < 2) return null;
  return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
}"""

# Danh sach dong video dang hien (toa do ten video) de click nhu nguoi
ROWS = """() => {
  const out = [];
  for (const e of document.querySelectorAll('ytcp-video-row')) {
    const a = e.querySelector('a#video-title');
    if (!a) continue;
    const r = a.getBoundingClientRect();
    out.push({id: (a.href.split('/video/')[1]||'').split('/')[0],
              title: a.innerText.trim(),
              x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
              h: Math.round(r.height)});
  }
  return out;
}"""

INPUTS = """() => {
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']); const out = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      if (skip.has(el.tagName)) continue;
      if (el.shadowRoot) walk(el.shadowRoot);
      if (el.tagName === 'INPUT') {
        const r = el.getBoundingClientRect();
        const v = (el.value || '');
        // o ngay cua Studio: "10/18/26" hoac "Oct 18, 2026"
        if (r.width > 2 && r.height > 2 && (/^\\d{1,2}\\/\\d{1,2}\\/\\d{2,4}$/.test(v) || /^[A-Z][a-z]{2} \\d{1,2}, \\d{4}$/.test(v)))
          out.push({val: v, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
      } } };
  walk(document); return out;
}"""


def _click_xy(page, x, y, log=None, why=""):
    """Di chuyen chuot tu tu roi bam — khong bay thang toa do."""
    page.mouse.move(x, y, steps=random.randint(9, 20))
    time.sleep(random.uniform(0.15, 0.45))
    page.mouse.click(x, y)
    if log and why:
        log(f"    · bam {why} @({x},{y})")


def click_label(page, label, log=None, tries=3, why=""):
    """Bam phan tu co chuoi = label (tab/menu/nut). Tra True neu bam duoc."""
    for i in range(tries):
        r = page.evaluate(FIND, label)
        if r:
            _click_xy(page, r["x"], r["y"], log, why or label)
            return True
        time.sleep(1.5 * (i + 1))
    if log:
        log(f"    · KHONG thay '{label}' de bam")
    return False


def maximize(page, log=None):
    """Phong to cua so (nhu nguoi bam nut maximize).

    Dinh that 2026-10-22: cua so profile GPM/AdsPower/9222 chi rong ~970px -> Studio thu menu trai
    thanh icon, chu 'Content' van co trong DOM nhung kich thuoc 0 -> tool tuong 'chua render',
    reload 3 lan roi bo ca lane (L, N, J, O, A, M deu chet vi vay).
    """
    try:
        cdp = page.context.new_cdp_session(page)
        w = cdp.send("Browser.getWindowForTarget")
        cdp.send("Browser.setWindowBounds", {"windowId": w["windowId"], "bounds": {"windowState": "maximized"}})
        time.sleep(1.5)
        if log:
            log(f"    · phong to cua so: {page.evaluate('() => innerWidth')}px")
    except Exception as e:
        if log:
            log(f"    · khong phong to duoc cua so: {str(e)[:80]}")


def wait_text(page, needles, tries=20, gap=2.0):
    parts = []
    for _ in range(tries):
        time.sleep(gap * random.uniform(0.85, 1.2))
        parts = page.evaluate(DEEP)
        j = " | ".join(parts)
        if any(n in j for n in needles):
            return parts
    return parts


def wait_url(page, needle, tries=20, gap=2.0):
    for _ in range(tries):
        if needle in (page.url or ""):
            return True
        time.sleep(gap * random.uniform(0.85, 1.2))
    return needle in (page.url or "")


# ---------------- cac buoc nguoi that ----------------
def open_studio(page, log=None):
    """Ve trang chu Studio (KHONG phai URL video). Lan goto dau hay dung o root -> goto lai."""
    for _ in range(2):
        hp.before_nav()
        page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=90000)
        if wait_url(page, "/channel/", tries=15):
            hp.after_read()
            if log:
                log(f"    · Studio: {page.url.split('/channel/')[-1][:24]}")
            return True
    return False


def open_content(page, log=None):
    """Bam 'Content' o menu trai -> danh sach video cua kenh.

    Neu dang dung trong trang analytics cua 1 video (sau khi doc xong video truoc), menu trai
    KHONG con chu 'Content' — luc do phai bam 'Channel content' (duong dan quay ve danh sach).
    Dinh that 2026-10-20: bo qua buoc nay thi moi video thu 2 tro di deu that bai.
    """
    hp.before_click()
    if not click_label(page, "Content", log, why="Content"):
        if not click_label(page, "Channel content", log, why="Channel content"):
            # chua o trong Studio (trang khac / trang chua tai xong) -> ve trang chu Studio
            # roi bam lai. KHONG goto URL video.
            if log:
                log(f"    · khong thay menu Content (dang o {page.url[:70]}) -> ve trang chu Studio")
            if not open_studio(page, log):
                return False
            if not click_label(page, "Content", log, why="Content (lan 2)"):
                if not click_label(page, "Channel content", log, why="Channel content (lan 2)"):
                    return False
    ok = wait_url(page, "/videos/upload", tries=6)
    if not ok:
        # Giao dien Content MOI (Studio tung dan theo kenh, gap 2026-10-22 o lane F/G): bam Content
        # ra trang tong quan dang luoi ("Discover your new content page"), URL van /channel/<id>,
        # KHONG co ytcp-video-row -> phai bam chip "Videos" moi vao danh sach /videos/upload cu.
        hp.before_click()
        if click_label(page, "Videos", log, why="chip Videos (giao dien Content moi)"):
            ok = wait_url(page, "/videos/upload", tries=15)
    if ok:
        hp.after_read()
    return ok


def _find_row(page, vid, max_scroll=12):
    """Tim dong video trong danh sach; cuon xuong nhu nguoi neu chua thay."""
    for i in range(max_scroll + 1):
        rows = page.evaluate(ROWS)
        hit = next((r for r in rows if r["id"] == vid), None)
        if hit:
            return hit
        if i == max_scroll:
            break
        page.mouse.move(random.randint(500, 900), random.randint(300, 600), steps=random.randint(6, 12))
        page.mouse.wheel(0, random.randint(500, 900))
        time.sleep(random.uniform(1.2, 2.6))
    return None


def click_video(page, vid, log=None):
    """CLICK vao dung dong video trong danh sach (khong goto URL)."""
    row = _find_row(page, vid)
    if not row:
        if log:
            log(f"    · khong thay video {vid} trong danh sach (da cuon 12 lan)")
        return False
    vh = page.evaluate("() => innerHeight") or 900
    for _ in range(3):                 # dong nam ngoai vung nhin -> cuon cho hien ra
        if 100 < row["y"] < vh - 60:
            break
        # Dinh 2026-10-22 (lane L): wheel khi chuot KHONG nam tren danh sach thi trang khong cuon
        # -> bam vao y=2079 (ngoai man hinh), truot ca lane. Dua chuot vao giua danh sach roi moi cuon.
        page.mouse.move(random.randint(600, 900), random.randint(350, 550), steps=random.randint(6, 12))
        page.mouse.wheel(0, row["y"] - vh // 2)
        time.sleep(random.uniform(1.0, 2.0))
        row = _find_row(page, vid, max_scroll=0) or row
    if not (100 < row["y"] < vh - 60):  # van chua hien -> cuon dung dong do vao giua man hinh
        page.evaluate("""(vid) => { for (const e of document.querySelectorAll('ytcp-video-row')) {
            const a = e.querySelector('a#video-title');
            if (a && a.href.includes('/video/' + vid)) { a.scrollIntoView({block: 'center'}); return; } } }""", vid)
        time.sleep(random.uniform(1.0, 2.0))
        row = _find_row(page, vid, max_scroll=0) or row
    if not (0 < row["y"] < vh):
        if log:
            log(f"    · video {vid} van nam ngoai man hinh (y={row['y']}) -> khong bam")
        return False
    hp.before_click()
    _click_xy(page, row["x"], row["y"], log, f"video {vid}")
    ok = wait_url(page, f"/video/{vid}", tries=20)
    if ok:
        wait_text(page, ["Analytics"], tries=12)
        hp.after_read()
        if log:
            log(f"    · mo duoc video: {row['title'][:44]}")
    return ok


def _has_menu(page):
    """Studio da render xong chua: phai thay menu trai 'Content' hoac 'Channel content'."""
    try:
        return bool(page.evaluate(FIND, "Content") or page.evaluate(FIND, "Channel content"))
    except Exception:
        return False      # context dang bi destroy (dang dieu huong) -> coi nhu chua san sang


def verify_channel(page, ch, log=None, vid=""):
    """Kiem tra dang dung DUNG kenh `ch` VA Studio da render xong.

    Nhan them `vid`: khi dang o /video/<vid> thi KHONG can /channel/ trong URL — chinh viec
    doi ve /channel/ giua chung lam mat trang dang doc va ton 12s/video (dinh that 2026-10-20).
    """
    url = page.url or ""
    if vid and f"/video/{vid}" in url:
        return True
    ok_url = (not ch) or f"/channel/{ch}" in url
    if ok_url and _has_menu(page):
        return True
    if log:
        log(f"    · chua san sang (url={url[:60]}, menu={'co' if _has_menu(page) else 'KHONG'}) -> chuyen lai")
    return switch_channel(page, ch, log)


CH_TITLES = {}   # channelId -> ten kenh (daily_0500_run dien tu Data API) — de bam dung muc trong channel_switcher


def _studio_cid(page):
    try:
        return page.evaluate("() => window.ytcfg && window.ytcfg.data_ && window.ytcfg.data_.CHANNEL_ID") or ""
    except Exception:
        return ""


def _switch_via_switcher(page, ch, log=None):
    """Mail quan NHIEU kenh (A+M, K+O, sengoku+J): kenh dang active khac `ch` thi goto /channel/<ch>
    ra trang "Oops" vinh vien (dinh 2026-10-22: lane A CHUA TUNG doc duoc tu 16/10). Phai doi kenh
    active nhu nguoi: youtube.com/channel_switcher -> bam ten kenh -> ve Studio, kiem CHANNEL_ID.
    Bam xong trang tu dieu huong -> moi loi 'context destroyed' trong luc do deu bo qua."""
    title = CH_TITLES.get(ch, "")
    if not title:
        if log:
            log(f"    · khong biet ten kenh {ch} -> khong dung channel_switcher duoc")
        return False
    hp.before_nav()
    page.goto("https://www.youtube.com/channel_switcher", wait_until="domcontentloaded", timeout=90000)
    time.sleep(random.uniform(5, 8))
    item = page.locator("ytd-account-item-renderer", has_text=title)
    if item.count() == 0:
        if log:
            log(f"    · channel_switcher khong co kenh '{title}'")
        return False
    box = item.first.bounding_box()
    hp.before_click()
    try:
        if box:
            _click_xy(page, int(box["x"] + box["width"] / 2), int(box["y"] + box["height"] / 2), log, f"kenh '{title}'")
        else:
            item.first.click()
    except Exception:
        pass
    time.sleep(random.uniform(7, 10))
    for _ in range(2):          # bay #5: lan goto dau hay dung o root
        page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=90000)
        time.sleep(random.uniform(8, 11))
        if _studio_cid(page) == ch and _has_menu(page):
            hp.after_read()
            if log:
                log(f"    · da doi kenh active sang '{title}' qua channel_switcher")
            return True
    if log:
        log(f"    · channel_switcher: Studio van o kenh {_studio_cid(page) or '?'} (can {ch})")
    return False


def switch_channel(page, ch, log=None):
    """Chuyen sang kenh `ch`: goto /channel/<ch> + RELOAD (bay #5); van khong vao (trang "Oops" vi kenh
    active cua mail la kenh khac) -> doi kenh active qua channel_switcher roi vao lai.

    Vi sao reload: goto /channel/<id> tra URL dung nhung SPA chua render menu trai.
    channel_switcher chi la DUONG DU PHONG (bam o do lam trang tu dieu huong — 2026-10-20 dung giua
    luc doc video thi mat phien), nen chi goi khi khong con cach nao khac, va goi TRUOC khi doc video.
    """
    if f"/channel/{ch}" in (page.url or "") and _has_menu(page):
        return True
    for i in range(2):
        hp.before_nav()
        page.goto(f"https://studio.youtube.com/channel/{ch}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(random.uniform(5, 8))
        if f"/channel/{ch}" in (page.url or "") and _has_menu(page):
            hp.after_read()
            return True
        oops = "Oops" in (page.title() or "")
        if log:
            log(f"    · chua vao duoc kenh sau goto (lan {i+1}{', trang Oops' if oops else ''})")
        if oops:
            break                # Oops = sai kenh active, reload bao nhieu cung vay
        page.reload(wait_until="domcontentloaded", timeout=90000)
        time.sleep(random.uniform(6, 10))
        if f"/channel/{ch}" in (page.url or "") and _has_menu(page):
            hp.after_read()
            return True
    if _switch_via_switcher(page, ch, log):
        return True
    if log:
        log(f"    · KHONG chuyen duoc sang kenh {ch}")
    return False


def click_tab(page, name, log=None, wait_s=None):
    """Bam tab trong trang video (Analytics / Reach / Overview ...).

    Phai CHO tab xuat hien: sau khi bam Analytics, thanh tab Overview/Reach/... chi hien
    sau vai giay (do that 2026-10-20: bam ngay thi khong thay 'Reach' -> truot ca video).

    Phai CUON LEN DAU trang truoc khi tim: hp.wander() cuon xuong de "doc so", lam thanh tab
    troi khoi man hinh -> tim khong thay roi bam vao toa do am (dinh that 2026-10-20).

    wait_s: mac dinh 45s khi chay 1 profile. Khi 2-4 profile chay SONG SONG, Studio cham han
    (do that 2026-10-20: lane K truot 3/3 video vi tab Reach khong hien trong 45s, chay don thi
    3-5s) -> noi goi truyen wait_s=120 cho tab Reach.
    """
    if wait_s is None:
        wait_s = int(os.environ.get("HUMAN_TAB_WAIT", "45"))
    try:
        page.evaluate("() => { window.scrollTo(0,0); const m=document.scrollingElement; if(m) m.scrollTop=0; }")
    except Exception:
        pass
    hp.before_click()
    deadline = time.time() + wait_s
    while time.time() < deadline:
        r = page.evaluate(FIND, name)
        if r and 0 < r["y"] < 900:
            _click_xy(page, r["x"], r["y"], log, f"tab {name}")
            time.sleep(random.uniform(1.5, 3.0))
            return True
        time.sleep(random.uniform(1.0, 2.0))
    if log:
        log(f"    · cho {wait_s}s khong thay tab '{name}'")
    return False


def set_day_range(page, start_d, end_d, log=None, tries=3):
    """Menu khoang thoi gian -> Custom -> go 2 ngay -> Apply. Tra True chi khi THAY so doi.

    Studio CHI cho chon NGAY (khong co gio) — da do 2026-10-20: hop Custom chi co 2 o ngay
    + Cancel/Apply. Vi vay "24h" = chon 1 NGAY tron (00:00-23:59 cua ngay do).

    Phai kiem tra THAT: bam Apply xong nhan khoang ngay phai doi sang "Oct 19, 2026"
    (khong con "— Now"). Khong doi = truot -> tra False, de noi goi KHONG lay nham so tron doi.
    """
    import re as _re
    for attempt in range(tries):
        parts = page.evaluate(DEEP)
        lab = [t for t in parts if ("Now" in t or "—" in t) and len(t) < 40]
        if not lab:
            if log:
                log("    · khong thay nhan khoang ngay de bam")
            return False
        hp.before_click()
        click_label(page, lab[0], log, why="nhan khoang ngay")
        time.sleep(random.uniform(1.5, 2.5))
        hp.before_click()
        if not click_label(page, "Custom", log, why="Custom"):
            continue
        time.sleep(random.uniform(2.0, 3.5))

        boxes = page.evaluate(INPUTS)
        if len(boxes) < 2:
            if log:
                log(f"    · hop Custom chi co {len(boxes)} o ngay -> thu lai")
            page.keyboard.press("Escape")
            time.sleep(random.uniform(1.5, 3.0))
            continue
        for box, d in zip(boxes[:2], (start_d, end_d)):
            _click_xy(page, box["x"], box["y"], log, f"o ngay {d}")
            time.sleep(random.uniform(0.4, 0.9))
            page.keyboard.press("Control+A")
            time.sleep(random.uniform(0.2, 0.5))
            for ch in d.strftime("%m/%d/%y"):
                page.keyboard.type(ch, delay=random.randint(70, 170))
            time.sleep(random.uniform(0.5, 1.1))
        hp.before_click()
        click_label(page, "Apply", log, why="Apply")
        time.sleep(random.uniform(2.5, 4.5))
        hp.wander(page)

        # xac minh: nhan khoang ngay phai het "Now"
        after = page.evaluate(DEEP)
        want = start_d.strftime("%b %-d, %Y") if os.name != "nt" else start_d.strftime("%b %d, %Y").replace(" 0", " ")
        if any("Now" not in t and ("—" in t or "–" in t) and len(t) < 40 for t in after) or any(want in t for t in after):
            if log:
                log(f"    · khoang ngay da doi sang {want}")
            return True
        if log:
            log(f"    · Apply khong doi duoc khoang ngay (lan {attempt+1}) -> thu lai")
    return False


def _parse_box_date(v):
    for fmt in ("%b %d, %Y", "%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(v.strip(), fmt).date()
        except Exception:
            pass
    return None


def _period_days(url):
    """URL tab Reach co dang .../period-<start_ms>,<end_ms> -> so ngay cua khoang (None neu khong co)."""
    import re as _re
    m = _re.search(r"period-(\d{12,}),(\d{12,})", url or "")
    return (int(m.group(2)) - int(m.group(1))) / 86400000 if m else None


def set_latest_day(page, log=None, tries=3):
    """Chon khoang = DUNG 1 NGAY du so gan nhat ma Studio cho chon. Tra date do, hoac None.

    Thay set_day_range(hom_qua) — dinh 2026-10-22 (lam Q = P hang loat tu 20/10):
      * luc 05:00-08:00 Studio CHUA co so hom qua, chi cho chon toi hom kia ("Enter 10/20/26 or
        earlier") -> go cung "hom qua" la sai.
      * go ngay BAT DAU > ngay KET THUC dang co -> Studio tra o bat dau ve ngay dang cu (Sep 26)
        -> khoang thanh "Sep 26 – Oct 20" = gan nhu tron doi, ma ham cu van bao "da doi".
    Cach dung: o KET THUC mac dinh = ngay du so moi nhat -> chi go o BAT DAU = chinh ngay do.
    Xac minh CHAT bang URL period-<start>,<end> phai dai dung ~1 ngay (chi doc URL, khong goto).
    """
    for attempt in range(tries):
        parts = page.evaluate(DEEP)
        lab = [t for t in parts if ("Now" in t or "—" in t or "–" in t) and len(t) < 40 and any(c.isdigit() for c in t)]
        if not lab:
            if log:
                log("    · khong thay nhan khoang ngay de bam")
            return None
        hp.before_click()
        click_label(page, lab[0], log, why="nhan khoang ngay")
        time.sleep(random.uniform(1.5, 2.5))
        hp.before_click()
        if not click_label(page, "Custom", log, why="Custom"):
            page.keyboard.press("Escape"); time.sleep(1.5)
            continue
        time.sleep(random.uniform(2.0, 3.5))
        boxes = page.evaluate(INPUTS)
        day = _parse_box_date(boxes[1]["val"]) if len(boxes) >= 2 else None
        if not day:
            if log:
                log(f"    · hop Custom khong doc duoc o ngay ket thuc ({[b['val'] for b in boxes]}) -> thu lai")
            page.keyboard.press("Escape"); time.sleep(random.uniform(1.5, 3.0))
            continue
        box = boxes[0]
        _click_xy(page, box["x"], box["y"], log, f"o ngay bat dau -> {day}")
        time.sleep(random.uniform(0.4, 0.9))
        page.keyboard.press("Control+A")
        time.sleep(random.uniform(0.2, 0.5))
        for ch in day.strftime("%m/%d/%y"):
            page.keyboard.type(ch, delay=random.randint(70, 170))
        time.sleep(random.uniform(0.6, 1.2))
        hp.before_click()
        click_label(page, "Apply", log, why="Apply")
        time.sleep(random.uniform(3.0, 5.0))
        n = _period_days(page.url)
        if n is not None and 0.9 <= n <= 1.1:
            if log:
                log(f"    · khoang ngay = 1 ngay {day} (URL xac nhan)")
            hp.wander(page)
            return day
        if log:
            log(f"    · khoang ngay KHONG phai 1 ngay (period={n}) lan {attempt+1} -> thu lai")
    return None
