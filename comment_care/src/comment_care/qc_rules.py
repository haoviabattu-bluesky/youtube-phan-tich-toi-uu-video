"""qc_rules.py — QC rule-based 0 token (spec mục L-A + I5). Trả danh sách lý do FAIL; rỗng = PASS."""
import re
from pathlib import Path

from .prefilter import japanese_ratio
from .reply_rules import body_fails

EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
INTERNAL = re.compile(r"\{|\}|\[|\]|CATEGORY|CONFIDENCE|REPLY_DECISION|PROPOSED|```|#{2,}|<\w+>")
VIET = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]")


def ja_len(text: str) -> int:
    return len(re.sub(r"[\s　]", "", text or ""))


class RuleQC:
    def __init__(self, blocklist_path: Path, other_channel_names: list[str]):
        pats = []
        for ln in Path(blocklist_path).read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                try:
                    pats.append(re.compile(ln, re.M))
                except re.error:
                    pass
        self.block = pats
        self.others = [n for n in other_channel_names if n]

    def blocklist_hits(self, text: str) -> list[str]:
        return [p.pattern for p in self.block if p.search(text or "")]

    def check(self, body: str, footer: str, dec, allowed_footers: list[str], recent_texts: list[str], comment_text: str = "",
              video_title: str = "") -> list[str]:
        fails = []
        if not body or not body.strip():
            return ["empty"]
        if japanese_ratio(body) < 0.6:
            fails.append(f"japanese_only ratio={japanese_ratio(body):.2f}")
        # 2026-10-22 HUONG_DAN_HERMES: tiếng Việt/Latin/emoji/@/link + CẤM trích dẫn lời khách/tiêu đề, cấm số, cấm nói về bản thân, thân ≤50
        fails += body_fails(body, comment_text, video_title)
        n = ja_len(body)
        lo, hi = dec.length
        if n < lo:
            fails.append(f"too_short {n}<{lo}")
        if n > hi:
            fails.append(f"too_long {n}>{hi}")
        if INTERNAL.search(body):
            fails.append("internal_text")
        hits = self.blocklist_hits(body)
        if hits:
            fails.append("blocklist:" + ";".join(hits[:3]))
        for name in self.others:
            if name in body:
                fails.append(f"other_channel_name:{name}")
        if dec.footer == "yes" and footer and footer not in allowed_footers:
            fails.append("footer_not_in_allowed")
        if dec.footer == "no" and footer:
            fails.append("footer_present_but_rule_no")
        for s in re.split(r"(?<=。)", body):
            if ja_len(s) > 75:
                fails.append("sentence_over_75")
                break
        full = (body + ("\n" + footer if footer else "")).strip()
        # câu cố định SENSITIVE (anh chốt 2026-10-15) / THANKS (2026-10-22) được phép lặp trong cùng video
        if getattr(dec, "template_key", None) not in ("SENSITIVE", "THANKS") and full in [t.strip() for t in recent_texts if t]:
            fails.append("duplicate_text")
        return fails
