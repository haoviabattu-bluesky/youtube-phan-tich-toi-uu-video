"""viet_reply.py — nhờ sol (gpt-5.6-sol) hoặc gemini viết PHẦN THÂN reply ngắn cho 1 bình luận. KHÔNG dùng Claude (anh hết quota 2026-10-22).

  py -3.13 E:\\CLAUDE\\YOUTUBE\\PHAN_TICH_TOI_UU_VIDEO\\comment_care\\tools\\viet_reply.py --channel F --draft-id 120 --n 3
  py -3.13 ...\\tools\\viet_reply.py --channel F --draft-id 120 --model gemini
  py -3.13 ...\\tools\\viet_reply.py --channel F --comment "コメント本文" --title "動画タイトル"

In ra từng phương án + số ký tự + kết quả tự kiểm luật (reply_rules). Chưa có câu xin like/đăng ký — người dùng tự gắn.
Không ghi gì vào DB / không đăng gì.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from comment_care.config import get_channel, load_settings  # noqa: E402
from comment_care.context import VideoContext  # noqa: E402
from comment_care.llm import LLM  # noqa: E402
from comment_care.reply_rules import BODY_MAX, body_fails, ja_len  # noqa: E402
from comment_care.store import Store  # noqa: E402

SYSTEM = """あなたはYouTubeチャンネル「{name}」の運営者です。主な視聴者: {audience}
視聴者のコメントへの返信本文を{n}通り書いてください。

ルール:
- 1案 = 1〜2文、{max}文字以内。普通の人が書くように短く。
- 中身は (A) 共感・受け止め か (B) 誰でも確かめられる一般的な知識での、やわらかい別の見方 のどちらか一つ ＋ 短いお礼。
- 引用禁止: コメントの言葉・動画のタイトルやセリフ・ことわざ・名言を繰り返さない、「」で囲まない。自分の言葉で言い換える。
- 数字・金額・制度・法律・薬・病気の説明をしない。助言・断定をしない。運営者自身の話(「私も」など)をしない。
- 「！」「w」、絵文字、@、リンク、英語、高評価・チャンネル登録のお願いは書かない。
- {n}案はそれぞれ違う書き出しにする。

出力: 返信本文だけを1行に1案ずつ、番号や記号を付けずに{n}行。"""


def load_ctx(store, draft_id):
    r = store.one("""SELECT c.text, v.title, v.description_head, v.context_json FROM drafts f JOIN comments c ON c.comment_id=f.comment_id
                     LEFT JOIN videos v ON v.video_id=f.video_id WHERE f.id=?""", draft_id)
    if not r:
        raise SystemExit(f"không có draft {draft_id} trong DB")
    vtext = f"タイトル: {r['title'] or ''}\n説明文(冒頭): {(r['description_head'] or '')[:500]}"
    if r.get("context_json"):
        try:
            vtext = VideoContext(**json.loads(r["context_json"])).to_prompt_text(1500)
        except (TypeError, ValueError):
            pass
    return r["text"] or "", r["title"] or "", vtext


def ask(llm, settings, model, system, user):
    order = ["sol", "gemini"] if model == "sol" else ["gemini"] if model == "gemini" else ["sol", "gemini"]
    errs = []
    for who in order:
        try:
            if who == "sol":
                return llm._sol(system, user, 800, "viet_reply", None)
            return llm._gemini_chain(settings["llm"]["generate_cheap_chain"], system, user, 0.6, 800, "viet_reply", None)
        except Exception as e:  # noqa: BLE001 — sol lỗi → tự chuyển gemini
            errs.append(f"{who}: {type(e).__name__} {str(e)[:80]}")
            print(f"  ! {errs[-1]} → thử model tiếp")
    raise SystemExit("sol và gemini đều lỗi → viết tay theo mục 4.2 hoặc chỉ cảm ơn. " + " | ".join(errs))


def main():
    ap = argparse.ArgumentParser(description="Viết phương án reply ngắn bằng sol/gemini (không Claude)")
    ap.add_argument("--channel", required=True)
    ap.add_argument("--draft-id", type=int)
    ap.add_argument("--comment", help="nội dung bình luận (khi không dùng --draft-id)")
    ap.add_argument("--title", default="", help="tiêu đề video (khi không dùng --draft-id)")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--model", choices=["auto", "sol", "gemini"], default="auto")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    s = load_settings()
    ch = get_channel(a.channel)
    if a.draft_id:
        comment, title, vtext = load_ctx(Store(s["paths"]["state_db"]), a.draft_id)
    elif a.comment:
        comment, title, vtext = a.comment, a.title, f"タイトル: {a.title}"
    else:
        raise SystemExit("cần --draft-id hoặc --comment")
    n = max(1, min(a.n, 5))
    system = SYSTEM.format(name=ch.channel_name, audience=ch.audience, n=n, max=BODY_MAX)
    user = f"## 動画\n{vtext}\n\n## 返信するコメント\n{comment.strip()}\n"
    out = ask(LLM(s), s, a.model, system, user)
    lines = [re.sub(r"^\s*(?:\d+[.)．、]|[-・*●])\s*", "", ln).strip().strip("「」\"") for ln in out.text.splitlines()]
    lines = [ln for ln in lines if ln][:n]
    print(f"model: {out.model} ({out.provider})  ·  bình luận: {comment.strip()[:60]}")
    for i, ln in enumerate(lines, 1):
        fails = body_fails(ln, comment, title)
        print(f"[{i}] {ln}")
        print(f"     {ja_len(ln)} ký tự · {'✓ đạt luật' if not fails else '✗ ' + ', '.join(fails)}")
    print("\nNhớ: tự soát lại mục 0 + 4.2, rồi tự gắn 1 câu xin like/đăng ký (trừ chuyện buồn/bệnh/chửi).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
