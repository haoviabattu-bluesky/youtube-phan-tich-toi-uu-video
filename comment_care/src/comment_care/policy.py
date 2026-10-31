"""policy.py — Policy Engine deterministic (spec mục G). LLM không có đường nào ghi đè bảng này."""
from dataclasses import dataclass
from pathlib import Path

import yaml

LLM_GENERATORS = ("LLM_STRONG", "LLM_CHEAP")


@dataclass
class Decision:
    decision: str            # REPLY | SKIP | ESCALATE | NO_REPLY_NEEDED | ALREADY_HANDLED
    risk: str = "LOW"
    generator: str = "NONE"  # TEMPLATE | LLM_STRONG | LLM_CHEAP | NONE
    footer: str = "no"       # yes | no (sau khi áp footer_policy của kênh)
    template_key: str | None = None
    length: tuple = (10, 200)
    reason: str = ""
    auto_phase: int = 99
    double_judge: bool = False
    policy_version: str = "v1"
    category: str = "UNCLEAR"


class Policy:
    def __init__(self, path: Path):
        self.t = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        self.version = str(self.t.get("policy_version", "v1"))
        self.th = self.t["thresholds"]
        self.cats = self.t["categories"]
        self.order = self.t.get("risk_order", ["LOW", "MEDIUM", "HIGH"])

    def _risk_max(self, *risks):
        return max((r for r in risks if r in self.order), key=self.order.index, default="LOW")

    def decide(self, cls, kind: str, context_level: str, bot_replies_in_thread: int, ch, prefilter_label: str | None = None) -> Decision:
        pv = self.version
        if prefilter_label == "OWNER":
            return Decision("ALREADY_HANDLED", reason="owner comment", policy_version=pv, category="OFF_TOPIC")
        if prefilter_label == "SPAM":
            return Decision("NO_REPLY_NEEDED", reason="prefilter spam", policy_version=pv, category="SPAM_PROMO")
        if prefilter_label == "NOT_JA":
            return Decision("SKIP", risk="HIGH", reason="not_japanese", policy_version=pv, category="UNCLEAR")
        cat = cls.primary
        row = dict(self.cats.get(cat) or self.cats["UNCLEAR"])
        # YAML đọc `yes`/`no` thành True/False → chuẩn hoá về chuỗi
        d = Decision(row["decision"], risk=row.get("risk", "LOW"), generator=row.get("generator", "NONE"),
                     footer="yes" if row.get("footer") in (True, "yes") else "no", template_key=row.get("template_key"), length=tuple(row.get("length", (10, 200))),
                     reason=row.get("reason", ""), auto_phase=int(row.get("auto_phase", 99)), double_judge=bool(row.get("double_judge", False)),
                     policy_version=pv, category=cat)
        # secondary nâng risk
        for s in cls.secondary:
            d.risk = self._risk_max(d.risk, (self.cats.get(s) or {}).get("risk", "LOW"))
            if s in ("GRIEF_LOSS", "HEALTH_SHARING", "CRISIS"):
                d.footer = "no"
                d.double_judge = True
            if s == "CRISIS":
                return Decision("ESCALATE", risk="HIGH", reason="crisis_signal (secondary)", policy_version=pv, category=cat)
        # flags
        fl = cls.flags or {}
        u_conf = cls.u_conf
        if fl.get("sarcasm_possible"):
            u_conf = min(u_conf, float(self.t["flag_overrides"]["sarcasm_possible"]["max_understanding_conf"]))
        if fl.get("not_japanese"):
            return Decision("SKIP", risk="HIGH", reason="not_japanese", policy_version=pv, category=cat)
        if fl.get("asks_question_factual") and d.decision == "REPLY":
            return self._thanks("can_fact_check (flag)", cat)
        if d.decision in ("SKIP", "ESCALATE", "NO_REPLY_NEEDED"):
            return d
        # confidence gate
        if cls.c_conf < float(self.th["skip_below"]) or u_conf < float(self.th["skip_below"]):
            if cat in self.t.get("sensitive_fallback_categories", []):
                # anh chốt 2026-10-15: câu nhạy cảm không hiểu chắc → không bỏ qua, đăng câu cố định SENSITIVE
                return Decision("REPLY", risk="MEDIUM", generator="TEMPLATE", footer="no", template_key="SENSITIVE", length=(10, 50),
                                reason=f"sensitive_fallback c={cls.c_conf:.2f} u={u_conf:.2f}", auto_phase=99, policy_version=pv, category=cat)
            if self.t.get("low_confidence_template"):
                # 2026-10-22 HUONG_DAN_HERMES: khó/không chắc → chỉ cảm ơn, không bỏ qua
                return self._thanks(f"low_confidence c={cls.c_conf:.2f} u={u_conf:.2f}", cat)
            return Decision("SKIP", risk="HIGH", reason=f"low_confidence c={cls.c_conf:.2f} u={u_conf:.2f}", policy_version=pv, category=cat)
        # follow-up: tối đa 1 reply bot / thread
        if cat == "FOLLOW_UP_TO_OWNER" and bot_replies_in_thread >= int(row.get("max_bot_replies_per_thread", 1)):
            return Decision("ESCALATE", risk="MEDIUM", reason="thread đã có reply của bot", policy_version=pv, category=cat)
        # LLM generation bắt buộc có context video (yêu cầu anh 2026-10-05)
        if d.generator in LLM_GENERATORS and context_level in ("NONE", ""):
            return Decision("SKIP", risk="HIGH", reason="no_video_context", policy_version=pv, category=cat)
        # footer theo policy kênh
        if ch.footer_policy in ("A", "C"):
            d.footer = "yes"
        return d

    def _thanks(self, reason, cat) -> Decision:
        """Chỉ một lời cảm ơn cố định (template THANKS), không footer, không bao giờ tự gửi."""
        return Decision("REPLY", risk="HIGH", generator="TEMPLATE", footer="no", template_key=self.t.get("low_confidence_template") or "THANKS",
                        length=(8, 50), reason=reason, auto_phase=99, policy_version=self.version, category=cat)

    def gate(self, d: Decision, cls, reply_conf: float, judge_pass: bool, ch, sent_today: int) -> str:
        """→ SEND | DRAFT | SKIP (chỉ có ý nghĩa ở mode auto_*; mode khác luôn DRAFT)."""
        if d.decision != "REPLY" or not judge_pass:
            return "SKIP" if d.decision != "REPLY" else "DRAFT"
        if sent_today >= ch.daily_cap:
            return "DRAFT"
        conf = min(cls.c_conf, cls.u_conf, reply_conf)
        if d.category == "HOSTILE":
            return "SEND" if (ch.mode == "auto_full" and cls.c_conf >= 0.90) else "DRAFT"
        if d.risk == "LOW" and ch.mode in ("auto_low", "auto_full") and conf >= max(float(self.th["auto_low"]), ch.min_confidence_auto):
            return "SEND"
        if d.risk == "MEDIUM" and ch.mode == "auto_full" and conf >= float(self.th["auto_medium"]):
            return "SEND"
        return "DRAFT"
