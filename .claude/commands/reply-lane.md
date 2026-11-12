---
description: Tiếp tục / chạy trọn quy trình trả lời bình luận YouTube cho 1 lane (mặc định X) — đăng từng cái qua GPM rồi đối chiếu API
argument-hint: "[lane, vd X | F | L | N | O | P | Q]  (bỏ trống = X)"
---

Anh gọi lệnh trả lời bình luận cho lane: **$ARGUMENTS** (nếu trống thì lane = **X**). Làm TRỌN các bước dưới, không hỏi lại từng bước.
Báo cáo bằng tiếng Việt, mọi câu tiếng Nhật kèm dịch Việt, mọi file ghi đường dẫn tuyệt đối.

## 0. Đọc luật trước
Đọc `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\HUONG_DAN_HERMES.md` (mục 0 = luật tuyệt đối: reply RẤT ngắn 1–2 câu ≤50 chữ,
CẤM trích dẫn, chỉ đồng tình hoặc phản biện nhẹ có kiến thức, khó → `コメントありがとうございます。`, không dislike, không kill Chrome).
Lệnh Python: `py -3.13`, luôn đặt `PYTHONIOENCODING=utf-8`. Thư mục: `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care`.

## 1. Kiểm tra trạng thái
- Giờ Nhật phải trong 08:00–22:00, ngoài giờ thì chỉ làm bước 2, không đăng.
- GPM: `curl http://127.0.0.1:9495/api/v1/profiles?page=1&per_page=1` phải trả success.
- Đếm việc còn treo của lane (draft EDITED/APPROVED chưa đăng):
  `py -3.13 -c "import sqlite3;c=sqlite3.connect(r'E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\state\comment_care.sqlite');print(c.execute(\"select d.status,count(*) from drafts d join channels ch on ch.channel_id=d.channel_id where ch.lane=? group by d.status\",('<LANE>',)).fetchall())"`
  (nếu bảng channels không có cột lane thì lấy channel_id từ `cc.py channels`).
  Lane X (2026-10-22): 20 reply đã đăng + xác nhận API, **62 draft EDITED đang chờ đăng** (đã viết sẵn, đúng luật — KHÔNG viết lại),
  5 cái lỗi "ô nhập reply không hiện" đã đối chiếu API là CHƯA đăng → đã mở khoá, nằm trong 62 cái chờ.

## 2. Bình luận MỚI (chuẩn bị — chạy đa luồng)
`py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py run --channel <LANE> --mode draft_only --limit 200`
Draft MỚI (status GENERATED/JUDGE_FAIL/BLOCKED, chưa EDITED/APPROVED) → em tự đọc bình luận + dịch Việt trong
`E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\reports\comment_care\<hôm nay>\<tab lane>\DRAFT_REVIEW.txt`, viết lại theo luật (cần phương án
thì `tools\viet_reply.py --channel <LANE> --draft-id <id>`, dùng sol/gemini), ghi bằng `Store.review_apply(id,'EDIT',text)` hoặc
`cc.py review --file ...`. Câu CTA xin like/đăng ký xoay 3 mẫu (mục 4.2 hướng dẫn); không CTA cho xin lỗi đọc sai, chửi, chuyện buồn.
Thù ghét/khủng hoảng/spam copy-paste → REJECT. Không có bình luận mới thì bỏ qua bước này.

## 3. Đăng — TỪNG BÌNH LUẬN MỘT như người thật (không song song, không 2 lane cùng lúc)
1. Id profile: `py -3.13 -c "import sys;sys.path.insert(0,r'E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\src');from comment_care.browser_poster import gpm_find;print(gpm_find('<mail lane>'))"`
   (lane X: mail theeuxanh1@gmail.com → `cbd86d34-eec8-42c4-95bf-4c6cf9aa7e02`; mail các lane khác xem `config\channels.yaml`).
2. Watchdog giữ cửa sổ hiện (chạy nền):
   `pwsh -NoProfile -File E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tools\keep_visible.ps1 -ProfileId <id> -MaxMinutes 300`
3. Đăng (chạy NỀN, ghi log ra file trong scratchpad):
   `py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py post-browser --channel <LANE>`
   Tool gõ 60–180 ms/ký tự, nghỉ 60–150 s giữa 2 reply, sau đó like/tim bình luận khách, tự tắt profile.
4. **Theo dõi log.** Nếu **3 lỗi liên tiếp** "ô nhập reply không hiện" (dấu hiệu YouTube đang chặn tạm) → DỪNG: kill đúng PID python
   `cc.py post-browser` (lọc CommandLine, không kill theo tên), `curl http://127.0.0.1:9495/api/v1/profiles/stop/<id>`, báo anh.
   `PROFILE_BUSY` → dừng, báo anh đóng cửa sổ profile. Không bao giờ kill chrome.

## 4. Đối chiếu API (bắt buộc trước khi báo "đã đăng")
`py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tools\verify_replies.py --channel <LANE> --days 2`
CHƯA THẤY → đợi 5–10 phút chạy lại. Nếu chắc chắn chưa đăng (lỗi trước khi gõ) và muốn cho đăng lại lần sau: đổi
`replies.idempotency_key = key||':fail_<ngày>'`, `status='FAILED_NOT_POSTED'` cho đúng dòng đó. Không bao giờ đăng lại khi chưa đối chiếu.

## 5. Báo anh
Bảng: video → bình luận (dịch Việt) → reply đã đăng (Nhật + dịch Việt) → ✓ API; số còn chờ; số lỗi; số like/tim;
"khán giả nói gì" (3–6 gạch đầu dòng); việc cần anh xử lý. Kèm đường dẫn tuyệt đối file log + DRAFT_REVIEW.
