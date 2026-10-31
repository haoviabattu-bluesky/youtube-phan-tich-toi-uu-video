# BÁO CÁO PHÂN TÍCH LANE M — 定年後の盲点【漫画】 / @teinengo-anaba

**Ngày đo:** 2026-10-18 05:20 (giờ máy) · **Nguồn:** YouTube Studio qua Chrome `HAOVIABATTU_PROFILE` cổng 9222 (`tools/studio_collect.py`) + YouTube Data API
**Kênh:** `UC-03gNBRs14lZHus7TiKofA` · 32 sub · 22.225 view tổng · 12 video công khai
**Snapshot CSV:** `youtube_postpublish_metrics.csv` (12 dòng mới, lane `M-teinengo-anaba`) · backup trước khi thu: `reports/backup_metrics_20261018_truoc_laneM.csv`

---

## 0. GIỚI HẠN DỮ LIỆU — đọc trước khi tin bất kỳ kết luận nào

| Vấn đề | Số đo thật | Ảnh hưởng |
|---|---|---|
| Studio còn **"2 days of data still processing"** | Bảng theo ngày chỉ có tới **2026-10-16** | "24h gần nhất" = ngày 10-16, KHÔNG phải 17/18. Ngày 17-18 chưa có số. |
| `hours_since_publish` của tool tính từ 00:00 ngày đăng | ep12 ghi **53h**, thật **44,0h**; ep14 ghi 29h, thật **20,0h**; ep10 ghi 77h, thật **68,0h** | ep12 **CHƯA đủ 48h** nhưng tool đã xếp vào diện xét. Mọi mốc tuổi dưới đây tôi tính lại từ `publishedAt` của Data API. |
| Cột `views` là **tổng view**, còn CTR tính trên **view-từ-impression** | ep05: 48.200 imp × 4,4% = 2.100 = đúng `engaged_views_from_impressions`; nhưng `views` = 10.100 | Phễu SOP phải dùng `engaged_views_from_impressions`, không dùng `views`, nếu không sẽ ra "CTR 2% mà 430 view" (vô lý). |
| `top_search_term_1` bị parse sai khi mục search **không đủ dữ liệu** | ep14 ghi "Browse features 57,1%", ep07 ghi "Browse features 54,3%" | Đã sửa `tools/studio_collect.py` (test: `reports/test_laneM_fixes.py` → ALL PASS). Giá trị đúng: ep14 = `草刈り` (50% của 4,7% ≈ 2 view), ep07 = **không có dữ liệu**. 2 ô sai trong CSV hôm nay đã xoá về rỗng. |
| `report_end_day` không khớp nhãn ngày của Studio (dùng U+2009 thin space) | Hàm trả `None` cho `Sep 19 – Oct 16, 2026` | Đây chính là bẫy "ngày im lặng bị bỏ khỏi bảng" trong CLAUDE.md — bẫy đang SỐNG. Đã sửa `tools/studio_daily.py`, test lại 4/4 nhãn. |
| 3 tập chưa đăng | ep11 (row 12), ep13 (row 14), ep15 (row 16) — cột L trống | Không đưa vào phân tích. |

**Mẫu:** 10 video ≥48h để tính baseline. Đây là mẫu nhỏ, đúng như `CONG_THUC_WIN_LANE_M.md` đã ghi (giả thuyết mạnh, chưa phải định luật).

---

## 1. LANE_BASELINE (n=10 video ≥48h, số trọn đời)

| Chỉ số | Median lane M | Ghi chú |
|---|---|---|
| median_ctr | **3,9%** | (7 ngày đầu tính từ lúc đăng: 4,5%) |
| median_ret30 | **64%** | |
| median_avd | **392,5s** (6:33) | video dài 1.370–1.560s |
| median_apv | **26,25%** | |
| median_48h_impressions | **787** | phân tán cực rộng: 14 → 10.641 |
| median_recommendation | **97,3%** | YouTube CÓ test gần như mọi video |
| median_browse / suggested / search | **82,0% / 15,9% / 1,35%** | search luôn <5% ⇒ IMMATERIAL |
| median_imp_24h / ctr_24h | **505 / 3,45%** | |

**Kết luận baseline:** lane này **không có vấn đề "chưa được test"**. Recommendation 97%+ nghĩa là YouTube đẩy vào Browse ngay. Vì vậy CTR ở đây **có giá trị chẩn đoán** (đúng mục 4 SOP) — khác hẳn các lane bị NOT_TESTED.

---

## 2. BẢNG 12 VIDEO (số trọn đời tại 2026-10-18 05:20)

| Tập | video_id | Tuổi thật | Imp | CTR | View (tổng) | View-từ-imp | AVD | APV | Ret30 | Rec | Browse | Sugg | Search | Imp 24h | CTR 24h | Δ dist |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ep05 | lbJMkB5Vus0 | 212h | **48.200** | 4,4% | **10.100** | 2.100 | 416s | 26,7% | 65% | 99,1% | 82,7% | 15,5% | 0,5% | 3.200 | 3,8% | **+53,3%** |
| ep06 | fRp-ynO-DJs | 188h | **20.600** | 3,5% | **4.200** | 711 | 413s | 26,8% | 65% | 98,4% | 84,7% | 13,6% | 0,6% | 955 | 3,6% | **+35,1%** |
| ep09 | cGZVfCjdRlE | 99,5h | 5.800 | **7,1%** | 2.000 | 400 | 248s | **16,8%** | 62% | 97,3% | **97,5%** | 1,1% | 0,7% | 851 | 7,3% | **−72,5%** |
| ep01 | 6rM_7jwLs2k | 427h | 10.400 | 5,1% | 1.700 | 517 | 415s | 27,8% | 69% | 97,9% | 62,7% | 32,4% | 1,5% | 1.027 | 4,5% | −42,0% |
| ep04 | axCH-36CNxI | 307h | 6.800 | 3,4% | 1.300 | 227 | 307s | 22,5% | **54%** | 96,6% | 88,9% | 8,7% | 1,4% | 54 | 3,7% | **−76,8%** |
| ep07 | 9Bn6J3RtCJ4 | 236h | 6.100 | 4,0% | 1.100 | 242 | 383s | 26,3% | 67% | 97,3% | 81,2% | 16,3% | 2,9% | 142 | 2,1% | −39,8% |
| ep03 | VFdj45ytUaI | 403h | 8.600 | 3,8% | 1.100 | 323 | 307s | 22,0% | 59% | 98,0% | 69,8% | 26,3% | 1,3% | 312 | 2,2% | −1,0% |
| ep10 | nNlqnf28Kak | 68h | 1.700 | **2,0%** | 430 | 33 | **220s** | **15,1%** | **47%** | 96,3% | 95,6% | 1,6% | 0,7% | 699 | 2,0% | −17,8% |
| ep02 | 7hnpdufAVHg | 475h | 4.300 | 3,8% | 415 | 161 | 402s | 26,2% | 63% | 95,4% | **36,9%** | **47,5%** | **8,2%** | 90 | 3,3% | −36,2% |
| ep08 | s8rmYRsePdk | 140h | 2.600 | 4,5% | 383 | 115 | **469s** | **31,4%** | 67% | 93,6% | 48,8% | 42,0% | 3,7% | 274 | 2,6% | −28,6% |
| ep12 | rsdKmuD-y-4 | **44h** | 768 | 3,1% | 217 | 9 | — | — | — | 64,8% | 94,0% | 3,2% | 0,9% | 210 | 4,3% | — |
| ep14 | 0gshT0RitS0 | **20h** | 496 | 2,2% | 42 | 11 | — | — | — | — | 57,1% | 38,1% | 2,4% | — | — | chưa có |

Tổng lane: **116.364 impressions → 22.987 view tổng**. Hai tập ep05+ep06 chiếm **62,2%** tổng view của cả kênh.

---

## 3. PER_VIDEO_REPORT — 4 tập có chẩn đoán rõ ràng

### ep05 `lbJMkB5Vus0` — 再雇用を断った63歳… (212h) · **TẬP THẮNG**
```
A. DISTRIBUTION  Imp 48.200 (4,6× median lane) · Rec 99,1% · Browse 82,7% · Sugg 15,5%
                 Status: EXPANDING (+53,3% vs 24h trước)
B. PACKAGING     CTR 4,4% (median 3,9%) · CTR 24h 3,8% · trend: 5,5→4,7→5,1→3,7→4,0→3,3→4,5→3,8 (giảm dần, bình thường khi mở rộng)
                 Status: OK
C. HOOK          Ret30 65% (median 64%) → Status: OK
D. BODY          AVD 416s · APV 26,7% (median 26,25%) → Status: OK
E. SUGGESTED     Nguồn: 「60歳で辞めた男と、65歳まで会社に残った男。5年後、差がついた…」 (video NGOÀI kênh, cùng ngách)
F. SEARCH        0,5% ⇒ IMMATERIAL (keyword 再雇用 chiếm 21,7% của 0,5% ≈ 10 view — KHÔNG diễn giải)
G. DIAGNOSIS     Không có nút thắt. Đây là video kênh này "được" — 4 chỉ số cùng trên median.
H. ACTION        KEEP
```
**Vì sao thắng:** đúng công thức trong `CONG_THUC_WIN_LANE_M.md` — nhân vật **từ chối** 再雇用, có **con số mất đi** (điều kiện tái tuyển), và **một quyết định**. Không phải "7 việc ngồi được" chung chung.

### ep06 `fRp-ynO-DJs` — 仕事はあるのに収入が安定しない… (188h) · **TẬP THẮNG, RAMP CHẬM**
```
A. DISTRIBUTION  Imp 20.600 · Rec 98,4% · Browse 84,7% · Status: EXPANDING (+35,1%)
                 Hình dạng: 205 → 229 → 2.004 → 14.255 → 1.895 → 707 → 955 (nổ ngày thứ 4, không phải ngày 1)
B. PACKAGING     CTR 3,5% (dưới median nhẹ) · CTR 24h 3,6% → Status: WATCH
C. HOOK          Ret30 65% → OK
D. BODY          AVD 413s · APV 26,8% → OK
E. SUGGESTED     Nguồn ngoài: 「国は教えてくれない…65歳前後に届く“あの封筒”…9選」 (cùng ngách TIỀN)
F. SEARCH        0,6% ⇒ IMMATERIAL
G. DIAGNOSIS     Packaging chỉ ở mức trung bình, nhưng body + chủ đề tiền kéo watch time đủ để YouTube mở rộng.
H. ACTION        KEEP
```
**Bài học riêng:** video này **không nổ trong 48h đầu** (chỉ 434 imp / 104 view). Nếu đánh giá ở mốc 48h sẽ kết luận sai là flop. ep01 cũng vậy (14 imp trong 2 ngày đầu, giờ 10.400 imp).

### ep09 `cGZVfCjdRlE` — 「知ってるつもり」が一番危ない？ (99,5h) · **CTR CAO NHẤT KÊNH NHƯNG BỊ CẮT PHÂN PHỐI**
```
A. DISTRIBUTION  Imp 5.800 · Rec 97,3% · Browse 97,5% (cao nhất lane) · Status: SHARP_DROP (−72,5%)
                 Hình dạng: 30 → 1.561 → 3.090 → 851 (được đẩy mạnh 1 ngày rồi dừng)
B. PACKAGING     CTR 7,1% = 1,8× median lane · CTR 24h 7,3% (vẫn cao) → Status: STRONG
C. HOOK          Ret30 62% (≈ median) → OK
D. BODY          AVD 248s (median 392s = −37%) · APV 16,8% (median 26,25%) → Status: REVIEW
E. SUGGESTED     Nguồn: 「60代、定年後の仕事選びに悩んでいませんか？」 (video NỘI BỘ)
F. SEARCH        0,7% ⇒ IMMATERIAL
G. DIAGNOSIS     PRIMARY = BODY. Packaging thắng click (CTR 7,1%) nhưng APV 16,8% + AVD 248s ⇒
                 watch-time-per-impression thấp ⇒ YouTube ngừng mở rộng. Đây là ca mục 15 SOP:
                 "CTR cao + retention thấp" nhưng KHÔNG phải hook (ret30 62% ổn) mà là THÂN BÀI.
H. ACTION        BODY_REVIEW
```
⚠️ Đây là ca dễ đọc sai nhất: nhìn CTR 7,1% sẽ tưởng "packaging tốt nên giữ nguyên". Thực tế phân phối đã bị cắt 72,5% **dù CTR tốt** — nguyên nhân nằm ở watch time, không ở thumbnail.

### ep10 `nNlqnf28Kak` — あなたの時間、タダで差し出していませんか？ (68h) · **NÚT THẮT KÉP**
```
A. DISTRIBUTION  Imp 1.700 · Rec 96,3% · Browse 95,6% · Status: STABLE (−17,8%)
B. PACKAGING     CTR 2,0% (median 3,9% = 51% của median) · CTR 24h 2,0% · KHÔNG cải thiện sau khi đổi tiêu đề 16/10
                 Status: REVIEW
C. HOOK          Ret30 47% (median 64% = −17 điểm) → Status: REVIEW
D. BODY          AVD 220s (median 392s = −44%) · APV 15,1% (median 26,25%) → Status: REVIEW
E. SUGGESTED     Nguồn: 「仕事はあるのに収入が安定しない…」 (video NỘI BỘ — chính ep06)
F. SEARCH        0,7% ⇒ IMMATERIAL
G. DIAGNOSIS     PRIMARY = PACKAGING (CTR 2,0% với 1.700 imp đã đủ mẫu).
                 SECONDARY = HOOK (47% ở giây 30) + BODY (APV 15,1%).
H. ACTION        PACKAGING_REVIEW
```
Ghi chú: tiêu đề đã đổi ngày 16/10 (cũ: 「時給1,250円が実質約816円に…遠距離通勤の落とし穴」) nhưng CTR 24h vẫn 2,0% — **đổi tiêu đề không cứu được**, nghi thumbnail là biến chưa đổi.

---

## 4. CHANNEL_COMPARISON — đọc theo cùng mốc tuổi (48h từ lúc đăng)

SOP mục 2/18: chỉ so A@48h với B@48h. Đây là bảng 48h tính từ ngày đăng:

| Tập | Tuổi | Imp 48h | CTR 48h | View 48h | Δ so median (787) |
|---|---|---|---|---|---|
| ep05 | 212h | **10.641** | 4,86% | 3.495 | **13,5×** |
| ep08 | 140h | 1.666 | 4,89% | 256 | 2,1× |
| ep09 | 99,5h | 1.591 | 7,58% | 497 | 2,0× |
| ep10 | 68h | 1.549 | 2,11% | 398 | 2,0× (nhưng CTR thấp) |
| ep07 | 236h | 985 | 4,53% | 217 | 1,25× |
| ep04 | 307h | 787 | 3,58% | 226 | 1,0× |
| ep06 | 188h | 434 | 5,56% | 104 | 0,55× → **rồi nổ ngày 4** |
| ep12 | 44h | 210 | 4,3% | 47 | <48h, chưa xét |
| ep02 | 475h | 32 | 6,27% | 4 | 0,04× → rồi hồi lên |
| ep03 | 403h | 17 | 0,0% | 6 | 0,02× → rồi hồi lên |
| ep01 | 427h | 14 | 0,0% | 2 | 0,02× → rồi lên 10.400 imp |

**Pattern quan trọng nhất:** **4/10 video có "khởi đầu chết" trong 48h đầu rồi sống lại sau 3–6 ngày** (ep01, ep02, ep03, ep06). Nghĩa là **mốc 48h KHÔNG dự báo được gì ở lane này**. Đừng kết luận flop ở 48h.

**Nhóm thắng theo chủ đề** (khớp `CONG_THUC_WIN_LANE_M.md`):
- Có **tiền/điều kiện bị cắt cụ thể** + quyết định: ep05 (10.100), ep06 (4.200), ep09 (2.000 — CTR cao nhất) → 16.300/22.987 view
- Chủ đề **tính cách / thiết kế thời gian / địa lý**: ep02 (415), ep08 (383), ep10 (430), ep04 (1.300) → thấp
- Ngoại lệ đáng chú ý: **ep09 chủ đề "知ってるつもり" (nhận thức) lại có CTR 7,1%** — chủ đề không nằm trong vùng WIN nhưng packaging thắng. Xem lại: tiêu đề có câu hỏi móc + 数字.

---

## 5. SUGGESTED_NEIGHBORHOOD — **phát hiện cấu trúc lớn nhất**

| Tập | Nguồn suggest #1 | Trong kênh? | Cùng ngách? |
|---|---|---|---|
| ep01 | 仕事はあるのに収入が安定しない… | ✅ NỘI BỘ | có |
| ep02 | 高学歴元エリート企業役員…警備バイト… | ❌ NGOÀI | có |
| ep03 | 60代、定年後の仕事選びに悩んでいませんか？ | ✅ NỘI BỘ | có |
| ep04 | 60代、定年後の仕事選びに悩んでいませんか？ | ✅ NỘI BỘ | có |
| ep05 | 60歳で辞めた男と、65歳まで会社に残った男 | ❌ NGOÀI | **rất đúng** |
| ep06 | 国は教えてくれない…“あの封筒”…9選 | ❌ NGOÀI | **rất đúng (tiền)** |
| ep07 | 再雇用を断った63歳… | ✅ NỘI BỘ | có |
| ep08 | 再雇用を断った63歳… | ✅ NỘI BỘ | có |
| ep09 | 60代、定年後の仕事選びに悩んでいませんか？ | ✅ NỘI BỘ | có |
| ep10 | 仕事はあるのに収入が安定しない… | ✅ NỘI BỘ | có |
| ep12 | 再雇用を断った63歳… | ✅ NỘI BỘ | có |
| ep14 | 脱サラしてコンビニ店長になった49歳… | ❌ NGOÀI | **LỆCH** |

- **8/12 nguồn suggest là video CỦA CHÍNH KÊNH** → kênh đang tự nuôi nhau, không lấy được khán giả mới.
- 3 nguồn ngoài đúng ngách đều nói về **một khoản tiền ở tuổi 60–65** (nghỉ hay ở, cái phong bì, lương hưu). Đây là **neighborhood thật** của kênh → nên viết cho đúng người đó.
- ep14 vừa đăng đã được ghép với video **49歳 コンビニ店長** — lệch hẳn nhóm 60+定年. Nếu giữ, phân phối sẽ đi sai tệp.

---

## 6. SEARCH_FINDINGS

- **IMMATERIAL toàn lane.** Median 1,35%; cao nhất ep02 = 8,2% (và ep02 chỉ 415 view).
- Theo luật SOP: search <5% ⇒ không diễn giải % keyword. Cụ thể ep05: 「再雇用」 chiếm 21,7% **của 0,5%** traffic ≈ 10 view — con số này KHÔNG nói lên điều gì về SEO.
- Chỉ ep02 vượt 5% (8,2%, keyword 「定年後の仕事」 3,0%) nhưng tuyệt đối chỉ ~34 view. Không đủ để làm chiến lược search.

---

## 7. TOP_PATTERNS

1. **YouTube luôn test (rec 97%+), nên CTR là chỉ số thật.** Không có video nào NOT_TESTED trong lane.
2. **Watch time quyết định mở rộng, không phải CTR.** ep09 CTR 7,1% (cao nhất) vẫn bị cắt 72,5% vì APV 16,8%. Ngược lại ep06 CTR 3,5% (dưới median) vẫn EXPANDING vì APV 26,8%.
3. **Mốc 48h vô dụng ở lane này** — 4/10 video sống lại sau 3–6 ngày. Phải chờ ≥7 ngày mới kết luận.
4. **Chủ đề "mất tiền cụ thể + quyết định" thắng gấp 4–20×** chủ đề "tính cách/thiết kế thời gian". Xác nhận lại công thức đã chốt 16/10, không cần sửa.
5. **Kênh đang tự suggest chính mình (8/12)** — trần tăng trưởng. Cần chủ đề hút nguồn ngoài (như ep05, ep06 đang làm).
6. **Đổi tiêu đề một mình không cứu được** (ep10: 2,2% → 2,0% sau khi đổi).

---

## 8. ĐÁNH DẤU SHEET — trạng thái hiện tại, CHƯA GHI

Theo luật cột K (CTR 24h < 2,5% ⇒ vàng), dùng **ngày đủ số gần nhất = 2026-10-16**:

| Tập | CTR 24h (10-16) | Đủ 48h? | Kết luận |
|---|---|---|---|
| ep01 | 4,5% | ✅ | để nguyên |
| ep02 | 3,3% | ✅ | để nguyên |
| ep03 | 2,2% | ✅ | **cần đánh dấu** (imp24 = 312, đủ mẫu) |
| ep04 | 3,7% | ✅ | để nguyên (nhưng imp24 chỉ 54 ⇒ sắp chết, xem lại sau) |
| ep05 | 3,8% | ✅ | để nguyên |
| ep06 | 3,6% | ✅ | để nguyên |
| ep07 | 2,1% | ✅ | **cần đánh dấu** (imp24 = 142) |
| ep08 | 2,6% | ✅ | để nguyên |
| ep09 | 7,3% | ✅ | để nguyên — nhưng **BODY_REVIEW** (xem §3) |
| ep10 | 2,0% | ✅ | **cần đánh dấu** |
| ep12 | 4,3% | ❌ **44h** | KHÔNG đánh dấu (chưa đủ 48h) |
| ep14 | chưa có số | ❌ 20h | KHÔNG đánh dấu (chưa đủ 48h) |

Ô K hiện tại: 6 video đang ghi "TIÊU ĐỀ MÔ TẢ + THUMB ĐÃ SỬA XONG 17/10 sửa 3 lần" (ep02, ep04, ep07, ep10, ep12, ep14). Theo luật, ghi đè phải **backup sang `reports/backup_sheet_...json` trước** — tôi chưa ghi gì vào sheet.

---

## 9. PRIORITY_ACTIONS

1. **ep09 → BODY_REVIEW (không phải thumbnail).** CTR 7,1% đang thắng click; cắt ở APV 16,8%/AVD 248s. Đọc lại thân bài từ giây 60 trở đi, so với ep05/ep06 (APV 26,7–26,8%). Nếu định "sửa thumbnail vì tụt phân phối" là sửa sai chỗ.
2. **ep10 → PACKAGING_REVIEW, ưu tiên THUMBNAIL.** Tiêu đề đã đổi 16/10 mà CTR vẫn 2,0% ⇒ biến còn lại là thumbnail. Đồng thời ret30 47% (median 64%) ⇒ hook cũng phải xem, nhưng **một biến một lần**: thumbnail trước.
3. **ep14 + ep12 → WAIT_FOR_MORE_DATA.** ep14 20h (496 imp), ep12 44h (768 imp). Tuyệt đối không đánh dấu, không kết luận — và nhớ 4/10 video lane này sống lại sau 3–6 ngày.
4. **Tái dùng nguồn ngoài của ep05/ep06.** 3 video ngoài đang feed kênh đều nói "một khoản tiền ở tuổi 60–65". Đây là chủ đề nên nhân bản (đúng §1.3 công thức WIN), thay vì tiếp tục chủ đề "tính cách".
5. **Sửa `hours_since_publish`** trong tool (đang cộng tối đa 17,5h) — nếu không, job 05:00 sẽ đánh dấu ep12 sớm hơn luật.

---

## 10. FILE ĐÃ ĐỘNG VÀO

| File | Việc |
|---|---|
| `youtube_postpublish_metrics.csv` | +12 dòng snapshot 2026-10-18 (backup: `reports/backup_metrics_20261018_truoc_laneM.csv`) |
| `tools/studio_collect.py` | Sửa parse `top_search_term_1` khi mục search không đủ dữ liệu (đọc nhầm "Browse features") |
| `tools/studio_daily.py` | Sửa `RANGE_RE` để khớp nhãn ngày có U+2009 thin space (bẫy "ngày im lặng" đang sống) |
| `reports/laneM_20261018_data.json` | Dữ liệu đã chuẩn hoá dùng cho báo cáo này |
| `reports/probe_*.py` | 8 script đo dùng để xác minh (giữ lại để tái kiểm) |

**Chưa động vào:** Google Sheet (0 ô), YouTube (0 thay đổi).
