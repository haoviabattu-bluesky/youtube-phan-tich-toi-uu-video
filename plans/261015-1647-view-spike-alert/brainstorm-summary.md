---
title: View spike alert — báo khi video mới đăng đạt ≥1000 view/giờ (Studio)
created: 2026-10-15
status: draft (chờ anh duyệt)
---

# Brainstorm — View spike alert (2 tầng)

## 1. Vấn đề
Video mới đăng có lúc bật lên (được đề xuất mạnh). Anh muốn biết NGAY khi một video đạt
≥1000 view/giờ theo số Studio, để kịp phản ứng (ghim comment, làm tập nối tiếp...).
Hiện chưa có gì theo dõi liên tục; `sheet_metrics_sync.py` chỉ chạy 24h/lần.

## 2. Mục tiêu đo được
- Video đạt ≥1000 view/giờ (Studio Realtime) → anh nhận báo trong ≤ ~30 phút.
- 0 lần mở profile GPM khi không có video nào "nghi đang lên".
- Không báo trùng một video quá 1 lần / 6 giờ.

## 3. Người dùng
Chỉ anh. Tool chạy nền, không cần GUI.

## 4. Kiến trúc 2 tầng (anh duyệt 2026-10-15)
```
[Tầng 1 — 15 phút/lần, KHÔNG mở profile]
  Sheet (cột L mọi tab lane) → video_id → Data API videos.list (50 id/lần, 1 unit)
  → snapshots.jsonl → view/giờ công khai = Δview / Δgiờ (cửa sổ ~60 phút)
  → ≥ NGƯỠNG_NGHI (mặc định 400/giờ, chốt lại sau Phase 1) → "NGHI"
[Tầng 2 — chỉ khi có NGHI]
  Mở đúng profile kênh (GPM theo mail / Chrome 9222 cho kênh haoviabattu)
  → Studio video → thẻ Realtime → view của giờ gần nhất (số Studio)
  → ≥1000 → BÁO ANH ; < 1000 → ghi log, cooldown 1 giờ rồi mới xét lại
  → đóng profile ngay sau khi đọc (trừ profile tool không tự mở)
```

## 5. Dữ liệu vào / ra
- Vào: Sheet `1xu4iNud…` các tab lane (A, Satori đã bị đình chỉ → bỏ, E, F, G, K, L, M, H, I, J),
  cột L = video_id; API key = cấu hình sẵn của comment_care (`YOUTUBE_API_KEY`).
- **Phạm vi (anh chốt 2026-10-15): mỗi lane chỉ 2 video MỚI NHẤT, và chỉ khi tuổi ≤ 72h**; quá 72h ngừng kiểm.
  Tuổi lấy từ `publishedAt` của API (chính xác tới giây), không đoán từ sheet.
- Ra: `view_spike/state/snapshots.jsonl`, `view_spike/state/alerts.jsonl`, log; báo anh.
- KHÔNG ghi gì vào Google Sheet (vai trò của dự án: chỉ ghi khi anh yêu cầu).

## 6. Cách báo anh — CHỐT 2026-10-15: toast góc màn hình (tạm thời)
Đề xuất mặc định (standalone, không cần Claude): **thông báo Windows (toast) + dòng trong
`alerts.jsonl`**. Tuỳ chọn thêm: Telegram bot (cần anh tạo bot + chat_id) hoặc email SMTP.

## 7. Chỗ chạy — CHỐT 2026-10-15: máy này
Mặc định: máy này, Task Scheduler 15 phút/lần. Tầng 2 cần GPM + profile nên PHẢI ở máy này
(VPS không có profile).

## 8. Rủi ro lớn nhất (Phase 1 kiểm trước)
1. **Đọc được view THEO GIỜ từ Studio không?** Thẻ Realtime vẽ biểu đồ cột 48h; số từng cột có
   thể chỉ nằm trong tooltip (không có trong DOM text) → phải tìm đường khác (Advanced mode
   granularity giờ, URL `period-<ms>,<ms>` 1 giờ như bẫy #7, hoặc hover cột).
2. **API trễ bao nhiêu so với Studio** khi video đang lên → quyết định NGƯỠNG_NGHI.

## 9. Ràng buộc an toàn (giữ nguyên luật dự án)
- `ProfileUsingByOther` → không chạm, báo trong log/alert "không xác minh được, anh đang mở".
- Chỉ đóng profile mà CHÍNH tool vừa mở; kênh haoviabattu cổng 9222 chỉ attach, không đóng.
- Không taskkill chrome theo tên. Không đổi gì trên YouTube.

## 10. Chi phí (anh yêu cầu tiết kiệm)
- Data API `videos.list` = 1 unit/lần, ≤50 id/lần → gom video của MỌI lane vào 1 lần gọi.
  15 phút/lần = 96 unit/ngày (~1% quota 10.000/ngày của key). Danh sách id lấy từ Sheet (Sheets API, không tính quota YouTube),
  chỉ đọc lại 1 lần/giờ.
- Key dùng chung với comment_care (commentThreads 1 unit/trang) → 2 module cộng lại vẫn rất xa trần.
- **0 token Claude/LLM**: tool chạy bằng Python thuần, Claude không tham gia vòng lặp.

## 11. Ngoài phạm vi
Không tự hành động khi video lên (không ghim, không đổi title). Không theo dõi video >72h, không theo dõi quá 2 video/lane.

## 12. Tiêu chí xong
Tool chạy 24h liên tục, có số đo: số vòng, unit API, số lần mở Studio, độ lệch API↔Studio;
giả lập 1 video vượt ngưỡng → anh nhận báo.
