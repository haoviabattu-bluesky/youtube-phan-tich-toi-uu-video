# -*- coding: utf-8 -*-
"""Chon video dung ngach + KHONG lo mat nguoi that: 1 LENH vision cho ca lo <=12 ung vien.

Loi vision cua h2dev (qc_character._chat: ramclouds -> ns24 -> hhtech -> sol) chi nhan 1 anh/lan
-> ghep thumbnail thanh 1 anh luoi 2 cot, moi o co so vang khop voi so trong danh sach tieu de.
Tra JSON ngan {"ok":[...]} vi bac ramclouds chi cho max_tokens=120.
Vision hong -> tra [] (KHONG xem video chua soi thumbnail: anh chot "tuyet doi khong xem video lo mat").
"""
import io, sys, base64, requests
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
from nw_common import H2DEV

if H2DEV not in sys.path:
    sys.path.insert(0, H2DEV)

W, H = 320, 180
TIMEOUT_S = 120

PROMPT = """You filter YouTube videos for a Japanese YouTube channel.
CHANNEL NICHE: {niche}
SOME TITLES OF THIS CHANNEL:
{examples}

CANDIDATE VIDEOS (number. title | channel | views | length):
{cands}

The image is a vertical strip of the candidates' thumbnails, top to bottom; the yellow box on the LEFT of
each thumbnail holds its candidate number.
Answer TWO separate questions:
A) "real": tiles where ANY photographed real human appears, even partially (face cut off at the edge,
   head, body, hands holding something, a doctor/presenter beside drawings), OR the tile is a real
   photo/footage of people, places, food or objects (vlog, talking head, interview, TV/news, lecture).
   Only a 100% drawn/illustrated/text-graphic tile is NOT real. If unsure -> list it as real.
B) "topic": candidates with the SAME SUBJECT as the channel, not merely the same audience (a
   senior-HEALTH channel rejects retirement-money/job videos and vice versa), in Japanese for
   Japanese viewers.
First name the channel's subject in at most 5 English words.
Reply JSON only: {{"subject":"...","real":[numbers],"topic":[numbers]}}"""


def _font():
    for name in ("arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, 44)
        except Exception:
            pass
    return ImageFont.load_default()


def grid_b64(cands):
    """1 COT doc, so to o LE TRAI ngoai anh. Do that 2026-10-22: luoi 2 cot 12 o -> model gan nham so
    (vlog anh do an that o so 4 bi bo lot, cung anh do o bo 7 thi bat dung)."""
    m = 90
    img = Image.new("RGB", (m + W, len(cands) * H), "white")
    d, font = ImageDraw.Draw(img), _font()
    for i, c in enumerate(cands):
        try:
            r = requests.get(f"https://i.ytimg.com/vi/{c['id']}/mqdefault.jpg", timeout=15)
            t = Image.open(io.BytesIO(r.content)).convert("RGB").resize((W, H))
        except Exception:
            t = Image.new("RGB", (W, H), "gray")   # o xam -> khong co gi de soi -> model van phai xet tieu de
        y = i * H
        img.paste(t, (m, y))
        d.rectangle([0, y, m - 4, y + H - 4], fill="yellow")
        d.text((14, y + H // 2 - 26), str(i + 1), fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def _line(i, c):
    v = f"{c['views']:,}" if c.get("views") else "?"
    return f"{i + 1}. {c['title'][:90]} | {c.get('channel', '')[:30]} | {v} views | {c.get('length') or '?'}"


def pick_ok(cands, niche, examples, model, log):
    """Tra danh sach ung vien DAT (giu nguyen dict). Moi loi -> [] + log."""
    if not cands:
        return []
    import qc_character as qcc
    prompt = PROMPT.format(niche=niche, examples="\n".join(f"- {t}" for t in examples) or "-",
                           cands="\n".join(_line(i, c) for i, c in enumerate(cands)))
    try:
        b64 = grid_b64(cands)
    except Exception as e:
        log(f"  [judge] khong ghep duoc luoi thumbnail: {e}")
        return []
    ex = ThreadPoolExecutor(max_workers=1)   # ep cung thoi gian: ramclouds tung DUNG IM khong timeout
    fut = ex.submit(qcc._chat, model, prompt, b64, True)
    try:
        raw = fut.result(timeout=TIMEOUT_S)
    except Exception as e:
        ex.shutdown(wait=False)
        log(f"  [judge] vision LOI -> bo lo nay: {type(e).__name__} {str(e)[:150]}")
        return []
    ex.shutdown(wait=False)
    # Do that 2026-10-22: gop 3 luat vao 1 danh sach "ok" thi model bo quen luat nay khi tap trung luat kia
    # (luc nhan video bac si that, luc nhan sai chu de) -> bat tra 2 danh sach rieng, CODE tu tru.
    try:
        j = qcc._parse_json(raw)
        real = {int(n) for n in j.get("real", [])}
        topic = [int(n) for n in j["topic"]]
    except Exception:
        log(f"  [judge] khong doc duoc JSON: {raw[:120]!r}")
        return []
    nums = [n for n in topic if n not in real and 1 <= n <= len(cands)]
    log(f"  [judge] {len(nums)}/{len(cands)} dat: {nums} | nguoi that/anh chup: {sorted(real)} | chu de: {j.get('subject', '?')}")
    return [cands[n - 1] for n in nums]
