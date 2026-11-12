# BÁO CÁO LANE X — kênh AI謎解き研究所 (1.720 sub) — 01/11/2026

**Nguồn số**: YouTube Analytics Studio của chính kênh (tab Reach + Overview, khoảng Custom publish→now),
YouTube Data API (view/like/comment), collector `daily_parallel` (lifetime N–S). Snapshot **01/11/2026 10:30–11:30 JST**.
**Giới hạn dữ liệu**: (1) Studio chỉ giữ bảng theo ngày 6 ngày gần nhất cho mỗi video → số "lifetime" lấy từ thẻ
Reach tổng, số AVD/APV/retention lấy từ tab Overview cùng khoảng; (2) kênh chỉ có **8 video** → mọi kết luận pattern
là **giả thuyết**, chưa đủ mẫu theo mục 17 SOP; (3) video `8ZNy6vD1uls` mới 1 ngày, Studio chưa đủ số retention.

> **KIỂM CHỨNG SỐ LIỆU 8ZNy (01/11, 11:21 – 11:27) — bản 11:20 ở trên đã bị huỷ, ghi lại đúng:**
> Đọc trực tiếp Studio với khoảng mặc định **“Since published” (Oct 31, 2026 — Now)**:
> **Thumbnail impressions 13,9K · CTR 3,4 % · Views 2,4K (2.423) · Watch time 114,3 h · Subscribers +3.**
> Số gốc trong bản đầu (13,7K / 3,4 % / 2.400) là **ĐÚNG** — chênh 13,7K→13,9K chỉ là tăng thêm trong 30 phút.
>
> Vì sao có màn “đính chính sai”: em đọc lại bằng URL **`period-<start_ms>,<end_ms>`** (cửa sổ custom).
> Với video **chưa đầy 24h**, cửa sổ custom trả nhãn “Oct 31 – 30, 2026” và mọi ô là `—` kèm dòng chữ
> *“Thumbnail impressions: Data is still processing. Please check back later.”* — em đọc `—` thành “chưa có dữ liệu”
> trong khi thực chất là **ô đang xử lý**. Chỉ khoảng mặc định `period-default` mới có số.
> Đã **phục hồi ô P12 = 3,40 %** trên sheet (backup lần xoá: `reports/backup_sheet_X_2026-11-01_truoc_xoa_P12.json`).
>
> Chênh lệch `13,9K × 3,4 % ≈ 473` click so với `2,4K` view **không phải lỗi đọc**: thumbnail impressions chỉ đếm
> các bề mặt có hiện thumbnail (home/browse/suggested/search), còn view từ “Up next”/playlist/notification và
> autoplay-chain không sinh impression. Video này có tỉ lệ view/impression cao bất thường ⇒ phần lớn view đến từ
> chuỗi gợi ý, không phải từ thumbnail.
> **AVD/APV/retention của 8ZNy vẫn là `—`**: tab Engagement trả “Oops, something went wrong” + dữ liệu đang xử lý,
> nên chưa kết luận được BODY (watch time 114,3h trên 2.423 view ≈ 2:50/view chỉ là suy ra từ số đang xử lý — không dùng).

> **CẬP NHẬT 11:49 — collector chạy lại toàn lane X (8/8 video, 0 lỗi, 17 phút).** Số mới nhất trên sheet
> (cột N/O/P/Q, `imp24h` = lượt hiển thị 24h từ cửa sổ Custom 1 ngày):
>
> | Video | N ngày | O view | P CTR tổng | Q CTR 24h | imp24h | Cờ |
> |---|---:|---:|---:|---:|---:|---|
> | `CR9KU_5djOg` (Nobunaga) | 12 | 424.800 | 3,1 % | 3,0 % | 42.100 | ĐỂ NGUYÊN |
> | `t_7hE3EJhvM` (Mitsuhide sống/chết) | 10 | 79.900 | 3,1 % | 3,5 % | 7.200 | ĐỂ NGUYÊN |
> | `37wgPZeeP4s` (chủ mưu) | 14 | 8.800 | 3,5 % | 3,3 % | 605 | ĐỂ NGUYÊN |
> | `IjGEOWgQOOw` (Hakkōda) | 11 | 6.600 | 2,6 % | 4,0 % | 1.200 | ĐỂ NGUYÊN |
> | `_c-opbU36dU` (Mitsuhide phản bội) | 5 | 6.400 | 3,1 % | **1,9 %** | 3.000 | **VÀNG — K8** |
> | `QSdhgQVmNFI` (Yoshitsune) | 3 | 5.600 | 4,2 % | 5,4 % | 2.500 | ĐỂ NGUYÊN |
> | `OGrlW37QTcg` (Sen no Rikyū) | 2 | 3.000 | 3,3 % | 2,6 % | 5.900 | ĐỂ NGUYÊN |
> | `8ZNy6vD1uls` (Hidetsugu) | 0 | 2.400 | 3,3 % | **3,3 %** | 14.000 | ĐỂ NGUYÊN |
>
> ⇒ **8ZNy đọc được đầy đủ** ở lần này (Q 3,3 %, imp24h 14.000). Vậy trạng thái `—` lúc 11:19 là **ô đang xử lý tạm thời**,
> đúng như đính chính ở trên; số impressions/CTR của video này là **thật**.
> Ô **K8** đã được chuẩn hoá về đúng chuỗi anh chốt `CTR 24h< 2.5- Yêu cầu thay đổi` (giữ nền vàng;
> backup `reports/backup_sheet_X_2026-11-01_truoc_chuanhoa_K8.json`).

---

## 1. LANE_BASELINE

| Chỉ số | Giá trị |
|---|---|
| Video đã đăng | 8 (17/10 → 31/10/2026) |
| Tổng view kênh (API) | **529.987** |
| Subscriber | 1.720 |
| Tổng like | 11.790 · Tổng comment | 390 |
| Độ dài video | 23:54 – 25:50 (toàn bộ dài, cùng format) |
| CTR thumbnail | 2,6 % – 4,2 % (trung vị ≈ 3,2 %) |
| Impressions | 13,9K – 3,4M |
| AVD / APV | 9:30 – 10:49 · 39,4 % – 44,0 % |
| Giữ chân tại 0:30 | 59 % – 71 % |
| Traffic | Browse **60–90 %** · Suggested 5–25 % · Search 0,3–2,1 % · Channel pages 0,8–18 % |

---

## 2. PER_VIDEO_REPORT (mới nhất → cũ nhất)

| # | Ngày | Video (tiêu đề dịch) | View | Like | Cmt | Impr | CTR | AVD | APV | Giữ 0:30 | Browse | Suggested | Search |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 1 | 31/10 | **Điều tra 430 năm: Tại sao Toyotomi Hidetsugu phải mổ bụng? Lệnh của Hideyoshi có thật không? AI giải mã bóng tối lịch sử** (`8ZNy6vD1uls`) | 2.222 | 8 | 2 | 13,9K | 3,4 % | — | — | — | **90,7 %** | 5,9 % | 0,8 % |
| 2 | 29/10 | **Điều tra 435 năm: Sen no Rikyū mổ bụng vì lý do gì? AI làm rõ sự thật gây sốc** (`OGrlW37QTcg`) | 2.943 | 6 | 8 | 18,4K | 3,4 % | 10:17 | 41,5 % | 68 % | 86,4 % | 4,7 % | 2,0 % |
| 3 | 28/10 | **Điều tra 837 năm: Minamoto no Yoshitsune có thật sự chết ở Yashima (衣川)? 7 bí ẩn được làm sáng tỏ** (`QSdhgQVmNFI`) | 5.500 | 29 | 7 | 36,6K | 4,2 % | 9:35 | 39,8 % | 70 % | 84,1 % | 9,3 % | 1,7 % |
| 4 | 26/10 | **Điều tra 444 năm: Akechi Mitsuhide phản bội Nobunaga vì sao? AI giải mã 3 nguyên nhân của Sự biến Honnō-ji** (`_c-opbU36dU`) | 6.322 | 36 | 24 | 51,1K | 3,1 % | 10:26 | 43,7 % | 71 % | 64,8 % | 25,2 % | 2,1 % |
| 5 | 21/10 | **Điều tra 440 năm: Akechi Mitsuhide có thật sự chết? Cho AI chấm 5 thuyết (kể cả thuyết Tenkai) bằng sử liệu 1582 — kết quả bất ngờ** (`t_7hE3EJhvM`) | **79.720** | 1.454 | 87 | 756,5K | 3,1 % | 10:49 | 44,0 % | 69 % | 80,6 % | 14,9 % | 1,1 % |
| 6 | 20/10 | **199/210 người: Cuộc hành quân tuyết Hakkōda — điều chia cắt số phận không phải thời tiết? AI suy luận chỉ từ hồ sơ 1902** (`IjGEOWgQOOw`) | 6.554 | 48 | 4 | 76,7K | 2,6 % | 10:26 | 42,9 % | 70 % | 60,4 % | 19,0 % | 1,9 % |
| 7 | 19/10 | **Điều tra 440 năm: Thi thể Nobunaga biến đi đâu? Chỉ đưa AI sử liệu gốc — nó chỉ ra một nơi bất ngờ** (`CR9KU_5djOg`) | **424.120** | 10.147 | 241 | **3,4M** | 3,1 % | 9:30 | 39,4 % | 65 % | 87,9 % | 10,2 % | 0,3 % |
| 8 | 17/10 | **Điều tra 440 năm: Ai là chủ mưu Sự biến Honnō-ji? Cho AI suy luận từ sử liệu gốc** (`37wgPZeeP4s`) | 8.794 | 62 | 17 | 84,7K | 3,5 % | 9:43 | 40,6 % | 59 % | 64,0 % | 12,9 % | 1,3 % |

### Trạng thái 5 mục SOP cho từng video

| Video | DISTRIBUTION | TRAFFIC_MODE | PACKAGING (CTR) | HOOK (0–30s) | BODY (AVD/APV) |
|---|---|---|---|---|---|
| CR9KU (424k) | BROWSE_DOMINANT | BROWSE | OK (3,1 %) | OK (65 %) | OK (9:30 / 39,4 %) |
| t_7hE (79,7k) | BROWSE_DOMINANT | BROWSE | OK (3,1 %) | OK (69 %) | OK (10:49 / 44,0 %) |
| 37wg (8,8k) | BROWSE+MIXED | BROWSE/CHANNEL | OK (3,5 %) | ĐẠT THẤP (59 %) | OK (9:43 / 40,6 %) |
| IjGEO (6,5k) | MIXED | BROWSE | **THẤP (2,6 %)** — nhưng impr 76,7K nên đọc được | OK (70 %) | OK (10:26 / 42,9 %) |
| _c-op (6,3k) | BROWSE+SUGGESTED | BROWSE | OK (3,1 %) | OK (71 %) | OK (10:26 / 43,7 %) |
| QSdh (5,5k) | BROWSE_DOMINANT | BROWSE | OK (4,2 %) | OK (70 %) | OK (9:35 / 39,8 %) |
| OGrl (2,9k) | BROWSE_DOMINANT | BROWSE | OK (3,4 %) | OK (68 %) | OK (10:17 / 41,5 %) |
| 8ZNy (2,2k) | BROWSE_DOMINANT | BROWSE | OK (3,4 %) — impressions 13,9K nên đọc được | CHƯA CÓ SỐ (Engagement đang xử lý) | CHƯA CÓ SỐ |

### CTR 24 giờ trượt (01/11 10:00 → 11:00, cửa sổ now-24h)

| Video | Impr 24h | CTR 24h | View 24h |
|---|---:|---:|---:|
| CR9KU (424k) | 42,1K | 3,0 % | 5.700 |
| t_7hE (79,7k) | 7,2K | 3,5 % | 947 |
| OGrl (Sen no Rikyū) | 5,9K | 2,6 % | 1.100 |
| _c-op (Mitsuhide phản bội) | 3,0K | **1,9 %** | 351 |
| QSdh (Yoshitsune) | 2,5K | 5,4 % | 524 |
| IjGEO (Hakkōda) | 1,2K | 4,0 % | 137 |
| 37wg (chủ mưu Honnō-ji) | 605 | 3,3 % | 61 |
| 8ZNy (Hidetsugu) | 14,0K | 3,3 % | — |

→ Chỉ **`_c-opbU36dU` (Mitsuhide phản bội, 26/10)** có CTR 24h < 2,5 % ⇒ đã ghi cột K
`CTR 24h< 2.5- Yêu cầu thay đổi` + tô vàng ô K8 (backup `reports/backup_sheet_X_2026-11-01_truoc_ghi_N_S_K.json`).
Video 424k **vẫn đang được phân phối**: 42,1K impressions + 5,7K view trong 24h qua ⇒ cụm chủ đề Chiến Quốc chưa chết,
chỉ là các tập mới không được cấp impressions.

---

## 3. CHANNEL_COMPARISON (trong lane)

**Impressions là biến số duy nhất thay đổi lớn — CTR gần như phẳng:**

```
Impr:     3,4M ── 756K ── 84,7K ── 76,7K ── 51,1K ── 36,6K ── 18,4K ── 13,9K
CTR:      3,1%    3,1%    3,5%    2,6%    3,1%    4,2%    3,4%    3,4%
View:    424,1K   79,7K    8,8K    6,5K    6,3K    5,5K    2,9K    2,2K
```

- Video có CTR **cao nhất** (QSdh 4,2 %) chỉ được 36,6K impressions → **không phải thumbnail tốt sẽ được đẩy**.
- Video 424k có CTR **thấp hơn** video 8,8k (3,1 % so với 3,5 %) → CTR không giải thích được khác biệt 48 lần.
- Kết luận: khác biệt nằm ở **lượng impressions YouTube chịu cấp** (thuật toán browse thử nghiệm), không phải ở packaging.

---

## 4. SUGGESTED_NEIGHBORHOOD

Suggested videos 4,7 % – 25,2 % (< 40 %) nên **không bắt buộc** thu danh sách "Content suggesting this video".
Video 424k phụ thuộc Browse 87,9 % — tức trang chủ + feed đề xuất, không phải "video gợi ý cạnh" → muốn nhân bản
hiệu ứng phải giữ chân khán giả trong **cùng cụm chủ đề**, không phải xin xuất hiện cạnh video khác.

## 5. SEARCH_FINDINGS

Search 0,3 % – 2,1 % ⇒ **IMMATERIAL** theo SOP. Không diễn giải keyword; không tối ưu SEO ở giai đoạn này.

---

## 6. PRIMARY_BOTTLENECK

**TOPIC / AUDIENCE_MATCH — cụm chủ đề làm YouTube ngừng cấp impressions.**

Bằng chứng chuỗi thời gian:

| Chủ đề | Cụm | Impr | View |
|---|---|---:|---:|
| Thi thể Nobunaga biến đi đâu (19/10) | "xác / mất tích" + nhân vật lớn | 3,4M | 424.120 |
| Mitsuhide có thật sự chết? (21/10) | "chết / mất tích" + nhân vật lớn | 756K | 79.720 |
| Chủ mưu Honnō-ji (17/10) | **cùng cụm Honnō-ji nhưng KHÔNG có câu hỏi "xác/chết"** | 84,7K | 8.794 |
| Hakkōda 1902 (20/10) | khác cụm | 76,7K | 6.554 |
| Mitsuhide phản bội vì sao (26/10) | quay lại Honnō-ji nhưng hỏi "vì sao" | 51,1K | 6.322 |
| Yoshitsune chết ở Yashima? (28/10) | "chết" nhưng nhân vật thời khác | 36,6K | 5.500 |
| Sen no Rikyū mổ bụng (29/10) | "chết" nhưng nhân vật khác | 18,4K | 2.943 |
| Hidetsugu mổ bụng (31/10) | "chết" + nhân vật khác | 13,9K | 2.222 |

Công thức đã nổ = **nhân vật lịch sử cực nổi + câu hỏi "xác/thân phận sau khi chết" + AI chấm nhiều thuyết bằng sử liệu gốc**,
và **chỉ hiệu quả khi nhân vật thuộc cụm Chiến Quốc quanh Oda Nobunaga**. Rời sang Rikyū / Yoshitsune / Hidetsugu ⇒ impressions
sụp còn 1/20 – 1/250 dù CTR và retention không đổi. Đây là **distribution stall do topic**, không phải packaging, không phải hook.

---

## 7. PRIORITY_ACTIONS

1. **Đăng ngay tập 「Thi thể Hideyoshi đã đi đâu?」 (dòng 11 sheet — ĐÃ sản xuất, CHƯA đăng).**
   Đây là tập duy nhất còn lại khớp đúng công thức đã nổ (nhân vật lớn + câu hỏi về thi thể + AI chấm 6 địa điểm từ sử liệu).
   Đăng trước mọi chủ đề khác; **giữ nguyên công thức tiêu đề** `【N年の謎】…遺体はどこへ消えたのか？…採点させたら…` và họ thumbnail hiện tại.
   *Không* đổi thumbnail/tiêu đề các video đang chạy (CTR 3,1–4,2 % ổn định; vấn đề là impressions, không phải CTR).
2. **Kiểm tra dòng 6 sheet (Toyotomi Hideyori, `wJNVCS24HPg`)** — ID này **không tồn tại công khai** trên kênh (8 video công khai không có
   tập Hideyori). Có thể video đang private/nháp hoặc ID sai. Xác nhận trước khi đăng, rồi cập nhật lại ID đúng.
3. **Sau 3 tập tới, đo lại**: nếu tập Hideyoshi mang lại ≥ 30K impressions trong 72h ⇒ cụm Chiến Quốc còn sống, tiếp tục khai thác
   (Nobunaga → Mitsuhide → Hideyoshi → Hideyori). Nếu vẫn < 20K ⇒ cụm đã cạn, phải tìm cụm mới bằng dữ liệu **Suggested** (thu danh sách
   "Content suggesting this video" của 424k) chứ không đoán.

---

## 8. VIỆC ĐÃ LÀM TRÊN SHEET (ngày 01/11)

- Đã điền **6 video_id còn thiếu** vào cột L của tab `X` (khớp tiêu đề tuyệt đối, backup tại
  `reports/backup_sheet_X_2026-11-01_truoc_ghi_L.json`):
  L2=`37wgPZeeP4s` · L3=`CR9KU_5djOg` (**chính là video 424k — trước đây sheet không có ID nên mọi báo cáo định kỳ bỏ sót**)
  · L8=`_c-opbU36dU` · L9=`QSdhgQVmNFI` · L10=`OGrlW37QTcg` · L12=`8ZNy6vD1uls`
- Cột N–S của 6 dòng mới **để trống**: lần chạy collector kế tiếp (mở máy) sẽ tự thu đủ N/O/P/Q + rotate R/S.
  Không ghi tay để tránh sai quy trình rotate.
- `P12` (8ZNy): đã ghi **3,40 %** — lần xoá lúc 11:20 là SAI, đã **phục hồi** (backup: `reports/backup_sheet_X_2026-11-01_truoc_xoa_P12.json`).
- `wJNVCS24HPg` (L6) **giữ nguyên**, chờ anh xác nhận.

## 9. SỰ CỐ KỸ THUẬT ĐÃ XỬ LÝ TRONG LẦN CHẠY NÀY

| Triệu chứng | Nguyên nhân gốc | Cách xử lý |
|---|---|---|
| `greenlet._greenlet` ImportError khi collector mở Chrome | `PYTHONPATH` bị tiêm trỏ vào venv Hermes → child process nạp nhầm site-packages | chạy với `PYTHONPATH=` rỗng |
| `goto studio.youtube.com interrupted by another navigation` | **triệu chứng phụ** của lỗi ngôn ngữ bên dưới: tool không thấy menu nên thử chọn lại kênh 4 lần, mỗi lần goto trong lúc trang còn điều hướng | **không cần làm nóng profile** — sửa cookie `PREF` là hết; bằng chứng: sau khi sửa `PREF`, `daily_parallel.py` chạy thẳng, không warm-up, ghi sheet bình thường |
| Studio không có menu "Content" → tool báo "chưa vào được kênh" | **cookie `PREF` của profile để `hl=vi`** → toàn bộ UI tiếng Việt ("Nội dung", "Số liệu phân tích"), tool tìm chữ tiếng Anh | đổi `hl=en` trong cookie PREF của profile (không đổi cài đặt tài khoản); UI đã sang tiếng Anh và giữ nguyên sau khi khởi động lại |
| `studio_collect.py` lỗi "KHONG thay 'Videos' để bấm" ở 2/3 video | tab Content đôi lúc chưa render xong danh sách video | dùng bộ đọc riêng `scratch_analysis/read_lane_x_all.py` đọc đủ 8 video |
| **Video < 24h: mọi ô Reach trả `—` dù đã có view** | URL `period-<start_ms>,<end_ms>` (cửa sổ custom) **chưa xử lý xong** cho video mới → nhãn "Oct 31 – 30, 2026", toàn bộ `—` kèm *"Data is still processing"* | đọc bằng **`period-default`** (= Since published) mới ra số: 13,9K impr / 3,4 % / 2,4K view. Bài học: `—` có **hai** nghĩa — (a) chưa đủ dữ liệu, (b) **ô đang xử lý**; phải đọc dòng chữ cảnh báo để phân biệt, không suy ra "không có số" |
| YIE báo `PARTIAL` | log collector hôm nay có 3 dòng "LOI lane" từ 3 lần chạy hỏng trước khi fix ngôn ngữ; engine đếm cả 3 là lane lỗi | giữ nguyên log (không sửa), số liệu 2 video vẫn đúng — lần chạy mai sẽ sạch |
