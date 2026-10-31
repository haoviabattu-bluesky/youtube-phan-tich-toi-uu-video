"""generator.py — soạn thân reply bằng LLM theo tier (spec mục K). Footer KHÔNG do model viết."""
import json

CATEGORY_RULES = {
    "EXPERIENCE_SHARING": "構成: 感謝 → 視聴者が書いた具体的な一点に触れる → 評価せず受け止める → 共感。1〜2文、短く。",
    "EMOTIONAL_SHARING": "お気持ちを決めつけず、書かれた言葉だけを受け止める。助言しない。1〜2文。",
    "GRIEF_LOSS": "短く、静かに。「頑張って」「元気を出して」「お気持ちは分かります」は禁止。慰めを重ねない。最後は「どうかご無理をなさらず、お身体を大切にお過ごしください」の趣旨で。2文まで。",
    "DISAGREEMENT_POLITE": "相手の考え方を一つの見方として認め、動画の立場を押しつけない。反論しない。「そうした考え方もありますね」の趣旨。1〜2文。",
    "QUESTION_OPINION": "断定の助言はしない。「状況は人それぞれ」「ご自身の生活や体調、収入を踏まえて」の趣旨で、答えを押しつけない。質問へのお礼を添える。2〜3文。",
    "HEALTH_SHARING": "診断・原因・治療・薬について一切触れない。共有への感謝と、お身体を気遣う言葉のみ。必要なら「専門の窓口にご相談されるのも一つかと思います」と中立に。2文まで。",
    "FOLLOW_UP_TO_OWNER": "すでに運営者が一度返信しているスレッドへの再返信。短く、同じ感謝表現を繰り返さない。議論を広げない。1〜2文。",
    "PRAISE": "1〜2文。お礼と励みになる旨のみ。",
    "CRITICISM_CONSTRUCTIVE": "指摘への感謝と「参考にします」の趣旨のみ。弁明しない。1〜2文。",
}


def build_system(tpl: str, ch, style_guide: str, vctx_text: str, cls, length: tuple) -> str:
    owner = json.dumps(ch.owner_facts, ensure_ascii=False) if ch.owner_facts else "(なし)"
    rule = CATEGORY_RULES.get(cls.primary, "1〜3文。")
    return (tpl.replace("{channel_name}", ch.channel_name).replace("{audience}", getattr(ch, "audience", "60〜80代の日本人")).replace("{style_guide}", style_guide).replace("{owner_facts}", owner)
            .replace("{video_context}", vctx_text or "(タイトルのみ)").replace("{category}", cls.primary)
            .replace("{summary_ja}", cls.summary_ja or "-").replace("{key_detail_ja}", cls.key_detail_ja or "(なし)")
            .replace("{length_rule}", f"{length[0]}〜{length[1]}文字(フッター除く)").replace("{category_rule}", rule))


def build_user(comment: dict, thread: str, recent_openings: list[str], feedback: str | None) -> str:
    u = f"## スレッド\n{thread or '(単独コメント)'}\n\n## 返信するコメント\n{(comment.get('text') or '').strip()}\n"
    if recent_openings:
        u += "\n## 最近この動画で使った書き出し(同じ書き出しを避けること)\n" + "\n".join(f"- {o}" for o in recent_openings[:3]) + "\n"
    if feedback:
        u += f"\n## 前回の下書きへの指摘(必ず直すこと)\n{feedback}\n"
    u += "\n返信本文の日本語のみを出力してください。"
    return u


def clean_body(text: str) -> str:
    t = (text or "").strip().strip('"「」『』')
    # bỏ dòng label lọt ra ngoài
    lines = [ln.strip() for ln in t.splitlines()]
    lines = [ln for ln in lines if ln and not ln.lower().startswith(("返信", "reply", "本文", "category", "json"))]
    t = "\n".join(lines)
    t = t.replace("!", "。").replace("！", "。").replace("。。", "。")
    return t.strip()


def openings(texts: list[str]) -> list[str]:
    return [t.split("。")[0][:20] for t in texts if t]


def generate(llm, tpl_system: str, ch, style_guide: str, vctx_text: str, cls, dec, comment: dict, thread: str,
             recent_texts: list[str], feedback: str | None = None):
    tier = "strong" if dec.generator == "LLM_STRONG" else "cheap"
    system = build_system(tpl_system, ch, style_guide, vctx_text, cls, dec.length)
    user = build_user(comment, thread, openings(recent_texts), feedback)
    out = llm.generate(system, user, tier=tier, comment_id=comment["comment_id"])
    return clean_body(out.text), out
