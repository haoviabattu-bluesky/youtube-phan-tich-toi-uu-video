# BÁO CÁO PHÂN TÍCH TẬP THẮNG — LANE M (2026-10-16)

**Gửi:** máy 1 (người/Claude viết kịch bản + packaging lane M).
**Kênh:** 定年後の穴場ノート · @teinengo-anaba · `UC-03gNBRs14lZHus7TiKofA` · tab sheet `M-teinengo-anaba`.
**Kết quả rút ra để làm theo:** `CONG_THUC_WIN_LANE_M.md` (cùng thư mục). File này là phần **bằng chứng**.

---

## 1. Nguồn dữ liệu và giới hạn

| Nguồn | Lấy lúc | Ghi chú |
|---|---|---|
| YouTube Studio (Reach, Engagement, Audience, bảng theo ngày) qua `tools/studio_collect.py`, Chrome profile `HAOVIABATTU_PROFILE` cổng 9222 | 2026-10-16 07:34–07:39 | 10/10 video, ghi vào `youtube_postpublish_metrics.csv` |
| YouTube Data API (view/like/comment công khai + toàn bộ bình luận) | 2026-10-16 | Kênh: 18.573 view, 28 sub, 10 video |
| 12 kịch bản `FlowHandoff_local\jobs\M-teinengo-anaba\ep01..ep12\script.txt` + title + ảnh thumbnail | 2026-10-16 | ep11, ep12 chưa đăng |

**Giới hạn (đọc trước khi tin kết luận):**
- Mới 10 video, cùng 1 nhân vật và 1 khuôn. Kết luận là **xu hướng mạnh**, chưa phải định luật. Kiểm lại khi có ≥15 tập.
- **Bình luận gần như không có** (10 bình luận/kênh, ep05 nhiều nhất: 6) → không đo tương tác bằng bình luận được. "Tương tác" dưới đây dùng like/1.000 view + engaged views, nhưng mẫu cũng nhỏ.
- ep09 mới 55 giờ: Studio **chưa có AVD/APV/retention**. ep10 mới 31 giờ: chưa kết luận.
- 84–97% traffic là Browse/Home ở hầu hết tập → chủ đề + packaging quyết định phân phối; search không đáng kể (<5%, IMMATERIAL theo SOP), trừ ep02 (7,3%).
- Ngày Studio đủ số gần nhất: **2026-10-14**.

---

## 2. Bảng số 10 tập

Map tập ↔ video: ep01 `6rM_7jwLs2k` · ep02 `7hnpdufAVHg` · ep03 `VFdj45ytUaI` · ep04 `axCH-36CNxI` · ep05 `lbJMkB5Vus0` · ep06 `fRp-ynO-DJs` · ep07 `9Bn6J3RtCJ4` · ep08 `s8rmYRsePdk` · ep09 `cGZVfCjdRlE` · ep10 `nNlqnf28Kak`.

| Tập | Chủ đề | Đăng | Tuổi (h) | Impr | CTR | View | Giờ xem | AVD | APV | Giữ ở 30s | Like/1k view | Phân phối 24h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ep05 | Từ chối 再雇用 | 10-09 | 175 | **43.200** | 4,4% | **9.600** | **191** | 6:54 | 26,6% | 64% | 2,2 | DECLINING |
| ep06 | Cắt ca, thu nhập bấp bênh | 10-10 | 151 | **19.000** | 3,5% | **3.900** | 75 | 6:16 | 24,4% | 64% | 2,3 | SHARP_DROP (từ đỉnh 14.255/ngày) |
| ep09 | Hiểu sai lương hưu → cắt ca người khác | 10-14 | 55 | 4.500 | **7,4%** | 1.600 | 17,8 | — | — | — | 3,2 | **EXPANDING** (30 → 1.561 impr/ngày) |
| ep01 | Việc ngồi làm được (mở bằng cắt ca 18→11) | 09-30 | 391 | 8.700 | 5,3% | 1.400 | 44,6 | 6:35 | 26,4% | 67% | 4,9 | EXPANDING (+31%) |
| ep08 | Kinh nghiệm 総務 bị coi là 0 | 10-12 | 103 | 2.200 | 4,8% | 332 | 8,4 | **8:00** | **32,1%** | **68%** | 6,0 | DECLINING |
| ep07 | Câu hỏi phỏng vấn | 10-08 | 199 | 5.800 | 4,1% | 1.100 | 21,2 | 6:09 | 25,3% | 66% | 2,8 | DECLINING |
| ep04 | Dậy sớm, 2 tiếng sáng | 10-05 | 271 | 6.600 | 3,4% | 1.300 | 15,0 | 4:57 | 21,7% | **54%** | 0,8 | STABLE |
| ep03 | Việc ít giao tiếp | 10-01 | 367 | 8.000 | 3,9% | 1.100 | 27,6 | 4:47 | **20,6%** | 59% | 4,6 | STABLE |
| ep02 | 週3日・午前だけ | 09-28 | 439 | 4.100 | 3,9% | **398** | 13,7 | 6:38 | 26,0% | 62% | 7,5 | STABLE |
| ep10 | Đường xa (1.250円 → thực 816円) | 10-15 | 31 | 642 | 1,9% | 178 | 0,5 | — | — | — | — | QUÁ SỚM |

**Baseline lane M** (median, bỏ ep10 vì quá sớm): CTR **4,1%** · APV **25,7%** · giữ ở 30s **64%** · độ dài 23–26 phút.

---

## 3. Xếp hạng thắng / thua

| Hạng | Tập | Lý do |
|---|---|---|
| **WIN #1** | ep05 再雇用を断った | Gấp 2,3 lần impressions tập thứ 2; 191 giờ xem; CTR + APV trên median; nhiều bình luận nhất; search 「再雇用」 24% |
| **WIN #2** | ep06 シフト削減 | 1 ngày đạt 14.255 impressions; giữ 30s đúng median. Đang rơi mạnh (−87%) là nhịp bình thường sau đợt đẩy |
| **WIN #3 (đang lên)** | ep09 年金の誤解 | CTR 7,4% cao nhất lane, phân phối nhảy 50 lần/ngày. Chờ số retention (kiểm lại 2026-10-18) |
| Bền (evergreen) | ep01 | CTR 5,3%, giữ 67%, vẫn tăng phân phối sau 16 ngày. Thắng nhờ **hook cắt ca**, không nhờ chủ đề "ngồi làm" |
| Thân bài tốt, chủ đề yếu | ep08 | APV/giữ chân tốt nhất nhưng chỉ 2.200 impressions → cách kể đúng, đề không kéo phân phối |
| Trung bình | ep07 | Mọi chỉ số quanh median |
| THUA | ep02, ep03, ep04 | ep02 phân phối kém nhất; ep03 APV thấp nhất; ep04 giữ 30s thấp nhất |
| Chưa xét | ep10 | 31 giờ, CTR 1,9% trên 642 impressions = chưa đủ mẫu (NOT_TESTED) |

---

## 4. Tập thắng tập trung vào chủ đề nào

**3/3 tập thắng + tập evergreen đều xoay quanh TIỀN BỊ CẮT DO TỔ CHỨC QUYẾT ĐỊNH THEO TUỔI:**

| Tập | Thứ bị lấy | Con số trên thumbnail/hook | Câu sỉ nhục |
|---|---|---|---|
| ep05 | Điều kiện tái tuyển (lương giảm, chỗ ngồi cạnh kho tài liệu) | 週5のまま、給料は下がる | 「ほかに行くところも、ないでしょうし」 |
| ep06 | 7 ngày ca/tháng | 先月18日→来月11日, 年金まであと2年 | 「年金もあるし、11日でも困らないですよね」 |
| ep09 | 7 ngày ca của 古賀 (58.800円) | 今月15日→8日 | 「年金、減っちゃうと困るでしょう。古賀さんのためですよ」 |
| ep01 | 7 ngày ca | 先月18日→来月11日 | 「代わりはいくらでもいるんで」 |

**Tập thua đều là chủ đề sở thích/tính cách**, không ai lấy gì của nhân vật: muốn rảnh buổi chiều (ep02), ngại giao tiếp (ep03), dậy sớm (ep04). Khán giả không thấy rủi ro mất tiền nên không bấm và không ở lại.

**Ngách hàng xóm xác nhận điều này:** traffic đề xuất của ep05/ep06 đến từ video 「60歳で辞めた男と、65歳まで会社に残った男」 và 「国は教えてくれない…65歳前後に届く“あの封筒”…失いかけたお金と手続き9選」. Khán giả = người 60–65 **đang cân nhắc ở lại công ty** và **sợ mất tiền vì không biết luật**.

⇒ **NGÁCH WIN LANE M:** 「会社・職場から年齢で値下げされた60代が、お金と尊厳を守る選択」. Các mảng con: 再雇用 · シフト削減/契約 · 年金・保険の誤解 · ở lại vs ra đi.

---

## 5. Các yếu tố trong tập thắng (so với tập thua)

| Yếu tố | Tập thắng (05, 06, 09, 01) | Tập thua (02, 03, 04) |
|---|---|---|
| Câu mở | Thoại của người có quyền, có con số | ep02 nội tâm mệt; ep04 câu tích cực của vợ; ep03 có tiếng quát nhưng chuyện là tính cách |
| Xung đột trong 3 câu đầu | Có, kèm con số mất (18→11, 15→8, 週5) | Yếu hoặc ở câu thứ 4 |
| Cái giá | Tiền + chỗ đứng (「年金まであと2年」) | Thoải mái, cảm giác |
| Kẻ đối đầu | Người có quyền trẻ hơn, lịch sự, nhìn tablet; cuối tập lộ bị 本社 ép | Có nhưng nhẹ (đồng nghiệp chế giễu, 係長 cắt ngân sách) |
| So kè | Ở lại vs ra đi (ep05, 小野寺), mình vs người thay (ep06, 牧), ngưỡng cũ vs mới (ep09, 51万/65万) | Sáng vs cả ngày, hậu trường vs mặt tiền, 部長 vs 総務 |
| Đỉnh cảm xúc | Phẩm giá: từ chối ký, từ chối quay lại 「条件は前と同じで」, không quát | Tự hào cá nhân khi tìm được việc hợp |
| Cái kết | Cân bằng: 「残る人には、残る理由がある」; kẻ đối đầu xin lỗi; còn 1 mất mát thật | Hòa giải + châm ngôn về bản thân |
| Đạo cụ | Thumbnail có con số trước/sau; ep09 có vật đóng khung (hộp trứng) | Thumbnail before/after cảm xúc, không con số |

Những gì **giống nhau ở mọi tập** nên **không phải** lý do thắng: nhân vật 田島/春江/柳瀬, format 7 hạng, câu hỏi A/B/C, CTA cố định, độ dài 23–26 phút.

**Bài học thân bài từ ep08** (APV 32%): đưa hạng 7 lên sớm nhất series (ký tự 735), mở vòng lặp ngay hook (「仕事がなかったんじゃない。名前がなかっただけだ」), mỗi hạng gắn 1 kỹ năng có tên. Áp vào chủ đề WIN để có cả phân phối lẫn giữ chân.

---

## 6. Lỗi đang có cần sửa ở tầng sản xuất

1. **ep12 (chưa đăng):** hook mở bằng tóm tắt 「定年後、俺は警備員になった。だが…」, là tập duy nhất không có xung đột trong 3 câu đầu. Nên viết lại theo khuôn ở mục 2 của công thức trước khi đăng. Lưu ý thêm: `promise.txt` còn ghi hook cũ (đội trưởng 31 tuổi, 「立ってるだけでいいんで」), lệch với kịch bản hiện tại. Chưa có thumbnail.
2. **ep11 (chưa đăng):** chưa có title/thumbnail. Chủ đề "ca đêm xưởng bánh" nằm ngoài vùng WIN. Khi đóng gói, nên đẩy trục **tiền** lên title/thumbnail: ca đêm 1.625円, giảm 4→3 đêm = mất hơn 4万円.
3. **Thumbnail lệch kịch bản:** ep09 ghi 「5つの落とし穴」 trong khi kịch bản có 7 việc; ep07 ghi 「残業多め・休日少なめ」, không có trong kịch bản.
4. **Lương từng việc trong danh sách:** ep05 và ep09 gần như không có số yên. Tập sau mỗi hạng phải có số tiền.
5. **ep02 (`7hnpdufAVHg`):** CTR ngày 2026-10-14 là 2,4% (<2,5%), video đã quá 48 giờ. Theo luật cột K thì dòng này thuộc diện đánh dấu, **nhưng lần này em CHƯA ghi gì vào sheet** (task chỉ là phân tích). Anh muốn em đánh dấu thì nói.

---

## 7. Đề xuất 5 đề tiếp theo (đều trong vùng WIN)

| # | Đề (gợi ý title) | Trục so kè | Con số hook |
|---|---|---|---|
| 1 | 【漫画】65歳まで残った同期と、63歳で辞めた俺｜2年後に差がついた穴場の仕事7選 | Ở lại vs ra đi (khớp video hàng xóm) | Lương 再雇用 giảm 4 phần 10 |
| 2 | 【漫画】「来月は8日で」と言われた64歳｜契約書の"この一行"で守れた仕事7選 | Mình vs người mới vào | 15日→8日, mất ○万円 |
| 3 | 【漫画】「働くと年金が減る」を信じて損した夫婦｜今年の基準で選び直した仕事7選 | Ngưỡng cũ vs mới | 51万→65万 |
| 4 | 【漫画】再雇用の面談で言われた一言｜63歳が"更新しない"と決めた日と、次の仕事7選 | Chỗ ngồi vs công việc | 週5・給料ダウン・席移動 |
| 5 | 【漫画】雇用保険に入れなかった66歳｜週20時間の壁で損しない穴場仕事7選 | Người biết luật vs không biết | 19,5時間 vs 20時間 |

---

## 8. Cần đo lại

- **2026-10-18:** ep09 có retention → xác nhận hook "cú lật tự mình gây ra" có giữ người không.
- **2026-10-18:** ep10 đủ 72 giờ → xem chủ đề tiền đi lại (816円) có vào vùng WIN không. CTR đầu 1,9% đang yếu.
- Sau 5 tập theo công thức: so median CTR/APV/giữ 30s với baseline ở mục 2 (4,1% / 25,7% / 64%).
