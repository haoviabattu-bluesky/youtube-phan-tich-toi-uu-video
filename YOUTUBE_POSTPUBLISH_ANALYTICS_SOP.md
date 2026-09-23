# SOP PHÂN TÍCH HIỆU SUẤT VIDEO YOUTUBE SAU KHI ĐĂNG
## Dùng cho Claude Code / agent phân tích từng video, so sánh trong từng kênh/lane và đề xuất hành động

## 1. Mục tiêu

Không đánh giá video chỉ bằng số view. Phải đọc toàn bộ phễu:

IMPRESSION → CLICK → HOOK RETENTION → WATCH TIME → RECOMMENDATION EXPANSION

Mục tiêu là xác định nút thắt chính nằm ở:
- Distribution
- Thumbnail/Title
- Hook 0–30s
- Thân video
- Topic/Audience fit
- Suggested neighborhood
- Search/SEO

---

## 2. Mốc thời gian cần lưu

Mỗi video nên chụp số liệu ở:
- T+6h
- T+12h
- T+24h
- T+48h
- T+72h
- T+7d
- T+14d nếu cần

Tối thiểu: 24h, 48h, 72h, 7d.

Không so video ở mốc thời gian khác nhau. Ví dụ chỉ so A@48h với B@48h.

---

## 3. Chỉ số bắt buộc thu thập

### A. Distribution
1. Thumbnail impressions
2. % from YouTube recommending your content
3. Browse features %
4. Suggested videos %
5. YouTube Search %
6. Direct/unknown %
7. External %

### B. Packaging
8. Thumbnail click-through rate (CTR)
9. CTR theo mốc 24h / 48h / 72h / 7d

### C. View quality
10. Views
11. Engaged views from impressions
12. Unique viewers
13. Watch time from impressions
14. Average view duration (AVD)
15. Average percentage viewed (APV)

### D. Hook
16. Retention 5s
17. Retention 10s
18. Retention 20s
19. Retention 30s
20. Retention 60s

### E. Suggested neighborhood
21. Content suggesting this video
22. Top suggested source videos
23. Top suggested source channels

### F. Search
24. YouTube search terms
25. Search traffic share

### G. Metadata
26. Video length
27. Publish date/time
28. Topic
29. Thumbnail version
30. Title version
31. Hook type
32. Channel/lane

---

## 4. Đọc Distribution trước CTR

Câu hỏi đầu tiên: YouTube đã thật sự test video chưa?

### NOT_TESTED / INSUFFICIENT_DISTRIBUTION
Ví dụ:
- Impressions < 100
- Recommendation thấp
- Traffic chủ yếu Search/Direct

Hành động:
- Chưa kết luận thumbnail fail
- Chưa thay thumbnail chỉ vì CTR thấp
- Kiểm tra topic, audience fit, lane consistency
- Chờ thêm dữ liệu

### TESTED
Ví dụ:
- Impressions khoảng 300+
- Recommendation 70–80% trở lên

Lúc này CTR bắt đầu có giá trị chẩn đoán.

### EXPANDING
Dấu hiệu:
- Impressions vẫn tăng
- Browse/Suggested tăng
- CTR giảm từ từ
- Retention vẫn ổn

Hành động: không sửa vội.

### STALLED
Dấu hiệu:
- Impressions tăng ban đầu rồi nằm ngang
- CTR thấp hoặc retention yếu

Hành động: review.

---

## 5. CTR là gì

CTR = Thumbnail click-through rate.

Nó phản ánh tổ hợp:
Thumbnail + Title + Topic + Audience Match

Không được suy luận:
CTR thấp = thumbnail chắc chắn xấu.

---

## 6. Ngưỡng CTR vận hành nội bộ

Đây là ngưỡng review thực hành, không phải luật tuyệt đối của YouTube:

- >= 8%: mạnh
- 6–8%: tốt
- 4–6%: trung bình / theo dõi
- 3–4%: bắt đầu review packaging
- < 3%: packaging có nguy cơ là nút thắt
- < 2%: cảnh báo mạnh nếu impressions đã đủ

Luôn xem cùng:
- impressions
- traffic source
- lane baseline
- impressions trend

---

## 7. Khi nào nên thay thumbnail

Không dùng rule cứng CTR < 5% = thay.

Nên review thumbnail khi:
1. Impressions >= khoảng 250–500
2. Recommendation cao
3. CTR <= khoảng 3–4%
4. Đường impressions đã stall
5. Không có dấu hiệu YouTube đang mở rộng audience mạnh

Nếu title không có lỗi rõ:
→ ưu tiên THUMBNAIL_REVIEW

Nếu title cũng yếu:
→ PACKAGING_REVIEW

---

## 8. A/B nội bộ

Không đổi title + thumbnail + description cùng lúc.

Ưu tiên:
- Version A: title cũ + thumbnail cũ
- Version B: title cũ + thumbnail mới
- Nếu vẫn yếu mới thử Version C: title mới + thumbnail tốt nhất

Mục tiêu: biết biến nào tạo khác biệt.

---

## 9. Đọc Traffic Source

### Browse cao
Ví dụ Browse = 93%

Kết luận:
- Video recommendation-driven
- Ưu tiên Thumbnail, Title, Topic, Hook, Retention
- SEO tags/search không phải KPI số 1

### Suggested cao
Ví dụ Suggested = 76.9%

Bắt buộc mở:
Content suggesting this video

### Search cao
Nếu Search >= 10–20%
→ mới phân tích sâu keyword/search intent.

Nếu Search < 5%
→ keyword report chỉ tham khảo.

---

## 10. Cách phân tích Content suggesting this video

Với mỗi source video đang suggest mình, ghi:
- SOURCE_VIDEO_TITLE
- SOURCE_CHANNEL
- SOURCE_TOPIC
- SOURCE_THUMB_STYLE
- SOURCE_TITLE_STRUCTURE
- SOURCE_VIDEO_LENGTH
- SIMILARITY_TO_OUR_VIDEO

Sau đó trả lời:
1. Có cùng niche thật không?
2. Có cùng audience không?
3. Có cùng emotional topic không?
4. Thumbnail style có cùng lane không?
5. Title structure có pattern gì?
6. Channel nào lặp lại nhiều lần?

Nếu qua nhiều video cùng lane liên tục xuất hiện các channel/topic giống nhau:
→ đó là RECOMMENDATION_NEIGHBORHOOD

---

## 11. Suggested cao nhưng CTR thấp

Ví dụ:
Suggested = 76.9%
CTR = 2.3%

Hai khả năng lớn:
A. Packaging yếu
B. YouTube đang suggest cạnh sai audience

Nếu source videos rất đúng niche mà CTR vẫn thấp:
→ thumbnail/title có khả năng yếu

Nếu source lệch niche:
→ audience mapping có thể sai

---

## 12. Search terms

Ví dụ:
Search share = 0.4%
Keyword A = 25%

Không được kết luận Keyword A mạnh, vì 25% của 0.4% traffic có thể chỉ là 1 view.

Rule:
- Search < 5% → IMMATERIAL
- Search 5–10% → WATCH
- Search >= 10–20% → MATERIAL, có thể phân tích SEO sâu

---

## 13. AVD và APV

Không đọc AVD một mình.

Ví dụ AVD = 4:33:
- video 6 phút → mạnh
- video 30 phút → yếu hơn nhiều

Phải luôn xem:
VIDEO_LENGTH + AVD + APV

---

## 14. Hook Retention

CTR trả lời:
Người ta có click không?

Hook retention trả lời:
Click rồi có ở lại không?

Lấy các mốc:
5s / 10s / 20s / 30s / 60s

Không dùng CTR để chẩn đoán hook.

---

## 15. Ma trận CTR × Retention

### CTR cao + Retention cao
→ Packaging tốt + Hook tốt
ACTION = KEEP

### CTR cao + Retention thấp
→ Packaging kéo click được nhưng opening yếu
ACTION = HOOK_REVIEW

### CTR thấp + Retention cao
→ Nội dung tốt nhưng packaging yếu
ACTION = THUMBNAIL_REVIEW / TITLE_REVIEW

### CTR thấp + Retention thấp
→ Cả packaging và opening đều có vấn đề
ACTION = PACKAGING_REVIEW + HOOK_REVIEW

---

## 16. Đọc retention 0–30s

Ví dụ khỏe:
- 0s 100%
- 5s 90%
- 10s 84%
- 20s 77%
- 30s 72%

Ví dụ yếu:
- 0s 100%
- 5s 78%
- 10s 63%
- 20s 51%
- 30s 42%

Không dùng một ngưỡng tuyệt đối cho mọi lane.
Phải so với median của 10 video gần nhất cùng lane.

---

## 17. Baseline theo lane

Sau khi có >= 10 video, tính median:
- median_ctr
- median_retention_30s
- median_avd
- median_apv
- median_browse
- median_suggested
- median_impressions_48h

Khi đó ưu tiên baseline riêng của lane thay cho ngưỡng chung.

---

## 18. So sánh video trong cùng kênh

Nên nhóm:
- same_channel
- same_lane
- similar_video_length
- similar_topic_class
- similar_publish_time_window

So:
- 24h impressions
- 48h impressions
- CTR
- Browse %
- Suggested %
- Retention 30s
- AVD
- APV

Không so video mới 12h với video đã 7 ngày.

---

## 19. Status bắt buộc agent phải trả

DISTRIBUTION_STATUS:
- NOT_TESTED
- TESTED
- EXPANDING
- STALLED

TRAFFIC_MODE:
- BROWSE
- SUGGESTED
- SEARCH
- MIXED

PACKAGING_STATUS:
- STRONG
- OK
- WATCH
- REVIEW
- INSUFFICIENT_DATA

HOOK_STATUS:
- STRONG
- OK
- REVIEW
- UNKNOWN

BODY_STATUS:
- STRONG
- OK
- REVIEW
- UNKNOWN

SEARCH_STATUS:
- MATERIAL
- IMMATERIAL
- UNKNOWN

---

## 20. Action agent được phép đề xuất

- KEEP
- WAIT_FOR_MORE_DATA
- THUMBNAIL_REVIEW
- TITLE_REVIEW
- PACKAGING_REVIEW
- HOOK_REVIEW
- BODY_REVIEW
- TOPIC_REVIEW
- AUDIENCE_MATCH_REVIEW
- SUGGESTED_NEIGHBORHOOD_REVIEW
- SEARCH_REVIEW

Không đề xuất DELETE_VIDEO hoặc REUPLOAD_VIDEO chỉ vì view thấp.

---

## 21. Rule mẫu

### Rule A — Packaging review
IF:
- impressions >= 300
- recommendation >= 70%
- CTR < 3.5%
- impressions trend = stalled
THEN:
- PACKAGING_REVIEW

### Rule B — Wait
IF:
- impressions < 100
THEN:
- INSUFFICIENT_DATA
- WAIT_FOR_MORE_DATA

### Rule C — Hook review
IF:
- CTR gần/nhỉnh hơn lane median
- retention_30s thấp rõ so với lane median
THEN:
- HOOK_REVIEW

### Rule D — Body review
IF:
- retention_30s ổn
- APV/AVD thấp
THEN:
- BODY_REVIEW

### Rule E — Suggested neighborhood
IF:
- Suggested >= 40%
THEN:
- bắt buộc thu top suggesting videos/channels

---

## 22. File dữ liệu đề xuất

Tạo:
youtube_postpublish_metrics.csv

Các cột:

channel
lane
episode
video_id
publish_time
snapshot_time
hours_since_publish
video_length_sec
impressions
recommendation_pct
browse_pct
suggested_pct
search_pct
external_pct
ctr
views
engaged_views_from_impressions
unique_viewers
watch_time_from_impressions_hours
avd_sec
apv_pct
ret_5s
ret_10s
ret_20s
ret_30s
ret_60s
top_suggesting_video_1
top_suggesting_channel_1
top_suggesting_video_2
top_suggesting_channel_2
distribution_status
traffic_mode
packaging_status
hook_status
body_status
recommended_action
notes

---

## 23. Báo cáo từng video

VIDEO:
CHANNEL:
LANE:
AGE:
LENGTH:

A. DISTRIBUTION
Impressions:
Recommendation:
Browse:
Suggested:
Search:
Status:

B. PACKAGING
CTR:
CTR vs lane median:
CTR trend:
Status:

C. HOOK
5s:
10s:
20s:
30s:
Status:

D. BODY
AVD:
APV:
Status:

E. SUGGESTED NEIGHBORHOOD
Top sources:
Are they niche-matched?
Status:

F. SEARCH
Search share:
Top terms:
Status:

G. DIAGNOSIS
Primary bottleneck:
Secondary bottleneck:

H. ACTION
KEEP / WAIT / REVIEW...

---

## 24. Báo cáo so sánh trong kênh

Mỗi tuần hoặc sau 5–10 video, tạo bảng:

| Video | 48h Impressions | CTR | Browse | Suggested | Ret 30s | AVD | APV | Diagnosis |

Sau đó tìm:
- video có packaging khỏe
- video có hook khỏe
- video có body khỏe
- video được distribution tốt
- video cần packaging review
- video cần hook review

Không kết luận pattern từ 1–2 video.

---

## 25. Pattern qua nhiều video

Sau >= 10 video, tìm:
- thumbnail pattern nào CTR tốt hơn
- hook type nào Ret30 tốt hơn
- title structure nào Browse tốt hơn
- topic nào Suggested tốt hơn
- video length nào APV tốt hơn
- publish time nào impressions 24h/48h tốt hơn

Chỉ kết luận khi có nhiều video cùng lane.

---

## 26. Ba case mẫu

### Mẫu A
Impressions: 2300
Recommendation: 99.4%
Browse: 93%
CTR: 5.9%

Diagnosis:
- DISTRIBUTION = TESTED / EXPANDING
- PACKAGING = OK
- SEARCH = IMMATERIAL
- ACTION = KEEP
- Cần xem thêm retention + AVD/APV

### Mẫu B
Impressions: 301
Recommendation: 91.3%
Suggested: 76.9%
CTR: 2.3%

Diagnosis:
- DISTRIBUTION = TESTED → STALLED
- PACKAGING = REVIEW
- ACTION:
  - inspect suggesting sources
  - test thumbnail mới

### Mẫu C
Impressions: 57
CTR: 0%
Search: 100%

Diagnosis:
- DISTRIBUTION = NOT_TESTED
- PACKAGING = INSUFFICIENT_DATA
- ACTION:
  - chưa kết luận thumbnail
  - kiểm tra topic/audience fit
  - chờ thêm distribution

---

## 27. SOP chạy cho Claude

STEP 1
Load tất cả video cùng channel/lane.

STEP 2
Chuẩn hóa snapshot:
24h / 48h / 72h / 7d.

STEP 3
Tính lane medians.

STEP 4
Classify distribution:
NOT_TESTED / TESTED / EXPANDING / STALLED.

STEP 5
Classify traffic mode:
BROWSE / SUGGESTED / SEARCH / MIXED.

STEP 6
Evaluate packaging:
CTR + impressions + source + baseline.

STEP 7
Evaluate hook:
5s / 10s / 20s / 30s retention.

STEP 8
Evaluate body:
AVD + APV.

STEP 9
Nếu Suggested >= 40%:
collect source videos/channels.

STEP 10
Nếu Search material:
collect top queries.

STEP 11
Assign primary bottleneck.

STEP 12
Return ONE primary recommended action.

---

## 28. Prompt giao việc cho Claude Code

NHIỆM VỤ:
Phân tích hiệu suất tất cả video đã đăng của từng channel/lane theo SOP này.

YÊU CẦU:
1. Không đánh giá bằng views đơn lẻ.
2. Chuẩn hóa số liệu theo 24h/48h/72h/7d.
3. Tính median của cùng lane.
4. Phân tích lần lượt:
   DISTRIBUTION → TRAFFIC → PACKAGING → HOOK → BODY → SUGGESTED → SEARCH.
5. Không kết luận thumbnail fail nếu impressions < 100.
6. Không dùng rule cứng CTR < 5% = thay thumbnail.
7. Khi CTR thấp phải kiểm tra recommendation source và impressions trend.
8. Khi Suggested >= 40%, bắt buộc phân tích Content suggesting this video.
9. Khi Search < 5%, không diễn giải mạnh keyword percentages.
10. Khi Browse/Suggested chiếm đa số, ưu tiên packaging + retention hơn tags.
11. Nếu impressions đã đủ, recommendation cao, CTR < khoảng 3–3.5% và đường impressions stall:
    đề xuất PACKAGING_REVIEW.
12. Nếu CTR ổn nhưng retention 30s yếu:
    đề xuất HOOK_REVIEW.
13. Nếu 30s retention ổn nhưng APV/AVD yếu:
    đề xuất BODY_REVIEW.
14. Không đề xuất DELETE hoặc REUPLOAD chỉ vì view thấp.
15. Mỗi video phải có:
    DISTRIBUTION_STATUS
    TRAFFIC_MODE
    PACKAGING_STATUS
    HOOK_STATUS
    BODY_STATUS
    PRIMARY_BOTTLENECK
    ACTION
16. Sau từng video, tạo bảng so sánh toàn channel/lane.
17. Cuối cùng rút pattern qua nhiều video.
18. Không kết luận pattern từ 1–2 video.

---

## 29. Output cuối cùng bắt buộc

REPORT_DATE:
CHANNEL:
LANE:
VIDEO_COUNT:

LANE_BASELINE:
median_ctr:
median_ret30:
median_avd:
median_apv:
median_48h_impressions:

PER_VIDEO_REPORT:
...

CHANNEL_COMPARISON:
...

SUGGESTED_NEIGHBORHOOD:
...

SEARCH_FINDINGS:
...

TOP_PATTERNS:
...

PRIORITY_ACTIONS:
1.
2.
3.

---

## 30. Nguyên tắc cuối

Không hỏi:
“Video này nhiều view hay ít view?”

Phải hỏi:
1. YouTube có test không?
2. Test ở đâu?
3. Người ta có click không?
4. Click rồi có ở lại không?
5. Ở lại được bao lâu?
6. YouTube đang xếp mình cạnh nội dung nào?
7. Search có thật sự đáng kể không?
8. Nút thắt chính nằm ở đâu?

Mục tiêu cuối:
IMPRESSION → CLICK → RETENTION → WATCH TIME → MORE DISTRIBUTION
