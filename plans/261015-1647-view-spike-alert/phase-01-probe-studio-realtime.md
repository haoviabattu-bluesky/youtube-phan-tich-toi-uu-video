---
phase: 01
title: Spike — đọc view/giờ trong Studio + đo lệch API↔Studio
status: completed
smoke_test: "2026-10-15 17:00-17:15, lane M (Chrome 9222): doc duoc view theo GIO bang hover yta-realtime-chart (10 cot lien tiep cGZVfCjdRlE: 35/85/86/36/17/41/32/13/18/4) + so tong the Realtime; API cong khai 604 vs Studio 815 cung luc (tre 26%) — lane F bi ProfileUsingByOther, chua do"
---

# Phase 01 — Kiểm giả thuyết rủi ro nhất trước khi viết tool

## Câu hỏi phải trả lời
1. Có đường nào đọc được **số view theo từng giờ** của 1 video trong Studio dưới dạng text không?
   Thử lần lượt, dừng ở cách đầu tiên chạy được:
   a. Thẻ Realtime trên tab Overview của video: text DEEP có số "60 phút qua"/"48 giờ qua" không;
      số từng cột có trong DOM (aria-label, svg title) hay chỉ trong tooltip khi hover.
   b. Hover từng cột bằng Playwright rồi đọc tooltip.
   c. URL `tab-overview/period-<now-1h ms>,<now ms>` (cách bẫy #7) — Studio có trả số cho cửa sổ 1 giờ không.
   d. Advanced mode `granularity=HOUR` (nếu Studio có).
2. Cùng thời điểm, view công khai (Data API) và view Studio lệch nhau bao nhiêu, trễ bao lâu.

## Cách làm
- Chọn 1 video ĐANG có view (anh chỉ định, hoặc em chọn video mới nhất có view tăng trong sheet).
- Script tạm `view_spike/probe_realtime.py`: attach profile kênh đó (theo đúng luật GPM/9222),
  dump text DEEP của thẻ Realtime + thử a→d, lưu kết quả ra `view_spike/state/probe_*.json`.
- Song song: mỗi 15 phút ghi view API + view Studio vào `probe_compare.csv`, chạy 3–4 giờ.
  (Studio mở/đóng đúng profile mỗi lần đo; gặp `ProfileUsingByOther` thì bỏ lượt đó.)

## Smoke test (số đo thật, không ghi PASS)
- Cách đọc view/giờ chọn được + ví dụ 48 giá trị theo giờ của 1 video.
- Bảng ≥12 mốc: thời điểm | view API | view Studio | chênh lệch.
- Đề xuất NGƯỠNG_NGHI cho tầng 1 dựa trên độ lệch đo được.

## Dừng lại
Báo bảng kết quả cho anh → anh chốt ngưỡng + cách báo → mới sang Phase 02.
Nếu cả a→d đều không đọc được view/giờ → báo anh, cân nhắc chỉ dùng tầng 1 hoặc
dùng số "48 giờ qua" lấy chênh lệch giữa 2 lần đọc.

## KẾT QUẢ (2026-10-15, lane M — lane F bị `ProfileUsingByOther` nên đổi sang M theo lệnh anh)
- Cách (a) DEEP text: thẻ Realtime có SỐ TỔNG + nhãn, đọc thẳng được:
  - video < ~vài giờ: `4 · Views · Last 60 minutes` (cột = PHÚT) → chính là view/giờ.
  - video 32h: `814 · Views · Last 48 hours` (cột = GIỜ).
- Số từng cột KHÔNG có trong DOM/aria (0 aria-label có số) → cách (b) hover chạy được: rê chuột lên
  phần tử `yta-realtime-chart`, tooltip vào DOM dạng `Today, 3:00 – 4:00 PM. 85.` (giờ theo máy).
  Cột 48h rộng ~5,8px → phải bước ≤3px để không bỏ cột (bước 6px bỏ sót 1 nửa).
  Cột ngoài cùng phải = giờ HIỆN TẠI (chưa trọn), cột kế = giờ trọn gần nhất.
- Bẫy: trang overview có 1 thẻ khác báo "Oops, something went wrong" — không ảnh hưởng thẻ Realtime.
- Lệch API ↔ Studio cùng lúc: `cGZVfCjdRlE` API 604 / Studio 815 (≈26% thấp hơn);
  `nNlqnf28Kak` API 1 / Studio 4 trong 60 phút đầu.
- ⇒ Đề xuất NGƯỠNG_NGHI tầng 1 = **300 view/giờ công khai** (API thấp hơn ~26% và cập nhật theo đợt).
