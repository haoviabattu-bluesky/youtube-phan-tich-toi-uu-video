# 05 — AI ANALYSIS, CURRENT STATE

Audit only.

---

## 1. HEADLINE FINDING

**The 05:00 pipeline uses no AI at all.**

```
grep -n "sol_client\|gemini\|claude\|llm" tools/daily_0500_run.py tools/daily_parallel.py \
        tools/sheet_metrics_sync.py tools/studio_collect.py tools/studio_daily.py tools/daily_sheet.py
→ only false positives on the word "fullmatch"
```

No model call, no prompt, no token, no API key is touched by the scheduled job. Its "analysis" is a
**deterministic threshold rule** (`tools/daily_k_rules.py`), 37 lines long.

AI exists in the repository, but in **two manual, out-of-band tools** and in an unrelated module:

| Where | Model | Triggered by | Output |
|---|---|---|---|
| `tools/sol_packaging_review.py` | `GPT-5.6-sol` via `h2dev/pipeline/sol_client.py` | **manual CLI, one video at a time** | `reports/<vid>/sol_packaging_review.md` |
| `comment_care/` | gemini-3.8-flash (classify), sol (judge) | separate scheduled/manual subsystem | reply drafts in SQLite |
| `niche_watch/judge.py` | `vision_model: gemini-3.8-flash` (`niche_watch/config.json:12`) | evening browsing tool — **task not registered** | in-memory filtering |
| `viral_hunt/analyze.py` | optional `--no-llm` flag | task **Disabled** | `reports/viral_hunt/` |

---

## 2. THE ACTUAL "ANALYSIS" — A THRESHOLD, NOT A MODEL

`tools/daily_k_rules.py:21-31`:

```python
THRESHOLD = 2.5

def k_note(hours, views, ctr_total, ctr_24h, imp_24h):
    if ctr_24h is None or ctr_24h < THRESHOLD:
        val = vn_pct(ctr_24h) if ctr_24h is not None else f"— ({vn_int(imp_24h or 0)} hiển thị)"
        return f"CTR 24h={val}, YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ", True      # → paint row yellow
    return (f"{int(hours)}h · {vn_int(views)} view · CTR tổng {vn_pct(ctr_total)} · CTR 24h {vn_pct(ctr_24h)}"
            f" · {vn_int(imp_24h)} lượt hiển thị/24h. ĐỂ NGUYÊN (CTR 24h đạt, đang được phân phối)."), False
```

Inputs: `hours`, `views`, `ctr_total`, `ctr_24h`, `imp_24h`. Output: one Vietnamese sentence + a boolean.
No comparison to the previous day, no comparison to peers, no traffic-source context, no retention.

### Inputs the rule *receives* but does not use
`views` and `ctr_total` are interpolated into the "healthy" message only — they never affect the decision.
So a video with 24 300 lifetime views and one with 3 views get the same verdict if `ctr_24h` is equal.

---

## 3. WHAT THE TASK ASKS, FIELD BY FIELD

| Question | Answer | Evidence |
|---|---|---|
| Which AI is used? | **None in the scheduled pipeline.** Manual tools: `GPT-5.6-sol`, `gemini-3.8-flash`, `claude-opus-5-5` (disabled), `deepseek-v4.1-flash` (fallback) | §1; `comment_care/config/settings.yaml:30-38` |
| What data does the LLM receive? | In `sol_packaging_review.py`: a **hand-typed metrics string** (`--metrics "301 impressions / CTR 2.3% / 13 views / 108h"`), the current title, the winner video's title+metrics, and up to `--script-limit` chars of `script.txt` (default truncated, `:200-203`) | `sol_packaging_review.py:9-16, 205-216` |
| Where are prompts stored? | **Inline in the Python file** as module constants `PROMPT_TITLE` / `PROMPT_THUMB` (`sol_packaging_review.py:77` region). Only `comment_care/prompts/v1/*.md` uses external prompt files with a version key. | |
| Report granularity | **One video per invocation**, comparing against **one** manually-named winner video. No per-channel, no system-wide report. | `sol_packaging_review.py:218-227` |
| Does AI compare to the previous day? | **No.** The metrics string is whatever the human typed; no yesterday/last-run value is loaded. | |
| Does AI compare at equal video age? | **Only if the human types ages into `--metrics` and `--winner-metrics`.** The tool itself does not compute or enforce age matching. The SOP rule (A@48h vs B@48h) lives in `YOUTUBE_POSTPUBLISH_ANALYTICS_SOP.md`, not in code. | |
| Does it evaluate CTR by traffic source? | **No.** Traffic-source percentages are not in the prompt template; the human may paste them into `--metrics` as free text. | |
| Does it analyse hook / title / thumbnail? | **Title and thumbnail: yes** (two separate prompts, thumbnail sent as an A\|B composite image, `gheph_ab()` `:80-100`). **Hook: no** — the hook would live in the first seconds of `script.txt`, which is truncated to `--script-limit`, and no retention input is given. | `:205-216` |
| Does it keep past recommendations and track outcomes? | **No.** Each run writes a fresh `reports/<vid>/sol_packaging_review.md`; nothing records "we changed the title on X, CTR moved from a→b". The `post_change_*` columns exist in the CSV schema and are **0/174 filled**. | `03_METRIC_INVENTORY.md` |
| Does it compute cost/tokens? | **Partially.** `sol_client.chat()` returns a usage dict which is **printed** (`print("   tokens:", u1)`) and then discarded — not stored. `comment_care` *does* store it: `llm_calls(tokens_in, tokens_out, elapsed_s)` = 123 rows. | `sol_packaging_review.py:209,216`; SQLite schema |

---

## 4. THE ONLY REAL "KNOWLEDGE" ARTEFACT

`reports/yCSzCQN_VsE/sol_packaging_review.md` (1 file, 2026-09-23) is the sole surviving AI analysis. Its
structure is worth noting because it is exactly the shape YIE wants to automate:

```
# Sol packaging review — <video_id>
- Ngày chấm: 2026-09-23 14:37
- Số liệu video flop: 108h sau khi dang: 301 thumbnail impressions, CTR 2.3%, 13 views,
  10 unique viewers, AVD 1:04 / video 31:25, APV 3.4%, Suggested 76.9% - Browse 15.4%,
  recommendation 91.3%, impressions da dung tang
- Tiêu đề đang dùng: …
- Đối chiếu video thắng: 75zDHRIaiYM — 「…」 (84h …, CTR 7.0%, 1300 views, …)
## 1. TIÊU ĐỀ      (scored 4/10, with reasoning)
## 2. THUMBNAIL
```

It contains: age, impressions, CTR, views, unique viewers, AVD **with video length**, APV, traffic mix,
recommendation %, distribution trend, and an explicit same-age winner comparison. **All of that data was
assembled by hand from the CSV.** Nothing in the repo can regenerate it.

---

## 5. WHAT "AI" WOULD NEED TO BE ADDED FOR THE YIE VISION

The YIE goals (compare episodes within a lane, build a lane knowledge base, propose topics/hooks/titles/
thumbnails) require inputs that today's pipeline does not produce:

| YIE need | Available today | Gap |
|---|---|---|
| Same-age peer comparison | Sheet `N` + `P`/`Q` give age and CTR per video → **possible** | needs a query layer; no code exists |
| Retention-based hook judgement | `ret_30s` in stale CSV only | must be collected daily |
| Traffic-mode context (browse vs suggested vs search) | stale CSV only | must be collected daily |
| AVD vs video length | stale CSV only | must be collected daily |
| Episode → script / hook text | folder link only | see `06` |
| Record of past recommendation + outcome | **nothing** | `post_change_*` columns empty; no history table |
| Token/cost accounting | only `comment_care.llm_calls` | no accounting for any metrics-related LLM call |

---

## 6. PROMPT / MODEL INVENTORY (for completeness — none of it is wired to the 05:00 job)

| File | Model id | Purpose |
|---|---|---|
| `comment_care/config/settings.yaml:30` | `gemini-3.8-flash` (ramclouds → ns24) | comment classification |
| `comment_care/config/settings.yaml:31` | `deepseek-v4.1-flash` | classify fallback |
| `comment_care/config/settings.yaml:32` | `claude-opus-5-5` | strong reply generator — **`generate_use_claude: false`** (quota exhausted, must not be re-enabled without approval) |
| `comment_care/config/settings.yaml:35` | `gemini-3.8-flash` | cheap generator chain |
| `comment_care/config/settings.yaml:36` | `sol` (gpt-5.6-sol) | judge |
| `niche_watch/config.json:12` | `gemini-3.8-flash` | thumbnail/serp vision filter |
| `tools/sol_packaging_review.py:1` | `GPT-5.6-sol` | title + thumbnail review of a flopped video |

No API keys were read, printed or copied during this audit.
