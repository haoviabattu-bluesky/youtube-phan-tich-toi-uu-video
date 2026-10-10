"""prefilter.py — lọc deterministic 0 token (spec mục K bước 1)."""
import re

JA = re.compile(r"[぀-ヿ一-鿿ｦ-ﾟ]")
LATIN = re.compile(r"[A-Za-z]")
URL = re.compile(r"https?://|www\.|\.com|\.jp/|LINE\s*(ID|追加)|ライン追加|公式LINE|副業|稼げ|投資で|ビットコイン|お金配り|DM\s*(ください|して)", re.I)
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
# comment cảm ơn/khen ngắn thuần tuý → template, không cần LLM (spec mục 35/78)
GRATITUDE = re.compile(r"^(いつも)?(ありがとう(ございます|ございました)?|感謝(です|します)?|良い(動画|お話)でした|いい(動画|話)(でした|ですね)?|"
                       r"勉強になりました|泣けました|感動しました|素晴らしい(です|動画)?|最高(です)?|面白かった(です)?|参考になりました)[。！!．.\s]*$")


def japanese_ratio(text: str) -> float:
    t = re.sub(r"\s", "", text or "")
    if not t:
        return 0.0
    return len(JA.findall(t)) / len(t)


def prefilter(c: dict) -> tuple[str | None, str]:
    """→ (nhãn, lý do). nhãn: OWNER | SPAM | NOT_JA | GRATITUDE_SHORT | None (đi tiếp sang classifier)."""
    text = (c.get("text") or "").strip()
    if c.get("is_owner"):
        return "OWNER", "comment của chính kênh"
    if not text:
        return "NOT_JA", "rỗng"
    if URL.search(text) or len(EMOJI.findall(text)) >= 5:
        return "SPAM", "url/quảng cáo/emoji dày"
    jr = japanese_ratio(text)
    if jr < 0.3 and len(text) >= 4:
        return "NOT_JA", f"tỉ lệ kana/kanji {jr:.2f}"
    if len(text) <= 30 and GRATITUDE.match(text):
        return "GRATITUDE_SHORT", "khớp pool cảm ơn ngắn"
    return None, ""
