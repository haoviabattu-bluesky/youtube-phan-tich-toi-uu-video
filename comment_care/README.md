# comment_care — chăm sóc bình luận YouTube tiếng Nhật (policy-driven, draft-first)

Đọc bình luận trên kênh của mình → đọc hiểu video (title/description + thư mục tập của h2dev) → phân loại 21 nhóm → Policy Engine quyết
định REPLY/SKIP/ESCALATE → soạn reply tiếng Nhật (template hoặc LLM) → QC rule + judge khác họ → `DRAFT_REVIEW.txt` để anh duyệt.
**Mặc định không gửi gì lên YouTube.** Spec: `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\docs\superpowers\specs\2026-10-05-youtube-comment-care-design.md`.

## Chạy

```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py channels
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py run --channel F --mode draft_only
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py run --channel F --mode draft_only --only-video vy7ucq5Zy64 --limit 5
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py review --file "E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\reports\comment_care\2026-10-05\F-teinengo-real\DRAFT_REVIEW.txt"
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py audit --comment-id Ugx...
py -3.13 -m unittest discover -s E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\tests
```

Mode: `fetch_only` (kéo + phân loại, không soạn) · `draft_only` (soạn, không gửi) · `shadow` (như draft nhưng ghi WOULD_SEND) ·
`auto_low` / `auto_full` (gửi — chỉ khi **cả 3**: env `COMMENT_CARE_AUTO_REPLY=1` + mode auto trong `config\channels.yaml` + cờ `--send`,
và đã có token OAuth `D:\CLAUDE\credentials\youtube_oauth\<channel_id>.json`). `--dry-run` thắng tất cả.

## Output mỗi run
`E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\reports\comment_care\<YYYY-MM-DD>\<tab lane>\`
`COMMENT_REPORT.txt` · `DRAFT_REVIEW.txt` (ghi `YOUR_DECISION: APPROVE | EDIT: <câu sửa> | REJECT | SKIP`) · `UNRESOLVED_COMMENTS.txt` ·
`HIGH_RISK.txt` · `reply_log.jsonl`. State: `comment_care\state\comment_care.sqlite` (gitignore).

## Cấu trúc
`config\` (channels.yaml, settings.yaml) · `policy\` (policy_table.yaml = luật, ja_style_guide.md, blocklist_ja.txt) · `prompts\v1\` ·
`templates\ja\templates.yaml` · `src\comment_care\` (yt_api, context, prefilter, classifier, policy, templates, generator, qc_rules, judge,
sender, report, review, pipeline, cli) · `tests\`.

## Nguồn dữ liệu
- Comment: YouTube Data API v3 bằng API key `YOUTUBE_API_KEY` (`E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env`), per video, 1 unit/100 thread.
- Nội dung video: Sheet `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` tab lane cột L (video_id) → cột C (thư mục assets) →
  `research\S1_TOM_TAT.json`, `promise.txt`, `story_facts.json`, `TIEU_DE_MO_TA.txt`; fallback khớp tiêu đề trong assets dir hoặc
  `E:\CLAUDE\YOUTUBE\h2dev\FlowHandoff_local\jobs\<tab>\<slug>\` (dan_y/script head). Không bao giờ nạp full script.
- LLM: module h2dev `llm_client` (gemini-3.8-flash classify), `claude_p_bridge` (claude-opus-5-5 soạn), `sol_client` (gpt-5.6-sol judge).

## Bẫy đã đo (2026-10-05)
- `allThreadsRelatedToChannelId` trả 403 commentsDisabled khi kênh có video tắt comment/kênh bị đình chỉ → tool đi theo từng `videoId`.
- Kênh Satori `UC9huXCiBIXBfUh11D7ZsFSA` đã bị Google đình chỉ → API trả 0, mọi video 404. Pilot = lane F.
- YAML `footer: no` đọc thành `False` → policy.py chuẩn hoá về chuỗi.
- Comment của chính kênh (câu hỏi ghim 👇) là `is_owner` → không bao giờ vào LLM; viewer trả lời câu hỏi đó là kind `answer`.
