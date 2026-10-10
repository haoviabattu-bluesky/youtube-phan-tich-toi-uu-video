---
phase: 1
title: "Fetch + store + video context + classifier + report (fetch_only)"
status: completed
priority: P1
effort: "1d"
dependencies: []
completed: 2026-10-05
smoke_test: "PASS 2026-10-05 08:15 — `cc.py run --channel F --mode fetch_only`: 8 video, 49 comment rows (24 thread + 25 reply), quota 9 unit, 12 pending → 12 classification gemini-3.8-flash (5 EXPERIENCE, 2 VIEWER_TO_VIEWER, 1 UNCLEAR 「再雇用」 u=0.20, 1 QUESTION_FACTUAL, 1 DISAGREEMENT, 1 CRITICISM, 1 FOLLOW_UP); 5/5 video map được ep_dir qua Sheet cột C/L → context L3; COMMENT_REPORT + UNRESOLVED (2) ghi đúng format; 22 unit test OK"
---

## Overview
Luồng dọc nhỏ nhất chứng minh giả thuyết rủi ro nhất: đọc được toàn bộ comment kênh mình bằng API key, map được video → thư mục tập để
hiểu nội dung, và classifier gemini trả JSON đúng khuôn với confidence. Chưa soạn reply.

## Context Links
plan.md · spec mục E (fetch), F (taxonomy), J (context), O (DB).

## Requirements
Functional: `cc.py run --channel F --mode fetch_only` → SQLite có channels/videos/comments/classifications; `COMMENT_REPORT.txt`.
Non-functional: ≤ 2 unit/video; không gọi LLM cho comment của chính kênh; context_level ghi rõ L1/L3/L3J/NONE.

## Architecture
`comment_care/src/comment_care/{config,store,yt_api,context,prefilter,llm,classifier,report,pipeline,cli}.py` + `cc.py` launcher.

## Related Code Files
Create: các file trên + `config/channels.yaml`, `config/settings.yaml`, `prompts/v1/classify.system.md`.
Modify: `.gitignore` (state/, reports/comment_care/).

## Acceptance Criteria
- [ ] 8 video kênh F có `ep_dir` trỏ đúng `E:\CLAUDE\YOUTUBE\h2dev\assets\teinengo-real\epNN-*` (qua sheet cột C/L).
- [ ] 24 thread + replies vào DB; 4 comment owner top-level và 14 owner reply đánh dấu `is_owner=1`.
- [ ] Mỗi comment pending có 1 dòng classifications với primary ∈ 21 category, 2 confidence.

## Smoke Test
Input: `py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\cc.py run --channel F --mode fetch_only`
Output mong đợi: in bảng category count, quota used, đường dẫn COMMENT_REPORT.txt.
