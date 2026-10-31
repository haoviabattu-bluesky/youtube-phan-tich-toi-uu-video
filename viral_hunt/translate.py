# -*- coding: utf-8 -*-
"""translate.py — dịch MỌI chuỗi tiếng Nhật sang tiếng Việt (luật anh chốt 2026-10-19).

Luật: trong báo cáo/chat/sheet **không được để tiếng Nhật mà không có nghĩa tiếng Việt**.
Bản Nhật gốc vẫn phải giữ (máy 1 dùng để đăng video), nhưng luôn kèm bản dịch Việt.

Cách làm: gom TẤT CẢ chuỗi cần dịch của cả báo cáo vào 1 call LLM duy nhất, trả JSON
{chuỗi gốc: nghĩa Việt}. Dịch theo lô để không tốn nhiều call; nếu lô nào lỗi thì các chuỗi
trong lô đó để trống bản dịch và báo rõ, KHÔNG bịa nghĩa.
"""
import json
import re
import sys

H2DEV_PIPELINE = r"E:\CLAUDE\YOUTUBE\h2dev\pipeline"

SYSTEM = (
    "Bạn là phiên dịch Nhật→Việt cho một kênh YouTube manga faceless. "
    "Dịch CHÍNH XÁC, giữ nguyên sắc thái và con số. "
    "Với tiêu đề video, dịch thành câu tiếng Việt tự nhiên như tiêu đề báo. "
    "Với tên kênh, dịch nghĩa (ví dụ 社会のなぜ研究室 = Phòng nghiên cứu 'vì sao' của xã hội). "
    "Không thêm bình luận, không giải thích."
)

PROMPT = """Dịch các chuỗi tiếng Nhật sau sang tiếng Việt.

Trả về DUY NHẤT một object JSON, khoá là ĐÚNG chuỗi gốc (giữ nguyên 100% ký tự), giá trị là bản dịch tiếng Việt.
Không markdown, không giải thích ngoài JSON.

Danh sách:
{items}"""


def _llm():
    if H2DEV_PIPELINE not in sys.path:
        sys.path.insert(0, H2DEV_PIPELINE)
    # BẪY CHẾT NGƯỜI (đo thật 2026-10-20): Task Scheduler chạy bằng `pythonw.exe` ⇒
    # `sys.stdout` / `sys.stderr` là **None**. `llm_client.py` dòng đầu làm
    # `sys.stdout.reconfigure(encoding="utf-8")` ⇒ AttributeError ⇒ import llm_client CHẾT
    # ⇒ cả 8 đề bài rơi về "khung xương" VÀ toàn bộ tiêu đề Nhật in "chưa dịch được".
    # Chạy tay bằng `py -3.13` thì không thấy lỗi này. Phải độn stream giả trước khi import.
    import io
    for name in ("stdout", "stderr"):
        if getattr(sys, name, None) is None:
            setattr(sys, name, io.TextIOWrapper(io.BytesIO(), encoding="utf-8",
                                                errors="replace", newline=""))
    import llm_client
    return llm_client


JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
# Kênh Thái/Hàn lọt vào bảng (reup manga Nhật) — tên kênh cũng phải có nghĩa Việt.
NON_VIET = re.compile(r"[\u0e00-\u0e7f\uac00-\ud7af]")


def has_jp(s):
    """Có chữ cần dịch không: Nhật (kana/kanji) HOẶC Thái/Hàn."""
    return bool(s) and bool(JP.search(str(s)) or NON_VIET.search(str(s)))


def translate_many(strings, batch=60, timeout=240):
    """{chuỗi Nhật: nghĩa Việt}. Chuỗi không có tiếng Nhật trả về chính nó."""
    uniq = []
    for s in strings:
        s = (s or "").strip()
        if s and s not in uniq:
            uniq.append(s)
    out = {s: s for s in uniq if not has_jp(s)}
    need = [s for s in uniq if has_jp(s)]
    if not need:
        return out

    try:
        lc = _llm()
    except Exception as e:                                    # noqa: BLE001
        for s in need:
            out[s] = ""
        out["_error"] = f"{type(e).__name__}: {e}"
        return out

    for i in range(0, len(need), batch):
        chunk = need[i:i + batch]
        items = "\n".join(f"{n}. {s}" for n, s in enumerate(chunk, 1))
        try:
            r = lc.chat(PROMPT.format(items=items), system=SYSTEM, task="short",
                        max_tokens=6000, temperature=0.2, timeout=timeout, verbose=False)
            txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", (r.text or "").strip(), flags=re.M)
            m = re.search(r"\{.*\}", txt, flags=re.S)
            obj = json.loads(m.group(0)) if m else {}
            for s in chunk:
                v = obj.get(s)
                out[s] = (v or "").strip()
        except Exception as e:                                # noqa: BLE001
            for s in chunk:
                out.setdefault(s, "")
            out["_error"] = f"lô {i // batch + 1}: {type(e).__name__} {str(e)[:100]}"

    # Vòng 2: chuỗi nào LLM bỏ sót (trả JSON thiếu khoá) thì dịch LẠI TỪNG CHUỖI.
    # Đo thật 2026-10-19: lô 44 chuỗi chỉ về 31, 13 chuỗi bị in "chưa dịch được" —
    # gửi 1 chuỗi/lần thì LLM trả đủ. Không được để trần tiếng Nhật (luật anh chốt).
    missing = [s for s in need if not out.get(s)]
    for s in missing:
        try:
            r = lc.chat(PROMPT.format(items="1. " + s), system=SYSTEM, task="short",
                        max_tokens=800, temperature=0.2, timeout=timeout, verbose=False)
            txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", (r.text or "").strip(), flags=re.M)
            m = re.search(r"\{.*\}", txt, flags=re.S)
            obj = json.loads(m.group(0)) if m else {}
            v = obj.get(s) or (list(obj.values())[0] if len(obj) == 1 else "")
            if v:
                out[s] = str(v).strip()
        except Exception:                                     # noqa: BLE001
            pass
    still = [s for s in need if not out.get(s)]
    if still:
        out["_error"] = (out.get("_error", "") +
                         f" | còn {len(still)} chuỗi chưa dịch: {still[:3]}").strip(" |")
    return out
