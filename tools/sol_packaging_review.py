# -*- coding: utf-8 -*-
r"""
NHO GPT-5.6-sol CHAM TIEU DE + THUMBNAIL cua MOT VIDEO DA FLOP (>48h).

Khac `qc_thumbnail_sol.py` cua h2dev: cai do QC TRUOC KHI DANG ("co loi gi khong"),
cai nay chay SAU KHI DANG va CO SO LIEU THAT ("da flop that roi, tieu de/thumb sai o dau,
sua the nao") + luon dat canh video THANG cung kenh de doi chieu.

  py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\sol_packaging_review.py ^
     --video yCSzCQN_VsE --winner 75zDHRIaiYM ^
     --script "E:\CLAUDE\YOUTUBE\h2dev\assets\satori_jp\simbot2-01-vU5PWT2zLDs\script.txt" ^
     --title "..." --winner-title "..." ^
     --metrics "301 impressions / CTR 2.3% / 13 views / 108h"

Thumbnail LAY BAN DANG SONG tren YouTube (i.ytimg.com), khong lay file local — file local co the
la ban cu truoc khi doi thumb.
sol_client.chat() chi nhan 1 anh -> ghep 2 thumbnail thanh 1 anh A|B de sol so sanh duoc.
"""
import os, sys, argparse, datetime, urllib.request
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _find_pipeline():
    """Tim h2dev/pipeline (noi chua sol_client.py).

    Moi may de h2dev mot cho khac nhau (may 1: E:/CLAUDE/YOUTUBE/h2dev,
    may 2: E:/CLAUDE/h2dev) -> khong duoc ghi cung duong dan.
    Thu tu uu tien: bien moi truong H2DEV_PIPELINE > cac vi tri quen thuoc quanh ROOT.
    """
    env = os.environ.get("H2DEV_PIPELINE")
    cands = [env] if env else []
    up1 = os.path.dirname(ROOT)          # .../YOUTUBE hoac .../CLAUDE
    up2 = os.path.dirname(up1)
    for base in (up1, up2):
        cands.append(os.path.join(base, "h2dev", "pipeline"))
        cands.append(os.path.join(base, "YOUTUBE", "h2dev", "pipeline"))
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "sol_client.py")):
            return c
    tried = "\n  ".join(c for c in cands if c)
    raise SystemExit(
        "Khong tim thay h2dev\\pipeline\\sol_client.py.\n"
        "Da thu:\n  " + tried + "\n"
        "Cach sua: dat bien moi truong tro dung thu muc pipeline, vi du\n"
        "  set H2DEV_PIPELINE=E:\\CLAUDE\\h2dev\\pipeline"
    )


PIPELINE = _find_pipeline()
sys.path.insert(0, PIPELINE)
import sol_client  # noqa: E402

# LUU Y: sol_client.chat() tra TUPLE (text, usage_dict), khong phai str.
from PIL import Image, ImageDraw  # noqa: E402

OUT_DIR = os.path.join(ROOT, "reports")


def tai_thumb(vid, dest):
    """Ban thumbnail NGUOI XEM DANG THAY. maxres co the khong ton tai -> tut xuong hq."""
    for name in ("maxresdefault.jpg", "sddefault.jpg", "hqdefault.jpg"):
        url = f"https://i.ytimg.com/vi/{vid}/{name}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                b = r.read()
            if len(b) > 5000:
                open(dest, "wb").write(b)
                return name
        except Exception:
            continue
    raise RuntimeError(f"khong tai duoc thumbnail cua {vid}")


def ghep_ab(a_path, b_path, out):
    """A = video flop, B = video thang. Dan nhan de sol khong lan."""
    a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
    h = 720
    a = a.resize((int(a.width * h / a.height), h))
    b = b.resize((int(b.width * h / b.height), h))
    pad, top = 20, 60
    cv = Image.new("RGB", (a.width + b.width + pad * 3, h + top + pad), (255, 255, 255))
    cv.paste(a, (pad, top)); cv.paste(b, (a.width + pad * 2, top))
    d = ImageDraw.Draw(cv)
    d.text((pad + 10, 18), "A = VIDEO FLOP (can sua)", fill=(200, 0, 0))
    d.text((a.width + pad * 2 + 10, 18), "B = VIDEO THANG (tham chieu)", fill=(0, 120, 0))
    cv.save(out, quality=92)
    return out


PROMPT_TITLE = """Bạn là chuyên gia packaging YouTube cho thị trường NHẬT BẢN, ngách kể chuyện
người cao tuổi (ngôi thứ nhất, giọng cụ bà, video dài 25-35 phút, khán giả 60-80 tuổi).

Đây KHÔNG phải QC trước khi đăng. Video ĐÃ ĐĂNG và ĐÃ FLOP. Số liệu thật:

{metrics}

Để so sánh, cùng kênh, cùng ngách, cùng độ dài, đăng cách nhau 1 ngày, có một video THẮNG:
  Tiêu đề video THẮNG: {winner_title}
  Số liệu video THẮNG: {winner_metrics}

TIÊU ĐỀ ĐANG DÙNG CỦA VIDEO FLOP:
{title}

TOÀN VĂN KỊCH BẢN (để bạn biết video thực sự kể gì — tiêu đề mới BẮT BUỘC phải đúng nội dung này,
tuyệt đối không được hứa điều kịch bản không có):
=== KỊCH BẢN ===
{script}
=== HẾT KỊCH BẢN ===

TRẢ LỜI ĐÚNG 4 CÂU HỎI SAU, THEO ĐÚNG THỨ TỰ, tiếng Việt (riêng các tiêu đề đề xuất viết tiếng Nhật):

1. TIÊU ĐỀ NÀY ĐÃ HAY CHƯA?
   Chấm điểm /10 và nói thẳng. Đừng khen xã giao.

2. CÓ HỢP LÝ KHÔNG?
   - Lời hứa của tiêu đề có khớp với thứ kịch bản thực sự kể không?
   - Với khán giả Nhật 60-80 tuổi đọc trên điện thoại, tiêu đề này có ĐỌC ĐƯỢC không
     (độ dài, số ký tự bị cắt, mật độ dấu ngoặc/dấu ba chấm)?
   - So với tiêu đề video THẮNG ở trên: khác nhau ở điểm nào về mặt cấu trúc và cảm xúc?
     Đây là câu quan trọng nhất — hãy chỉ ra cơ chế, đừng nói chung chung.

3. NÊN SỬA GÌ KHÔNG?
   Liệt kê từng vấn đề cụ thể, mỗi vấn đề 1 dòng, kèm lý do.

4. SỬA THẾ NÀO?
   Đề xuất 3 tiêu đề MỚI bằng tiếng Nhật, đánh số. Với mỗi cái ghi rõ:
   - Tiêu đề (tiếng Nhật)
   - Cơ chế gây tò mò dùng ở đây là gì
   - Câu nào/chi tiết nào trong kịch bản bảo chứng cho lời hứa đó (trích dẫn)
   - Rủi ro nếu có
   Xếp theo thứ tự bạn khuyên dùng. Tuyệt đối không đề xuất tiêu đề mà kịch bản không trả được.
"""

PROMPT_THUMB = """Bạn là chuyên gia packaging YouTube cho thị trường NHẬT BẢN, ngách kể chuyện
người cao tuổi (khán giả 60-80 tuổi, xem chủ yếu trên điện thoại và TV).

Ảnh đính kèm ghép 2 thumbnail ĐANG CHẠY THẬT trên YouTube:
  A (bên trái, viền đỏ ghi "VIDEO FLOP")  = video đã flop, cần sửa
  B (bên phải, ghi "VIDEO THANG")         = video thắng cùng kênh, để tham chiếu

Số liệu thật:
  A: {metrics}
     Tiêu đề A: {title}
  B: {winner_metrics}
     Tiêu đề B: {winner_title}

Nội dung video A (tóm tắt từ kịch bản):
{summary}

TRẢ LỜI ĐÚNG 4 CÂU HỎI SAU, tiếng Việt (chữ đề xuất cho thumbnail viết tiếng Nhật):

1. THUMBNAIL A ĐÃ HAY CHƯA?
   Trước hết ĐỌC TO toàn bộ chữ tiếng Nhật bạn nhìn thấy trên A và trên B (ghi lại nguyên văn), rồi
   chấm A /10. Nếu chữ trên A khó đọc ở kích thước nhỏ thì nói rõ.

2. CÓ HỢP LÝ KHÔNG?
   - Chữ trên A có khớp tiêu đề và nội dung video không?
   - Ở kích thước thumbnail thật trên điện thoại (~320px ngang), A còn đọc được mấy chữ?
   - A và B khác nhau ở những điểm nào: bố cục, số lượng chữ, tương phản, biểu cảm gương mặt,
     tông màu, điểm nhìn đầu tiên của mắt? Chỉ ra cơ chế vì sao B kéo được click mà A thì không.

3. NÊN SỬA GÌ KHÔNG?
   Liệt kê từng lỗi cụ thể của A, mỗi lỗi 1 dòng.

4. SỬA THẾ NÀO?
   Đưa phương án sửa cụ thể, đủ để người khác dựng lại được:
   - Chữ overlay mới (tiếng Nhật), tối đa 2 dòng, ghi rõ dòng nào to dòng nào nhỏ
   - Bố cục: nhân vật đặt đâu, chữ đặt đâu, vùng nào để trống
   - Cảm xúc gương mặt cần có
   - Tông màu / độ tương phản
   - 1 câu prompt tả ảnh nền để sinh lại bằng AI nếu cần
   Nếu bạn cho rằng chỉ cần sửa chữ, giữ nguyên ảnh nền, thì nói rõ như vậy.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--winner", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--winner-title", required=True)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--winner-metrics", required=True)
    ap.add_argument("--script-limit", type=int, default=9000)
    a = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    wd = os.path.join(OUT_DIR, a.video)
    os.makedirs(wd, exist_ok=True)

    ta = os.path.join(wd, f"{a.video}_live.jpg")
    tb = os.path.join(wd, f"{a.winner}_live.jpg")
    print("Tai thumbnail dang song:", tai_thumb(a.video, ta), "|", tai_thumb(a.winner, tb))
    ab = ghep_ab(ta, tb, os.path.join(wd, "AB.jpg"))
    print("Ghep A|B ->", ab)

    script = open(a.script, encoding="utf-8").read()
    if len(script) > a.script_limit:
        script = script[:a.script_limit] + "\n…(đã cắt bớt phần sau)"
    summary = script[:1200]

    print("\n>>> Hoi sol ve TIEU DE…", flush=True)
    r1, u1 = sol_client.chat(PROMPT_TITLE.format(metrics=a.metrics, winner_title=a.winner_title,
                                             winner_metrics=a.winner_metrics, title=a.title,
                                             script=script), max_tokens=3000, timeout=600)
    print(r1[:400]); print("   tokens:", u1)

    print("\n>>> Hoi sol ve THUMBNAIL…", flush=True)
    r2, u2 = sol_client.chat(PROMPT_THUMB.format(metrics=a.metrics, title=a.title,
                                             winner_metrics=a.winner_metrics,
                                             winner_title=a.winner_title, summary=summary),
                         image_path=ab, max_tokens=3000, timeout=600)
    print(r2[:400]); print("   tokens:", u2)

    rep = os.path.join(wd, "sol_packaging_review.md")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(f"# Sol packaging review — {a.video}\n\n")
        f.write(f"- Ngày chấm: {datetime.datetime.now():%Y-%m-%d %H:%M}\n")
        f.write(f"- Số liệu video flop: {a.metrics}\n")
        f.write(f"- Tiêu đề đang dùng: {a.title}\n")
        f.write(f"- Đối chiếu video thắng: {a.winner} — {a.winner_title} ({a.winner_metrics})\n\n")
        f.write("## 1. TIÊU ĐỀ\n\n" + r1 + "\n\n## 2. THUMBNAIL\n\n" + r2 + "\n")
    print("\nDa ghi:", rep)


if __name__ == "__main__":
    main()
