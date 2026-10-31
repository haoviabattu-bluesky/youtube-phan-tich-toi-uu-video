# Job 05:00 — đồng bộ N–S + ghi K + tô vàng (anh duyệt 2026-10-16)

Luật đã chốt: xem memory mark-column-k-yellow / daily-0500-profile-busy / lane-profiles-n-j.

## File
- tools/daily_lanes.json      — tab → cách mở profile (gpm mail | ads user_id | cdp 9222), gom lane chung profile
- tools/daily_profiles.py     — tự bật GPM/AdsPower, mở/đóng profile, xử lý ProfileUsingByOther (stop + kill đúng PID)
- tools/daily_k_rules.py      — chuỗi cột K + có tô vàng hay không
- tools/daily_sheet.py        — đọc/sao lưu/ghi giá trị + tô/bỏ vàng cả dòng
- tools/daily_0500_run.py     — điều phối, khoá chung với view_spike, log, toast
- sheet_metrics_sync.read_video: thêm read_video_full trả thêm impressions 24h (hàm cũ giữ nguyên)

## Phase
1. dry-run 1 lane (F) → báo anh
2. chạy thật 1 lane → anh kiểm
3. tạo task DailyMetrics0500 (05:00, StartWhenAvailable) + chạy thử
