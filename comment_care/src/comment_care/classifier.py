"""classifier.py — bước HIỂU + PHÂN LOẠI (LLM rẻ, JSON cố định). Output chỉ là gợi ý cho policy engine."""
from dataclasses import dataclass, field

from .llm import parse_json

CATEGORIES = ["GRATITUDE_SIMPLE", "PRAISE", "EXPERIENCE_SHARING", "EMOTIONAL_SHARING", "GRIEF_LOSS", "AGREEMENT", "DISAGREEMENT_POLITE",
              "CRITICISM_CONSTRUCTIVE", "QUESTION_OPINION", "QUESTION_FACTUAL", "REQUEST", "HEALTH_SHARING", "FINANCIAL_SPECIFIC", "CRISIS",
              "POLITICAL_SOCIAL", "HOSTILE", "SPAM_PROMO", "OFF_TOPIC", "VIEWER_TO_VIEWER", "FOLLOW_UP_TO_OWNER", "UNCLEAR"]
FLAG_KEYS = ["mentions_age", "mentions_money", "contains_url", "contains_pii", "not_japanese", "sarcasm_possible", "asks_question",
             "asks_question_factual", "addresses_owner_directly", "emoji_used", "role_ambiguous"]


@dataclass
class Classification:
    primary: str = "UNCLEAR"
    secondary: list = field(default_factory=list)
    flags: dict = field(default_factory=dict)
    summary_ja: str = ""
    key_detail_ja: str = ""
    viewer_intent: str = "other"
    c_conf: float = 0.0
    u_conf: float = 0.0
    notes: str = ""
    model: str = ""
    provider: str = ""
    raw: str = ""


def from_row(r: dict) -> Classification:
    """Dựng lại Classification từ dòng DB (tái dùng, không gọi LLM lần 2)."""
    import json
    return Classification(primary=r["primary_cat"], secondary=json.loads(r.get("secondary_cats") or "[]"), flags=json.loads(r.get("flags_json") or "{}"),
                          summary_ja=r.get("summary_ja") or "", key_detail_ja=r.get("key_detail_ja") or "", viewer_intent=r.get("viewer_intent") or "other",
                          c_conf=float(r.get("classification_conf") or 0), u_conf=float(r.get("understanding_conf") or 0), notes=r.get("notes") or "",
                          model=r.get("model") or "", provider=r.get("provider") or "")


def _clip(x, lo=0.0, hi=1.0):
    try:
        return max(lo, min(hi, float(x)))
    except (TypeError, ValueError):
        return 0.0


def thread_text(top: dict | None, replies: list[dict], current_id: str, max_chars=1500) -> str:
    """Dựng văn bản thread theo thứ tự thời gian, đánh dấu [運営者] / [視聴者] / [このコメント]."""
    lines = []
    for c in ([top] if top else []) + list(replies):
        if not c:
            continue
        who = "運営者" if c.get("is_owner") else "視聴者"
        mark = " ←このコメント" if c["comment_id"] == current_id else ""
        lines.append(f"[{who}]{mark} {str(c.get('text', '')).strip()[:400]}")
    return "\n".join(lines)[:max_chars]


def build_user_prompt(comment: dict, kind: str, thread: str, video_ctx_text: str) -> str:
    return (f"## 動画の文脈\n{video_ctx_text}\n\n## スレッド({'返信' if kind == 'follow_up' else 'トップレベル'})\n{thread or '(単独コメント)'}\n\n"
            f"## 分析対象のコメント\n{(comment.get('text') or '').strip()}\n\n"
            f"投稿日: {comment.get('published_at')} / いいね: {comment.get('like_count', 0)} / 種別: {kind}\nJSONのみを返してください。")


def classify(llm, system: str, comment: dict, kind: str, thread: str, video_ctx_text: str) -> Classification:
    user = build_user_prompt(comment, kind, thread, video_ctx_text)
    out = llm.classify(system, user, comment_id=comment["comment_id"])
    cls = Classification(model=out.model, provider=out.provider, raw=out.text)
    try:
        d = parse_json(out.text)
    except ValueError:
        # thử lại 1 lần với nhắc JSON
        out = llm.classify(system, user + "\n\n(前回の出力はJSONとして読めませんでした。JSONオブジェクトのみを返してください。)", comment_id=comment["comment_id"])
        cls.model, cls.provider, cls.raw = out.model, out.provider, out.text
        try:
            d = parse_json(out.text)
        except ValueError:
            cls.notes = "JSON parse fail x2"
            return cls
    p = str(d.get("primary", "")).strip().upper()
    cls.primary = p if p in CATEGORIES else "UNCLEAR"
    cls.secondary = [s for s in (d.get("secondary") or []) if isinstance(s, str) and s.upper() in CATEGORIES and s.upper() != cls.primary][:2]
    cls.secondary = [s.upper() for s in cls.secondary]
    fl = d.get("flags") or {}
    cls.flags = {k: bool(fl.get(k, False)) for k in FLAG_KEYS}
    cls.summary_ja = str(d.get("summary_ja", ""))[:120]
    cls.key_detail_ja = str(d.get("key_detail_ja", ""))[:60]
    cls.viewer_intent = str(d.get("viewer_intent", "other"))[:20]
    cls.c_conf = _clip(d.get("classification_confidence"))
    cls.u_conf = _clip(d.get("understanding_confidence"))
    cls.notes = str(d.get("notes", ""))[:200]
    if cls.flags.get("role_ambiguous"):
        cls.u_conf = min(cls.u_conf, 0.5)   # không rõ ai là thủ phạm/nạn nhân → không bao giờ soạn (luật mục 9)
    # kind='answer' (viewer trả lời câu hỏi ghim của kênh) giữ nguyên category như top-level
    if kind == "follow_up" and cls.flags.get("addresses_owner_directly", True) \
            and cls.primary not in ("HOSTILE", "SPAM_PROMO", "CRISIS", "UNCLEAR", "VIEWER_TO_VIEWER"):
        if "FOLLOW_UP_TO_OWNER" not in cls.secondary:
            cls.secondary = [cls.primary] + cls.secondary[:1]
        cls.primary = "FOLLOW_UP_TO_OWNER"
    return cls
