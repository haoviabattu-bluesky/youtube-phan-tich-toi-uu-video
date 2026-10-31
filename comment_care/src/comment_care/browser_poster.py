"""browser_poster.py — ĐĂNG reply bằng trình duyệt thật của profile GPM (anh chốt 2026-10-05: "mở lane F lên, mở từng video,
đọc từng comment, gõ chậm như người"). Đường B của spec Z-1; dùng khi chưa có OAuth.

An toàn:
- Chỉ đăng draft đã APPROVED/EDITED trong DB (anh duyệt). Mỗi comment tối đa 1 reply (bảng replies, idempotency_key).
- Xác minh identity TRƯỚC khi gõ: studio.youtube.com phải redirect về đúng channel_id của config (CASE 8).
- Trước khi gõ: kiểm comment highlight (`&lc=`) đúng nội dung; thread chưa có reply của kênh (live).
- Gõ từng ký tự 60–180 ms, nghỉ dài ở dấu câu, "đọc" video/comment 15–45 s, nghỉ giữa 2 reply 60–150 s, 2 video cách 30–90 s.
- GPM báo ProfileUsingByOther → DỪNG, không kill (luật dự án). Đăng xong là TẮT profile (anh chốt 2026-10-08); `--keep-open` để giữ mở.
"""
import json
import random
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))  # tái dùng helper GPM của repo
GPM = "http://127.0.0.1:9495/api/v1"
BANNER = "GPMLogin Global API"


class PostBlocked(RuntimeError):
    pass


# ---------------------------------------------------------------- GPM
def gpm_find(mail):
    page = 1
    while True:
        try:
            d = requests.get(f"{GPM}/profiles", params={"page": page, "per_page": 100}, timeout=30).json()["data"]
        except (requests.RequestException, ValueError, KeyError) as e:
            raise PostBlocked(f"GPM_NOT_RUNNING: GPMLogin không trả lời ở {GPM} ({type(e).__name__}) → báo anh mở GPM, không tự sửa") from e
        for p in d["data"]:
            n = p["name"].strip().lower()
            if n == mail.strip().lower() or n == mail.strip().lower().split("@")[0]:
                return p["id"]
        if page >= d["last_page"]:
            return None
        page += 1


def gpm_start(pid):
    try:
        j = requests.get(f"{GPM}/profiles/start/{pid}", timeout=180).json()
    except (requests.RequestException, ValueError) as e:
        raise PostBlocked(f"GPM_NOT_RUNNING: không mở được profile {pid} ({type(e).__name__}) → báo anh") from e
    d = j.get("data")
    if j.get("message") == "ProfileUsingByOther":
        raise PostBlocked("PROFILE_BUSY: profile đang được dùng ở nơi khác (có thể anh đang mở tay) → không chạy, không kill.")
    if not j.get("success") or d == BANNER or not isinstance(d, dict):
        raise PostBlocked(f"GPM start fail: {j.get('message') or d}")
    ws = d.get("websocket_debugging_url") or ""
    if not ws:
        raise PostBlocked("GPM websocket RỖNG → stop + đóng chrome của đúng profile rồi chạy lại (xem CLAUDE.md bẫy #3)")
    return ws


# ---------------------------------------------------------------- nhịp người
def pause(a, b, log=None, why=""):
    t = random.uniform(a, b)
    if log and why:
        log(f"    ⏳ {why} {t:.0f}s")
    time.sleep(t)


def human_type(page, text, log=None):
    """Gõ từng ký tự với độ trễ ngẫu nhiên; nghỉ dài ở dấu câu/xuống dòng; thỉnh thoảng dừng 'suy nghĩ'."""
    for i, ch in enumerate(text):
        if ch == "\n":
            page.keyboard.press("Enter")
            time.sleep(random.uniform(0.5, 1.1))
            continue
        page.keyboard.type(ch)
        time.sleep(random.uniform(0.06, 0.18))
        if ch in "。、！？":
            time.sleep(random.uniform(0.4, 0.9))
        if i and i % random.randint(18, 30) == 0:
            time.sleep(random.uniform(0.8, 2.2))


# ---------------------------------------------------------------- YouTube watch page
def verify_identity(page, channel_id, log):
    """studio.youtube.com đứng ở root lần đầu, lần 2 mới nhảy /channel/<id> (bẫy #5) → goto tối đa 3 lần."""
    for _ in range(3):
        page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=90000)
        time.sleep(4)
        m = re.search(r"studio\.youtube\.com/channel/(UC[\w-]{22})", page.url)
        if m:
            if m.group(1) != channel_id:
                raise PostBlocked(f"IDENTITY_MISMATCH: profile đang đăng nhập kênh {m.group(1)} ≠ {channel_id}")
            log(f"  ✓ identity OK: {m.group(1)}")
            return
    if "accounts.google.com" in page.url:
        raise PostBlocked("profile CHƯA đăng nhập Google")
    raise PostBlocked(f"không xác định được kênh từ Studio (url={page.url[:80]})")


def _norm(s):
    # YouTube vẽ emoji thành <img> nên inner_text không có emoji (đo 2026-10-09, comment 😮😊😂 lane O) → bỏ emoji cả 2 phía.
    s = re.sub(r"[\U0001F000-\U0001FAFF☀-➿️‍⬀-⯿]", "", s or "")
    return re.sub(r"\s", "", s)[:25]


def _find_highlighted_thread(page, comment_text, is_reply=False):
    """→ (thread, target). Comment được &lc= highlight nằm đầu danh sách. Nếu là REPLY (id có dấu '.'), YouTube tự mở
    nhánh replies và highlight reply đó → target là phần tử reply bên trong #replies, thread là thread cha."""
    want = _norm(comment_text)
    for _ in range(20):
        threads = page.locator("ytd-comment-thread-renderer")
        n = threads.count()
        for i in range(min(n, 5)):
            t = threads.nth(i)
            if not is_reply:
                try:
                    if _norm(t.locator("#comment #content-text").first.inner_text(timeout=2000)) == want:
                        return t, t.locator("#comment").first
                except Exception:  # noqa: BLE001
                    continue
            else:
                try:
                    more = t.locator("#more-replies button, ytd-comment-replies-renderer #more-replies").first
                    if more.count() and more.is_visible():
                        more.click()
                        time.sleep(random.uniform(1.5, 3))
                except Exception:  # noqa: BLE001
                    pass
                # Đo thật 2026-10-05: reply được &lc= highlight xuất hiện 2 lần — 1 bản ẩn trong DIV#teaser-replies (bbox 0)
                # và 1 bản thật trong nhánh đã mở → chỉ nhận phần tử có kích thước thật.
                reps = t.locator("#replies ytd-comment-view-model, #replies ytd-comment-renderer")
                for j in range(reps.count()):
                    r = reps.nth(j)
                    try:
                        if _norm(r.locator("#content-text").first.inner_text(timeout=2000)) != want:
                            continue
                        bb = r.locator("#content-text").first.bounding_box()
                        if bb and bb["height"] > 0:
                            return t, r
                    except Exception:  # noqa: BLE001
                        continue
        page.mouse.wheel(0, random.randint(300, 700))
        time.sleep(1.5)
    return None, None


def thread_has_owner_reply(thread, handle):
    """Mở replies (nếu có) và tìm reply của chính kênh."""
    try:
        more = thread.locator("#replies ytd-button-renderer, #more-replies button, ytd-comment-replies-renderer #more-replies").first
        if more.count() and more.is_visible():
            more.click()
            time.sleep(random.uniform(1.5, 3))
    except Exception:  # noqa: BLE001
        pass
    h = (handle or "").lstrip("@").lower()
    if not h:   # handle rỗng → "" khớp MỌI tác giả → báo nhầm "kênh đã trả lời" (lane O thiếu handle tới 2026-10-22)
        raise PostBlocked("kênh thiếu `handle` trong channels.yaml → không kiểm được thread đã có reply của kênh")
    try:
        authors = thread.locator("#replies ytd-comment-view-model #author-text, #replies ytd-comment-renderer #author-text").all_inner_texts()
    except Exception:  # noqa: BLE001
        authors = []
    return any(h in a.lower().replace("@", "") for a in authors)


_RECT_JS = """(el, sel) => {
  const cands = sel ? Array.from(el.querySelectorAll(sel)) : [el];
  let best = null, area = 0;
  for (const c of cands) { const r = c.getBoundingClientRect(); const a = r.width * r.height; if (a > area) { area = a; best = c; } }
  if (!best) return null;
  best.scrollIntoView({block: 'center', behavior: 'smooth'});
  const r = best.getBoundingClientRect();
  return {x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height};
}"""


def _mouse_click(page, target, selector, log=None):
    """Polymer host (ytd-comment-view-model) có display:contents → Playwright coi là 'not visible'. Lấy bbox của phần tử con
    thật bằng JS rồi click bằng chuột thật (di chuyển → click), giống người hơn locator.click()."""
    h = target.element_handle(timeout=10000)
    for _ in range(3):
        rect = h.evaluate(_RECT_JS, selector)
        if rect and rect["w"] > 0 and rect["h"] > 0:
            time.sleep(random.uniform(0.6, 1.2))
            rect = h.evaluate(_RECT_JS, selector) or rect  # đo lại sau khi scroll xong (None khi DOM vẽ lại → giữ số đo đầu)
            page.mouse.move(rect["x"] + random.uniform(-3, 3), rect["y"] + random.uniform(-2, 2), steps=random.randint(8, 18))
            time.sleep(random.uniform(0.2, 0.5))
            page.mouse.click(rect["x"], rect["y"])
            return True
        time.sleep(1.0)
    raise PostBlocked(f"không thấy phần tử '{selector}' có kích thước để click")


def post_reply(page, thread, text, handle, log, target=None):
    target = target or thread.locator("#comment").first
    # di chuột lên comment (hiện nút Reply ở reply-type), rồi click nút Reply bằng chuột thật
    _mouse_click(page, target, "#content-text")
    pause(0.8, 1.6)
    _mouse_click(page, target, "#reply-button-end button, #reply-button-end")
    pause(1.0, 2.0)
    # ô nhập: có thể có nhiều #contenteditable-root trong thread (bản ẩn trong teaser) → chọn bản có kích thước thật
    box = None
    for _ in range(15):
        boxes = thread.locator("#contenteditable-root")
        for i in range(boxes.count()):
            bb = boxes.nth(i).bounding_box()
            if bb and bb["height"] > 0:
                box = boxes.nth(i)
                break
        if box:
            break
        time.sleep(1.0)
    if box is None:
        raise PostBlocked("ô nhập reply không hiện sau khi bấm Reply")
    box.click()
    pause(0.8, 1.6)
    human_type(page, text, log)
    pause(2.0, 4.5, log, "đọc lại trước khi gửi")
    submit = None
    subs = thread.locator("#submit-button button")
    for i in range(subs.count()):
        bb = subs.nth(i).bounding_box()
        if bb and bb["height"] > 0:
            submit = subs.nth(i)
    if submit is None or not submit.is_enabled():
        raise PostBlocked("nút gửi không bật — có thể ô nhập không nhận chữ")
    submit.click()
    pause(3.0, 5.0)
    # xác nhận reply xuất hiện với tên kênh. Reply-cho-reply được YouTube tự thêm "@tên " ở đầu → bỏ prefix đó khi so.
    want = re.sub(r"\s", "", text.split("\n")[0])[:20]
    for _ in range(8):
        try:
            replies = thread.locator("#replies #content-text").all_inner_texts()
            authors = thread.locator("#replies #author-text").all_inner_texts()
        except Exception:  # noqa: BLE001
            replies, authors = [], []
        for r, a in zip(replies, authors):
            body = re.sub(r"^@\S+\s*", "", r.strip())
            if re.sub(r"\s", "", body)[:20] == want:
                return a.strip()
        time.sleep(1.5)
    return ""


# ---------------------------------------------------------------- phiên trình duyệt (dùng chung post-browser / react-browser)
def ensure_channel(page, ch, log):
    """Đúng kênh → None. Mail quản nhiều kênh (K+O) mà đang đứng ở kênh ANH EM cùng mail → tự đổi qua channel_switcher,
    trả về channel_id cũ để chuyển về sau khi xong (CLAUDE.md 2026-10-15). Kênh lạ không cùng mail → dừng."""
    try:
        verify_identity(page, ch.channel_id, log)
        return None
    except PostBlocked as e:
        m = re.search(r"IDENTITY_MISMATCH: profile đang đăng nhập kênh (UC[\w-]{22})", str(e))
        if not m:
            raise
        orig = m.group(1)
    from .config import load_channels
    chans = load_channels()
    if orig not in {c.channel_id for c in chans if c.mail.lower() == ch.mail.lower()}:
        raise PostBlocked(f"IDENTITY_MISMATCH: profile đang ở kênh {orig} — không phải kênh anh em cùng mail {ch.mail} → dừng")
    import studio_human as sh  # tools/studio_human.py (đã sys.path ở đầu file)
    sh.CH_TITLES.update({c.channel_id: c.channel_name for c in chans if c.channel_name})
    log(f"  ↺ profile đang ở kênh {orig} (cùng mail) → chuyển sang {ch.channel_name}")
    if not sh.switch_channel(page, ch.channel_id, log):
        raise PostBlocked(f"không chuyển được sang kênh {ch.channel_name} qua channel_switcher")
    verify_identity(page, ch.channel_id, log)
    return orig


def _switch_back(page, orig, log):
    try:
        import studio_human as sh
        ok = sh.switch_channel(page, orig, log)
        log(f"  ↺ chuyển về kênh cũ {orig}: {'OK' if ok else 'KHÔNG được — báo anh'}")
    except Exception as e:  # noqa: BLE001
        log(f"  ! chuyển về kênh cũ {orig} lỗi {type(e).__name__} {e} — báo anh")


@contextmanager
def session(ch, log=print, keep_open=False, cdp_port=None):
    """yield page đã đứng ĐÚNG kênh. Thoát (kể cả lỗi): chuyển về kênh cũ nếu đã đổi + TẮT profile GPM (anh chốt 2026-10-08)."""
    from playwright.sync_api import sync_playwright
    pid = None
    if cdp_port:  # lane A/M (haoviabattu): Chrome riêng, không qua GPM. Không tắt Chrome này (dùng chung AUTO_LIST).
        ws = f"http://127.0.0.1:{cdp_port}"
    else:
        pid = gpm_find(ch.mail)
        if not pid:
            raise PostBlocked(f"không thấy profile GPM tên {ch.mail}")
        ws = gpm_start(pid)
        log(f"  GPM profile {pid} mở, ws ok")
    try:
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(ws)
            # tab NỀN không ăn chuột/smooth-scroll ổn định (đo 2026-10-14: like FAILED, ô reply không hiện, bbox None) → tab riêng + đưa lên trước
            page = br.contexts[0].new_page()
            page.bring_to_front()
            orig = ensure_channel(page, ch, log)
            try:
                yield page
            finally:
                if orig:
                    _switch_back(page, orig, log)
    finally:
        if pid and not keep_open:
            requests.get(f"{GPM}/profiles/stop/{pid}", timeout=60)
            log(f"  GPM profile {pid} đã tắt")


def open_comment(page, vid, comment_id, text, log):
    """goto &lc= → (thread, target) của comment đang highlight, hoặc (None, None)."""
    page.goto(f"https://www.youtube.com/watch?v={vid}&lc={comment_id}", wait_until="domcontentloaded", timeout=90000)
    pause(6, 12, log, "đọc comment")
    return _find_highlighted_thread(page, text, "." in comment_id)


# ---------------------------------------------------------------- main
def run(store, ch, drafts: list[dict], log=print, keep_open=False, dry_run=False, cdp_port=None, like_ids=(), heart_ids=()):
    """drafts: [{draft_id, comment_id, video_id, final_text, text}] đã APPROVED. Trả danh sách kết quả.
    Anh chốt 2026-10-08: lane nào đăng xong thì TẮT profile (GPM stop đúng profile id của kênh) để người khác làm việc — kể cả khi lỗi giữa chừng."""
    with session(ch, log, keep_open, cdp_port) as page:
        return _run(store, ch, drafts, page, log, dry_run, (set(like_ids), set(heart_ids)))


def _run(store, ch, drafts, page, log, dry_run, react_ids=(set(), set())):
    from .reactions import react
    results = []
    by_video = {}
    for d in drafts:
        by_video.setdefault(d["video_id"], []).append(d)
    for vi, (vid, items) in enumerate(by_video.items()):
        if vi:
            pause(30, 90, log, "chuyển sang video khác, nghỉ")
        log(f"\n  ▶ video {vid} ({len(items)} reply)")
        page.goto(f"https://www.youtube.com/watch?v={vid}", wait_until="domcontentloaded", timeout=90000)
        pause(15, 45, log, "xem video/đọc mô tả")
        for i in range(random.randint(3, 6)):
            page.mouse.wheel(0, random.randint(250, 600))
            time.sleep(random.uniform(0.8, 2.0))
        for ri, d in enumerate(items):
            if ri:
                pause(60, 150, log, "nghỉ giữa 2 reply")
            key = f"{ch.channel_id}:{d['comment_id']}"
            # mọi trạng thái (kể cả UNKNOWN_RECONCILE / SKIPPED_OWNER_EXISTS) đều chặn: không bao giờ đăng lại khi chưa đối chiếu
            prev = store.one("SELECT status FROM replies WHERE idempotency_key=?", key)
            if prev:
                log(f"    ↷ {d['comment_id'][-8:]} đã có reply row ({prev['status']}) → bỏ qua")
                continue
            thread, target = open_comment(page, vid, d["comment_id"], d["text"], log)
            is_reply = "." in d["comment_id"]
            if thread is None:
                log(f"    ✗ {d['comment_id'][-8:]} không thấy comment highlight → bỏ qua")
                results.append({**d, "status": "NOT_FOUND"})
                continue
            # top-level: thread đã có reply của kênh → bỏ. Reply-type (viewer trả lời câu hỏi ghim / follow-up): kênh có thể đã
            # reply trong thread trước đó (hợp lệ), chỉ chặn khi đã có reply của kênh MỚI HƠN comment này (kiểm qua DB replies).
            if not is_reply and thread_has_owner_reply(thread, ch.handle):
                log(f"    ↷ {d['comment_id'][-8:]} kênh đã trả lời thread này → bỏ qua")
                store.x("INSERT OR IGNORE INTO replies(channel_id,comment_id,draft_id,idempotency_key,final_text,status,error) VALUES(?,?,?,?,?,'SKIPPED_OWNER_EXISTS','')",
                        ch.channel_id, d["comment_id"], d["draft_id"], key, d["final_text"])
                results.append({**d, "status": "SKIPPED_OWNER_EXISTS"})
                continue
            rx = None
            if d["draft_id"] in react_ids[0] or d["draft_id"] in react_ids[1]:
                rx = react(page, target, _mouse_click, log, like=d["draft_id"] in react_ids[0],
                           heart=d["draft_id"] in react_ids[1], dry_run=dry_run)
                d = {**d, "reactions": rx}
                if not dry_run:
                    store.save_reaction(ch.channel_id, d["comment_id"], rx)
            if dry_run:
                log(f"    [dry-run] sẽ gõ {len(d['final_text'])} ký tự vào {d['comment_id'][-8:]}")
                results.append({**d, "status": "DRY_RUN"})
                continue
            rid = store.x("INSERT INTO replies(channel_id,comment_id,draft_id,idempotency_key,final_text,status) VALUES(?,?,?,?,?,'SENDING')",
                          ch.channel_id, d["comment_id"], d["draft_id"], key, d["final_text"])
            try:
                author = post_reply(page, thread, d["final_text"], ch.handle, log, target)
            except Exception as e:  # noqa: BLE001
                store.x("UPDATE replies SET status='UNKNOWN_RECONCILE',error=? WHERE id=?", str(e)[:300], rid)
                log(f"    ✗ {d['comment_id'][-8:]} lỗi khi gửi: {type(e).__name__} {str(e)[:120]} → UNKNOWN_RECONCILE (không gửi lại)")
                results.append({**d, "status": "UNKNOWN_RECONCILE", "error": str(e)[:200]})
                continue
            if author:
                store.x("UPDATE replies SET status='SENT',sent_at=?,api_response_json=? WHERE id=?", time.strftime("%Y-%m-%dT%H:%M:%S"),
                        json.dumps({"via": "browser", "author_seen": author, "reactions": rx}, ensure_ascii=False), rid)
                store.x("UPDATE drafts SET status='SENT' WHERE id=?", d["draft_id"])
                log(f"    ✓ {d['comment_id'][-8:]} đã đăng (hiện tên: {author})")
                results.append({**d, "status": "SENT", "author_seen": author})
            else:
                store.x("UPDATE replies SET status='UNKNOWN_RECONCILE',error='không thấy reply sau khi bấm gửi' WHERE id=?", rid)
                log(f"    ? {d['comment_id'][-8:]} đã bấm gửi nhưng chưa thấy reply hiện → UNKNOWN_RECONCILE")
                results.append({**d, "status": "UNKNOWN_RECONCILE"})
    return results
