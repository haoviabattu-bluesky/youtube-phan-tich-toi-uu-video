# -*- coding: utf-8 -*-
"""Unit test policy engine + rule QC + templates + prefilter (acceptance CASE 1/3/9/10/13/14 — không gọi LLM, không gọi API).
Chạy: py -3.13 -m unittest discover -s E:\\CLAUDE\\YOUTUBE\\PHAN_TICH_TOI_UU_VIDEO\\comment_care\\tests -v
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from comment_care.classifier import Classification  # noqa: E402
from comment_care.config import POLICY_DIR, TEMPLATES_DIR, load_channels, get_channel, load_settings  # noqa: E402
from comment_care.policy import Policy  # noqa: E402
from comment_care.prefilter import prefilter  # noqa: E402
from comment_care.qc_rules import RuleQC  # noqa: E402
from comment_care.templates import Templates  # noqa: E402
from comment_care import sender  # noqa: E402

POL = Policy(POLICY_DIR / "policy_table.yaml")
TPL = Templates(TEMPLATES_DIR / "templates.yaml", seed=1)
QC = RuleQC(POLICY_DIR / "blocklist_ja.txt", ["人生の夕暮れ", "健康の知恵袋"])
CH = get_channel("F")


def cls(primary, c=0.95, u=0.95, **k):
    x = Classification(primary=primary, c_conf=c, u_conf=u)
    for a, b in k.items():
        setattr(x, a, b)
    return x


class TestConfig(unittest.TestCase):
    def test_channels_load_and_pilot(self):
        chans = load_channels()
        self.assertTrue(any(c.lane == "F" and c.enabled for c in chans))
        self.assertFalse(any(c.lane == "Satori" and c.enabled for c in chans), "kênh bị đình chỉ phải tắt")
        self.assertEqual(CH.footer_policy, "BC")


class TestPolicy(unittest.TestCase):
    def test_case1_single_word_unclear(self):
        d = POL.decide(cls("UNCLEAR", 0.3, 0.3), "top", "L3", 0, CH)
        self.assertEqual(d.decision, "SKIP")

    def test_low_confidence_skips(self):
        d = POL.decide(cls("EXPERIENCE_SHARING", 0.6, 0.9), "top", "L3", 0, CH)
        self.assertEqual(d.decision, "SKIP")
        self.assertIn("low_confidence", d.reason)

    def test_case3_hostile_template_no_footer(self):
        d = POL.decide(cls("HOSTILE"), "top", "L3", 0, CH)
        self.assertEqual((d.decision, d.generator, d.footer), ("REPLY", "TEMPLATE", "no"))
        self.assertEqual(TPL.render("HOSTILE")[0], "ご意見をお寄せいただき、ありがとうございます。")

    def test_case4_factual_skip(self):
        self.assertEqual(POL.decide(cls("QUESTION_FACTUAL"), "top", "L3", 0, CH).decision, "SKIP")
        d = POL.decide(cls("EXPERIENCE_SHARING", flags={"asks_question_factual": True}), "top", "L3", 0, CH)
        self.assertEqual(d.decision, "SKIP")

    def test_crisis_escalates_even_as_secondary(self):
        self.assertEqual(POL.decide(cls("CRISIS"), "top", "L3", 0, CH).decision, "ESCALATE")
        self.assertEqual(POL.decide(cls("EXPERIENCE_SHARING", secondary=["CRISIS"]), "top", "L3", 0, CH).decision, "ESCALATE")

    def test_grief_secondary_raises_risk_and_drops_footer(self):
        d = POL.decide(cls("EXPERIENCE_SHARING", secondary=["GRIEF_LOSS"]), "top", "L3", 0, CH)
        self.assertEqual((d.risk, d.footer, d.double_judge), ("HIGH", "no", True))

    def test_llm_requires_video_context(self):
        d = POL.decide(cls("EXPERIENCE_SHARING"), "top", "NONE", 0, CH)
        self.assertEqual((d.decision, d.reason), ("SKIP", "no_video_context"))
        self.assertEqual(POL.decide(cls("GRATITUDE_SIMPLE"), "top", "NONE", 0, CH).decision, "REPLY")

    def test_follow_up_max_one_bot_reply(self):
        # anh 2026-10-08: khách trả lời lại reply của mình → được đáp thêm 1 lần (tối đa 2 reply bot/thread), vẫn xin like/đăng ký
        self.assertEqual(POL.decide(cls("FOLLOW_UP_TO_OWNER"), "follow_up", "L3", 2, CH).decision, "ESCALATE")
        d = POL.decide(cls("FOLLOW_UP_TO_OWNER"), "follow_up", "L3", 1, CH)
        self.assertEqual((d.decision, d.footer), ("REPLY", "yes"))

    def test_gate_never_sends_in_draft_mode(self):
        d = POL.decide(cls("GRATITUDE_SIMPLE"), "top", "L1", 0, CH)
        self.assertEqual(POL.gate(d, cls("GRATITUDE_SIMPLE"), 0.95, True, CH, 0), "DRAFT")  # CH.mode = draft_only

    def test_gate_high_risk_never_auto(self):
        auto = type(CH)(**{**CH.__dict__, "mode": "auto_full"})
        d = POL.decide(cls("GRIEF_LOSS"), "top", "L3", 0, auto)
        self.assertEqual(POL.gate(d, cls("GRIEF_LOSS"), 0.99, True, auto, 0), "DRAFT")
        d2 = POL.decide(cls("GRATITUDE_SIMPLE"), "top", "L3", 0, auto)
        self.assertEqual(POL.gate(d2, cls("GRATITUDE_SIMPLE"), 0.95, True, auto, 0), "SEND")
        self.assertEqual(POL.gate(d2, cls("GRATITUDE_SIMPLE"), 0.95, True, auto, auto.daily_cap), "DRAFT")


class TestQC(unittest.TestCase):
    def dec(self, cat="EXPERIENCE_SHARING"):
        return POL.decide(cls(cat), "top", "L3", 0, CH)

    def test_case9_vietnamese_fails(self):
        self.assertTrue(any("vietnamese" in f or "japanese_only" in f for f in QC.check("Cảm ơn bạn đã chia sẻ。", "", self.dec(), [], [])))

    def test_case10_condescending_blocked(self):
        f = QC.check("あなたは動画を理解していないようですね。もう少し勉強してください。", "", self.dec(), [], [])
        self.assertTrue(any(x.startswith("blocklist") for x in f))

    def test_identity_claim_blocked(self):
        f = QC.check("私も65歳で退職しましたので、お気持ちがよく分かります。穏やかな日々が続きますように。", "", self.dec(), [], [])
        self.assertTrue(any(x.startswith("blocklist") for x in f))

    def test_good_reply_passes(self):
        body = "お話を聞かせていただき、ありがとうございます。再雇用で三年間働かれたご経験、とても考えさせられました。無理のない働き方を見つけられたとのこと、何よりかと思います。どうかお身体を大切にお過ごしください。"
        self.assertEqual(QC.check(body, "", self.dec(), TPL.all_footer_texts(), []), [])

    def test_other_channel_name_blocked(self):
        f = QC.check("人生の夕暮れをご覧いただきありがとうございます。穏やかな日々が続きますように。", "", self.dec("PRAISE"), [], [])
        self.assertTrue(any("other_channel" in x for x in f))

    def test_emoji_and_internal_text(self):
        f = QC.check("コメントありがとうございます😊 CATEGORY: PRAISE", "", self.dec("PRAISE"), [], [])
        self.assertTrue({"emoji", "internal_text"} <= set(f))


class TestTemplates(unittest.TestCase):
    def test_case14_no_repeat_combo(self):
        seen = []
        for _ in range(12):
            t, combo = TPL.render("GRATITUDE_SIMPLE", avoid_combos=seen)
            self.assertNotIn(combo, seen)
            seen.append(combo)
            self.assertEqual(QC.check(t, "", POL.decide(cls("GRATITUDE_SIMPLE"), "top", "L1", 0, CH), [], []), [])

    def test_footer_policy_matrix(self):
        self.assertEqual(TPL.footer("BC", "no", "vid", False), "")
        self.assertIn(TPL.footer("BC", "yes", "vid", False), TPL.all_footer_texts()[1:])
        self.assertIn("チャンネル登録", TPL.footer("BC", "yes", "vid", True))
        self.assertIn("高評価", TPL.footer("A", "no", "vid", False))

    def test_criticism_detail_slot(self):
        t, _ = TPL.render("CRITICISM_CONSTRUCTIVE", detail="音声の聞き取りづらさ")
        self.assertIn("音声の聞き取りづらさの点は、", t)
        t2, _ = TPL.render("CRITICISM_CONSTRUCTIVE", detail="")
        self.assertNotIn("の点は、", t2)


class TestPrefilter(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(prefilter({"text": "x", "is_owner": True})[0], "OWNER")
        self.assertEqual(prefilter({"text": "ありがとうございます。"})[0], "GRATITUDE_SHORT")
        self.assertEqual(prefilter({"text": "副業で稼げます LINE追加 https://x.com"})[0], "SPAM")
        self.assertEqual(prefilter({"text": "Great video thanks a lot"})[0], "NOT_JA")
        self.assertIsNone(prefilter({"text": "再雇用3年で精神を少し病み退職しました。"})[0])


class TestKillSwitch(unittest.TestCase):
    def test_case13_send_blocked_by_default(self):
        s = load_settings()
        auto = type(CH)(**{**CH.__dict__, "mode": "auto_low"})
        ok, why = sender.can_send(auto, s, cli_send=True, dry_run=False)
        self.assertFalse(ok)  # env không set → chặn
        ok, why = sender.can_send(auto, s, cli_send=False, dry_run=False)
        self.assertFalse(ok)
        ok, why = sender.can_send(CH, s, cli_send=True, dry_run=False)
        self.assertFalse(ok)  # mode draft_only


if __name__ == "__main__":
    unittest.main()
