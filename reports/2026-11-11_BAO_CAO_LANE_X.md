# BÁO CÁO PHÂN TÍCH HIỆU SUẤT & ĐỀ XUẤT TẬP TIẾP THEO — LANE X (2026-11-11)

- **REPORT_DATE:** `2026-11-11` (snapshot thu lúc `15:35–15:57` giờ VN / `17:35–17:57 JST`)
- **CHANNEL:** `AI謎解き研究所` (`@AINazotokiLab` · `UC8BO9Ni37bUDbJrHez1zA7w`) — **1.850 subscribers** · **607.139 tổng view công khai** (kênh đã bật kiếm tiền)
- **LANE:** `X` · Profile GPM: `theeuxanh1@gmail.com` (đã mở đọc bằng đường người thật 100% click, đóng profile an toàn lúc `15:56:49`)
- **VIDEO_COUNT:** **19 video trên Studio** = **18 video `Public`** + **1 video `Scheduled`** (`cq3BCZlYlwM`)
- **Nguồn dữ liệu:**
  1. **YouTube Studio Analytics** (Overview + Engagement + Reach `Since published` + Reach `Custom 1 ngày đủ số gần nhất = 2026-11-09`): [lane_x_studio_2026-11-11.json](file:///E:/CLAUDE/YOUTUBE/PHAN_TICH_TOI_UU_VIDEO/reports/lane_x_studio_2026-11-11.json), đã nối 18 dòng snapshot vào [youtube_postpublish_metrics.csv](file:///E:/CLAUDE/YOUTUBE/PHAN_TICH_TOI_UU_VIDEO/youtube_postpublish_metrics.csv).
  2. **YouTube Data API v3**: giờ đăng chính xác, thời lượng, view/like/comment lẻ và đo nhu cầu thị trường các đề tài ứng viên ([lane_x_demand_2kw_2026-11-11.json](file:///E:/CLAUDE/YOUTUBE/PHAN_TICH_TOI_UU_VIDEO/reports/lane_x_demand_2kw_2026-11-11.json)).
  3. **Google Sheet tab `X`** (chỉ đọc đối chiếu, **không tự ghi đè bất kỳ ô nào**).

> [!NOTE]
> Quy ước SOP: dấu `—` là Studio chưa xử lý xong hoặc mẫu quá nhỏ để tính %, **không phải `0`**. Kênh đã đạt **18 video công khai (≥ 10 video)** nên theo Mục 17 SOP, **baseline (median) riêng của Lane X chính thức thay thế ngưỡng chung**.

---

## 1 · `LANE_BASELINE` (18 VIDEO CÔNG KHAI)

| Chỉ số | Median (Chuẩn Lane X) | Mean | Khoảng (Min – Max) | Số tập có số | Nhận xét |
|---|---:|---:|---:|---:|---|
| **Impressions trọn đời** | **30.150** | 274.328 | 4.500 – 3.600.000 | 18/18 | Mean bị kéo mạnh bởi 2 tập nổ lớn (`CR9KU` 3,6M và `t_7hE` 795,4K) |
| **CTR trọn đời** | **3,05%** | 3,11% | 1,8% – 4,3% | 18/18 | Rất ổn định quanh ~3,1%; dưới `2,5%` mới là bất thường thật sự của lane |
| **CTR 1 ngày gần nhất (`09/11`)** | **3,10%** | 2,95% | 1,0% – 4,6% | 17/18 | Tập `i4_dGGnjfrM` đăng tối `10/11` (23,3h) nên chưa có ngày `09/11` |
| **Impressions 1 ngày (`09/11`)** | **389** | 2.338 | 134 – 17.100 | 17/18 | Top phân phối hiện tại: `CR9KU` (17,1K) → `aTk9Q` (8,7K) → `ts2jR` (6,1K) |
| **View trọn đời (API)** | **4.968** | 33.812 | 361 – 456.389 | 18/18 | Riêng `CR9KU` (Tín Trường) chiếm **75,1%** tổng view cả kênh |
| **Retention 0:30 (`HOOK`)** | **70,0%** | 69,5% | 60% – 77% | 17/18 | Mặt bằng hook rất tốt và đồng đều (16/17 tập đạt ≥ 63%) |
| **AVD (`BODY`)** | **10:12 (612,5s)** | 9:58 (597,6s) | 8:10 – 10:51 | 18/18 | Độ dài video chuẩn 20:20 – 25:50 |
| **APV (`BODY`)** | **43,2%** | 42,3% | 35,6% – 48,9% | 17/18 | Khán giả đã bấm vào thì xem trung bình hơn 43% thời lượng (~10 phút) |
| **Browse / Suggested / Search** | **79,0% / 13,0% / 1,9%** | 78,3% / 12,7% / 1,8% | Search: 0,4% – 3,2% | 18/18 | **100% Browse-dominant**; Search `< 5%` ở cả 18/18 tập (`IMMATERIAL`) |

---

## 2 · `PER_VIDEO_REPORT` — CHỈ SỐ CHI TIẾT & CHẨN ĐOÁN SOP (MỚI NHẤT → CŨ NHẤT)

### 2.1. Bảng số liệu toàn kênh (18 Public + 1 Scheduled)

| # | Đăng (JST) | Tuổi | ID · Chủ đề (dịch ngắn) | Dài | Impr | CTR | View (API) | Imp `09/11` | CTR `09/11` | Ret 30s | AVD / APV | Browse / Sugg / Search | Ghi chú Studio |
|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| S1 | *Hẹn giờ* | — | `cq3BCZlYlwM` · **[3D IF] Đưa 1 xạ thủ bắn tỉa vào Honnō-ji, Tín Trường có sống?** | 10:48 | — | — | 0 | — | — | — | — / — | — | `Scheduled` (dòng 23 Sheet) |
| 1 | 10/11 18:37 | 23h | `i4_dGGnjfrM` · Di hài Hijikata Toshizō biến đi đâu? (5 thuyết) | 24:11 | 4.500 | 2,3% | 361 | — | — | — | 10:17 / — | 74,1 / 15,5 / 2,6% | `A/B Test running` |
| 2 | 09/11 18:30 | 47h | `aTk9Qx6sFIA` · Trận Okehazama: Tín Trường thắng nhờ đánh úp thật không? | 21:51 | 9.900 | **1,8%** | 998 | 8.700 | **1,7%** | **77%** | **10:40 / 48,9%** | 76,9 / 17,6 / 0,9% | Hook & Body #1 kênh, CTR đáy |
| 3 | 08/11 18:30 | 3d | `oaNH9x8wGJ8` · Sau Honnō-ji, gia tộc Oda còn lại ra sao? | 23:12 | 13.100 | 2,7% | 1.821 | 1.900 | 3,3% | 72% | 9:26 / 40,7% | 77,3 / 17,3 / 1,9% | — |
| 4 | 07/11 18:30 | 4d | `ts2jRcYt33s` · **Gia Khang chết ở Osaka 1615? Kiểm chứng "mộ Gia Khang ở Sakai"** | 21:57 | **29.800** | **3,8%** | **4.136** | **6.100** | **3,5%** | **74%** | 9:32 / 43,5% | 81,4 / 13,6 / 1,3% | **Mạnh nhất tuần qua** |
| 5 | 06/11 18:30 | 5d | `bdTMvknayUg` · Tín Trường có thoát khỏi Honnō-ji? Kiểm chứng thư Tú Cát | 23:59 | 15.500 | 2,7% | 1.877 | 511 | 2,7% | 70% | 10:35 / 44,2% | 83,0 / 9,1 / 2,7% | `A/B Test running` |
| 6 | 05/11 18:30 | 6d | `XCfPtmsdtiM` · Thiên hoàng Antoku có thật sự chết ở Dan-no-ura? | 23:39 | 18.400 | 3,3% | 2.563 | 704 | 3,3% | 70% | 10:39 / 45,1% | 82,3 / 10,4 / 2,2% | `A/B Test running` |
| 7 | 04/11 18:30 | 7d | `F9ckrsz1yZI` · Date Masamune có cho bắn cha mình (Terumune)? | 20:20 | 6.100 | **2,2%** | **657** | 152 | **1,3%** | 70% | 8:10 / 40,2% | 76,4 / 9,4 / 3,2% | Thấp nhất kênh |
| 8 | 03/11 18:30 | 8d | `BV5I5UNUOdU` · **Di hài Vũ Điền Tín Huyền biến đi đâu? (6 ứng viên)** | 24:54 | **58.900** | **4,3%** | **8.692** | 901 | 3,8% | 71% | 10:25 / 41,9% | 90,5 / 6,0 / 0,9% | **CTR #1 toàn kênh** |
| 9 | 02/11 18:30 | 9d | `30egJcn3Q8o` · Con trai Tín Trường (Tín Trung) có chạy thoát được không? | 22:17 | 13.700 | 2,6% | 1.558 | 201 | **1,0%** | 67% | 9:46 / 43,9% | 75,8 / 12,3 / 2,4% | Đã tắt phân phối |
| 10 | 01/11 18:50 | 10d | `ugjhBQ6fupU` · **Di hài Phong Thần Tú Cát biến đi đâu?** | 22:37 | 39.900 | **3,9%** | 6.191 | 320 | 3,1% | 72% | 8:18 / 36,7% | 88,6 / 6,6 / 1,1% | `A/B Test completed` |
| 11 | 31/10 18:30 | 11d | `8ZNy6vD1uls` · Vì sao Phong Thần Tú Thứ mổ bụng? Lệnh Tú Cát có thật? | 25:50 | 30.500 | 3,5% | 5.799 | 172 | **1,7%** | 63% | 9:11 / 35,6% | 91,5 / 4,2 / 1,0% | APV thấp nhất kênh |
| 12 | 29/10 19:06 | 13d | `OGrlW37QTcg` · Vì sao Thiên Lợi Hưu phải mổ bụng? | 24:49 | 24.200 | 3,2% | 3.347 | 134 | 3,0% | 68% | 10:46 / 43,4% | 83,7 / 4,9 / 2,3% | Sheet đang báo vàng oan |
| 13 | 28/10 18:30 | 14d | `QSdhgQVmNFI` · Nguyên Nghĩa Kinh có thật sự chết ở Koromogawa? | 24:06 | 43.300 | **4,2%** | 6.209 | 389 | **4,6%** | 72% | 10:08 / 42,1% | 77,7 / 13,7 / 2,2% | `A/B Test completed` |
| 14 | 26/10 18:30 | 16d | `_c-opbU36dU` · Vì sao Quang Tú phản bội Tín Trường? (3 nguyên nhân) | 23:54 | 62.200 | 3,0% | 7.341 | 225 | 2,7% | 70% | 10:32 / 44,1% | 64,9 / 24,9 / 1,9% | `A/B Test completed` |
| 15 | 21/10 18:30 | 21d | `t_7hE3EJhvM` · **Minh Trí Quang Tú có thật sự chết? Kiểm chứng thuyết Tenkai** | 24:36 | **795.400** | 3,1% | **83.858** | 1.800 | 3,8% | 69% | **10:51 / 44,1%** | 80,2 / 14,9 / 1,4% | Hit #2 kênh, vẫn sống khỏe |
| 16 | 20/10 18:30 | 22d | `IjGEOWgQOOw` · Hành quân tuyết núi Hakkōda (199/210 người) | 24:21 | 82.500 | 2,7% | 7.050 | 217 | **4,6%** | 70% | 10:31 / 43,2% | 57,3 / 21,4 / 2,6% | Channel pages 13,5% |
| 17 | 19/10 18:30 | 23d | `CR9KU_5djOg` · **Thi thể Tín Trường biến đi đâu? Suy luận từ sử liệu gốc** | 24:07 | **3.600.000** | 3,0% | **456.389** | **17.100** | 2,8% | 66% | 9:37 / 39,9% | 86,3 / 11,7 / 0,4% | `A/B Test running` · Hit #1 |
| 18 | 18/10 06:34 | 24d | `37wgPZeeP4s` · Kẻ chủ mưu sau Biến cố Honnō-ji | 23:59 | 90.000 | 3,6% | 9.282 | 217 | 3,2% | 60% | 9:52 / 41,1% | 62,1 / 14,2 / 1,5% | Sheet đang báo vàng oan |

### 2.2. Bảng 6 Status SOP + Bottleneck + 1 Action bắt buộc cho từng video

*(Tất cả 18 video đều có `SEARCH_STATUS = IMMATERIAL` vì Search `0,4%–3,2% < 5%`.)*

| ID (Chủ đề ngắn) | `DISTRIBUTION` | `TRAFFIC_MODE` | `PACKAGING` | `HOOK` | `BODY` | `PRIMARY_BOTTLENECK` | `ACTION` (1 hành động chính) | Cờ cột K (`CTR 09/11 < 2,5%`) |
|---|---|---|---|---|---|---|---|---|
| `i4_dGGnjfrM` (Hijikata, 23h) | `TESTED` | `BROWSE` | `WATCH` (2,3%) | `UNKNOWN` | `UNKNOWN` | Chuyển thời kỳ sang Bakumatsu + mới 23h đang chạy A/B test | `WAIT_FOR_MORE_DATA` | Chưa đủ 48h (đang A/B test) |
| `aTk9Qx6sFIA` (Okehazama, 47h) | `TESTED` | `BROWSE` | **`REVIEW` (1,8%)** | **`STRONG` (77%)** | **`STRONG` (48,9%)** | **Packaging sai khuôn**: mở bằng tên trận đánh sách giáo khoa thay vì bí ẩn, kéo CTR tụt đáy dù nội dung hay nhất kênh | **`PACKAGING_REVIEW`** | **VÀNG (`1,7%` / 8.700 imp)** |
| `oaNH9x8wGJ8` (Gia tộc Oda, 3d) | `TESTED` | `BROWSE` | `WATCH` (2,7%) | `OK` (72%) | `OK` (40,7%) | Chủ đề hậu sự không có cá nhân trung tâm / vật chứng mất tích | `KEEP` (CTR 1d đạt `3,3%`) | ĐỂ NGUYÊN (`3,3%`) |
| `ts2jRcYt33s` (Gia Khang mộ Sakai, 4d) | **`EXPANDING`** | `BROWSE` | **`STRONG` (3,8%)** | **`STRONG` (74%)** | `OK` (43,5%) | Không có nút thắt — đang mở rộng Browse (6.100 imp/ngày) | **`KEEP`** | ĐỂ NGUYÊN (`3,5%`) |
| `bdTMvknayUg` (Tín Trường thoát, 5d) | `STALLED` | `BROWSE` | `WATCH` (2,7%) | `OK` (70%) | `OK` (44,2%) | Đề tài "Tín Trường sống sót" bão hoà + trùng tệp tập 456k; đang chạy A/B test | `KEEP` (chờ A/B test xong) | ĐỂ NGUYÊN (`2,7%`) |
| `XCfPtmsdtiM` (Antoku, 6d) | `TESTED` | `BROWSE` | `OK` (3,3%) | `OK` (70%) | `STRONG` (45,1%) | Nhân vật thời Genpei có trần phân phối thấp hơn cụm Chiến Quốc | `KEEP` (chờ A/B test xong) | ĐỂ NGUYÊN (`3,3%`) |
| `F9ckrsz1yZI` (Masamune bắn cha, 7d) | **`STALLED`** | `BROWSE` | **`REVIEW` (2,2%)** | `OK` (70%) | `OK` (40,2%) | Đề tài gia tộc địa phương hẹp + Rec chỉ 71,8% + CTR 1d rơi còn `1,3%` | **`TOPIC_REVIEW`** (hoặc `PACKAGING_REVIEW`) | **VÀNG (`1,3%` / 152 imp)** |
| `BV5I5UNUOdU` (Di hài Tín Huyền, 8d) | `EXPANDING` | `BROWSE` | **`STRONG` (4,3%)** | `OK` (71%) | `OK` (41,9%) | Không có nút thắt — đạt chuẩn mẫu mực của công thức "di hài" | **`KEEP`** | ĐỂ NGUYÊN (`3,8%`) |
| `30egJcn3Q8o` (Tín Trung tự sát, 9d) | **`STALLED`** | `BROWSE` | **`REVIEW` (2,6%)** | `OK` (67%) | `OK` (43,9%) | Nhân vật phụ + câu hỏi "có chạy được không" kém sức hút (CTR 1d `1,0%`) | **`THUMBNAIL_REVIEW`** | **VÀNG (`1,0%` / 201 imp)** |
| `ugjhBQ6fupU` (Di hài Tú Cát, 10d) | `TESTED` | `BROWSE` | **`STRONG` (3,9%)** | `OK` (72%) | **`REVIEW` (36,7%)** | Packaging + Hook tốt nhưng giữ chân giữa/cuối thân bài rơi sớm (AVD 8:18) | `BODY_REVIEW` (rút kinh nghiệm tập sau) | ĐỂ NGUYÊN (`3,1%`) |
| `8ZNy6vD1uls` (Tú Thứ mổ bụng, 11d) | `STALLED` | `BROWSE` | `OK` (3,5%) | `REVIEW` (63%) | **`REVIEW` (35,6%)** | Video dài nhất kênh (25:50) làm APV tụt đáy `35,6%`, kéo CTR 1d giảm `1,7%` | **`THUMBNAIL_REVIEW`** | **VÀNG (`1,7%` / 172 imp)** *(đã vàng ở K12)* |
| `OGrlW37QTcg` (Lợi Hưu mổ bụng, 13d) | `STALLED` | `BROWSE` | `OK` (3,2%) | `OK` (68%) | `OK` (43,4%) | Nhân vật trà đạo trần phân phối hẹp (24,2K imp) | `KEEP` | ĐỂ NGUYÊN (`3,0%` — *K10 đang vàng oan*) |
| `QSdhgQVmNFI` (Nghĩa Kinh, 14d) | `TESTED` | `BROWSE` | **`STRONG` (4,2%)** | `OK` (72%) | `OK` (42,1%) | Trần chủ đề Genpei (43,3K imp dù CTR 4,2% & CTR 1d 4,6%) | `KEEP` | ĐỂ NGUYÊN (`4,6%`) |
| `_c-opbU36dU` (Quang Tú phản bội, 16d) | `TESTED` | `MIXED` | `OK` (3,0%) | `OK` (70%) | `OK` (44,1%) | Câu hỏi "vì sao phản bội" sống nhờ Suggested từ tập 456k (24,9%) | `KEEP` | ĐỂ NGUYÊN (`2,7%`) |
| `t_7hE3EJhvM` (Quang Tú sống/chết, 21d) | **`EXPANDING`** | `BROWSE` | `OK` (3,1%) | `OK` (69%) | `OK` (44,1%) | Không có nút thắt — vẫn ăn 1.800 imp/ngày với CTR 3,8% | **`KEEP`** | ĐỂ NGUYÊN (`3,8%`) |
| `IjGEOWgQOOw` (Hakkōda 1902, 22d) | `TESTED` | `MIXED` | `WATCH` (2,7%) | `OK` (70%) | `OK` (43,2%) | Khác thời đại Chiến Quốc nhưng sống bền nhờ tệp xem lại từ trang kênh (13,5%) | `KEEP` | ĐỂ NGUYÊN (`4,6%`) |
| `CR9KU_5djOg` (Thi thể Tín Trường, 23d) | **`EXPANDING`** | `BROWSE` | `OK` (3,0%) | `OK` (66%) | `OK` (39,9%) | Trụ cột kéo cả kênh — sau 23 ngày vẫn nhận **17.100 imp / +2.300 view mỗi ngày** | **`KEEP`** | ĐỂ NGUYÊN (`2,8%`) |
| `37wgPZeeP4s` (Chủ mưu Honnō-ji, 24d) | `TESTED` | `MIXED` | `OK` (3,6%) | `REVIEW` (60%) | `OK` (41,1%) | Hook tập đầu tiên thấp nhất kênh (60%), hiện ăn theo trang kênh (18,4%) | `KEEP` | ĐỂ NGUYÊN (`3,2%` — *K2 đang vàng oan*) |

> [!IMPORTANT]
> **Lưu ý về 4 video đang chạy `A/B Test running` trên Studio** (`i4_dGGnjfrM`, `bdTMvknayUg`, `XCfPtmsdtiM`, `CR9KU_5djOg`): tuyệt đối **không thay đổi thủ công** tiêu đề/thumbnail trong lúc YouTube đang chạy thử nghiệm A/B để tránh làm hỏng phân phối và nhiễu biến (Mục 8 SOP).

---

## 3 · `CHANNEL_COMPARISON` — SO SÁNH CHUẨN HOÁ CÙNG ĐỘ TUỔI

*(Tuân thủ luật cứng SOP: chỉ đối chiếu các video trong cùng dải tuổi.)*

### Nhóm tuổi 1: Mới đăng `< 48h` (2 tập)
- `aTk9Qx6sFIA` (*Okehazama*, 47h): **9.900 imp** · CTR **1,8%** · Ret30 **77%** · APV **48,9%** · **998 view**.
- `i4_dGGnjfrM` (*Di hài Hijikata*, 23h): **4.500 imp** · CTR **2,3%** · AVD **10:17** · **361 view** *(mới 1 nửa tuổi của Okehazama)*.
- **Đọc nhanh:** So với mốc ~40h của *Di hài Tín Huyền* ghi nhận hôm `04/11` (`29.900 imp`, `CTR 4,1%`, `4.099 view`), cả 2 tập mới đều khởi đầu chậm hơn từ **3 đến 6 lần** về impressions. Với *Okehazama*, lỗi nằm trọn ở **vỏ ngoài (CTR 1,8%)** chứ không phải kịch bản (Ret30 77% cao kỷ lục). Với *Hijikata*, việc nhảy từ Chiến Quốc sang Bakumatsu (1869) làm thuật toán phải dò lại tệp người xem từ đầu.

### Nhóm tuổi 2: Từ `3 – 6 ngày` (4 tập: `oaNH`, `ts2jR`, `bdTM`, `XCfP`)
- **Đứng đầu tuyệt đối:** `ts2jRcYt33s` (*Gia Khang chết ở Osaka? Mộ ở Sakai*, 4 ngày) đạt **29.800 imp · CTR 3,8% · Ret30 74% · 4.136 view**, và riêng ngày `09/11` vẫn nhận **6.100 imp** — gấp **3 đến 12 lần** lượng hiển thị ngày của 3 tập cùng lứa (`oaNH` 1.900, `XCfP` 704, `bdTM` 511).
- **Bài học trực tiếp giữa 2 tập cùng nhân vật hạng S:** `ts2jRcYt33s` (*Gia Khang + ngôi mộ ở Sakai*, 4 ngày = 4.136 view) thắng gấp **2,2 lần** `bdTMvknayUg` (*Tín Trường thoát khỏi Honnō-ji*, 5 ngày = 1.877 view) nhờ **có vật chứng địa điểm cụ thể ngay trên tiêu đề (`「堺の家康の墓」`)** và không bị bão hoà/trùng lặp với tập 456k.

### Nhóm tuổi 3: Từ `7 – 11 ngày` (5 tập: `F9ck`, `BV5I`, `30eg`, `ugjh`, `8ZNy`)
- **2 tập thắng rõ:** `BV5I5UNUOdU` (*Di hài Tín Huyền*, 8d: **58.900 imp · CTR 4,3% · 8.692 view**) và `ugjhBQ6fupU` (*Di hài Tú Cát*, 10d: **39.900 imp · CTR 3,9% · 6.191 view**).
- **2 tập đáy:** `F9ckrsz1yZI` (*Date Masamune bắn cha*, 7d: **6.100 imp · CTR 2,2% · 657 view**) và `30egJcn3Q8o` (*Oda Nobutada*, 9d: **13.700 imp · CTR 2,6% · 1.558 view**). Chênh lệch **13 lần view** dù đăng cách nhau đúng 24 giờ!

### Nhóm tuổi 4: Đã trưởng thành `13 – 24 ngày` (7 tập)
- Phân tầng thành 3 bậc rõ rệt: **Siêu hit** (`CR9KU` 456k) → **Á quân** (`t_7hE` 83,9k) → **Mặt bằng ổn định** (`37wg` 9,3k · `_c-op` 7,3k · `IjGEO` 7,1k · `QSdh` 6,2k · `OGrl` 3,3k). Cả 7 tập đều có CTR ngày `09/11` đạt **2,7% – 4,6%** (không tập nào dưới ngưỡng 2,5%).

---

## 4 · `SUGGESTED_NEIGHBORHOOD` & `SEARCH_FINDINGS`

### 4.1. `SUGGESTED_NEIGHBORHOOD`
Toàn bộ 18 tập có tỷ trọng Suggested từ **4,2% đến 24,9%** (đều `< 40%`). Tuy nhiên, danh sách *"Content suggesting this video"* thu trực tiếp từ Studio cho thấy **3 tín hiệu chiến lược rất rõ**:
1. **Chuỗi tự nuôi nội bộ quanh `CR9KU` (456k):** Tập *Thi thể Tín Trường* là nguồn kéo view số 1 cho `_c-opbU36dU` (**27,4%** traffic gợi ý), `37wgPZeeP4s` (**25,3%**), `oaNH9x8wGJ8` (**18,3%**), `aTk9Qx6sFIA` (**13,0%**) và `t_7hE3EJhvM` (**12,5%**). Mỗi tập bám đúng cụm Tam Anh Kiệt / Honnō-ji đều được hưởng dòng chảy tự nhiên từ tập 456k.
2. **Hàng xóm ngoại kênh hé lộ những đề tài đối thủ đang ăn view trong cùng tệp khán giả:**
   - Cạnh `ts2jRcYt33s` (*Gia Khang*): xuất hiện `【437年の謎】秀頼の兄・豊臣鶴松の本当の父親をAIに当時の記録で採点させたら…` (4,0%) và `【432年の謎】石川五右衛門は実在したのか？釜ゆでにされた男の正体を当時の記録から追う` (1,3%) — chứng tỏ đã có **kênh đối thủ nhái sát format câu chữ `AIに当時の記録で採点させたら` của Lane X**!
   - Cạnh `aTk9Qx6sFIA` (*Okehazama*): xuất hiện `【150年の謎】西郷隆盛は本当に「美しく切腹」したのか？首が消えた最期を記録から検証` (5,6%).
   - Cạnh `ugjhBQ6fupU` (*Di hài Tú Cát*): xuất hiện `【428年の謎】秀吉の遺体は260日後、「隠密」に山へ運ばれた——家康が閉ざした"神の社"と、明治の山頂の壺` (2,2%).
3. **Cảnh báo lệch tệp ở tập `i4_dGGnjfrM` (*Hijikata — Bakumatsu*, 23h):** Top 2 video đang gợi ý sang tập này hiện là **video review đồ 100 yên CanDo và áo khoác Uniqlo** (mỗi cái 3,4%) — dấu hiệu thuật toán chưa ghép được tập Bakumatsu vào cụm lịch sử Chiến Quốc sẵn có của kênh trong 24h đầu.

### 4.2. `SEARCH_FINDINGS`
- Tỷ trọng Search toàn kênh đạt **0,4% – 3,2%** (`< 5%` ở cả 18/18 tập) ⇒ **`SEARCH_STATUS = IMMATERIAL`**.
- Theo đúng luật SOP, **không diễn giải phần trăm từng từ khoá tìm kiếm** và không tối ưu tag/SEO; chỉ có một tín hiệu nhận diện thương hiệu nhỏ là đã có khán giả gõ trực tiếp tên kênh `ai謎解き研究所` vào ô tìm kiếm.

---

## 5 · `TOP_PATTERNS` — KIỂM NGHIỆM THỰC TẾ SAU 18 TẬP (ĐỂ CHỌN TẬP TIẾP THEO)

Báo cáo ngày `04/11` (khi mới có 11 tập và *Di hài Tín Huyền* mới 40h) tạm xếp Kiểu B trên Kiểu A. Nay với **17 tập đã đủ tuổi (≥ 47h)** và kết quả thực chiến của loạt tập tuần `04/11–09/11`, bức tranh thực sự đã đảo chiều rõ ràng:

| Hạng | Kiểu câu hỏi | Số tập (≥47h) | Median Impr | **Median CTR** | **Median View** | Các tập tiêu biểu | Kết luận thực chiến |
|---:|---|---:|---:|---:|---:|---|---|
| **1** | **A. Vật chứng / Di hài biến đi đâu?** (`遺体はどこへ`) | 3 | **58.900** | **3,90%** | **8.692** *(mean 157.091)* | Tín Trường (**456.389**) · Tín Huyền (**8.692**, CTR 4,3%) · Tú Cát (**6.191**, CTR 3,9%) | **Công thức số 1 của kênh.** 3/3 tập Chiến Quốc đều vượt xa median kênh cả về Impressions lẫn CTR |
| **2** | **B. Sống sót / Thế thân (`本当に死んだのか`)** | 5 | 29.800 | 3,30% | **4.136** *(mean 19.729)* | Quang Tú (**83.858**) · Nghĩa Kinh (**6.209**) · **Gia Khang mộ Sakai (4.136, đang tăng mạnh)** · Antoku (2.563) · Tín Trường thoát (1.877) | **Chỉ mạnh khi đi kèm "vật chứng/địa điểm thật"** (chùa Tenkai, ngôi mộ ở Sakai). Nếu hỏi chung chung hoặc nhảy sang Genpei thì giảm nửa lực |
| **3** | **C. Động cơ / Hung thủ / Vì sao?** (`なぜ切腹` / `黒幕`) | 5 | 30.500 | 3,20% | **5.799** *(mean 5.285)* | Chủ mưu Honnō-ji (9.282) · Quang Tú phản bội (7.341) · Tú Thứ (5.799) · Lợi Hưu (3.347) · Masamune bắn cha (**657**) | **Bám Honnō-ji thì trung bình khá; rời sang chuyện nội bộ gia tộc địa phương (Masamune) là rơi xuống đáy 657 view** |
| **4** | **D. Chiến thuật quân sự / Hậu sự** (`奇襲` / `逃げられた` / `一族`) | 4 | **13.400** | **2,65%** | **1.690** *(mean 2.857)* | Hakkōda (7.050) · Gia tộc Oda (1.821) · Tín Trung (1.558) · Okehazama (**998**, CTR 1,8% nhưng Ret30 **77%**) | **Yếu nhất toàn kênh.** Người xem trên Home/Browse KHÔNG click vào câu hỏi kiểu bài giảng quân sự/hậu sự (CTR tụt còn 1,8–2,7%) |

### 3 quy luật rút ra cho việc chọn tập tiếp theo:
1. **Phải có "Vật chứng vật lý" ngay ở Tiêu đề + Thumbnail:** *thi thể biến mất*, *ngôi mộ bí ẩn ở Sakai*, *chiếc đầu mất tích*, *hộp sọ/bảo vật thất lạc*. Khi có vật chứng vật lý + đại danh tướng Chiến Quốc, CTR bật lên **3,8% – 4,3%** và Browse tự mở 30K–60K+ impressions.
2. **Giữ trục Chiến Quốc (Tam Anh Kiệt + đại danh tướng hạng S) làm xương sống ≥ 80% lịch đăng:** Mỗi lần rời Chiến Quốc sang Genpei (*Antoku* 2,5k), trà nhân (*Rikyū* 3,3k), gia tộc vùng Đông Bắc (*Masamune* 657), hay Bakumatsu (*Hijikata* 361 sau 23h), impressions lập tức co lại.
3. **Không dùng nhãn sách giáo khoa `【Tên trận đánh・Năm】` ở đầu tiêu đề:** Cả 2 tập mới dùng kiểu mở đầu `【桶狭間の戦い・1560年】` (CTR 1,8%) và `【箱館戦争・1869年】` (CTR 2,3%) đều tụt CTR mạnh so với khuôn chuẩn `【N年の謎】` / `【N年の歴史ミステリー】` (CTR 3,1–4,3%).

---

## 6 · MENU LỰA CHỌN CÁC TẬP TIẾP THEO (ĐỂ ANH CHỐT)

### 6A. Kiểm kê các tập ĐANG HẸN GIỜ hoặc TỒN KHO trên máy / Sheet

| Mã / Dòng Sheet | Đề tài | Trạng thái thật (đã kiểm Studio + ổ cứng) | Đánh giá & Đề xuất cho anh chọn |
|---|---|---|---|
| **`cq3BCZlYlwM`** *(Dòng 23 Sheet)* | `【AI検証】本能寺に現代の狙撃手を1人送り込んだら、信長は生き延びられたのか？` *(3D lịch sử IF — dài 10:48)* | **ĐÃ UPLOAD & ĐANG `Scheduled` TRÊN STUDIO LANE X** | Đây là format mới (10:48, 3D quân sư IF từ `3D\episodes\ls\ep02-honnoji`), ngắn bằng 1/2 chuẩn 24 phút của kênh. **Anh quyết định:** giữ lịch đăng để test phản ứng tệp khán giả Honnō-ji của kênh, hay dời sang kênh 3D riêng (`歴史の真相ファイル`). |
| **`ep20-saigo-shiroyama`** *(Dòng 21 Sheet)* | Saigō Takamori có thật sự chết ở Shiroyama 1877? Chiếc đầu biến mất | **CHƯA ĐĂNG STUDIO**, nhưng **ĐÃ DỰNG XONG `final.mp4` (1.069,8 MB)** + 6 thumbnail trong `MG_STUDIO\episodes\x\ep20-saigo-shiroyama\`, cột E trên Sheet còn trống | **Nên tận dụng đăng (không bỏ phí file đã render)**, NHƯNG lưu ý: search `西郷隆盛 生存説` rất thấp (top 3,2k view), trong khi video đối thủ đang ăn gợi ý cạnh kênh mình dùng góc **`首が消えた` (cái đầu biến mất)**. **Đề xuất:** khi lên tiêu đề/thumb cột E, xoáy vào **`【149年の謎】西郷隆盛の「首」はどこへ消えたのか？…`** (Kiểu A — vật chứng), không dùng chữ `生存説` làm chính, và xếp xen kẽ sau 1–2 tập Chiến Quốc. |
| **`ep05-hideyori`** *(Dòng 6 Sheet, `done x2`)* | Toyotomi Hideyori có chết ở thành Osaka 1615? (thuyết trốn sang Satsuma) | ID `wJNVCS24HPg` **không có trên Studio kênh X**, file `final.mp4` đã xoá (còn `canh.json`, `DANG.md`, 4 thumb) | **Rất khớp mạch đang nóng!** Tập `ts2jRcYt33s` (*Gia Khang ở Osaka 1615*) đang `EXPANDING` mạnh nhất tuần qua (6.100 imp/ngày), và thị trường Nhật có nhu cầu tốt (`豊臣秀頼 生存説`: **top 200.423 view**, 4/9 video dài ≥50k). Nếu tập này trước đây đăng ở kênh nháp khác hoặc chưa lên kênh X, **dựng lại từ `canh.json` có sẵn sẽ cực nhanh và nối thẳng tệp người xem Osaka 1615**. |
| **`ep06-ryoma`** *(Dòng 7 Sheet, `done x2`)* | Ai đã ám sát Sakamoto Ryōma ở Ōmiya 1867? (5 thuyết) | **Không có trên Studio kênh X**, `final.mp4` đã xoá (còn `canh.json`, `DANG.md`, 4 thumb) | Nhu cầu thị trường cực lớn (**top 1.019.333 view**), nhưng **bão hoà 100%** (12/12 video dài top đều ≥50k) và thuộc thời Bakumatsu. Chỉ nên dựng lại sau khi xem tập *Hijikata* (cùng Bakumatsu) sau 72h có vượt được 3.000 view hay không. |
| **Hồ sơ `Uesugi Kenshin`** *(`_bo/ep21-kenshin-shiin`)* | `【448年の謎】上杉謙信は毒殺・暗殺されたのか？それとも脳卒中だったのか？` | Hồ sơ đặc tả [LANE_X_EP20_HO_SO_GIAO_CLAUDE.md](file:///E:/CLAUDE/YOUTUBE/MG_STUDIO/episodes/x/LANE_X_EP20_HO_SO_GIAO_CLAUDE.md) rất kỹ, thư mục nháp đang để ở `_bo/` | Đúng đại danh tướng Chiến Quốc hạng S (đối trọng trực tiếp của tập *Tín Huyền* 8,7k view!), nhu cầu vừa sức (**top 58.691 view**, chỉ **2/5 video dài ≥50k** — cạnh tranh thấp!). Góc thư gốc 1578 `「不慮之虫気」` vs `「閑所」` (nhà vệ sinh) là "vật chứng văn bản + hiện trường" rất hợp Lane X. **Đáng khôi phục sản xuất.** |

---

### 6B. Top 6 Đề tài làm mới hoàn toàn (đã đo nhu cầu video dài ≥ 4 phút bằng Data API ngày `11/11`)

*(Xếp hạng ưu tiên kết hợp: **Đúng Kiểu A/B có vật chứng** + **Đúng trục Chiến Quốc** + **Nhu cầu thực tế trên YouTube Nhật từ 06/2024** + **Độ bão hoà vừa phải**.)*

| Ưu tiên | Đề tài đề xuất & Góc câu hỏi chuẩn công thức Lane X | Kiểu | Top 1 View (≥4p) | Số video ≥50k / tổng dài | Lý do chọn & Cách đóng gói để thắng CTR |
|---:|---|---|---:|---:|---|
| **Lựa chọn 1** | **Sanada Yukimura có thật sự chết ở Osaka 1615? Bí ẩn "ngôi mộ & dòng dõi ở Satsuma/Akita"**<br>*(真田幸村は大坂夏の陣で本当に死んだのか？首実検の矛盾と生存説をAIが検証)* | **B + A** *(Sống chết + Vật chứng thủ cấp)* | **375.836** | **1 / 4** *(cạnh tranh rất thoáng)* | **Ứng viên số 1 làm mới.** Nhân vật Chiến Quốc được yêu thích bậc nhất Nhật Bản, nối trực tiếp luồng khán giả *Osaka Natsu no Jin 1615* đang nổ của tập *Gia Khang mộ Sakai* (`ts2jRcYt33s`), có mâu thuẫn sử liệu cực đắt: người mang đầu Yukimura về nhận thưởng khai không khớp tóc/tuổi trong ghi chép đương thời! |
| **Lựa chọn 2** | **Vũ Điền Tín Huyền chết vì bạo bệnh hay bị bắn tỉa ở thành Noda? AI chấm 5 thuyết tử vong 1573**<br>*(【453年の謎】武田信玄はなぜ急死したのか？野田城の狙撃説と病死説をAIが史料で検証)* | **C/B + Vật chứng** | **656.109** | **2 / 7** *(cạnh tranh thấp)* | Tập *Di hài Tín Huyền* (`BV5I5UNUOdU`) vừa đạt **CTR cao nhất toàn kênh (4,3%) và 8.692 view**! Khán giả của kênh đã chứng minh rất thích Tín Huyền; làm tập tiền truyện về bí ẩn viên đạn đêm ở thành Noda sẽ ăn thẳng Suggested từ tập 8,7k view. |
| **Lựa chọn 3** | **Di hài thật của Đức Xuyên Gia Khang nằm ở Kunōzan hay Nikkō? Bí ẩn cuộc cải táng đêm năm 1617**<br>*(【409年の謎】徳川家康の遺体は日光にないのか？久能山と日光、AIが埋葬記録を徹底検証)* | **A** *(Di hài ở đâu)* | **93.655** | **1 / 3** *(gần như bỏ trống)* | Khép trọn **bộ tứ "Di hài Tam Anh Kiệt + Tín Huyền"** (Tín Trường 456k · Tín Huyền 8,7k · Tú Cát 6,2k → Gia Khang), đồng thời nối luôn khán giả tập *mộ Gia Khang ở Sakai* (4,1k đang tăng). Cạnh tranh cực thấp (chỉ 1 video ≥50k). |
| **Lựa chọn 4** | **Thành Azuchi của Tín Trường cháy rụi sau Honnō-ji: Ai đã phóng hoả? AI chấm 4 nghi phạm từ sử liệu 1582**<br>*(【444年の謎】安土城はなぜ焼け落ちたのか？放火犯4つの説をAIが一次史料で採点)* | **A/C** *(Hiện trường + Cụm Honnō-ji)* | **194.542** | **1 / 6** *(cạnh tranh rất thấp)* | Quay đúng về **tâm chấn Honnō-ji 1582** (nguồn sống của tập 456k), có hiện trường vật chất khổng lồ (toà thành 7 tầng biến thành tro sau 13 ngày, chính sử mâu thuẫn giữa quân Quang Tú, con trai Tín Hùng, hay dân cướp bóc). |
| **Lựa chọn 5** | **Thủ cấp Bình Tướng Môn (Taira no Masakado) biến đi đâu? Bí ẩn gò mộ Shōmonzuka giữa trung tâm Tokyo**<br>*(【1086年の謎】平将門の首はどこへ消えたのか？大手町の首塚と複数伝承をAIが史料検証)* | **A** *(Thủ cấp / Ngôi mộ)* | **1.600.706** *(Top 2: 1,56M)* | **12 / 12** *(bão hoà cao)* | Nhu cầu khổng lồ bậc nhất lịch sử Nhật + đúng công thức "thủ cấp biến đi đâu", nhưng ngoài thời Chiến Quốc và độ bão hoà rất cao (12/12 ≥50k). Chỉ chọn khi muốn thử 1 cú đánh lớn bằng góc **thuần sử liệu gốc 『将門記』** tách khỏi truyền thuyết tâm linh. |
| **Lựa chọn 6** | **Cái chết bí ẩn của Phong Thần Tú Cát năm 1598: Bệnh chết hay bị đầu độc? AI kiểm chứng ghi chép giáo sĩ & ngự y**<br>*(【428年の謎】豊臣秀吉は毒殺されたのか？死因の記録をAIが徹底検証)* | **C** *(Nghi án đầu độc)* | **1.732.361** *(Top 2: 600K)* | **15 / 15** *(bão hoà cao)* | Đúng Tam Anh Kiệt + nối tập *Di hài Tú Cát* (6,2k view), nhu cầu cực đại (top 1,73M), nhưng cạnh tranh dày đặc. Phải đối chiếu chặt chẽ nhật ký giáo sĩ Dòng Tên và ghi chép y quan đương thời để khác biệt với video kể chuyện đại trà. |

*(Lưu ý: như đã thấy ở `Content suggesting this video` mục 4.1, đề tài **Ishikawa Goemon có thật sự tồn tại / bị nấu vạc dầu?** và **Toyotomi Tsurumatsu** đã bị kênh đối thủ clone format làm trước — không nên đâm đầu làm trùng ngay lúc này.)*

---

## 7 · `PRIORITY_ACTIONS` & CÁC MỤC CHỜ ANH QUYẾT ĐỊNH

1. **Chọn lô 3–4 tập sản xuất / đăng tiếp theo từ Mục 6:**
   - **Tổ hợp an toàn & hiệu suất cao nhất (khuyến nghị):**
     1. **Làm mới Lựa chọn 1 (*Sanada Yukimura sống/chết ở Osaka 1615*)** hoặc **khôi phục `ep05-hideyori` (*Toyotomi Hideyori ở Osaka 1615*)** — đón đầu ngay sóng Browse 6.100 imp/ngày của tập *Gia Khang mộ Sakai*!
     2. **Làm mới Lựa chọn 2 (*Cái chết bí ẩn của Vũ Điền Tín Huyền ở thành Noda*)** hoặc **khôi phục hồ sơ *Uesugi Kenshin* (`_bo/ep21`)** — đón sóng CTR 4,3% của tập *Di hài Tín Huyền*.
     3. **Làm mới Lựa chọn 3 (*Di hài Gia Khang: Kunōzan hay Nikkō?*)** — hoàn tất bộ tứ "Di hài".
     4. **Tận dụng file đã render `ep20-saigo-shiroyama` (1,07 GB)** bằng tiêu đề xoáy vào **`首はどこへ消えたのか？` (cái đầu biến mất)** để không lãng phí tài nguyên đã dựng.
2. **Giải cứu ngay tập `aTk9Qx6sFIA` (*Trận Okehazama*, đăng 09/11) bằng 1 biến Packaging:**
   - Tập này có **Hook 77% và APV 48,9% cao số 1 lịch sử kênh**, nhưng đang chết oan vì **CTR 1,8%** (nhãn `【桶狭間の戦い・1560年】` quá giống sách giáo khoa). Nếu anh đổi **1 biến trước** (ưu tiên Thumbnail nổi bật nghi vấn trinh thám, hoặc đổi prefix tiêu đề về chuẩn `【466年の謎】桶狭間の戦い、信長の「奇襲」は存在しなかった？一次史料をAIが検証したら…`), tập này rất dễ bật lại vì nội dung giữ chân cực tốt.
3. **Đồng bộ lại Google Sheet tab `X` (chỉ chạy khi anh duyệt):**
   - Hiện trên Sheet tab `X` có **10 dòng tập đã đăng/hẹn giờ đang trống cột L (`video_id`)**: dòng 11 (`ugjhBQ6fupU`), dòng 13 (`30egJcn3Q8o`), dòng 14 (`BV5I5UNUOdU`), dòng 15 (`F9ckrsz1yZI`), dòng 16 (`XCfPtmsdtiM`), dòng 17 (`bdTMvknayUg`), dòng 19 (`aTk9Qx6sFIA`), dòng 20 (`oaNH9x8wGJ8`), dòng 22 (`i4_dGGnjfrM`), và dòng 23 (`cq3BCZlYlwM` — Scheduled). Vì trống cột L nên job tự động buổi sáng đang bỏ sót cả 10 tập này!
   - Đồng thời trên Sheet, **dòng 2 (`37wgPZeeP4s`, CTR 1d = 3,2%)** và **dòng 10 (`OGrlW37QTcg`, CTR 1d = 3,0%)** đang bị tô vàng oan từ lỗi kẹt lịch ngày `08/11`, trong khi 3 tập thực sự `< 2,5%` là `aTk9Qx6sFIA` (`1,7%`), `F9ckrsz1yZI` (`1,3%`), `30egJcn3Q8o` (`1,0%`) lại chưa có ID trên Sheet. Anh nhắn em 1 câu nếu muốn em điền đủ 10 ID vào cột L và cập nhật chuẩn N–S + cột K (có backup JSON trước khi ghi).
