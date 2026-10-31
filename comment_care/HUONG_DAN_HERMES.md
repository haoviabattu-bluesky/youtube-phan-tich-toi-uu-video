# HƯỚNG DẪN CHO HERMES — Đọc và trả lời bình luận YouTube (kênh tiếng Nhật của anh)

> Bản 2026-10-22 (đã đối chiếu với code thật). Đọc HẾT file này trước khi làm. Mọi lệnh dưới đây chạy được ngay trên máy này.
> Thư mục làm việc: `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care`
> Lệnh Python luôn là `py -3.13`. Trước mỗi phiên đặt (PowerShell):
> ```
> $env:PYTHONIOENCODING="utf-8"
> $env:SOL_DUNG_9ROUTER="0"
> ```
> Dòng 1: không có thì lỗi `UnicodeEncodeError` khi in tiếng Nhật/Việt. Dòng 2: key sol qua 9router đang hỏng (401), bỏ qua để
> đi thẳng ns24 cho nhanh.
> Máy này **không có `pwsh`**, chỉ có `powershell` (Windows PowerShell 5.1).

---

## 0. LUẬT TUYỆT ĐỐI (vi phạm = dừng ngay, báo anh)

1. **Reply phải RẤT NGẮN như người thật**: 1–2 câu, phần thân ≤ 50 ký tự Nhật (không tính câu xin like/đăng ký).
   Không văn vở, không giảng giải dài, không liệt kê.
2. **CẤM TRÍCH DẪN**: không lặp lại/ngoặc 「」 câu của người bình luận, câu thoại/tiêu đề/lời kể trong video, tục ngữ, danh ngôn,
   hay bất kỳ văn bản nào. Luôn nói lại bằng lời của mình.
3. Nội dung reply chỉ là MỘT trong hai: **đồng tình/thấu hiểu**, hoặc **phản biện nhẹ nhàng có kiến thức** (kiến thức phổ thông,
   ai cũng kiểm chứng được) — kèm 1 lời cảm ơn.
4. **Khó quá / không chắc → chỉ ghi lời cảm ơn**: `コメントありがとうございます。` (xem mục 4.3).
5. **Chỉ dùng gemini hoặc sol (qua ns24) để viết. KHÔNG gọi Claude** (`claude -p`) — anh hết quota.
   Đã tắt trong `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\config\settings.yaml` (`generate_use_claude: false`). Đừng bật lại.
6. **Không bao giờ bấm DISLIKE** bình luận của khách. Không xoá, không ẩn, không báo cáo bình luận nào.
7. **Chrome/GPM**: không `taskkill`/kill chrome theo tên. Tool báo `PROFILE_BUSY` / `GPM_NOT_RUNNING` → **DỪNG**, báo anh.
   Chỉ được tắt đúng profile của lane vừa làm (tool tự tắt).
8. **Google Sheet: KHÔNG xoá/ghi đè gì.** Việc trả lời bình luận không cần đụng sheet.
9. Không đăng bình luận MỚI dưới video, chỉ trả lời (reply) bình luận của khách. Mỗi thread tối đa 1 reply của mình
   (riêng khách trả lời lại mình: tối đa 2). Tool đã chặn trùng, **không bao giờ đăng lại** khi chưa đối chiếu (bước 5).
10. Không nói về bản thân chủ kênh (tuổi, giới tính, nghề, gia đình, "私も…"). Không bịa nội dung không có trong video.
11. Báo cáo cho anh luôn bằng **tiếng Việt**, có dịch nghĩa mọi câu tiếng Nhật, và ghi **đường dẫn tuyệt đối đầy đủ**.

Tool đã tự kiểm phần lớn luật trên (trích dẫn, số, "私も", emoji, @, link, quá 50 ký tự, 2 câu CTA): nháp vi phạm sẽ tự rơi về
lời cảm ơn; câu `EDIT:` vi phạm sẽ bị `review` từ chối (mục 5). Nhưng tool **không hiểu nghĩa** — việc đọc hiểu là của bạn.

---

## 1. Các lane đang làm

Xem nhanh: `py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py channels`

| Lane | Kênh | channel_id | Mail = tên profile GPM | Tab báo cáo | Ghi chú |
|---|---|---|---|---|---|
| F | 定年後のリアル | UCIimxP275YufOXXIlu9y9Lg | VirgiliTraino95@gmail.com | `F-teinengo-real` | khán giả 60–80 tuổi |
| L | 社会のなぜ研究室 | UCjy5fWoigvtCfduJDJ3jTbg | SyedualiBajwa92@gmail.com | `L-shakai-no-naze` | khán giả 20–50 tuổi, đừng dùng giọng người già |
| N | シニア暮らし研究所 | UCqXxSE88mHQiZMvzCdlmk3w | thienduongly7890@gmail.com | `Lane-N` | |
| O | 人生のつづき | UCnwgkB18gTTON1YXNQvxsbg | rosellagreysonbk920@gmail.com | `Lane-O` | chung mail với K → tool **tự chuyển kênh** sang O rồi chuyển về K khi xong |
| P | 日本企業ウォッチ | UC0AVbIBy108MV7dp1Rmux9g | tiffanyhenrietta3@gmail.com | `Lane-P` | chủ đề Nhật–Trung, nhiều bình luận chính trị; không có hồ sơ tập → tool chỉ biết tiêu đề + mô tả |
| Q | 凛とした日本 | UCdz_XWaievFUBOi6wL_evZg | JordaneLaetitia694@gmail.com | `Lane-Q` | như P |

**KHÔNG làm**: lane M (anh chốt không làm — đã tắt trong config), Satori (kênh bị Google đình chỉ), G/E/K/J (đang tắt).
Chỉ làm lane anh giao. Lane mới chưa có trong bảng → dừng, báo anh.

---

## 2. Chuẩn bị (mỗi phiên 1 lần)

```
curl "http://127.0.0.1:9495/api/v1/profiles?page=1&per_page=1"
```
Phải trả JSON `success` trong vài giây. Không trả lời / treo → phần mềm GPMLogin chưa mở hoặc đang treo → báo anh, không tự cài/sửa.
(Bước 1 kéo bình luận + soạn nháp KHÔNG cần GPM, vẫn làm được; chỉ bước đăng mới cần.)

Giờ đăng: 08:00–22:00 giờ Nhật (= 06:00–20:00 giờ Việt Nam). Tool **tự chặn** đăng/like ngoài khung này (in `⏸ ... ngoài khung`).
Ngoài giờ thì chỉ soạn + duyệt, để sáng đăng. Không dùng `--ignore-hours` trừ khi anh bảo.

---

## 3. Bước 1 — Kéo bình luận + soạn nháp tự động

```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py run --channel F --mode draft_only
```
(thay `F` bằng lane được giao; nhiều lane thì chạy lần lượt từng lane.) `--mode draft_only` là bắt buộc — không bao giờ dùng `auto_*` hay `--send`.

Tool làm: lấy bình luận mới qua YouTube Data API → đọc tiêu đề/mô tả video + hồ sơ tập → phân loại bằng gemini →
luật chính sách quyết định → soạn nháp (mẫu cố định, hoặc sol → gemini) → kiểm luật → dịch Việt. **Không đăng gì.** Mất vài phút.

Tool tự xử lý sẵn:
- Hỏi về lương hưu/thuế/luật/thuốc, hoặc em hiểu không chắc → nháp `コメントありがとうございます。` (không CTA).
- Chính trị/xã hội/gay gắt → nháp cố định `はい、ご意見ありがとうございます。` (không CTA). Câu này đúng luật, `APPROVE` được
  (trừ khi bình luận miệt thị/thù ghét → `REJECT`, xem 4.3).
- sol + gemini đều lỗi, hoặc viết mãi vẫn sai luật → nháp tự rơi về `コメントありがとうございます。`.

Kết quả ở `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\reports\comment_care\<YYYY-MM-DD>\<tab lane>\`, ví dụ
`E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\reports\comment_care\2026-10-22\F-teinengo-real\`:

| File | Dùng làm gì |
|---|---|
| `DRAFT_REVIEW.txt` | **File chính.** Mỗi block = 1 bình luận: link, bình luận tiếng Nhật + dịch Việt, phân loại, nháp reply + dịch Việt, dòng `YOUR_DECISION:` |
| `UNRESOLVED_COMMENTS.txt` | bình luận tool bỏ qua (vô nghĩa/1 chữ, không phải tiếng Nhật, khủng hoảng…) — đọc hết, xem 4.3 |
| `HIGH_RISK.txt` | bình luận nhạy cảm (sức khoẻ, mất người thân, khủng hoảng…) — đọc kỹ |
| `COMMENT_REPORT.txt` | thống kê tổng |

"Không có bình luận mới" / 0 draft → lane đó xong phần reply, ghi vào báo cáo, sang lane khác.

---

## 4. Bước 2 — Đọc hiểu và viết reply

### 4.1. Đọc hiểu trước khi viết
Với mỗi block trong `DRAFT_REVIEW.txt`:
- Đọc dòng `VIDEO:` (tiêu đề video) và `COMMENT (dịch tiếng Việt)` — hiểu khách đang **đồng tình, phản đối, kể chuyện, hỏi, hay chửi**.
- Bình luận mơ hồ không rõ ai là người tốt/xấu trong truyện, ai làm gì → không đoán, chỉ cảm ơn.
- Cần thêm ngữ cảnh video: mở `COMMENT_URL` hoặc xem tiêu đề/mô tả. Không bịa chi tiết video.

### 4.2. Viết reply — công thức
```
[1 câu đồng tình HOẶC 1 câu phản biện nhẹ có kiến thức] + [cảm ơn] + [1 câu xin like/đăng ký]
```
Phần thân ≤ 50 ký tự, giọng です・ます đơn giản. Câu xin like/đăng ký — chọn 1, xoay vòng giữa các reply (đúng từng chữ, tool nhận diện theo 3 câu này):
- `よかったら高評価とチャンネル登録、お願いします。`
- `よければ高評価とチャンネル登録もお願いします。`
- `よかったらチャンネル登録と高評価、よろしくお願いします。`

**KHÔNG gắn câu xin like/đăng ký** khi bình luận nói về: người thân mất, bệnh tật, nỗi đau lớn, hoặc là bình luận chửi bới / chính trị.

Mẫu tốt (đồng tình):
- `本当にそうですね。コメントありがとうございます。よかったら高評価とチャンネル登録、お願いします。`
- `同じように思います。見ていただきありがとうございます。よければ高評価とチャンネル登録もお願いします。`
- `大変でしたね。お話ししてくださりありがとうございます。` (chuyện buồn → không CTA)

Mẫu tốt (phản biện nhẹ, có kiến thức phổ thông):
- `見た目より、非常時に開けやすいことが大事だと言われていますね。コメントありがとうございます。`
- `地域によって事情が違うこともあるようです。ご意見ありがとうございます。`

Mẫu SAI (không được dùng):
- `「隠す方がダサい」というお言葉、まさにその通りです…` → trích dẫn bình luận.
- `動画の中で「〜」と言っていたように…` → trích dẫn video.
- `年金は65歳から月○万円なので…` → đưa con số/chế độ.
- 3–4 câu cảm ơn + chúc sức khoẻ + hẹn gặp lại → quá dài, giọng bot.
- `私も同じ経験があります` → nói về bản thân chủ kênh.
- Có emoji, `！！`, `w`, `@tên`, link.

### 4.3. Khi nào chỉ ghi lời cảm ơn / khi nào không trả lời

| Tình huống | Làm gì |
|---|---|
| Khó hiểu, mơ hồ, nhiều nghĩa, không rõ ai là ai | `EDIT: コメントありがとうございます。` |
| Hỏi về lương hưu, thuế, luật, chế độ, thuốc, bệnh, chữa trị | Chỉ cảm ơn (tool thường đã soạn sẵn → `APPROVE`) |
| Chính trị, quốc gia, dân tộc (hay gặp ở lane P, Q) nhưng lịch sự | Chỉ cảm ơn — nháp `はい、ご意見ありがとうございます。` → `APPROVE` |
| Chửi bới kênh/video (HOSTILE) | `APPROVE` nháp cố định, hoặc `EDIT: ご意見をお寄せいただき、ありがとうございます。` (không CTA) |
| Miệt thị dân tộc, kêu gọi bạo lực, thù ghét | `REJECT` — không trả lời, không like. Ghi vào báo cáo để anh tự ẩn trong Studio |
| Có ý tự tử/tự hại, khủng hoảng thật | `REJECT`, báo anh ngay ở đầu báo cáo |
| Spam, quảng cáo, có link | `REJECT` |
| Bình luận của chính kênh | `SKIP` |
| Nháp tool đã ngắn, đúng luật mục 0 | `APPROVE` |
| Nháp dài/trang trọng/có trích dẫn | `EDIT:` viết lại theo 4.2 |

**Bình luận nằm trong `UNRESOLVED_COMMENTS.txt`** (không có block trong DRAFT_REVIEW nên không ghi `EDIT` được). Nếu nó là
bình luận thật bằng tiếng Nhật mà mơ hồ/khó hiểu → tạo reply chỉ cảm ơn bằng `COMMENT_ID` trong file:
```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py thank --channel F --comment-ids UgxAAA,UgyBBB
```
(tự duyệt sẵn, bước đăng sẽ đăng luôn). Vô nghĩa / không phải tiếng Nhật / spam / khủng hoảng → để nguyên, chỉ ghi vào báo cáo.

### 4.4. Nhờ sol / gemini viết khi cần (không dùng Claude)
Nháp của tool (dòng `MODEL:` trong block) đã do sol hoặc gemini viết. Muốn có phương án mới cho 1 draft:
```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tools\viet_reply.py --channel F --draft-id 120 --n 3
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tools\viet_reply.py --channel F --draft-id 120 --model gemini
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tools\viet_reply.py --channel F --comment "コメント本文" --title "動画タイトル"
```
In ra phần thân (chưa có CTA) + số ký tự + `✓ đạt luật` / `✗ <lỗi>`. Chọn 1 phương án `✓`, **tự soát lại theo mục 0 và 4.2**
(máy không hiểu nghĩa), rồi tự gắn câu CTA. sol lỗi → tool tự chuyển gemini. Không ghi gì vào DB.
Ví dụ đã chạy thật 2026-10-22 (sol, ~13 giây): `働くうえでの安心は大切ですね。ご意見をありがとうございます。` (30 ký tự, ✓).

### 4.5. Tự kiểm trước khi ghi
- [ ] Toàn tiếng Nhật, không chữ Việt/Anh, không emoji, không `@`, không link
- [ ] Phần thân ≤ 50 ký tự, 1–2 câu
- [ ] Không có 「」 hay câu lặp lại lời khách/video
- [ ] Không con số/chế độ/thuốc/bệnh; không nói về bản thân chủ kênh
- [ ] Có cảm ơn; có đúng 1 câu CTA (trừ trường hợp buồn/bệnh/chửi/chính trị)
- [ ] Đọc bản dịch Việt của chính câu mình viết thấy tự nhiên như người thật

---

## 5. Bước 3 — Ghi quyết định vào DRAFT_REVIEW.txt

Sửa dòng `YOUR_DECISION:` của từng block, **mọi thứ trên CÙNG 1 DÒNG** (tool chỉ đọc 1 dòng, câu CTA viết liền sau phần thân):
```
YOUR_DECISION: APPROVE
YOUR_DECISION: EDIT: 本当にそうですね。コメントありがとうございます。よかったら高評価とチャンネル登録、お願いします。
YOUR_DECISION: REJECT
YOUR_DECISION: SKIP
```
`EDIT:` thay TOÀN BỘ câu sẽ đăng bằng câu mình ghi. Để trống = chưa xử lý (không đăng).

Áp vào cơ sở dữ liệu:
```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py review --file "E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\reports\comment_care\2026-10-22\F-teinengo-real\DRAFT_REVIEW.txt"
```
Kết quả từng block:
- `draft <id>: EDIT → EDITED` / `APPROVE → APPROVED` … → đã áp.
- `draft <id>: ✗ EDIT KHÔNG áp — sai luật: <lý do>` → câu của bạn vi phạm luật (vd `quote_comment:...` = đang chép lời khách,
  `number`, `owner_self_talk`, `body_too_long 63>50`, `cta_x2`, `no_thanks`). Sửa lại dòng đó rồi chạy lại lệnh. **Không dùng `--force`.**
- `draft <id>: ↷ đã có lượt đăng … → không đổi` → bình luận đã đăng/đang chờ đối chiếu, tool chặn để không đăng lại. Bình thường.

Anh đã chốt **không cần anh duyệt** — xong bước này là sang bước đăng (trừ các trường hợp REJECT/báo anh ở 4.3).

---

## 6. Bước 4 — Đăng qua trình duyệt GPM (gõ chậm như người)

**6.1. Lấy id profile GPM của lane** (thay mail theo bảng mục 1):
```
py -3.13 -c "import sys;sys.path.insert(0,r'E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\src');from comment_care.browser_poster import gpm_find;print(gpm_find('VirgiliTraino95@gmail.com'))"
```
(lane F ra `0de2b1bb-a691-4570-a61d-81af46c40974`.) Ra `None` → không thấy profile → báo anh.

**6.2. Bật watchdog giữ cửa sổ hiện trên màn hình** (chạy NỀN trước khi đăng — anh yêu cầu cửa sổ phải hiện thật, không chạy ẩn):
```
powershell -NoProfile -ExecutionPolicy Bypass -File E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tools\keep_visible.ps1 -ProfileId 0de2b1bb-a691-4570-a61d-81af46c40974
```
Nó chỉ khôi phục/kéo vào màn hình cửa sổ của đúng profile đó (không đóng, không kill gì), tự thoát khi profile đóng
(hoặc sau 5 phút nếu profile không mở).

**6.3. Đăng** (lần đầu trong phiên chạy `--dry-run` trước — mở trình duyệt, tìm bình luận, không gõ, không bấm like):
```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py post-browser --channel F --dry-run
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py post-browser --channel F
```
Tool tự: mở profile GPM = mail kênh → kiểm đúng kênh (lane O: tự chuyển từ K sang O, xong chuyển về) → mở từng video, cuộn,
mở đúng bình luận → **like + thả tim** theo luật dưới → gõ 60–180 ms/ký tự → nghỉ 60–150 giây giữa 2 reply, 30–90 giây khi chuyển
video → **tự tắt profile** khi xong (kể cả khi lỗi). 10 reply mất khoảng 20–30 phút — chạy nền, đừng ngắt giữa chừng.
Không dùng `--keep-open` trừ khi anh bảo.

Luật like/tim tự động (dòng đầu lệnh in `like N · tim M`):
- **Like**: mọi bình luận của khách, TRỪ chính trị/gay gắt/khủng hoảng/spam/vô nghĩa và câu tool hiểu không chắc
  (anh chốt 2026-10-15: like/tim lên câu nhạy cảm = kênh đồng tình).
- **Tim**: chỉ bình luận tích cực (khen, cảm ơn, đồng tình, kể chuyện, xin chủ đề).
- Không bao giờ dislike. Nút đã bật sẵn thì không bấm lại (bấm lại là gỡ). `--no-react` = không like/tim gì.

Chỉ muốn like/tim (không reply), ví dụ bình luận cũ chưa like:
```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py react-browser --channel F --list
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py react-browser --channel F
```
(`--list` chỉ in danh sách; mặc định 14 ngày gần nhất, tối đa 30 bình luận — đổi bằng `--days`, `--limit`.)

Đọc kết quả JSON cuối lệnh: `SENT` = đã thấy reply hiện; `UNKNOWN_RECONCILE` = đã bấm gửi nhưng chưa thấy (**không đăng lại**, sang bước 5);
`NOT_FOUND` = không tìm thấy bình luận (có thể khách đã xoá); `SKIPPED_OWNER_EXISTS` = kênh đã trả lời thread này rồi.
Lệnh in `✗ DỪNG: ...` (GPM tắt/bận, sai kênh, chưa đăng nhập…) → xem mục 9.

---

## 7. Bước 5 — Đối chiếu bằng YouTube Data API (bắt buộc trước khi báo "đã đăng")

```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tools\verify_replies.py --channel F
```
`✓ ĐÃ THẤY` → đã ghi `youtube_reply_id`. `✗ CHƯA THẤY` → đợi 5–10 phút chạy lại (API có độ trễ; YouTube tự chèn `@tên` ở đầu reply,
tool đã xử lý). Chạy lại vẫn chưa thấy → mở link bình luận xem tận mắt, ghi vào báo cáo. **Tuyệt đối không đăng lại.**
Tốn ~1 unit quota / thread.

---

## 8. Bước 6 — Báo cáo cho anh (tiếng Việt)

```
LANE F — 定年後のリアル — 2026-10-22
Bình luận mới: 12 trên 4 video | Đã reply: 9 | Chỉ cảm ơn: 2 | Không trả lời: 1 (lý do) | Like: 12, tim: 7
| Video | Bình luận khách (dịch Việt) | Reply đã đăng (Nhật) | Dịch Việt | API |
| ...   | ...                          | ...                  | ...       | ✓   |
KHÁN GIẢ NÓI GÌ: chủ đề lặp lại, chuyện thật họ kể, câu hỏi/phản đối hay gặp, tín hiệu nhạy cảm (3–6 gạch đầu dòng).
CẦN ANH XỬ LÝ: bình luận thù ghét cần ẩn (kèm link), khủng hoảng, UNKNOWN_RECONCILE còn treo, lỗi GPM.
File: E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\reports\comment_care\2026-10-22\F-teinengo-real\DRAFT_REVIEW.txt
```

---

## 9. Xử lý sự cố

| Gặp | Làm |
|---|---|
| `✗ DỪNG: PROFILE_BUSY` | DỪNG lane đó, báo anh đóng cửa sổ profile. Không kill |
| `✗ DỪNG: GPM_NOT_RUNNING` | GPMLogin không trả lời → báo anh mở/khởi động lại GPM. Không tự sửa |
| `✗ DỪNG: GPM websocket RỖNG` | Profile bị mở dở: `curl http://127.0.0.1:9495/api/v1/profiles/stop/<id>`, đợi 10 giây, chạy lại. Vẫn lỗi → báo anh |
| `✗ DỪNG: không thấy profile GPM tên …` | Báo anh (tên profile trong GPM khác mail) |
| `✗ DỪNG: IDENTITY_MISMATCH` / `CHƯA đăng nhập` / `không chuyển được sang kênh` | Dừng, báo anh. Không tự đăng nhập Google |
| `⏸ ... ngoài khung 8–22h` | Ngoài giờ Nhật → để sáng chạy lại |
| `quotaExceeded` (YouTube API) | Dừng phần kéo bình luận/đối chiếu, hẹn hôm sau |
| sol và gemini đều lỗi khi soạn | Tool đã tự rơi về lời cảm ơn; muốn hay hơn thì viết tay theo 4.2 |
| `không có draft APPROVED/EDITED nào để đăng` | Chưa chạy bước 3 (`cc.py review`) hoặc dòng YOUR_DECISION để trống / bị từ chối |
| `UnicodeEncodeError` | Quên đặt `$env:PYTHONIOENCODING="utf-8"` |
| Tra lịch sử 1 bình luận | `py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py audit --comment-id <id>` |

## 10. Không được đụng
- Không sửa code trong `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\src\`, `E:\CLAUDE\YOUTUBE\h2dev\`, không sửa
  `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\config\channels.yaml` trừ khi anh bảo.
- Không xoá `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\state\comment_care.sqlite` (nhớ những gì đã trả lời và đã like — xoá là đăng trùng / bấm like lần 2 thành gỡ like).
- Không đổi tiêu đề/mô tả/thumbnail video, không vào Studio sửa gì, không đụng Google Sheet.
