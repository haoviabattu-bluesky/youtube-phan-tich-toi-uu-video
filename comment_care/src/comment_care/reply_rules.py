"""reply_rules.py — luật reply NGẮN như người thật (anh chốt 2026-10-22, HUONG_DAN_HERMES mục 0 + 4.5).

Dùng chung cho: QC bản LLM soạn (qc_rules) · câu EDIT ghi tay trong DRAFT_REVIEW (review) · tools/viet_reply.py · `cc.py thank`.
Trả danh sách lý do FAIL; rỗng = đạt.
"""
import difflib
import re

import yaml

from .config import TEMPLATES_DIR

BODY_MAX = 50            # ký tự Nhật của phần thân (không tính câu xin like/đăng ký)
BODY_MAX_SENTENCES = 2
QUOTE_MIN_RUN = 8        # chuỗi liền ≥8 ký tự trùng bình luận = đang chép lời khách

EMOJI = re.compile(r"[\U0001F000-\U0001FAFF☀-➿⬀-⯿]")
VIET = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]")
QUOTE_MARKS = re.compile(r"[「」『』\"“”]")
DIGITS = re.compile(r"[0-9０-９]")
SELF_TALK = re.compile(r"私も|私は|私の|僕も|僕は|僕の|わたしも|自分も|うちの(?:母|父|妻|夫|親)")
# cụm câu chuẩn ai cũng viết → bỏ trước khi dò trích dẫn, kẻo "ありがとうございます" bị coi là chép lời khách
STOCK = ("コメントありがとうございます", "ありがとうございます", "コメント", "高評価", "チャンネル登録", "よろしくお願いします",
         "お願いします", "本当に", "そうですね")


def ja_len(text: str) -> int:
    return len(re.sub(r"[\s　]", "", text or ""))


def cta_phrases() -> list[str]:
    f = yaml.safe_load((TEMPLATES_DIR / "templates.yaml").read_text(encoding="utf-8"))["footer"]
    return [f["full"]] + list(f["variants"])


def split_cta(final: str, ctas=None) -> tuple[str, int]:
    """→ (phần thân, số câu CTA tìm thấy). CTA viết liền cùng dòng hay xuống dòng đều nhận."""
    body, n = final or "", 0
    for c in ctas or cta_phrases():
        k = body.count(c)
        if k:
            n += k
            body = body.replace(c, "")
    return body.strip(), n


def _strip_stock(s: str) -> str:
    s = re.sub(r"[\s　、。！？!?]", "", s or "")
    for w in STOCK:
        s = s.replace(w, "")
    return s


def quote_run(body: str, source: str) -> str:
    """Chuỗi liền dài nhất của `body` trùng `source` (sau khi bỏ cụm câu chuẩn)."""
    a, b = _strip_stock(body), _strip_stock(source)
    if not a or not b:
        return ""
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return a[m.a:m.a + m.size]


def body_fails(body: str, comment_text: str = "", video_title: str = "") -> list[str]:
    """Luật cho PHẦN THÂN (không có CTA)."""
    fails = []
    if not (body or "").strip():
        return ["empty"]
    if VIET.search(body):
        fails.append("vietnamese_chars")
    if re.search(r"[A-Za-z]{3,}", body):
        fails.append("latin_word")
    if EMOJI.search(body):
        fails.append("emoji")
    if "@" in body or "＠" in body:
        fails.append("at_mention")
    if re.search(r"https?://|www\.", body):
        fails.append("url")
    if QUOTE_MARKS.search(body):
        fails.append("quote_marks「」")
    if DIGITS.search(body):
        fails.append("number")
    if SELF_TALK.search(body):
        fails.append("owner_self_talk")
    if "！" in body or "!" in body or re.search(r"[wｗ]{2,}", body):
        fails.append("exclamation_or_w")
    n = ja_len(body)
    if n > BODY_MAX:
        fails.append(f"body_too_long {n}>{BODY_MAX}")
    sents = [s for s in re.split(r"(?<=[。？?])", body) if s.strip()]
    if len(sents) > BODY_MAX_SENTENCES + 1:      # +1: câu cảm ơn ngắn được tính thêm
        fails.append(f"too_many_sentences {len(sents)}")
    for src, tag in ((comment_text, "quote_comment"), (video_title, "quote_title")):
        run = quote_run(body, src)
        if len(run) >= QUOTE_MIN_RUN:
            fails.append(f"{tag}:{run[:15]}")
    return fails


def final_fails(final: str, comment_text: str = "", video_title: str = "") -> list[str]:
    """Luật cho CÂU SẼ ĐĂNG (thân + tối đa 1 câu CTA). Dùng cho EDIT / thank / viet_reply."""
    body, n_cta = split_cta(final)
    fails = body_fails(body, comment_text, video_title)
    if n_cta > 1:
        fails.append(f"cta_x{n_cta}")
    if "ありがと" not in final and "感謝" not in final:
        fails.append("no_thanks")
    return fails
