---
title: Comment Care — implementation plan
status: in-progress
priority: P0
created: 2026-10-05
type: implementation
source: brainstorm-summary.md
---

# Comment Care — plan

Module `comment_care` trong repo PHAN_TICH_TOI_UU_VIDEO: đọc bình luận kênh mình, hiểu video, phân loại, soạn reply tiếng Nhật theo policy,
đưa anh duyệt. Spec đầy đủ: `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\docs\superpowers\specs\2026-10-05-youtube-comment-care-design.md`.

## Phases
| # | Phase | Status | Priority | Effort | Depends On |
|---|---|---|---|---|---|
| 1 | Fetch + store + video context + classifier + report (fetch_only) | in-progress | P1 | 1d | – |
| 2 | Policy + templates + generator + rule QC + judge + DRAFT_REVIEW + review CLI (draft_only) | pending | P1 | 1.5d | 1 |
| 2b | OAuth per kênh + sender idempotent + reconcile + kill switch (anh authorize) | pending | P1 | 1d | 2 |
| 3 | Shadow 100 comment + SHADOW_REVIEW + benchmark 5 model | pending | P2 | 1d | 2 |
| 4 | Auto LOW cap 5/ngày, 1 kênh | pending | P2 | 0.5d | 2b, 3 |
| 5 | Mở MEDIUM + HOSTILE template + thêm kênh | pending | P3 | 0.5d | 4 |
| 6 | Daily + AUDIENCE_INSIGHTS_WEEKLY (V2) | pending | P3 | 1d | 5 |

## Key Dependencies
Python 3.13.5; `google-api-python-client`, `google-auth`, `PyYAML`, `requests` (đã cài). YouTube API key `YOUTUBE_API_KEY` trong
`E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env`. h2dev `pipeline\llm_client.py`, `claude_p_bridge.py`, `sol_client.py` (ping OK 2026-10-05:
ramclouds/ns24 gemini-3.8-flash, ns24 deepseek-v4.1-flash, sol gpt-5.6-sol; claude CLI 2.1.289; 9router đang chạy port 20128).

## Decisions Locked
Xem brainstorm §10.

## Out of Scope
Xem brainstorm §11.

## Success Criteria (Plan-Level)
- [ ] Phase 1 chạy thật kênh F: 24 thread vào SQLite, mỗi comment có classification + video context level.
- [ ] Phase 2: DRAFT_REVIEW.txt cho kênh F; anh chấm được; HOSTILE = template; UNRESOLVED đủ field.
- [ ] 0 reply gửi đi cho tới khi anh authorize OAuth và bật 3 kill switch.

## Next Step
Code phase 1 + smoke test trên kênh F.
