---
title: YouTube Comment Care (chăm sóc bình luận tiếng Nhật, policy-driven)
date: 2026-10-05
status: approved
type: brainstorm
next: plan.md
---

# Brainstorm summary — Comment Care

> Bản đầy đủ 26 mục A–Z (taxonomy, policy, model routing, DB, rollout, acceptance tests) nằm ở
> `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\docs\superpowers\specs\2026-10-05-youtube-comment-care-design.md`.
> File này chỉ đóng băng quyết định sau khi anh duyệt ngày 2026-10-05 ("cho phép triển khai đến khi hoàn thiện").

## 1. Problem Statement
Các kênh YouTube tiếng Nhật (người xem 60–80 tuổi) đang nhận bình luận kể trải nghiệm thật về 定年・再雇用・年金. Chủ kênh không đủ sức
đọc và trả lời từng bình luận một cách chân thành. Cần một hệ thống đọc comment → hiểu nội dung video + comment → phân loại → quyết định theo
policy → soạn reply tiếng Nhật lịch sự → QC → (giai đoạn đầu) đưa anh duyệt bằng file TXT. Không phải bot trả lời 100%.

## 2. Requirements (Approved)
Functional: fetch comment theo kênh; đọc nội dung video (title/description API + thư mục tập trong `h2dev\assets` hoặc
`h2dev\FlowHandoff_local\jobs`) TRƯỚC khi soạn; 21 category; policy deterministic; template cho HOSTILE/GRATITUDE; LLM cho EXPERIENCE/GRIEF;
rule QC + judge khác họ; `UNRESOLVED_COMMENTS.txt`; `DRAFT_REVIEW.txt` để anh APPROVE/EDIT/REJECT; audit trail SQLite; multi-channel isolation.
Non-functional: 0 reply gửi đi khi chưa có OAuth + 3 kill switch; fail closed; token tiết kiệm (không full transcript); file ≤ ~200 dòng.

## 3. Tech Stack (Approved)
Python 3.13 · SQLite · PyYAML · YouTube Data API v3 (API key có sẵn ở `E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env`) ·
LLM qua module h2dev có sẵn: `llm_client.py` (gemini-3.8-flash ramclouds/ns24, deepseek), `claude_p_bridge.py` (Opus 5.5 qua `claude -p`),
`sol_client.py` (gpt-5.6-sol judge) · Sheets service account `D:\CLAUDE\credentials\google-sheets-key.json` (chỉ đọc cột C/L để map video→tập).

## 4. Evaluated Approaches
| Approach | Pros | Cons | Decision |
|---|---|---|---|
| A. Data API (đọc bằng key, gửi bằng OAuth force-ssl) | 1 unit/100 thread, có reply id, idempotent, quota rõ | Phải authorize OAuth từng Gmail; consent Testing hết hạn 7 ngày | **Selected** (gửi ở Phase 2b, chờ anh authorize) |
| B. Studio browser automation (GPM) | Không cần OAuth | Fragile, không có reply id, dễ duplicate, chiếm profile | Rejected (chỉ fallback) |
| C. LLM tự quyết toàn bộ | Ít code | Không kiểm soát được HOSTILE/GRIEF, không audit | Rejected |
| D. Policy engine + LLM hiểu/soạn + judge khác họ | Policy thắng model, audit được | Nhiều file hơn | **Selected** |

## 5. Final Architecture
Xem diagram mục K của spec. Tóm tắt: `fetch → store → prefilter → classify(gemini) → policy(yaml) → template | generate(opus) → footer →
rule QC → judge(sol) → gate → DRAFT_REVIEW / UNRESOLVED / report`.

## 6. Project Structure
`E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\{config,policy,prompts\v1,templates\ja,src\comment_care,state,tests}` +
`reports\comment_care\<ngày>\<lane>\`.

## 7. Implementation Phasing
| Phase | Deliverable |
|---|---|
| 1 | Fetch + store + context builder + classifier + report (fetch_only) — chạy thật trên kênh F |
| 2 | Policy + templates + generator + rule QC + judge + DRAFT_REVIEW/review — draft_only, anh chấm |
| 2b | OAuth per kênh (anh authorize) + sender idempotent + reconcile, kill switch |
| 3–6 | Shadow 100 comment → auto LOW cap 5 → mở rộng → daily |

## 8. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Kênh Satori đã bị Google đình chỉ (phát hiện 2026-10-05) | Pilot đổi sang lane F (定年後のリアル, 8 video, 24 thread) |
| Model bịa nội dung video | Context bắt buộc từ assets/jobs; không có context → LLM category bị SKIP |
| Reply thiếu lịch sự | Blocklist + judge 11 tiêu chí + template cho HOSTILE |
| Duplicate khi gửi | idempotency key + SENDING→SENT + reconcile (Phase 2b) |
| Lộ key | Không hardcode; key đọc từ env/.env ngoài repo; state/reports gitignore |

## 9. Success Criteria
Phase 1: fetch toàn bộ 24 thread kênh F, 0 lỗi, phân loại ra 21 category có confidence. Phase 2: ≥ 90% draft nhóm LOW được anh APPROVE
không sửa; 0 draft chứa tiếng Việt/blocklist; HOSTILE luôn = template; mọi comment UNCLEAR có mặt trong UNRESOLVED với đủ 11 field.

## 10. Decisions Locked
1. Gửi reply bằng Data API OAuth (chưa authorize; sender bị chặn tới khi có token). 2. Footer policy mặc định **BC** (rotate 3 bản ngắn, bỏ ở
HOSTILE/GRIEF/HEALTH/CRISIS/follow-up lần 2) — đổi được trong `channels.yaml`. 3. HOSTILE template = 「ご意見をお寄せいただき、ありがとうございます。」,
không footer. 4. Emoji = 0. 5. Không @username. 6. `owner_facts` trống. 7. Pilot = lane F. 8. Generator mạnh tạm = `claude-opus-5-5`, chốt lại sau
benchmark. 9. Không sửa file nào trong h2dev. 10. Retention raw comment 90 ngày.

## 11. Out of Scope (V1)
Audience insight weekly; fact-check bằng web; xoá/ẩn/report spam; GUI; scheduler (anh tự lập lịch); reply lần 2 trở đi trong cùng thread;
comment heldForReview.

## 12. Next Step
`plan.md` → `phase-01-fetch-classify.md`.
