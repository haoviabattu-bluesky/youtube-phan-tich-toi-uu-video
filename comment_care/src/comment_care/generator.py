"""generator.py — soạn thân reply bằng LLM theo tier (spec mục K). Footer KHÔNG do model viết."""
import json

# 2026-10-22 HUONG_DAN_HERMES: mọi nhóm 1–2 câu, ≤50 ký tự, không trích dẫn, không câu kết rập khuôn
CATEGORY_RULES = {
    "EXPERIENCE_SHARING": "話してくれたことへの共感を一言＋お礼。評価・助言しない。1〜2文。",
    "EMOTIONAL_SHARING": "気持ちを決めつけず、短く受け止める＋お礼。助言しない。1〜2文。",
    "GRIEF_LOSS": "短く静かに受け止める＋お話ししてくださったことへのお礼。「頑張って」「元気を出して」「お気持ちは分かります」は禁止。2文まで。",
    "DISAGREEMENT_POLITE": "相手の考えを一つの見方として認める＋お礼。言い返さない。一般的に知られている別の見方を一言添えてもよい。1〜2文。",
    "QUESTION_OPINION": "答えを押しつけない。「人それぞれ」の趣旨＋質問へのお礼。1〜2文。",
    "HEALTH_SHARING": "診断・原因・治療・薬に触れない。共有へのお礼と、短い気づかいのみ。2文まで。",
    "FOLLOW_UP_TO_OWNER": "再返信。前と同じお礼表現を繰り返さない。短く。1〜2文。",
    "PRAISE": "お礼と励みになる旨のみ。1〜2文。",
    "CRITICISM_CONSTRUCTIVE": "指摘へのお礼と「参考にします」の趣旨のみ。弁明しない。1〜2文。",
}


def build_system(tpl: str, ch, style_guide: str, vctx_text: str, cls, length: tuple) -> str:
    owner = json.dumps(ch.owner_facts, ensure_ascii=False) if ch.owner_facts else "(なし)"
    rule = CATEGORY_RULES.get(cls.primary, "1〜2文。")
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
