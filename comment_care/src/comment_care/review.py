"""review.py — đọc DRAFT_REVIEW.txt anh đã ghi `YOUR_DECISION:` và áp vào DB (APPROVE / EDIT: <text> / REJECT / SKIP).

2026-10-22: câu EDIT phải qua reply_rules.final_fails (≤50 ký tự thân, không trích dẫn, không số, không nói về bản thân, ≤1 CTA…)
— sai luật thì KHÔNG áp, in lý do để người sửa lại dòng YOUR_DECISION (`--force` để bỏ qua, chỉ khi anh bảo).
"""
import re
from pathlib import Path

from .reply_rules import final_fails

BLOCK = re.compile(r"DRAFT_ID:\s*(\d+)(.*?)YOUR_DECISION:\s*([^\n]*)", re.S)


def parse(path: Path) -> list[tuple[int, str, str | None]]:
    out = []
    for m in BLOCK.finditer(Path(path).read_text(encoding="utf-8")):
        did, raw = int(m.group(1)), m.group(3).strip()
        if not raw:
            continue
        up = raw.upper()
        if up.startswith("APPROVE"):
            out.append((did, "APPROVE", None))
        elif up.startswith("EDIT"):
            txt = raw.split(":", 1)[1].strip() if ":" in raw else ""
            out.append((did, "EDIT", txt or None))
        elif up.startswith("REJECT"):
            out.append((did, "REJECT", None))
        elif up.startswith("SKIP"):
            out.append((did, "SKIP", None))
    return out


def apply(store, path: Path, force=False) -> list[str]:
    log = []
    for did, dec, txt in parse(path):
        # so theo idempotency_key như poster: key đã đổi đuôi ':failedYYYYMMDD' (API xác nhận CHƯA đăng) thì được duyệt lại
        cur = store.one("SELECT f.status, (SELECT r.status FROM replies r WHERE r.idempotency_key=f.channel_id||':'||f.comment_id) rs "
                        "FROM drafts f WHERE f.id=?", did)
        if cur and (cur["status"] == "SENT" or cur["rs"]):
            log.append(f"draft {did}: ↷ đã có lượt đăng ({cur['rs'] or cur['status']}) → không đổi (chống đăng lại)")
            continue
        if dec == "EDIT":
            if not txt:
                log.append(f"draft {did}: ✗ EDIT trống → không áp")
                continue
            if not force:
                ctx = store.one("SELECT c.text, v.title FROM drafts f JOIN comments c ON c.comment_id=f.comment_id "
                                "LEFT JOIN videos v ON v.video_id=f.video_id WHERE f.id=?", did) or {}
                fails = final_fails(txt, ctx.get("text") or "", ctx.get("title") or "")
                if fails:
                    log.append(f"draft {did}: ✗ EDIT KHÔNG áp — sai luật: {', '.join(fails)} → sửa lại dòng YOUR_DECISION rồi chạy lại")
                    continue
        try:
            st = store.review_apply(did, dec, edited_text=txt)
            log.append(f"draft {did}: {dec} → {st}")
        except KeyError as e:
            log.append(f"draft {did}: lỗi {e}")
    return log
