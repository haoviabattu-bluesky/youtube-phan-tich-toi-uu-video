"""reactions.py — LIKE + THẢ TIM (creator heart) cho comment đang highlight, bằng chuột thật (anh yêu cầu 2026-10-14, lane M).

DOM đo thật 2026-10-14 (watch page, comment top-level):
- like:  `#like-button button`  aria-pressed "false"/"true"
- tim:   `#creator-heart-button button`  aria-label "Heart" khi CHƯA thả (chỉ hiện khi đang đứng tư cách CHỦ KÊNH)
Bấm lại lần 2 là GỠ like/tim → chỉ bấm khi trạng thái đang TẮT; đọc lại trạng thái sau khi bấm để xác nhận.
"""
import random
import time

_STATE_JS = r"""(el) => {
  const like = el.querySelector('#like-button button');
  const heart = el.querySelector('#creator-heart-button button');
  const hearted = !!el.querySelector('#creator-heart #hearted, #creator-heart [id="hearted-thumbnail"]');
  return {
    like_found: !!like, liked: like ? like.getAttribute('aria-pressed') === 'true' : null,
    heart_found: !!heart, heart_label: heart ? (heart.getAttribute('aria-label') || '') : '', hearted_img: hearted,
  };
}"""


def read_state(target):
    st = target.element_handle(timeout=10000).evaluate(_STATE_JS)
    st["hearted"] = st["hearted_img"] or (st["heart_found"] and st["heart_label"].strip().lower() not in ("heart", ""))
    return st


def react(page, target, mouse_click, log, like=True, heart=True, dry_run=False):
    """Trả dict {'like': 'DONE|ALREADY|NOT_FOUND|FAILED|DRY_RUN|OFF', 'heart': ...}. Không bao giờ bấm khi đã bật sẵn."""
    res = {"like": "OFF", "heart": "OFF"}
    st = read_state(target)
    jobs = []
    if like:
        jobs.append(("like", "#like-button button", st["like_found"], st["liked"]))
    if heart:
        jobs.append(("heart", "#creator-heart-button button", st["heart_found"], st["hearted"]))
    for name, sel, found, on in jobs:
        if not found:
            res[name] = "NOT_FOUND"
            log(f"    · {name}: không thấy nút" + (" (tim chỉ hiện khi đứng tư cách chủ kênh)" if name == "heart" else ""))
            continue
        if on:
            res[name] = "ALREADY"
            log(f"    · {name}: đã bật sẵn → không bấm (bấm lại là gỡ)")
            continue
        if dry_run:
            res[name] = "DRY_RUN"
            log(f"    [dry-run] sẽ bấm {name}")
            continue
        mouse_click(page, target, sel)
        time.sleep(random.uniform(1.5, 2.5))
        st = read_state(target)
        ok = st["liked"] if name == "like" else st["hearted"]
        res[name] = "DONE" if ok else "FAILED"
        log(f"    {'✓' if ok else '✗'} {name}: {res[name]}")
        time.sleep(random.uniform(1.0, 2.5))
    return res
