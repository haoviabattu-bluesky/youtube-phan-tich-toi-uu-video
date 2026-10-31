# Plan — niche_watch: nuôi ngách 10 lane mỗi tối 18:00–21:00 (anh duyệt 2026-10-22)

## Anh đã chốt
- 10 lane E,H,F,L,M,O,N,Q,P,X — xoay vòng, mỗi lượt 3–4 profile (10 lane = 3 lượt 4/3/3, ~60 phút/lane).
- Lane M (Chrome 9222, dùng chung AUTO_LIST) cuối giờ ĐÓNG CẢ Chrome.
- Được like + đăng ký.
- Profile bận (ProfileUsingByOther) → tự stop + đóng chrome đúng PID rồi mở lại (force_busy=True).
- Hướng A: nâng cấp warmup thành bản nhiều lane, truy vấn từ sheet (E tiêu đề/hashtag, F tags),
  lọc bằng LLM + soi thumbnail, dùng lại tools/daily_profiles.py, lịch bằng Task Scheduler.

## Kiến trúc (thư mục niche_watch/)
| File | Việc |
|---|---|
| config.json | giờ chạy, batch, phút xem, xác suất like/sub, 10 lane (engine/mail/port/channel) |
| nw_common.py | đường dẫn, log, hạn chót/STOP, sổ "profile đang mở" (state/active_<lane>.json) |
| sheet_queries.py | đọc tab lane → ngách + kho truy vấn (tiêu đề / hashtag / cặp tag) + id video của mình |
| judge.py | ghép ≤12 thumbnail thành 1 ảnh lưới đánh số + tiêu đề → 1 lệnh vision (h2dev qc_character._chat) |
| yt_actions.py | gõ tìm, đọc kết quả/đề xuất, xem 10–15', like/sub, tắt autoplay, tắt tiếng, 360p |
| lane_worker.py | 1 lane: mở profile → (M/O chuyển kênh) → vòng tìm/xem/đề xuất đến hạn → ĐÓNG |
| run_evening.py | điều phối 18:00: chia lượt, chạy worker, quá hạn thì taskkill cây + đóng profile |
| close_all.py | đóng profile theo lane; --sweep lúc 21:05 là lưới an toàn |
| install_tasks.ps1 | tạo NicheWatch1800 + NicheWatchClose2105 |

Sửa thêm: view_spike/spike_studio_realtime.py — bỏ qua lane có profile đang nuôi ngách (tránh stop ngang).

## Phase
1. Code + `--dry-run` (đọc sheet, in truy vấn/ngách) cho 10 lane — không mở browser.
2. Chạy thật 1 lane ~20' (`run_evening.py --start-now --lanes E --end <now+20'>`): đo số video xem,
   lệnh LLM, video bị loại vì lộ mặt, profile đã đóng. STOP chờ anh.
3. Cài Task Scheduler sau khi anh xác nhận phase 2.
