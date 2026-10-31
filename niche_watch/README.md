# niche_watch — nuôi ngách 10 lane mỗi tối 18:00–21:00

Plan: `plans/261022-1900-niche-watch/plan.md`. Anh chốt 2026-10-22.

Mỗi profile kênh: gõ tìm (tiêu đề cột E / hashtag trong E / cặp tag cột F) → lọc 10 kết quả đầu bằng
**1 lệnh vision** (tiêu đề + ảnh lưới thumbnail: đúng ngách, dạng manga/minh hoạ/ゆっくり, **không người
thật/không quay thật**) → xem video ĐẠT nhiều view nhất 10–15 phút (có like/đăng ký ngẫu nhiên) → đi tiếp
theo cột đề xuất bên phải (tối đa 4 video liền) → hết chuỗi thì tìm truy vấn khác → hết giờ **đóng profile**.

## Lệnh
```
py -3.13 niche_watch\run_evening.py --dry-run                         # xem lịch chia lượt hôm nay
py -3.13 niche_watch\lane_worker.py --lane E --dry-run                # đọc sheet: ngách + truy vấn
py -3.13 niche_watch\lane_worker.py --lane E --until-min 20           # chạy tay 1 lane 20 phút
py -3.13 niche_watch\run_evening.py --start-now --end 19:30 --lanes E,F
py -3.13 niche_watch\close_all.py --sweep                             # đóng mọi profile tool còn mở
powershell -ExecutionPolicy Bypass -File niche_watch\install_tasks.ps1   # cài lịch 18:00 + 21:05
```
Dừng giữa chừng: tạo file `niche_watch\STOP` (worker dừng ≤30s rồi tự đóng profile).

## Luật
- Xoay vòng: 10 lane, mỗi lượt 3–4 profile (4/3/3 ≈ 60'/lane). Thứ tự xoay theo ngày.
- **Đóng bắt buộc**, 3 lớp: worker tự đóng khi tới hạn → run_evening taskkill cây + đóng lại → task 21:05 `--sweep`.
  Đóng theo GPM id / AdsPower user_id / PID khớp `--user-data-dir`. Không bao giờ kill chrome.exe theo tên.
- Lane M = Chrome 9222 (chung AUTO_LIST): **đóng cả Chrome** (anh chốt). Lane M/O dùng chung mail →
  chuyển đúng kênh (`studio_human.switch_channel`, kiểm CHANNEL_ID) trước khi xem; không chuyển được → không xem.
- Profile bận: **chạy theo lịch** (`--force-busy`) → tự stop + đóng đúng PID rồi mở lại; **chạy tay** → dừng, không kill (bẫy #9).
- Vision lỗi → bỏ lô đó, KHÔNG xem video chưa soi thumbnail. Không xem video của chính kênh (id cột L, tên kênh).
- view_spike tầng 2 bỏ qua profile đang nuôi ngách (`state/active_<lane>.json`), tránh `stop()` ngang.

## File
| | |
|---|---|
| config.json | giờ, batch, phút xem, xác suất like/sub, 10 lane; `niche` ghi đè B1, `seed_queries` khi tab chưa có E |
| sheet_queries.py · judge.py · yt_actions.py | đọc sheet · lọc vision · thao tác YouTube |
| lane_worker.py · run_evening.py · close_all.py | 1 lane · điều phối · đóng profile |
| state/ | seen_<lane>.json (video đã xem), queries_<lane>.json, active_<lane>.json |
| reports/niche_watch/<ngày>/ | <lane>.log, watched_<lane>.csv (= danh sách đối thủ cùng ngách), run_evening.log |
