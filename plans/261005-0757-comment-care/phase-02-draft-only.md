---
phase: 2
title: "Policy + templates + generator + rule QC + judge + DRAFT_REVIEW + review CLI (draft_only)"
status: completed
priority: P1
effort: "1.5d"
dependencies: [1]
completed: 2026-10-05
smoke_test: "PASS 2026-10-05 — `cc.py run --channel F --mode draft_only` ×2: 10 pending → 9 draft WOULD_REPLY + 1 NEEDS_HUMAN_REVIEW (judge FAIL tiêu chí 6/8) + 1 UNCLEAR 「再雇用」 + 1 QUESTION_FACTUAL SKIP; generator claude-opus-5-5 24 lần (227s), judge gpt-5.6-sol 24 lần (276s), classify gemini 12 lần; GRIEF secondary → footer bỏ + 2 judge PASS; 0 draft chứa tiếng Việt/blocklist; 22 unit test OK; 0 reply gửi (sender chặn: không token, mode draft_only). Chờ anh chấm DRAFT_REVIEW.txt"
---

## Overview
Từ classification ra quyết định theo `policy_table.yaml`, soạn reply (template hoặc LLM), gắn footer theo policy, QC rule + judge khác họ,
xuất `DRAFT_REVIEW.txt` + `UNRESOLVED_COMMENTS.txt` + `HIGH_RISK.txt`. Anh ghi APPROVE/EDIT/REJECT vào file, `cc.py review` đọc lại.

## Context Links
spec mục G (policy), H (style), I (sensitive), K (generation), L (judge), M (footer), Q–R (report).

## Requirements
Functional: 21 category → decision; HOSTILE deterministic; GRIEF 2 judge; regen ≤ 2; footer BC; không @, không emoji.
Non-functional: temperature classify 0.1 / generate 0.3; policy_version + prompt_version lưu mỗi draft.

## Related Code Files
Create: `policy/policy_table.yaml`, `policy/ja_style_guide.md`, `policy/blocklist_ja.txt`, `templates/ja/templates.yaml`,
`prompts/v1/generate.system.md`, `prompts/v1/judge.system.md`, `src/comment_care/{policy,templates,generator,qc_rules,judge,review}.py`,
`tests/test_policy.py`, `tests/test_qc_rules.py`, `tests/test_templates.py`.

## Acceptance Criteria
- [ ] CASE 3 (hostile) → final_text == template, không footer.
- [ ] CASE 9/10 (tiếng Việt / câu xấc) → QC FAIL, không vào DRAFT_REVIEW phần WOULD_REPLY.
- [ ] CASE 1 「再雇用」 → UNRESOLVED.
- [ ] DRAFT_REVIEW.txt có đủ COMMENT / CATEGORY / PROPOSED REPLY / CONFIDENCE / ACTION / DRAFT_ID.

## Smoke Test
`py -3.13 ...\cc.py run --channel F --mode draft_only` → file `reports\comment_care\<ngày>\F-teinengo-real\DRAFT_REVIEW.txt`;
unit tests `py -3.13 -m unittest discover -s comment_care\tests` pass.
