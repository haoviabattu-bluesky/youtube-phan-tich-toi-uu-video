"""judge.py — Japanese Quality Judge 11 tiêu chí (spec mục L-B), model khác họ với generator."""
from dataclasses import dataclass, field

from .llm import parse_json

CRITERIA = ["1_natural_japanese", "2_polite", "3_not_rude_to_seniors", "4_not_condescending", "5_not_argumentative", "6_relevant_to_comment",
            "7_not_ai_sounding", "8_no_unneeded_assertion", "9_cta_not_awkward", "10_no_fabricated_owner_identity", "11_no_fabricated_video_content"]


@dataclass
class JudgeResult:
    passed: bool = False
    fails: list = field(default_factory=list)
    reasons: list = field(default_factory=list)
    reply_conf: float = 0.0
    fix: str = ""
    model: str = ""
    provider: str = ""
    raw: str = ""
    parse_ok: bool = False
    warnings: list = field(default_factory=list)

    def to_dict(self):
        return {"passed": self.passed, "fails": self.fails, "warnings": self.warnings, "reasons": self.reasons, "reply_conf": self.reply_conf,
                "fix": self.fix, "model": self.model, "provider": self.provider, "parse_ok": self.parse_ok}


HARD = {"2_polite", "3_not_rude_to_seniors", "4_not_condescending", "5_not_argumentative", "6_relevant_to_comment",
        "8_no_unneeded_assertion", "10_no_fabricated_owner_identity", "11_no_fabricated_video_content", "1_natural_japanese"}


def soften(jr: "JudgeResult", footer: str) -> str:
    """Hiệu chỉnh đo thật 2026-10-05 (sol chấm 5/8 draft FAIL chỉ vì 7 'AI っぽい' hoặc 9 CTA):
    - 9 FAIL → BỎ footer (giữ thân), coi như đạt tiêu chí 9.
    - 7 FAIL đơn lẻ (không kèm tiêu chí cứng) và reply_conf ≥ 0.70 → giữ làm cảnh báo, không chặn.
    Trả footer mới; sửa jr tại chỗ."""
    if "9_cta_not_awkward" in jr.fails:
        footer = ""
        jr.fails = [f for f in jr.fails if f != "9_cta_not_awkward"]
        jr.reasons.append("[soften] footer removed per criterion 9")
    if jr.fails and not (set(jr.fails) & HARD) and jr.reply_conf >= 0.70:
        jr.reasons.append(f"[soften] soft-only fails kept as warning: {jr.fails}")
        jr.warnings = list(jr.fails)
        jr.fails = []
    jr.passed = jr.parse_ok and not jr.fails
    return footer


def build_user(comment: dict, vctx_text: str, cls, body: str, footer: str, thread: str) -> str:
    return (f"## Video context\n{vctx_text}\n\n## Thread\n{thread or '(single comment)'}\n\n## Viewer comment\n{(comment.get('text') or '').strip()}\n\n"
            f"## Category: {cls.primary} (secondary {cls.secondary}) / key_detail_ja: {cls.key_detail_ja or '(none)'}\n\n"
            f"## DRAFT body\n{body}\n\n## Footer that will be appended (judge criterion 9 only; NA if empty)\n{footer or '(none)'}\n\nReturn the JSON only.")


def judge(llm, system: str, comment: dict, vctx_text: str, cls, body: str, footer: str, thread: str, generator_family: str) -> JudgeResult:
    out = llm.judge(system, build_user(comment, vctx_text, cls, body, footer, thread), generator_family, comment_id=comment["comment_id"])
    jr = JudgeResult(model=out.model, provider=out.provider, raw=out.text)
    try:
        d = parse_json(out.text)
    except ValueError:
        jr.reasons = ["judge JSON parse fail"]
        return jr
    jr.parse_ok = True
    crit = d.get("criteria") or {}
    jr.fails = [k for k in CRITERIA if str(crit.get(k, "PASS")).upper() == "FAIL"]
    jr.reasons = [str(r) for r in (d.get("reasons") or [])][:6]
    try:
        jr.reply_conf = max(0.0, min(1.0, float(d.get("reply_confidence", 0))))
    except (TypeError, ValueError):
        jr.reply_conf = 0.0
    jr.fix = str(d.get("suggested_fix_ja", ""))[:120]
    jr.passed = not jr.fails
    return jr
